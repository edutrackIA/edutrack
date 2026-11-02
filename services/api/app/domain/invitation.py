from datetime import datetime

from sqlalchemy import BigInteger, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.time import utcnow
from app.domain.enums import TokenPurpose
from app.domain.types import BigIntPK
from app.domain.user import User


class Invitation(Base):
    """One-time link to set a password: an invitation (7 days) or a reset (1 hour).

    Only the SHA-256 of the token is stored: a database leak does not expose usable links.
    """

    __tablename__ = "invitations"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    purpose: Mapped[TokenPurpose] = mapped_column(
        Enum(TokenPurpose, name="token_purpose"), default=TokenPurpose.INVITATION
    )
    expires_at: Mapped[datetime]
    accepted_at: Mapped[datetime | None]
    revoked_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    user: Mapped[User] = relationship()

    def is_usable(self, now: datetime) -> bool:
        return self.accepted_at is None and self.revoked_at is None and self.expires_at > now
