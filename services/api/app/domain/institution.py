from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.domain.types import BigIntPK


class Institution(Base):
    __tablename__ = "institutions"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    ugel: Mapped[str] = mapped_column(String(50))
    district: Mapped[str] = mapped_column(String(100))
