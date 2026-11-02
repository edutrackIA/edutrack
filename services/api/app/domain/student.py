from datetime import date

from sqlalchemy import BigInteger, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.domain.classroom import Classroom
from app.domain.enums import ExitReason, Sex, StudentStatus
from app.domain.types import BigIntPK
from app.domain.user import User


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    institution_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("institutions.id"))
    classroom_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("classrooms.id"))
    code: Mapped[str] = mapped_column(String(20), unique=True)
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    birth_date: Mapped[date]
    sex: Mapped[Sex] = mapped_column(Enum(Sex, name="student_sex"))
    status: Mapped[StudentStatus] = mapped_column(
        Enum(StudentStatus, name="student_status"), default=StudentStatus.ENROLLED
    )
    exit_date: Mapped[date | None]
    exit_reason: Mapped[ExitReason | None] = mapped_column(Enum(ExitReason, name="exit_reason"))
    exit_note: Mapped[str | None] = mapped_column(String(500))

    classroom: Mapped[Classroom] = relationship(back_populates="students")
    guardians: Mapped[list[User]] = relationship(secondary="guardianships", viewonly=True)

    @property
    def is_enrolled(self) -> bool:
        return self.status == StudentStatus.ENROLLED

    @property
    def full_name(self) -> str:
        return f"{self.last_name}, {self.first_name}"


class Guardianship(Base):
    __tablename__ = "guardianships"

    guardian_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id", ondelete="CASCADE"), primary_key=True
    )
    kinship: Mapped[str] = mapped_column("relationship", String(30))
