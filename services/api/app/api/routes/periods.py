from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.repositories.academic_repository import AcademicRepository
from app.schemas.period import PeriodResponse

router = APIRouter(prefix="/periods", tags=["periods"])


@router.get("", response_model=list[PeriodResponse])
def list_periods(user: CurrentUser, db: DbSession) -> list[PeriodResponse]:
    periods = AcademicRepository(db).list_periods(user.institution_id)
    return [PeriodResponse.from_model(period) for period in periods]
