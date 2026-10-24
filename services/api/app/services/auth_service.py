from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import UnauthorizedError
from app.core.security import (
    create_access_token,
    dummy_password_hash,
    generate_refresh_token,
    hash_token,
    verify_password,
)
from app.core.time import utcnow
from app.domain import RefreshToken, User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.tokens = RefreshTokenRepository(db)
        self.settings = get_settings()

    def login(self, email: str, password: str) -> TokenResponse:
        user = self.users.get_by_email(email)
        if user is None:
            verify_password(password, dummy_password_hash())
            raise self._invalid_credentials()
        if not verify_password(password, user.password_hash) or not user.is_active:
            raise self._invalid_credentials()

        tokens = self._issue_tokens(user)
        self.db.commit()
        return tokens

    def refresh(self, raw_token: str) -> TokenResponse:
        stored = self.tokens.get_by_hash(hash_token(raw_token))
        if stored is None:
            raise UnauthorizedError("Invalid refresh token", code="INVALID_REFRESH_TOKEN")

        now = utcnow()
        if stored.revoked_at is not None:
            # A revoked token being reused suggests it was stolen: end every session.
            self.tokens.revoke_all_for_user(stored.user_id, now)
            self.db.commit()
            raise UnauthorizedError("Refresh token reused", code="INVALID_REFRESH_TOKEN")
        if stored.expires_at <= now:
            raise UnauthorizedError("Refresh token expired", code="INVALID_REFRESH_TOKEN")

        user = self.users.get_by_id(stored.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("Invalid refresh token", code="INVALID_REFRESH_TOKEN")

        stored.revoked_at = now
        tokens = self._issue_tokens(user)
        self.db.commit()
        return tokens

    def logout(self, user: User, raw_token: str) -> None:
        stored = self.tokens.get_by_hash(hash_token(raw_token))
        if stored is not None and stored.user_id == user.id and stored.revoked_at is None:
            stored.revoked_at = utcnow()
            self.db.commit()

    def _issue_tokens(self, user: User) -> TokenResponse:
        access_token = create_access_token(
            user_id=user.id, role=user.role.value, institution_id=user.institution_id
        )
        raw_refresh = generate_refresh_token()
        self.tokens.add(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_token(raw_refresh),
                expires_at=utcnow() + timedelta(days=self.settings.refresh_token_ttl_days),
            )
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            expires_in=self.settings.access_token_ttl_minutes * 60,
        )

    @staticmethod
    def _invalid_credentials() -> UnauthorizedError:
        return UnauthorizedError("Invalid email or password", code="INVALID_CREDENTIALS")
