from fastapi import APIRouter, status

from app.api.deps import DbSession
from app.schemas.invitation import AcceptInvitation, InvitationInfo
from app.services.invitation_service import InvitationService

# Public: the person opening the link has no account yet.
router = APIRouter(prefix="/invitations", tags=["invitations"])


@router.get("/{token}", response_model=InvitationInfo)
def get_invitation(token: str, db: DbSession) -> InvitationInfo:
    user = InvitationService(db).get_usable(token).user
    return InvitationInfo(full_name=user.full_name, email=user.email)


@router.post("/{token}/accept", status_code=status.HTTP_204_NO_CONTENT)
def accept_invitation(token: str, body: AcceptInvitation, db: DbSession) -> None:
    InvitationService(db).accept(token, body.password)
