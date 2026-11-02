from sqlalchemy import BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.domain.types import BigIntPK


class Subject(Base):
    """A course taught at a school. Each school names its own courses."""

    __tablename__ = "subjects"
    __table_args__ = (UniqueConstraint("institution_id", "name"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    institution_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("institutions.id"))
    name: Mapped[str] = mapped_column(String(80))
