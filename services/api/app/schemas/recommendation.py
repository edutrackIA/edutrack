from datetime import datetime

from pydantic import BaseModel, Field

from app.domain import Alert, Recommendation, RecommendationStatus, RiskLevel
from app.schemas.student import StudentListItem


class RecommendationResponse(BaseModel):
    id: int
    student: StudentListItem
    period_id: int
    status: RecommendationStatus
    parent_items: list[str]
    teacher_items: list[str]
    reviewed_by: int | None
    reviewed_at: datetime | None
    sent_at: datetime | None
    created_at: datetime

    @classmethod
    def from_model(cls, recommendation: Recommendation) -> "RecommendationResponse":
        return cls(
            id=recommendation.id,
            student=StudentListItem.from_model(recommendation.student, recommendation.assessment),
            period_id=recommendation.period_id,
            status=recommendation.status,
            parent_items=recommendation.parent_items,
            teacher_items=recommendation.teacher_items,
            reviewed_by=recommendation.reviewed_by,
            reviewed_at=recommendation.reviewed_at,
            sent_at=recommendation.sent_at,
            created_at=recommendation.created_at,
        )


class RecommendationItemsUpdate(BaseModel):
    parent_items: list[str] = Field(min_length=1, max_length=6)


class AlertResponse(BaseModel):
    id: int
    student: StudentListItem
    level: RiskLevel
    is_read: bool
    created_at: datetime

    @classmethod
    def from_model(cls, alert: Alert) -> "AlertResponse":
        assessment = alert.assessment
        return cls(
            id=alert.id,
            student=StudentListItem.from_model(assessment.student, assessment),
            level=assessment.level,
            is_read=alert.is_read,
            created_at=alert.created_at,
        )


class AlertsPage(BaseModel):
    total: int
    items: list[AlertResponse]


class AlertUpdate(BaseModel):
    is_read: bool
