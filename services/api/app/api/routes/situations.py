from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, DbSession, SchoolToday
from app.schemas.situation import (
    CheckinResponse,
    SituationInput,
    SituationKindInfo,
    SituationResponse,
    SituationUpdate,
)
from app.services.situation_service import SituationService
from app.services.situations.catalog import SITUATIONS

router = APIRouter(tags=["situations"])


@router.get("/situations/catalog", response_model=list[SituationKindInfo])
def situation_catalog(_: CurrentUser) -> list[SituationKindInfo]:
    return [
        SituationKindInfo(
            kind=kind, label=info.label, group=info.group, description=info.description
        )
        for kind, info in SITUATIONS.items()
    ]


@router.get("/students/{student_id}/situations", response_model=list[SituationResponse])
def list_student_situations(
    student_id: int,
    user: CurrentUser,
    db: DbSession,
    today: SchoolToday,
    include_resolved: Annotated[bool, Query()] = False,
) -> list[SituationResponse]:
    items = SituationService(db, today).list_for_student(user, student_id, include_resolved)
    return [SituationResponse.from_model(item) for item in items]


@router.post(
    "/students/{student_id}/situations",
    status_code=status.HTTP_201_CREATED,
    response_model=SituationResponse,
)
def create_situation(
    student_id: int, body: SituationInput, user: CurrentUser, db: DbSession, today: SchoolToday
) -> SituationResponse:
    situation = SituationService(db, today).create(user, student_id, body)
    return SituationResponse.from_model(situation)


@router.patch("/situations/{situation_id}", response_model=SituationResponse)
def update_situation(
    situation_id: int, body: SituationUpdate, user: CurrentUser, db: DbSession, today: SchoolToday
) -> SituationResponse:
    situation = SituationService(db, today).update(user, situation_id, body)
    return SituationResponse.from_model(situation)


@router.get("/classrooms/{classroom_id}/situations", response_model=list[SituationResponse])
def list_classroom_situations(
    classroom_id: int, user: CurrentUser, db: DbSession, today: SchoolToday
) -> list[SituationResponse]:
    items = SituationService(db, today).active_for_classroom(user, classroom_id)
    return [SituationResponse.from_model(item) for item in items]


@router.get("/classrooms/{classroom_id}/checkins/current", response_model=CheckinResponse)
def current_checkin(
    classroom_id: int, user: CurrentUser, db: DbSession, today: SchoolToday
) -> CheckinResponse:
    return SituationService(db, today).current_checkin(user, classroom_id)


@router.post(
    "/classrooms/{classroom_id}/checkins/current/complete", response_model=CheckinResponse
)
def complete_checkin(
    classroom_id: int, user: CurrentUser, db: DbSession, today: SchoolToday
) -> CheckinResponse:
    return SituationService(db, today).complete_checkin(user, classroom_id)
