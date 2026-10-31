from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ModelVersionView(BaseModel):
    version: str
    trained_at: str | None
    active: bool
    synthetic_samples: int | None
    school_samples: int | None
    school_dropouts: int | None
    # Score on held-out real cases of this school (school-trained versions only).
    school_holdout: dict[str, Any] | None
    trained_by: str | None
    activated_by: str | None
    activated_at: datetime | None


class TrainingReadiness(BaseModel):
    labeled: int
    dropouts: int
    min_labeled: int
    min_dropouts: int
    can_train: bool


class ModelsOverview(BaseModel):
    versions: list[ModelVersionView]
    training: TrainingReadiness


class TrainingResult(BaseModel):
    candidate: ModelVersionView
    # The active model scored on the same held-out cases.
    active_on_holdout: dict[str, Any] | None
