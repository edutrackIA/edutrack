from datetime import datetime
from typing import Any, Self

from pydantic import BaseModel, Field, model_validator

from app.domain import RiskAssessment, RiskLevel
from app.services.risk.features import FEATURE_LABELS


class RiskFactor(BaseModel):
    feature: str
    label: str
    value: Any
    contribution: float


class RiskAssessmentResponse(BaseModel):
    id: int
    period_id: int
    probability: float
    level: RiskLevel
    model_version: str
    top_factors: list[RiskFactor]
    created_at: datetime

    @classmethod
    def from_model(cls, assessment: RiskAssessment) -> "RiskAssessmentResponse":
        return cls(
            id=assessment.id,
            period_id=assessment.period_id,
            probability=assessment.probability,
            level=assessment.level,
            model_version=assessment.model_version,
            top_factors=[
                RiskFactor(
                    feature=factor["feature"],
                    label=FEATURE_LABELS.get(factor["feature"], factor["feature"]),
                    value=factor["value"],
                    contribution=factor["contribution"],
                )
                for factor in assessment.top_factors
            ],
            created_at=assessment.created_at,
        )


class RunRiskRequest(BaseModel):
    period_id: int
    classroom_id: int | None = None


class SkippedStudent(BaseModel):
    student_id: int
    code: str
    full_name: str
    reason: str


class RunRiskResponse(BaseModel):
    evaluated: int
    skipped: int
    model_version: str | None
    by_level: dict[RiskLevel, int]
    skipped_students: list[SkippedStudent]


class RiskThresholds(BaseModel):
    medium_from: float = Field(gt=0, lt=1)
    high_from: float = Field(gt=0, lt=1)

    @model_validator(mode="after")
    def medium_below_high(self) -> Self:
        if self.medium_from >= self.high_from:
            raise ValueError("medium_from must be lower than high_from")
        return self
