from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, SchoolToday, require_roles
from app.domain import Role, User
from app.schemas.model_lifecycle import ModelsOverview, ModelVersionView, TrainingResult
from app.services.model_lifecycle_service import ModelLifecycleService
from app.services.risk.model_registry import ModelRegistry, get_model_registry

router = APIRouter(prefix="/models", tags=["model lifecycle"])

Leadership = Annotated[User, Depends(require_roles(Role.DIRECTOR, Role.ANALYST))]
Analyst = Annotated[User, Depends(require_roles(Role.ANALYST))]
Director = Annotated[User, Depends(require_roles(Role.DIRECTOR))]
Registry = Annotated[ModelRegistry, Depends(get_model_registry)]


@router.get("", response_model=ModelsOverview)
def models(
    user: Leadership, db: DbSession, registry: Registry, today: SchoolToday
) -> ModelsOverview:
    return ModelLifecycleService(db, registry, today).overview(user)


@router.post("/train", response_model=TrainingResult)
def train(user: Analyst, db: DbSession, registry: Registry, today: SchoolToday) -> TrainingResult:
    """Analysis trains a candidate; it does not go live until direction activates it."""
    return ModelLifecycleService(db, registry, today).train(user)


@router.post("/{version}/activation", response_model=ModelVersionView)
def activate(
    version: str, user: Director, db: DbSession, registry: Registry, today: SchoolToday
) -> ModelVersionView:
    """Also used to roll back: activating an older version brings it back."""
    return ModelLifecycleService(db, registry, today).activate(user, version)
