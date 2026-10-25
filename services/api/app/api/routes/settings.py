from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, require_roles
from app.domain import Role, User
from app.schemas.risk import RiskThresholds
from app.services.risk_service import RiskService

router = APIRouter(prefix="/settings", tags=["settings"])

ManagementUser = Annotated[User, Depends(require_roles(Role.DIRECTOR, Role.ANALYST))]
AnalystUser = Annotated[User, Depends(require_roles(Role.ANALYST))]


@router.get("/risk-thresholds", response_model=RiskThresholds)
def get_risk_thresholds(user: ManagementUser, db: DbSession) -> RiskThresholds:
    thresholds = RiskService(db).get_thresholds(user)
    return RiskThresholds(medium_from=thresholds.medium_from, high_from=thresholds.high_from)


@router.put("/risk-thresholds", response_model=RiskThresholds)
def update_risk_thresholds(
    body: RiskThresholds, user: AnalystUser, db: DbSession
) -> RiskThresholds:
    thresholds = RiskService(db).update_thresholds(user, body)
    return RiskThresholds(medium_from=thresholds.medium_from, high_from=thresholds.high_from)
