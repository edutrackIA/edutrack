from datetime import datetime

from sqlalchemy import BigInteger, Enum, ForeignKey, SmallInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utcnow
from app.domain.enums import ParentEducation
from app.domain.types import BigIntPK


class FamilySurvey(Base):
    __tablename__ = "family_surveys"
    __table_args__ = (UniqueConstraint("student_id", "period_id"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    period_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("academic_periods.id"))
    responder_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    study_hours_week: Mapped[int] = mapped_column(SmallInteger)
    parent_education: Mapped[ParentEducation] = mapped_column(
        Enum(ParentEducation, name="parent_education")
    )
    home_internet: Mapped[bool]
    has_study_device: Mapped[bool]
    family_communication: Mapped[int] = mapped_column(SmallInteger)
    student_works: Mapped[bool]
    household_size: Mapped[int] = mapped_column(SmallInteger)
    submitted_at: Mapped[datetime] = mapped_column(default=utcnow)
