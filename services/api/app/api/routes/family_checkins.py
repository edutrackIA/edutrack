from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, DbSession, SchoolToday, require_roles
from app.core.time import month_start
from app.domain import Role, User
from app.schemas.family_checkin import (
    CurrentFamilyCheckin,
    FamilyCheckinInput,
    FamilyCheckinResponse,
)
from app.services.family_checkin_service import FamilyCheckinService
from app.services.notifications.email_sender import EmailSender, get_email_sender

router = APIRouter(tags=["family check-ins"])

ReviewerUser = Annotated[User, Depends(require_roles(Role.DIRECTOR, Role.TEACHER))]
Sender = Annotated[EmailSender, Depends(get_email_sender)]


@router.get("/students/{student_id}/family-checkins/current", response_model=CurrentFamilyCheckin)
def current_family_checkin(
    student_id: int, user: CurrentUser, db: DbSession, sender: Sender, today: SchoolToday
) -> CurrentFamilyCheckin:
    checkin = FamilyCheckinService(db, sender, today).current(user, student_id)
    return CurrentFamilyCheckin(
        month=month_start(today),
        checkin=FamilyCheckinResponse.from_model(checkin) if checkin else None,
    )


@router.put("/students/{student_id}/family-checkins/current", response_model=FamilyCheckinResponse)
def submit_family_checkin(
    student_id: int,
    body: FamilyCheckinInput,
    user: CurrentUser,
    db: DbSession,
    sender: Sender,
    today: SchoolToday,
) -> FamilyCheckinResponse:
    checkin = FamilyCheckinService(db, sender, today).submit(user, student_id, body)
    return FamilyCheckinResponse.from_model(checkin)


@router.get("/family-checkins/pending", response_model=list[FamilyCheckinResponse])
def pending_family_checkins(
    user: ReviewerUser, db: DbSession, sender: Sender, today: SchoolToday
) -> list[FamilyCheckinResponse]:
    checkins = FamilyCheckinService(db, sender, today).pending(user)
    return [FamilyCheckinResponse.from_model(checkin) for checkin in checkins]


@router.post("/family-checkins/{checkin_id}/review", response_model=FamilyCheckinResponse)
def review_family_checkin(
    checkin_id: int, user: ReviewerUser, db: DbSession, sender: Sender, today: SchoolToday
) -> FamilyCheckinResponse:
    checkin = FamilyCheckinService(db, sender, today).review(user, checkin_id)
    return FamilyCheckinResponse.from_model(checkin)
