from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession, require_roles
from app.domain import RecommendationStatus, Role, User
from app.schemas.recommendation import (
    AlertResponse,
    AlertsPage,
    AlertUpdate,
    RecommendationItemsUpdate,
    RecommendationResponse,
)
from app.services.notifications.email_sender import EmailSender, get_email_sender
from app.services.recommendation_service import RecommendationService

router = APIRouter(tags=["recommendations"])

ReviewerUser = Annotated[User, Depends(require_roles(Role.DIRECTOR, Role.TEACHER))]
Sender = Annotated[EmailSender, Depends(get_email_sender)]


@router.get("/recommendations", response_model=list[RecommendationResponse])
def list_recommendations(
    user: ReviewerUser,
    db: DbSession,
    status: Annotated[RecommendationStatus | None, Query()] = None,
) -> list[RecommendationResponse]:
    items = RecommendationService(db).queue(user, status)
    return [RecommendationResponse.from_model(item) for item in items]


@router.get("/students/{student_id}/recommendations", response_model=list[RecommendationResponse])
def list_student_recommendations(
    student_id: int, user: CurrentUser, db: DbSession
) -> list[RecommendationResponse]:
    items = RecommendationService(db).list_for_student(user, student_id)
    return [RecommendationResponse.from_model(item) for item in items]


@router.patch("/recommendations/{recommendation_id}", response_model=RecommendationResponse)
def edit_recommendation(
    recommendation_id: int, body: RecommendationItemsUpdate, user: ReviewerUser, db: DbSession
) -> RecommendationResponse:
    item = RecommendationService(db).update_items(user, recommendation_id, body.parent_items)
    return RecommendationResponse.from_model(item)


@router.post("/recommendations/{recommendation_id}/approve", response_model=RecommendationResponse)
def approve_recommendation(
    recommendation_id: int, user: ReviewerUser, db: DbSession, sender: Sender
) -> RecommendationResponse:
    item = RecommendationService(db).approve(user, recommendation_id, sender)
    return RecommendationResponse.from_model(item)


@router.post("/recommendations/{recommendation_id}/send", response_model=RecommendationResponse)
def send_recommendation(
    recommendation_id: int, user: ReviewerUser, db: DbSession, sender: Sender
) -> RecommendationResponse:
    item = RecommendationService(db).resend(user, recommendation_id, sender)
    return RecommendationResponse.from_model(item)


@router.post("/recommendations/{recommendation_id}/discard", response_model=RecommendationResponse)
def discard_recommendation(
    recommendation_id: int, user: ReviewerUser, db: DbSession
) -> RecommendationResponse:
    item = RecommendationService(db).discard(user, recommendation_id)
    return RecommendationResponse.from_model(item)


@router.get("/alerts", response_model=AlertsPage)
def list_alerts(
    user: CurrentUser,
    db: DbSession,
    unread: Annotated[bool | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> AlertsPage:
    total, alerts = RecommendationService(db).list_alerts(user, unread=unread, page=page, size=size)
    return AlertsPage(total=total, items=[AlertResponse.from_model(alert) for alert in alerts])


@router.patch("/alerts/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: int, body: AlertUpdate, user: CurrentUser, db: DbSession
) -> AlertResponse:
    alert = RecommendationService(db).mark_alert(user, alert_id, is_read=body.is_read)
    return AlertResponse.from_model(alert)
