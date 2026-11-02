from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession, SchoolToday, require_roles
from app.domain import Role, User
from app.schemas.class_register import (
    AttendanceInput,
    AttendanceSheet,
    BehaviorInput,
    BehaviorSheet,
    Gradebook,
    GradebookInput,
    MyTeaching,
)
from app.services.class_register_service import ClassRegisterService

router = APIRouter(tags=["class register"])

Teacher = Annotated[User, Depends(require_roles(Role.TEACHER))]
Staff = Annotated[User, Depends(require_roles(Role.DIRECTOR, Role.ANALYST, Role.TEACHER))]


@router.get("/me/teaching", response_model=MyTeaching)
def my_teaching(user: Teacher, db: DbSession, today: SchoolToday) -> MyTeaching:
    return ClassRegisterService(db, today).my_teaching(user)


@router.get("/gradebook", response_model=Gradebook)
def get_gradebook(
    user: Staff,
    db: DbSession,
    today: SchoolToday,
    classroom_id: Annotated[int, Query()],
    subject_id: Annotated[int, Query()],
    period_id: Annotated[int, Query()],
) -> Gradebook:
    return ClassRegisterService(db, today).gradebook(user, classroom_id, subject_id, period_id)


@router.put("/gradebook", response_model=Gradebook)
def save_gradebook(
    body: GradebookInput, user: Staff, db: DbSession, today: SchoolToday
) -> Gradebook:
    return ClassRegisterService(db, today).save_grades(user, body)


@router.get("/classrooms/{classroom_id}/attendance", response_model=AttendanceSheet)
def get_attendance(
    classroom_id: int,
    user: Staff,
    db: DbSession,
    today: SchoolToday,
    day: Annotated[date | None, Query(alias="date")] = None,
) -> AttendanceSheet:
    return ClassRegisterService(db, today).attendance(user, classroom_id, day or today)


@router.put("/classrooms/{classroom_id}/attendance", response_model=AttendanceSheet)
def save_attendance(
    classroom_id: int, body: AttendanceInput, user: Staff, db: DbSession, today: SchoolToday
) -> AttendanceSheet:
    return ClassRegisterService(db, today).save_attendance(user, classroom_id, body)


@router.get("/classrooms/{classroom_id}/behavior", response_model=BehaviorSheet)
def get_behavior(
    classroom_id: int,
    user: Staff,
    db: DbSession,
    today: SchoolToday,
    period_id: Annotated[int, Query()],
) -> BehaviorSheet:
    return ClassRegisterService(db, today).behavior(user, classroom_id, period_id)


@router.put("/classrooms/{classroom_id}/behavior", response_model=BehaviorSheet)
def save_behavior(
    classroom_id: int, body: BehaviorInput, user: Staff, db: DbSession, today: SchoolToday
) -> BehaviorSheet:
    return ClassRegisterService(db, today).save_behavior(user, classroom_id, body)
