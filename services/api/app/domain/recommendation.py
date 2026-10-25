from datetime import datetime

from sqlalchemy import JSON, BigInteger, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.time import utcnow
from app.domain.enums import RecommendationStatus
from app.domain.risk import RiskAssessment
from app.domain.student import Student
from app.domain.types import BigIntPK


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    assessment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("risk_assessments.id", ondelete="CASCADE"), unique=True
    )
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    period_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("academic_periods.id"))
    status: Mapped[RecommendationStatus] = mapped_column(
        Enum(RecommendationStatus, name="recommendation_status"),
        default=RecommendationStatus.PENDING_REVIEW,
    )
    parent_items: Mapped[list[str]] = mapped_column(JSON)
    teacher_items: Mapped[list[str]] = mapped_column(JSON)
    reviewed_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None]
    sent_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    student: Mapped[Student] = relationship()
    assessment: Mapped[RiskAssessment] = relationship()


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (UniqueConstraint("assessment_id", "recipient_id"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    assessment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("risk_assessments.id", ondelete="CASCADE")
    )
    recipient_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    is_read: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    assessment: Mapped[RiskAssessment] = relationship()
