from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.domain.types import BigIntPK
from app.domain.user import User

if TYPE_CHECKING:
    from app.domain.student import Student


class Classroom(Base):
    __tablename__ = "classrooms"
    __table_args__ = (UniqueConstraint("institution_id", "year", "grade", "section"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    institution_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("institutions.id"))
    tutor_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    year: Mapped[int] = mapped_column(SmallInteger)
    grade: Mapped[int] = mapped_column(SmallInteger)
    section: Mapped[str] = mapped_column(String(2))

    tutor: Mapped[User | None] = relationship()
    students: Mapped[list["Student"]] = relationship(back_populates="classroom")

    @property
    def label(self) -> str:
        return f"{self.grade}° {self.section}"
