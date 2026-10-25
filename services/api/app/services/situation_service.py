from datetime import date

from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, UnprocessableError
from app.core.time import utcnow, week_deadline, week_start
from app.domain import (
    Classroom,
    Role,
    SituationAction,
    SituationEvent,
    Student,
    StudentSituation,
    User,
    WeeklyCheckin,
)
from app.repositories.classroom_repository import ClassroomRepository
from app.repositories.situation_repository import SituationRepository
from app.repositories.student_repository import StudentRepository
from app.schemas.situation import CheckinResponse, SituationInput, SituationUpdate
from app.services.access_policy import AccessPolicy


class SituationService:
    def __init__(self, db: Session, today: date) -> None:
        self.db = db
        self.today = today
        self.situations = SituationRepository(db)
        self.students = StudentRepository(db)
        self.classrooms = ClassroomRepository(db)
        self.policy = AccessPolicy(db)

    # --- Situaciones ---------------------------------------------------------

    def list_for_student(
        self, user: User, student_id: int, include_resolved: bool
    ) -> list[StudentSituation]:
        student = self._get_student(student_id)
        self.policy.ensure_can_manage_situations(user, student)
        return self.situations.list_for_student(student.id, include_resolved=include_resolved)

    def active_for_classroom(self, user: User, classroom_id: int) -> list[StudentSituation]:
        classroom = self._get_classroom(classroom_id)
        self.policy.ensure_can_manage_checkin(user, classroom)
        return self.situations.active_for_classroom(classroom.id)

    def create(self, user: User, student_id: int, data: SituationInput) -> StudentSituation:
        student = self._get_student(student_id)
        self.policy.ensure_can_manage_situations(user, student)
        started_on = data.started_on or self.today
        if started_on > self.today:
            raise UnprocessableError("The start date cannot be in the future")

        situation = self.situations.add(
            StudentSituation(
                student_id=student.id,
                kind=data.kind,
                note=_clean(data.note),
                started_on=started_on,
                created_by=user.id,
            )
        )
        self._log(situation, SituationAction.CREATED, user)
        self.db.commit()
        return situation

    def update(self, user: User, situation_id: int, data: SituationUpdate) -> StudentSituation:
        situation = self.situations.get(situation_id)
        if situation is None:
            raise NotFoundError("Situation not found")
        student = self._get_student(situation.student_id)
        self.policy.ensure_can_manage_situations(user, student)

        changes = data.model_dump(exclude_unset=True)
        if "note" in changes:
            situation.note = _clean(data.note)
            self._log(situation, SituationAction.UPDATED, user)
        if data.resolved is True and situation.resolved_on is None:
            situation.resolved_on = self.today
            self._log(situation, SituationAction.RESOLVED, user)
        elif data.resolved is False and situation.resolved_on is not None:
            situation.resolved_on = None
            self._log(situation, SituationAction.REOPENED, user)

        self.db.commit()
        return situation

    # --- Seguimiento semanal ---------------------------------------------------

    def current_checkin(self, user: User, classroom_id: int) -> CheckinResponse:
        classroom = self._get_classroom(classroom_id)
        self.policy.ensure_can_manage_checkin(user, classroom)
        return self._checkin_response(classroom)

    def complete_checkin(self, user: User, classroom_id: int) -> CheckinResponse:
        classroom = self._get_classroom(classroom_id)
        self.policy.ensure_can_manage_checkin(user, classroom)
        if user.role != Role.TEACHER:
            raise UnprocessableError("Only the classroom tutor completes the weekly check-in")

        start = week_start(self.today)
        if self.today > week_deadline(start):
            raise ConflictError("The weekly check-in closes on Saturday")

        checkin = self.situations.get_checkin(classroom_id=classroom.id, week_start=start)
        if checkin is None:
            self.situations.add_checkin(
                WeeklyCheckin(classroom_id=classroom.id, week_start=start, completed_by=user.id)
            )
        else:
            # Confirming again during the week records the latest review.
            checkin.completed_by = user.id
            checkin.completed_at = utcnow()
        self.db.commit()
        return self._checkin_response(classroom)

    # --- Internos ----------------------------------------------------------------

    def _checkin_response(self, classroom: Classroom) -> CheckinResponse:
        start = week_start(self.today)
        deadline = week_deadline(start)
        checkin = self.situations.get_checkin(classroom_id=classroom.id, week_start=start)
        return CheckinResponse(
            classroom_id=classroom.id,
            week_start=start,
            deadline=deadline,
            editable=self.today <= deadline,
            completed=checkin is not None,
            completed_at=checkin.completed_at if checkin else None,
        )

    def _log(self, situation: StudentSituation, action: SituationAction, user: User) -> None:
        self.situations.log(SituationEvent(situation_id=situation.id, action=action, user_id=user.id))

    def _get_student(self, student_id: int) -> Student:
        student = self.students.get(student_id)
        if student is None:
            raise NotFoundError("Student not found")
        return student

    def _get_classroom(self, classroom_id: int) -> Classroom:
        classroom = self.classrooms.get(classroom_id)
        if classroom is None:
            raise NotFoundError("Classroom not found")
        return classroom


def _clean(note: str | None) -> str | None:
    if note is None:
        return None
    note = note.strip()
    return note or None
