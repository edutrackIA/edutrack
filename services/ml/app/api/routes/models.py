"""Model registry: list versions, train a candidate with school data, activate a version.

These actions change what every prediction returns, so they require the admin token
shared only with the EduTrack API.
"""

import secrets
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.core.config import get_settings
from app.model_store import active_version, list_versions, save_version, set_active
from app.schemas.models import ModelVersion, SchoolTrainingRequest, SchoolTrainingResponse
from training.school import score, train_with_school_data

router = APIRouter(prefix="/v1/models", tags=["models"])


def require_admin(x_admin_token: Annotated[str | None, Header()] = None) -> None:
    expected = get_settings().admin_token
    if not expected or not x_admin_token or not secrets.compare_digest(expected, x_admin_token):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin token required")


Admin = Annotated[None, Depends(require_admin)]


def _root() -> Path:
    return Path(get_settings().model_dir)


def _version(metadata: dict[str, Any], active: str | None) -> ModelVersion:
    return ModelVersion(
        version=metadata["version"],
        trained_at=metadata.get("trained_at"),
        active=metadata["version"] == active,
        metrics=metadata.get("metrics", {}),
        dataset=metadata.get("dataset", {}),
        school_holdout=metadata.get("school_holdout"),
    )


@router.get("", response_model=list[ModelVersion])
def models(_: Admin) -> list[ModelVersion]:
    active = active_version(_root())
    return [_version(metadata, active) for metadata in list_versions(_root())]


@router.post("/train", response_model=SchoolTrainingResponse)
def train(body: SchoolTrainingRequest, request: Request, _: Admin) -> SchoolTrainingResponse:
    """Train and store a candidate. It does not replace the active model."""
    try:
        result = train_with_school_data(
            [row.model_dump(mode="json") for row in body.rows], seed=body.seed
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    save_version(result.bundle, _root())

    active = request.app.state.model
    active_score = None
    if active is not None and set(active.features) <= set(result.holdout.columns):
        active_score = score(active, result.holdout)
    return SchoolTrainingResponse(
        candidate=_version(result.bundle.metadata, active_version(_root())),
        active_on_holdout=active_score,
    )


@router.post("/{version}/activate", response_model=ModelVersion)
def activate(version: str, request: Request, _: Admin) -> ModelVersion:
    try:
        bundle = set_active(_root(), version)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Unknown model version") from exc
    request.app.state.model = bundle
    return _version(bundle.metadata, bundle.version)
