from fastapi import APIRouter, Request, status

from app.api.deps import CurrentUser, DbSession, client_address
from app.core.errors import TooManyRequestsError, UnauthorizedError
from app.core.rate_limit import login_by_account, login_by_address
from app.domain import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService

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
