from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, SchoolToday, require_roles
from app.domain import Role, User
from app.schemas.student import PromotionInput, PromotionPlan, StudentResponse, WithdrawalInput
from app.services.enrollment_service import EnrollmentService

router = APIRouter(tags=["enrollment"])

Admin = Annotated[User, Depends(require_roles(Role.DIRECTOR, Role.ANALYST))]
Director = Annotated[User, Depends(require_roles(Role.DIRECTOR))]


@router.post("/students/{student_id}/withdrawal", response_model=StudentResponse)
def withdraw_student(
    student_id: int, body: WithdrawalInput, user: Admin, db: DbSession, today: SchoolToday
) -> StudentResponse:
    student = EnrollmentService(db, today).withdraw(user, student_id, body)
    return StudentResponse.from_model(student)


@router.post("/students/{student_id}/reinstatement", response_model=StudentResponse)
def reinstate_student(
    student_id: int, user: Admin, db: DbSession, today: SchoolToday
) -> StudentResponse:
    return StudentResponse.from_model(EnrollmentService(db, today).reinstate(user, student_id))


@router.post("/school-years/{year}/promotion", response_model=PromotionPlan)
def promote_year(
    year: int, body: PromotionInput, user: Director, db: DbSession, today: SchoolToday
) -> PromotionPlan:
    """With dry_run (the default) only shows the plan; without it, applies it."""
    return EnrollmentService(db, today).promote(user, year, body)
