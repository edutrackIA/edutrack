from collections.abc import Callable
from typing import TypeVar

from fastapi import APIRouter, Request, status

from app.api.deps import DbSession, client_address
from app.core.errors import ConflictError, NotFoundError, TooManyRequestsError
from app.core.rate_limit import invitations_by_address
from app.schemas.invitation import AcceptInvitation, InvitationInfo
from app.services.invitation_service import InvitationService

# Public: the person opening the link has no account yet.
router = APIRouter(prefix="/invitations", tags=["invitations"])

T = TypeVar("T")


def _limited(request: Request, action: Callable[[], T]) -> T:
    """Invalid or expired links count as failures; too many from one address are blocked."""
    address = client_address(request)
    wait = invitations_by_address.retry_after(address)
    if wait is not None:
        raise TooManyRequestsError("Too many invalid invitation links", retry_after=wait)
    try:
        return action()
    except (NotFoundError, ConflictError):
        invitations_by_address.record_failure(address)
        raise


@router.get("/{token}", response_model=InvitationInfo)
def get_invitation(token: str, request: Request, db: DbSession) -> InvitationInfo:
    user = _limited(request, lambda: InvitationService(db).get_usable(token).user)
    return InvitationInfo(full_name=user.full_name, email=user.email)


@router.post("/{token}/accept", status_code=status.HTTP_204_NO_CONTENT)
def accept_invitation(token: str, body: AcceptInvitation, request: Request, db: DbSession) -> None:
    _limited(request, lambda: InvitationService(db).accept(token, body.password))
