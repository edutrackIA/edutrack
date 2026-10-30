"""School configuration: periods, courses, classrooms, staff and course assignments."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DbSession, require_roles
from app.domain import AcademicPeriod, Role, User
from app.repositories.academic_repository import AcademicRepository
from app.schemas.classroom import ClassroomResponse
from app.schemas.period import PeriodResponse
from app.schemas.school_setup import (
    AssignmentInput,
    AssignmentResponse,
    ClassroomInput,
    ClassroomTutor,
    PeriodDates,
    PeriodInput,
    StaffInput,
    StaffResponse,
    StaffStatus,
    SubjectInput,
    SubjectResponse,
)
from app.services.notifications.email_sender import EmailSender, get_email_sender
from app.services.school_setup_service import SchoolSetupService

router = APIRouter(tags=["school setup"])

Director = Annotated[User, Depends(require_roles(Role.DIRECTOR))]
Staff = Annotated[User, Depends(require_roles(Role.DIRECTOR, Role.ANALYST, Role.TEACHER))]
Sender = Annotated[EmailSender, Depends(get_email_sender)]


def _period(db: DbSession, period: AcademicPeriod) -> PeriodResponse:
    with_grades = AcademicRepository(db).periods_with_grades(period.institution_id)
    return PeriodResponse.from_model(period, has_grades=period.id in with_grades)


# --- Bimestres -----------------------------------------------------------------------


@router.post("/periods", status_code=status.HTTP_201_CREATED, response_model=PeriodResponse)
def create_period(body: PeriodInput, user: Director, db: DbSession) -> PeriodResponse:
    return _period(db, SchoolSetupService(db).create_period(user, body))


@router.patch("/periods/{period_id}", response_model=PeriodResponse)
def update_period(
    period_id: int, body: PeriodDates, user: Director, db: DbSession
) -> PeriodResponse:
    return _period(db, SchoolSetupService(db).update_period(user, period_id, body))


# --- Cursos -------------------------------------------------------------------------


@router.get("/subjects", response_model=list[SubjectResponse])
def list_subjects(user: Staff, db: DbSession) -> list[SubjectResponse]:
    return [SubjectResponse.from_model(s) for s in SchoolSetupService(db).list_subjects(user)]


@router.post("/subjects", status_code=status.HTTP_201_CREATED, response_model=SubjectResponse)
def create_subject(body: SubjectInput, user: Director, db: DbSession) -> SubjectResponse:
    return SubjectResponse.from_model(SchoolSetupService(db).create_subject(user, body))


@router.patch("/subjects/{subject_id}", response_model=SubjectResponse)
def rename_subject(
    subject_id: int, body: SubjectInput, user: Director, db: DbSession
) -> SubjectResponse:
    return SubjectResponse.from_model(SchoolSetupService(db).rename_subject(user, subject_id, body))


# --- Aulas --------------------------------------------------------------------------


@router.post("/classrooms", status_code=status.HTTP_201_CREATED, response_model=ClassroomResponse)
def create_classroom(body: ClassroomInput, user: Director, db: DbSession) -> ClassroomResponse:
    return ClassroomResponse.from_model(SchoolSetupService(db).create_classroom(user, body))


@router.patch("/classrooms/{classroom_id}", response_model=ClassroomResponse)
def set_classroom_tutor(
    classroom_id: int, body: ClassroomTutor, user: Director, db: DbSession
) -> ClassroomResponse:
    classroom = SchoolSetupService(db).set_tutor(user, classroom_id, body.tutor_id)
    return ClassroomResponse.from_model(classroom)


# --- Personal -------------------------------------------------------------------------


@router.get("/staff", response_model=list[StaffResponse])
def list_staff(user: Director, db: DbSession) -> list[StaffResponse]:
    return [StaffResponse.from_model(m) for m in SchoolSetupService(db).list_staff(user)]


@router.post("/staff", status_code=status.HTTP_201_CREATED, response_model=StaffResponse)
def invite_staff(body: StaffInput, user: Director, db: DbSession, sender: Sender) -> StaffResponse:
    return SchoolSetupService(db, sender).invite_staff(user, body)


@router.patch("/staff/{member_id}", response_model=StaffResponse)
def set_staff_status(
    member_id: int, body: StaffStatus, user: Director, db: DbSession
) -> StaffResponse:
    member = SchoolSetupService(db).set_active(user, member_id, body.is_active)
    return StaffResponse.from_model(member)


@router.post("/staff/{member_id}/invitation", response_model=StaffResponse)
def resend_staff_invitation(
    member_id: int, user: Director, db: DbSession, sender: Sender
) -> StaffResponse:
    return SchoolSetupService(db, sender).resend_staff_invitation(user, member_id)


# --- Asignaciones -----------------------------------------------------------------------


@router.get("/course-assignments", response_model=list[AssignmentResponse])
def list_assignments(
    user: Director, db: DbSession, classroom_id: Annotated[int | None, Query()] = None
) -> list[AssignmentResponse]:
    return SchoolSetupService(db).list_assignments(user, classroom_id)


@router.post(
    "/course-assignments", status_code=status.HTTP_201_CREATED, response_model=AssignmentResponse
)
def assign_course(body: AssignmentInput, user: Director, db: DbSession) -> AssignmentResponse:
    return SchoolSetupService(db).assign(user, body)


@router.delete("/course-assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def unassign_course(assignment_id: int, user: Director, db: DbSession) -> None:
    SchoolSetupService(db).unassign(user, assignment_id)
