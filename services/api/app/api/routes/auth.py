from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import CurrentUser, DbSession, client_address
from app.core.errors import (
    ConflictError,
    NotFoundError,
    TooManyRequestsError,
    UnauthorizedError,
    UnprocessableError,
)
from app.core.rate_limit import (
    invitations_by_address,
    login_by_account,
    login_by_address,
    resets_by_address,
    resets_by_email,
)
from app.domain import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    NewPassword,
    RefreshRequest,
    ResetTarget,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.services.notifications.email_sender import EmailSender, get_email_sender
from app.services.password_service import PasswordService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, db: DbSession) -> TokenResponse:
    address = client_address(request)
    account = f"{address}|{body.email.strip().lower()}"
    for limiter, key in ((login_by_account, account), (login_by_address, address)):
        wait = limiter.retry_after(key)
        if wait is not None:
            raise TooManyRequestsError("Too many failed login attempts", retry_after=wait)

    try:
        tokens = AuthService(db).login(body.email, body.password)
    except UnauthorizedError:
        login_by_account.record_failure(account)
        login_by_address.record_failure(address)
        raise
    login_by_account.reset(account)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: DbSession) -> TokenResponse:
    return AuthService(db).refresh(body.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(body: RefreshRequest, user: CurrentUser, db: DbSession) -> None:
    AuthService(db).logout(user, body.refresh_token)


@router.get("/me", response_model=UserResponse)
def me(user: CurrentUser) -> User:
    return user


# --- Contraseñas ---------------------------------------------------------------------


@router.post("/password/forgot", status_code=status.HTTP_202_ACCEPTED)
def forgot_password(
    body: ForgotPasswordRequest,
    request: Request,
    db: DbSession,
    sender: Annotated[EmailSender, Depends(get_email_sender)],
) -> None:
    """Always answers the same, whether or not the email exists."""
    address = client_address(request)
    wait = resets_by_address.retry_after(address)
    if wait is not None:
        raise TooManyRequestsError("Too many password reset requests", retry_after=wait)
    resets_by_address.record_failure(address)

    email = body.email.strip().lower()
    if resets_by_email.retry_after(email) is not None:
        return  # Silently ignored: answering differently would reveal the account exists.
    resets_by_email.record_failure(email)
    PasswordService(db, sender).request_reset(email)


def _reset_link_failure(request: Request) -> None:
    invitations_by_address.record_failure(client_address(request))


@router.get("/password/reset/{token}", response_model=ResetTarget)
def reset_target(token: str, request: Request, db: DbSession) -> ResetTarget:
    wait = invitations_by_address.retry_after(client_address(request))
    if wait is not None:
        raise TooManyRequestsError("Too many invalid links", retry_after=wait)
    try:
        user = PasswordService(db).reset_target(token)
    except (NotFoundError, ConflictError):
        _reset_link_failure(request)
        raise
    return ResetTarget(email=user.email)


@router.post("/password/reset/{token}", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(token: str, body: NewPassword, request: Request, db: DbSession) -> None:
    wait = invitations_by_address.retry_after(client_address(request))
    if wait is not None:
        raise TooManyRequestsError("Too many invalid links", retry_after=wait)
    try:
        PasswordService(db).reset(token, body.password)
    except (NotFoundError, ConflictError):
        _reset_link_failure(request)
        raise


@router.post("/password/change", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    body: ChangePasswordRequest, request: Request, user: CurrentUser, db: DbSession
) -> None:
    """Closes every session, including this one: the client signs in again."""
    account = f"{client_address(request)}|{user.email}"
    wait = login_by_account.retry_after(account)
    if wait is not None:
        raise TooManyRequestsError("Too many failed attempts", retry_after=wait)
    try:
        PasswordService(db).change(user, body.current_password, body.new_password)
    except UnprocessableError as exc:
        if exc.code == "WRONG_PASSWORD":
            login_by_account.record_failure(account)
        raise
