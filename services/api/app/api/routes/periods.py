from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.repositories.academic_repository import AcademicRepository
from app.schemas.period import PeriodResponse

router = APIRouter(prefix="/periods", tags=["periods"])


@router.get("", response_model=list[PeriodResponse])
def list_periods(user: CurrentUser, db: DbSession) -> list[PeriodResponse]:
    academic = AcademicRepository(db)
    with_grades = academic.periods_with_grades(user.institution_id)
    return [
        PeriodResponse.from_model(period, has_grades=period.id in with_grades)
        for period in academic.list_periods(user.institution_id)
    ]
