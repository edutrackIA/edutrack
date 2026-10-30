from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import DbSession, require_roles
from app.domain import Role, User
from app.schemas.guardian import GuardianInput, GuardianResponse
from app.services.guardian_service import GuardianService
from app.services.notifications.email_sender import EmailSender, get_email_sender

router = APIRouter(prefix="/students/{student_id}/guardians", tags=["guardians"])

AdminUser = Annotated[User, Depends(require_roles(Role.DIRECTOR, Role.ANALYST))]
Sender = Annotated[EmailSender, Depends(get_email_sender)]


@router.get("", response_model=list[GuardianResponse])
def list_guardians(
    student_id: int, user: AdminUser, db: DbSession, sender: Sender
) -> list[GuardianResponse]:
    return GuardianService(db, sender).list(user, student_id)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=GuardianResponse)
def add_guardian(
    student_id: int, body: GuardianInput, user: AdminUser, db: DbSession, sender: Sender
) -> GuardianResponse:
    return GuardianService(db, sender).add(user, student_id, body)


@router.delete("/{guardian_id}", status_code=status.HTTP_204_NO_CONTENT)
def unlink_guardian(
    student_id: int, guardian_id: int, user: AdminUser, db: DbSession, sender: Sender
) -> None:
    GuardianService(db, sender).unlink(user, student_id, guardian_id)


@router.post("/{guardian_id}/invitation", response_model=GuardianResponse)
def resend_invitation(
    student_id: int, guardian_id: int, user: AdminUser, db: DbSession, sender: Sender
) -> GuardianResponse:
    return GuardianService(db, sender).resend(user, student_id, guardian_id)
