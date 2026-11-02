"""Everything a school configures before (and while) using EduTrack.

Only the director changes the setup. Messages are in Spanish because they are shown
as they are in the configuration screens.
"""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, UnprocessableError
from app.domain import AcademicPeriod, Classroom, CourseAssignment, Role, Subject, User
from app.repositories.academic_repository import AcademicRepository
from app.repositories.user_repository import UserRepository
from app.schemas.school_setup import (
    AssignmentInput,
    AssignmentResponse,
    ClassroomInput,
    PeriodDates,
    PeriodInput,
    StaffInput,
    StaffResponse,
    SubjectInput,
)
from app.services.guardian_links import GuardianLinkError, normalize_email
from app.services.invitation_service import InvitationService
from app.services.notifications.email_sender import EmailSender


def _invalid(message: str) -> UnprocessableError:
    return UnprocessableError(message, code="SETUP_INVALID")


def _conflict(message: str) -> ConflictError:
    return ConflictError(message, code="SETUP_CONFLICT")


class SchoolSetupService:
    def __init__(self, db: Session, sender: EmailSender | None = None) -> None:
        self.db = db
        self.academic = AcademicRepository(db)
        self.users = UserRepository(db)
        self.invitations = InvitationService(db, sender)

    # --- Bimestres ----------------------------------------------------------------------

    def create_period(self, user: User, data: PeriodInput) -> AcademicPeriod:
        existing = self.db.scalar(
            select(AcademicPeriod).where(
                AcademicPeriod.institution_id == user.institution_id,
                AcademicPeriod.year == data.year,
                AcademicPeriod.bimester == data.bimester,
            )
        )
        if existing is not None:
            raise _conflict(f"El bimestre {data.bimester} de {data.year} ya existe")
        period = AcademicPeriod(
            institution_id=user.institution_id,
            year=data.year,
            bimester=data.bimester,
            start_date=data.start_date,
            end_date=data.end_date,
        )
        self._check_dates(period, data.start_date, data.end_date)
        self.db.add(period)
        self.db.commit()
        return period

    def update_period(self, user: User, period_id: int, data: PeriodDates) -> AcademicPeriod:
        period = self.academic.get_period(period_id)
        if period is None or period.institution_id != user.institution_id:
            raise NotFoundError("Period not found")
        self._check_dates(period, data.start_date, data.end_date)
        period.start_date, period.end_date = data.start_date, data.end_date
        self.db.commit()
        return period

    def _check_dates(self, period: AcademicPeriod, start: date, end: date) -> None:
        if start >= end:
            raise _invalid("La fecha de inicio debe ser anterior a la de fin")
        if start.year != period.year or end.year != period.year:
            raise _invalid(f"Las fechas deben estar dentro del año {period.year}")
        overlapping = self.db.scalar(
            select(AcademicPeriod).where(
                AcademicPeriod.institution_id == period.institution_id,
                AcademicPeriod.id != (period.id or 0),
                AcademicPeriod.start_date <= end,
                AcademicPeriod.end_date >= start,
            )
        )
        if overlapping is not None:
            raise _invalid(
                f"Las fechas se cruzan con el bimestre {overlapping.bimester} de {overlapping.year}"
            )

    # --- Cursos -----------------------------------------------------------------------

    def list_subjects(self, user: User) -> list[Subject]:
        return self.academic.list_subjects(user.institution_id)

    def create_subject(self, user: User, data: SubjectInput) -> Subject:
        name = self._subject_name(user, data.name)
        subject = Subject(institution_id=user.institution_id, name=name)
        self.db.add(subject)
        self.db.commit()
        return subject

    def rename_subject(self, user: User, subject_id: int, data: SubjectInput) -> Subject:
        subject = self._subject(user, subject_id)
        subject.name = self._subject_name(user, data.name, current=subject)
        self.db.commit()
        return subject

    def _subject_name(self, user: User, raw: str, current: Subject | None = None) -> str:
        name = " ".join(raw.split())
        existing = self.academic.get_subject_by_name(user.institution_id, name)
        if existing is not None and existing is not current:
            raise _conflict(f"Ya existe el curso {existing.name}")
        return name

    # --- Aulas --------------------------------------------------------------------------

    def create_classroom(self, user: User, data: ClassroomInput) -> Classroom:
        section = data.section.strip().upper()
        if not section.isalpha():
            raise _invalid("La sección debe ser una o dos letras, por ejemplo A")
        duplicated = self.db.scalar(
            select(Classroom).where(
                Classroom.institution_id == user.institution_id,
                Classroom.year == data.year,
                Classroom.grade == data.grade,
                Classroom.section == section,
            )
        )
        if duplicated is not None:
            raise _conflict(f"El aula {data.grade}° {section} de {data.year} ya existe")
        classroom = Classroom(
            institution_id=user.institution_id,
            year=data.year,
            grade=data.grade,
            section=section,
            tutor_id=self._teacher(user, data.tutor_id).id if data.tutor_id else None,
        )
        self.db.add(classroom)
        self.db.commit()
        self.db.refresh(classroom)
        return classroom

    def set_tutor(self, user: User, classroom_id: int, tutor_id: int | None) -> Classroom:
        classroom = self._classroom(user, classroom_id)
        classroom.tutor_id = self._teacher(user, tutor_id).id if tutor_id else None
        self.db.commit()
        self.db.refresh(classroom)
        return classroom

    # --- Personal -------------------------------------------------------------------------

    def list_staff(self, user: User) -> list[User]:
        query = select(User).where(
            User.institution_id == user.institution_id, User.role != Role.PARENT
        )
        return list(self.db.scalars(query.order_by(User.full_name)))

    def invite_staff(self, user: User, data: StaffInput) -> StaffResponse:
        try:
            email = normalize_email(data.email)
        except GuardianLinkError as exc:
            raise _invalid(exc.message) from exc
        if self.users.get_by_email(email) is not None:
            raise _conflict(f"El correo {email} ya está registrado")
        member = User(
            institution_id=user.institution_id,
            email=email,
            password_hash=None,
            full_name=" ".join(data.full_name.split()),
            role=Role(data.role),
        )
        self.db.add(member)
        self.db.commit()
        sent = self.invitations.invite(member)
        return StaffResponse.from_model(member, invitation_sent=sent)

    def resend_staff_invitation(self, user: User, member_id: int) -> StaffResponse:
        member = self._staff(user, member_id)
        sent = self.invitations.invite(member)
        return StaffResponse.from_model(member, invitation_sent=sent)

    def set_active(self, user: User, member_id: int, is_active: bool) -> User:
        member = self._staff(user, member_id)
        if member.id == user.id and not is_active:
            raise _invalid("No puedes desactivar tu propia cuenta")
        member.is_active = is_active
        self.db.commit()
        return member

    # --- Asignaciones ---------------------------------------------------------------------

    def list_assignments(self, user: User, classroom_id: int | None) -> list[AssignmentResponse]:
        query = (
            select(CourseAssignment, Classroom, Subject, User)
            .join(Classroom, Classroom.id == CourseAssignment.classroom_id)
            .join(Subject, Subject.id == CourseAssignment.subject_id)
            .join(User, User.id == CourseAssignment.teacher_id)
            .where(Classroom.institution_id == user.institution_id)
            .order_by(Classroom.year.desc(), Classroom.grade, Classroom.section, Subject.name)
        )
        if classroom_id is not None:
            query = query.where(Classroom.id == classroom_id)
        return [AssignmentResponse.from_model(*row) for row in self.db.execute(query).all()]

    def assign(self, user: User, data: AssignmentInput) -> AssignmentResponse:
        classroom = self._classroom(user, data.classroom_id)
        subject = self._subject(user, data.subject_id)
        teacher = self._teacher(user, data.teacher_id)
        taken = self.db.scalar(
            select(func.count())
            .select_from(CourseAssignment)
            .where(
                CourseAssignment.classroom_id == classroom.id,
                CourseAssignment.subject_id == subject.id,
            )
        )
        if taken:
            raise _conflict(f"{subject.name} ya tiene docente en {classroom.label}")
        assignment = CourseAssignment(
            classroom_id=classroom.id, subject_id=subject.id, teacher_id=teacher.id
        )
        self.db.add(assignment)
        self.db.commit()
        return AssignmentResponse.from_model(assignment, classroom, subject, teacher)

    def unassign(self, user: User, assignment_id: int) -> None:
        assignment = self.db.get(CourseAssignment, assignment_id)
        if assignment is None:
            raise NotFoundError("Assignment not found")
        self._classroom(user, assignment.classroom_id)
        self.db.delete(assignment)
        self.db.commit()

    # --- Búsquedas con control de institución --------------------------------------------

    def _classroom(self, user: User, classroom_id: int) -> Classroom:
        classroom = self.db.get(Classroom, classroom_id)
        if classroom is None or classroom.institution_id != user.institution_id:
            raise NotFoundError("Classroom not found")
        return classroom

    def _subject(self, user: User, subject_id: int) -> Subject:
        subject = self.academic.get_subject(subject_id)
        if subject is None or subject.institution_id != user.institution_id:
            raise NotFoundError("Subject not found")
        return subject

    def _staff(self, user: User, member_id: int) -> User:
        member = self.db.get(User, member_id)
        if member is None or member.institution_id != user.institution_id:
            raise NotFoundError("User not found")
        if member.role == Role.PARENT:
            raise NotFoundError("User not found")
        return member

    def _teacher(self, user: User, teacher_id: int | None) -> User:
        teacher = self.db.get(User, teacher_id) if teacher_id else None
        if (
            teacher is None
            or teacher.institution_id != user.institution_id
            or teacher.role != Role.TEACHER
            or not teacher.is_active
        ):
            raise _invalid("El docente elegido no existe o está desactivado")
        return teacher
