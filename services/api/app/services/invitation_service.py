from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ConflictError, NotFoundError, UnprocessableError
from app.core.security import hash_password, hash_url_token, new_url_token, password_problems
from app.core.time import utcnow
from app.domain import Guardianship, Institution, Invitation, Student, User
from app.services.notifications.delivery import deliver
from app.services.notifications.email_sender import EmailSender
from app.services.notifications.templates import InvitationEmail

INVITATION_DAYS = 7


class InvitationService:
    def __init__(self, db: Session, sender: EmailSender | None = None) -> None:
        self.db = db
        self.sender = sender

    def invite(self, user: User) -> bool:
        """Revoke previous links, create a new one and email it. Returns whether it was sent."""
        if user.has_access:
            raise ConflictError("The user already has access", code="ALREADY_HAS_ACCESS")
        now = utcnow()
        for previous in self._open_invitations(user.id):
            previous.revoked_at = now

        raw, token_hash = new_url_token()
        self.db.add(
            Invitation(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=now + timedelta(days=INVITATION_DAYS),
            )
        )
        self.db.commit()
        return self._send(user, raw)

    def get_usable(self, raw_token: str) -> Invitation:
        invitation = self.db.scalar(
            select(Invitation).where(Invitation.token_hash == hash_url_token(raw_token))
        )
        if invitation is None:
            raise NotFoundError("Invitation not found", code="INVITATION_NOT_FOUND")
        if not invitation.is_usable(utcnow()):
            raise ConflictError("The invitation is no longer valid", code="INVITATION_EXPIRED")
        return invitation

    def accept(self, raw_token: str, password: str) -> User:
        invitation = self.get_usable(raw_token)
        problems = password_problems(password)
        if problems:
            raise UnprocessableError(". ".join(problems), code="WEAK_PASSWORD")

        invitation.accepted_at = utcnow()
        invitation.user.password_hash = hash_password(password)
        self.db.commit()
        return invitation.user

    # --- Internos -------------------------------------------------------------------

    def _open_invitations(self, user_id: int) -> list[Invitation]:
        return list(
            self.db.scalars(
                select(Invitation).where(
                    Invitation.user_id == user_id,
                    Invitation.accepted_at.is_(None),
                    Invitation.revoked_at.is_(None),
                )
            )
        )

    def _send(self, user: User, raw_token: str) -> bool:
        if self.sender is None:
            return False
        institution = self.db.get(Institution, user.institution_id)
        students = self.db.scalars(
            select(Student)
            .join(Guardianship, Guardianship.student_id == Student.id)
            .where(Guardianship.guardian_id == user.id)
            .order_by(Student.first_name)
        ).all()
        email = InvitationEmail(
            guardian_name=user.full_name.split()[0],
            student_names=[student.first_name for student in students],
            institution_name=institution.name if institution else "Su colegio",
            link=f"{get_settings().portal_url}/invitacion/{raw_token}",
            valid_days=INVITATION_DAYS,
        )
        return deliver(
            self.sender, to=user.email, subject=email.subject, text=email.text(), html=email.html()
        )
