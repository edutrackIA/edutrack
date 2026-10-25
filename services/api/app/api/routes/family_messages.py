from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, require_roles
from app.domain import Role, User
from app.schemas.family_message import FamilyMessageResponse
from app.services.family_message_service import FamilyMessageService
from app.services.notifications.email_sender import EmailSender, get_email_sender

router = APIRouter(prefix="/family-messages", tags=["family messages"])

ReviewerUser = Annotated[User, Depends(require_roles(Role.DIRECTOR, Role.TEACHER))]
Sender = Annotated[EmailSender, Depends(get_email_sender)]


@router.get("/held", response_model=list[FamilyMessageResponse])
def list_held_messages(
    user: ReviewerUser, db: DbSession, sender: Sender
) -> list[FamilyMessageResponse]:
    messages = FamilyMessageService(db, sender).list_held(user)
    return [FamilyMessageResponse.from_model(message) for message in messages]


@router.post("/{message_id}/release", response_model=FamilyMessageResponse)
def release_message(
    message_id: int, user: ReviewerUser, db: DbSession, sender: Sender
) -> FamilyMessageResponse:
    message = FamilyMessageService(db, sender).release(user, message_id)
    return FamilyMessageResponse.from_model(message)


@router.post("/{message_id}/discard", response_model=FamilyMessageResponse)
def discard_message(
    message_id: int, user: ReviewerUser, db: DbSession, sender: Sender
) -> FamilyMessageResponse:
    message = FamilyMessageService(db, sender).discard(user, message_id)
    return FamilyMessageResponse.from_model(message)
