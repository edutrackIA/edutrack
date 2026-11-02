"""Forgot-password links and password changes.

Requesting a reset never reveals whether an email exists. Any password change closes
every open session, so a stolen session does not survive the owner fixing their password.
"""

from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import UnprocessableError
from app.core.security import hash_password, new_url_token, password_problems, verify_password
from app.core.time import utcnow
from app.domain import Invitation, TokenPurpose, User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.services.invitation_service import InvitationService
from app.services.notifications.delivery import deliver
from app.services.notifications.email_sender import EmailSender
from app.services.notifications.templates import PasswordResetEmail

RESET_MINUTES = 60


class PasswordService:
    def __init__(self, db: Session, sender: EmailSender | None = None) -> None:
        self.db = db
        self.sender = sender
        self.links = InvitationService(db, sender)
        self.tokens = RefreshTokenRepository(db)

    def request_reset(self, email: str) -> None:
        user = UserRepository(self.db).get_by_email(email.strip().lower())
        if user is None or not user.is_active:
            return
        if not user.has_access:
            # Never accepted the invitation: a fresh invitation is what they need.
            self.links.invite(user)
            return

        now = utcnow()
        for previous in self.links.open_links(user.id, TokenPurpose.PASSWORD_RESET):
            previous.revoked_at = now
        raw, token_hash = new_url_token()
        self.db.add(
            Invitation(
                user_id=user.id,
                token_hash=token_hash,
                purpose=TokenPurpose.PASSWORD_RESET,
                expires_at=now + timedelta(minutes=RESET_MINUTES),
            )
        )
        self.db.commit()
        if self.sender is not None:
            email_message = PasswordResetEmail(
                recipient_name=user.full_name.split()[0],
                link=f"{get_settings().portal_url}/restablecer/{raw}",
                valid_minutes=RESET_MINUTES,
            )
            deliver(
                self.sender,
                to=user.email,
                subject=email_message.subject,
                text=email_message.text(),
                html=email_message.html(),
            )

    def reset_target(self, raw_token: str) -> User:
        return self.links.get_usable(raw_token, TokenPurpose.PASSWORD_RESET).user

    def reset(self, raw_token: str, password: str) -> None:
        link = self.links.get_usable(raw_token, TokenPurpose.PASSWORD_RESET)
        self._set_password(link.user, password)
        link.accepted_at = utcnow()
        self.db.commit()

    def change(self, user: User, current_password: str, new_password: str) -> None:
        if user.password_hash is None or not verify_password(current_password, user.password_hash):
            raise UnprocessableError("The current password is wrong", code="WRONG_PASSWORD")
        if verify_password(new_password, user.password_hash):
            raise UnprocessableError(
                "La nueva contraseña debe ser distinta de la actual", code="WEAK_PASSWORD"
            )
        self._set_password(user, new_password)
        self.db.commit()

    def _set_password(self, user: User, password: str) -> None:
        problems = password_problems(password)
        if problems:
            raise UnprocessableError(". ".join(problems), code="WEAK_PASSWORD")
        user.password_hash = hash_password(password)
        self.tokens.revoke_all_for_user(user.id, utcnow())
