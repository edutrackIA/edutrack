from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ConflictError, NotFoundError
from app.core.time import month_start, utcnow
from app.domain import FamilyCheckin, Role, Student, User
from app.repositories.student_repository import StudentRepository
from app.schemas.family_checkin import FamilyCheckinInput
from app.services.access_policy import AccessPolicy
from app.services.notifications.delivery import deliver
from app.services.notifications.email_sender import EmailSender
from app.services.notifications.templates import StaffNoticeEmail
from app.services.privacy_service import PrivacyService


class FamilyCheckinService:
    def __init__(self, db: Session, sender: EmailSender, today: date) -> None:
        self.db = db
        self.sender = sender
        self.month = month_start(today)
        self.students = StudentRepository(db)
        self.policy = AccessPolicy(db)

    # --- Familia --------------------------------------------------------------------

    def current(self, user: User, student_id: int) -> FamilyCheckin | None:
        student = self._get_student(student_id)
        self.policy.ensure_is_guardian(user, student)
        return self._for_month(student.id)

    def submit(self, user: User, student_id: int, data: FamilyCheckinInput) -> FamilyCheckin:
        """Create or edit this month's check-in. Each edit goes back to the tutor."""
        PrivacyService(self.db).ensure_consent(user)
        student = self._get_student(student_id)
        self.policy.ensure_is_guardian(user, student)

        checkin = self._for_month(student.id)
        raised_concern = data.peer_concern and not (checkin and checkin.peer_concern)
        if checkin is None:
            checkin = FamilyCheckin(student_id=student.id, month=self.month)
            self.db.add(checkin)
        checkin.guardian_id = user.id
        checkin.mood = data.mood
        checkin.home_changes = sorted({change.value for change in data.home_changes})
        checkin.peer_concern = data.peer_concern
        checkin.comment = (data.comment or "").strip() or None
        checkin.submitted_at = utcnow()
        checkin.reviewed_at = None
        checkin.reviewed_by = None
        self.db.flush()

        if raised_concern:
            self._alert_tutor(student)
        self.db.commit()
        return checkin

    # --- Tutor ------------------------------------------------------------------------

    def pending(self, user: User) -> list[FamilyCheckin]:
        query = (
            select(FamilyCheckin)
            .join(Student, Student.id == FamilyCheckin.student_id)
            .where(
                Student.institution_id == user.institution_id, FamilyCheckin.reviewed_at.is_(None)
            )
            .order_by(FamilyCheckin.peer_concern.desc(), FamilyCheckin.submitted_at.desc())
        )
        if user.role != Role.DIRECTOR:
            query = query.where(Student.classroom_id.in_(self.policy.tutored_ids(user)))
        return [checkin for checkin in self.db.scalars(query) if checkin.needs_attention]

    def review(self, user: User, checkin_id: int) -> FamilyCheckin:
        checkin = self.db.get(FamilyCheckin, checkin_id)
        if checkin is None:
            raise NotFoundError("Check-in not found")
        self.policy.ensure_can_manage_commitments(user, checkin.student)
        if checkin.reviewed_at is not None:
            raise ConflictError("The check-in was already reviewed")
        checkin.reviewed_at = utcnow()
        checkin.reviewed_by = user.id
        self.db.commit()
        return checkin

    # --- Internos ----------------------------------------------------------------------

    def _for_month(self, student_id: int) -> FamilyCheckin | None:
        return self.db.scalar(
            select(FamilyCheckin).where(
                FamilyCheckin.student_id == student_id, FamilyCheckin.month == self.month
            )
        )

    def _alert_tutor(self, student: Student) -> None:
        """A possible bullying report from the family reaches the tutor right away."""
        tutor = student.classroom.tutor
        if tutor is None:
            return
        name = f"{student.first_name} {student.last_name}"
        email = StaffNoticeEmail(
            recipient_name=tutor.full_name.split()[0],
            subject=f"Prioritario: la familia de {name} reporta una preocupación",
            paragraphs=[
                f"La familia de {name} indicó que le preocupa cómo lo tratan sus compañeros.",
                "Revisa el reporte en el seguimiento semanal y, si corresponde, activa el "
                "protocolo de convivencia escolar.",
            ],
            portal_url=f"{get_settings().portal_url}/seguimiento",
        )
        deliver(
            self.sender, to=tutor.email, subject=email.subject, text=email.text(), html=email.html()
        )

    def _get_student(self, student_id: int) -> Student:
        student = self.students.get(student_id)
        if student is None:
            raise NotFoundError("Student not found")
        return student
