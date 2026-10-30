from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.api.deps import DbSession, SchoolToday, require_roles
from app.domain import Role, User
from app.schemas.model_monitoring import ModelPerformance
from app.services.model_monitoring_service import ModelMonitoringService

router = APIRouter(prefix="/model-performance", tags=["model monitoring"])

Leadership = Annotated[User, Depends(require_roles(Role.DIRECTOR, Role.ANALYST))]
Analyst = Annotated[User, Depends(require_roles(Role.ANALYST))]


@router.get("", response_model=ModelPerformance)
def model_performance(user: Leadership, db: DbSession, today: SchoolToday) -> ModelPerformance:
    return ModelMonitoringService(db, today).performance(user)


@router.get("/dataset.csv", response_class=Response)
def anonymized_dataset(user: Analyst, db: DbSession, today: SchoolToday) -> Response:
    """Features and real outcome per assessment, without names, codes or dates."""
    content = ModelMonitoringService(db, today).dataset_csv(user)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="edutrack-dataset-anonimizado.csv"'},
    )
