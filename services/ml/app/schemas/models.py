from typing import Any

from pydantic import BaseModel, Field

from app.schemas.prediction import Features


class TrainingRow(BaseModel):
    features: Features
    dropout: bool


class SchoolTrainingRequest(BaseModel):
    rows: list[TrainingRow] = Field(min_length=1, max_length=50_000)
    seed: int = 42


class ModelVersion(BaseModel):
    version: str
    trained_at: str | None
    active: bool
    metrics: dict[str, Any]
    dataset: dict[str, Any]
    # Score on the school's held-out real cases (only for school-trained versions).
    school_holdout: dict[str, Any] | None = None


class SchoolTrainingResponse(BaseModel):
    candidate: ModelVersion
    # The active model scored on the same held-out cases, for a fair comparison.
    active_on_holdout: dict[str, Any] | None
