from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.domain import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: DbSession) -> TokenResponse:
    return AuthService(db).login(body.email, body.password)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: DbSession) -> TokenResponse:
    return AuthService(db).refresh(body.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(body: RefreshRequest, user: CurrentUser, db: DbSession) -> None:
    AuthService(db).logout(user, body.refresh_token)


@router.get("/me", response_model=UserResponse)
def me(user: CurrentUser) -> User:
    return user
