from datetime import datetime

from sqlalchemy import BigInteger, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.time import utcnow
from app.domain.enums import Role
from app.domain.institution import Institution
from app.domain.types import BigIntPK


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    institution_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("institutions.id"))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    # Null until an invited guardian creates their password.
    password_hash: Mapped[str | None] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(150))
    role: Mapped[Role] = mapped_column(Enum(Role, name="user_role"))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    institution: Mapped[Institution] = relationship()

    @property
    def has_access(self) -> bool:
        return self.password_hash is not None
