import json
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.deps import CurrentUser, DbSession, require_roles
from app.core.privacy import PRIVACY_NOTICE_VERSION
from app.domain import Role, User
from app.schemas.privacy import (
    ConsentInput,
    DataRequestInput,
    DataRequestResolution,
    DataRequestResponse,
    PrivacyStatus,
)
from app.services.notifications.email_sender import EmailSender, get_email_sender
from app.services.privacy_service import PrivacyService

router = APIRouter(tags=["privacy"])

Parent = Annotated[User, Depends(require_roles(Role.PARENT))]
Director = Annotated[User, Depends(require_roles(Role.DIRECTOR))]
Sender = Annotated[EmailSender, Depends(get_email_sender)]


@router.get("/me/privacy", response_model=PrivacyStatus)
def privacy_status(user: CurrentUser, db: DbSession) -> PrivacyStatus:
    consent = PrivacyService(db).consent(user)
    return PrivacyStatus(
        version=PRIVACY_NOTICE_VERSION, accepted_at=consent.accepted_at if consent else None
    )


@router.post("/me/privacy/acceptance", response_model=PrivacyStatus)
def accept_privacy(body: ConsentInput, user: CurrentUser, db: DbSession) -> PrivacyStatus:
    consent = PrivacyService(db).accept(user, body.version)
    return PrivacyStatus(version=consent.notice_version, accepted_at=consent.accepted_at)


@router.post(
    "/data-requests", status_code=status.HTTP_201_CREATED, response_model=DataRequestResponse
)
def create_data_request(
    body: DataRequestInput, user: Parent, db: DbSession, sender: Sender
) -> DataRequestResponse:
    return PrivacyService(db, sender).create_request(user, body)


@router.get("/data-requests", response_model=list[DataRequestResponse])
def list_data_requests(user: CurrentUser, db: DbSession) -> list[DataRequestResponse]:
    """Guardians see their own requests; direction sees all of the school."""
    return PrivacyService(db).list_requests(user)


@router.post("/data-requests/{request_id}/resolution", response_model=DataRequestResponse)
def resolve_data_request(
    request_id: int, body: DataRequestResolution, user: Director, db: DbSession, sender: Sender
) -> DataRequestResponse:
    return PrivacyService(db, sender).resolve(user, request_id, body)


@router.get("/students/{student_id}/data-export", response_class=Response)
def export_student_data(student_id: int, user: Director, db: DbSession) -> Response:
    """Everything kept about a student, to answer an access request."""
    data = PrivacyService(db).export_student(user, student_id)
    filename = f"expediente-{data['student']['code']}.json"
    return Response(
        content=json.dumps(data, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
