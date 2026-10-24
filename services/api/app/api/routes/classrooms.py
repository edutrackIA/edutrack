from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession, require_roles
from app.domain import Role, User
from app.schemas.classroom import ClassroomResponse
from app.schemas.student import StudentListItem
from app.services.classroom_service import ClassroomService

router = APIRouter(prefix="/classrooms", tags=["students"])

StaffUser = Annotated[User, Depends(require_roles(Role.DIRECTOR, Role.ANALYST, Role.TEACHER))]


@router.get("", response_model=list[ClassroomResponse])
def list_classrooms(
    user: StaffUser, db: DbSession, year: Annotated[int | None, Query()] = None
) -> list[ClassroomResponse]:
    classrooms = ClassroomService(db).list_visible(user, year)
    return [ClassroomResponse.from_model(classroom) for classroom in classrooms]


@router.get("/{classroom_id}/students", response_model=list[StudentListItem])
def list_classroom_students(
    classroom_id: int, user: StaffUser, db: DbSession
) -> list[StudentListItem]:
    students = ClassroomService(db).list_students(user, classroom_id)
    return [StudentListItem.from_model(student) for student in students]
