from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, DbSession, require_roles
from app.domain import Role, User
from app.schemas.risk import RiskAssessmentResponse, RunRiskRequest, RunRiskResponse
from app.services.risk.ml_client import MlClient, get_ml_client
from app.services.risk_service import RiskService

router = APIRouter(tags=["risk"])

AnalystUser = Annotated[User, Depends(require_roles(Role.ANALYST))]
Ml = Annotated[MlClient, Depends(get_ml_client)]


@router.post("/risk-assessments/run", response_model=RunRiskResponse)
def run_risk_assessment(
    body: RunRiskRequest, user: AnalystUser, db: DbSession, ml: Ml
) -> RunRiskResponse:
    return RiskService(db).run(user, ml, period_id=body.period_id, classroom_id=body.classroom_id)


@router.get("/students/{student_id}/risk", response_model=list[RiskAssessmentResponse])
def student_risk_history(
    student_id: int, user: CurrentUser, db: DbSession
) -> list[RiskAssessmentResponse]:
    assessments = RiskService(db).history(user, student_id)
    return [RiskAssessmentResponse.from_model(item) for item in assessments]
