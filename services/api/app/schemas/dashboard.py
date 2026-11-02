from pydantic import BaseModel

from app.domain import RiskLevel


class ClassroomRiskSummary(BaseModel):
    classroom_id: int
    label: str
    evaluated: int
    low: int
    medium: int
    high: int


class FactorFrequency(BaseModel):
    feature: str
    label: str
    frequency: int


class StudentRiskItem(BaseModel):
    student_id: int
    code: str
    full_name: str
    classroom_id: int
    classroom: str
    level: RiskLevel
    probability: float


class DashboardSummary(BaseModel):
    period_id: int | None
    period_label: str | None
    total_students: int
    evaluated_students: int
    by_level: dict[RiskLevel, int]
    by_classroom: list[ClassroomRiskSummary]
    top_factors: list[FactorFrequency]
    students: list[StudentRiskItem]
