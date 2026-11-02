from datetime import date

from pydantic import BaseModel

from app.domain import ExitReason, RiskLevel


class PerformanceMetrics(BaseModel):
    true_positives: int
    false_negatives: int
    false_positives: int
    true_negatives: int
    # Of the students who dropped out, how many had been alerted.
    recall: float | None
    # Of the alerts, how many ended in a dropout.
    precision: float | None


class DropoutCase(BaseModel):
    student_id: int
    code: str
    full_name: str
    exit_date: date | None
    exit_reason: ExitReason | None
    last_level: RiskLevel
    last_probability: float
    alerted: bool


class ModelPerformance(BaseModel):
    window_days: int
    model_versions: list[str]
    labeled: int
    dropouts: int
    pending: int
    min_labeled: int
    min_dropouts: int
    # Null until there are enough real outcomes to say something reliable.
    metrics: PerformanceMetrics | None
    cases: list[DropoutCase]
