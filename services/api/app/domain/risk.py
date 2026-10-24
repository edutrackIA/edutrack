from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, Enum, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utcnow
from app.domain.enums import RiskLevel
from app.domain.types import BigIntPK

DEFAULT_MEDIUM_FROM = 0.40
DEFAULT_HIGH_FROM = 0.70


class RiskThreshold(Base):
    __tablename__ = "risk_thresholds"

    institution_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("institutions.id"), primary_key=True
    )
    medium_from: Mapped[float] = mapped_column(Float)
    high_from: Mapped[float] = mapped_column(Float)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    def classify(self, probability: float) -> RiskLevel:
        if probability >= self.high_from:
            return RiskLevel.HIGH
        if probability >= self.medium_from:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    __table_args__ = (UniqueConstraint("student_id", "period_id", "model_version"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    period_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("academic_periods.id"))
    probability: Mapped[float] = mapped_column(Float)
    level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel, name="risk_level"))
    model_version: Mapped[str] = mapped_column(String(50))
    top_factors: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
