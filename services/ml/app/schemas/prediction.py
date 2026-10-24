from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ParentEducation(StrEnum):
    NONE = "NONE"
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    TECHNICAL = "TECHNICAL"
    UNIVERSITY = "UNIVERSITY"


class Features(BaseModel):
    avg_score: float = Field(ge=0, le=20)
    failed_subjects: int = Field(ge=0)
    score_trend: float
    attendance_rate: float = Field(ge=0, le=1)
    late_count: int = Field(ge=0)
    behavior_rating: int = Field(ge=1, le=5)
    study_hours_week: int = Field(ge=0, le=60)
    parent_education: ParentEducation
    home_internet: bool
    has_study_device: bool
    family_communication: int = Field(ge=1, le=5)
    student_works: bool
    household_size: int = Field(ge=1, le=20)


class PredictionRequest(BaseModel):
    student_id: int
    features: Features


class BatchPredictionRequest(BaseModel):
    items: list[PredictionRequest] = Field(min_length=1, max_length=500)


class Factor(BaseModel):
    feature: str
    value: float | int | bool | str
    contribution: float


class Prediction(BaseModel):
    student_id: int
    probability: float
    model_version: str
    top_factors: list[Factor]


class BatchPredictionResponse(BaseModel):
    model_version: str
    items: list[Prediction]


class ModelMetrics(BaseModel):
    f1: float
    roc_auc: float
    recall: float
    precision: float


class ModelInfo(BaseModel):
    version: str
    algorithm: str
    trained_at: datetime
    features: list[str]
    metrics: ModelMetrics
