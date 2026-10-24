from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query

from app.api.deps import CurrentUser, DbSession, require_roles
from app.domain import Role, User
from app.schemas.student import (
    BehaviorInput,
    BehaviorResponse,
    GradeInput,
    GradeResponse,
    StudentListItem,
    StudentResponse,
    StudentUpdate,
)
from app.services.student_service import StudentService

router = APIRouter(tags=["students"])

ParentUser = Annotated[User, Depends(require_roles(Role.PARENT))]


@router.get("/students/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, user: CurrentUser, db: DbSession) -> StudentResponse:
    student = StudentService(db).get(user, student_id)
    return StudentResponse.model_validate(student)


@router.patch("/students/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: int, body: StudentUpdate, user: CurrentUser, db: DbSession
) -> StudentResponse:
    student = StudentService(db).update(user, student_id, body)
    return StudentResponse.model_validate(student)


@router.get("/students/{student_id}/grades", response_model=list[GradeResponse])
def list_grades(
    student_id: int,
    user: CurrentUser,
    db: DbSession,
    period_id: Annotated[int | None, Query()] = None,
) -> list[GradeResponse]:
    grades = StudentService(db).list_grades(user, student_id, period_id)
    return [GradeResponse.from_model(grade) for grade in grades]


@router.put("/students/{student_id}/grades", response_model=list[GradeResponse])
def upsert_grades(
    student_id: int,
    body: Annotated[list[GradeInput], Body(min_length=1)],
    user: CurrentUser,
    db: DbSession,
) -> list[GradeResponse]:
    grades = StudentService(db).upsert_grades(user, student_id, body)
    return [GradeResponse.from_model(grade) for grade in grades]


@router.put("/students/{student_id}/behavior", response_model=BehaviorResponse)
def record_behavior(
    student_id: int, body: BehaviorInput, user: CurrentUser, db: DbSession
) -> BehaviorResponse:
    record = StudentService(db).record_behavior(user, student_id, body)
    return BehaviorResponse.from_model(record)


@router.get("/me/children", response_model=list[StudentListItem])
def list_my_children(user: ParentUser, db: DbSession) -> list[StudentListItem]:
    students = StudentService(db).list_children(user)
    return [StudentListItem.from_model(student) for student in students]
