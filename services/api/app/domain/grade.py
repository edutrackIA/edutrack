from sqlalchemy import BigInteger, ForeignKey, Numeric, SmallInteger, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.domain.subject import Subject
from app.domain.types import BigIntPK


class Grade(Base):
    __tablename__ = "grades"
    __table_args__ = (UniqueConstraint("student_id", "subject_id", "period_id"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    subject_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("subjects.id"))
    period_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("academic_periods.id"))
    score: Mapped[float] = mapped_column(Numeric(4, 2, asdecimal=False))

    subject: Mapped[Subject] = relationship(lazy="joined")


class BehaviorRecord(Base):
    __tablename__ = "behavior_records"
    __table_args__ = (UniqueConstraint("student_id", "period_id"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    period_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("academic_periods.id"))
    rating: Mapped[int] = mapped_column(SmallInteger)
    notes: Mapped[str | None] = mapped_column(Text)
