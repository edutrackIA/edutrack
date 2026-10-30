from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ConflictError, NotFoundError
from app.core.time import utcnow
from app.domain import (
    FamilyMessage,
    FamilyMessageKind,
    FamilyMessageStatus,
    Guardianship,
    Institution,
    Role,
    SituationKind,
    Student,
    StudentStatus,
    User,
)
from app.repositories.messaging_repository import MessagingRepository
from app.repositories.situation_repository import SituationRepository
from app.services.access_policy import AccessPolicy
from app.services.notifications.delivery import deliver
from app.services.notifications.email_sender import EmailSender
from app.services.notifications.templates import InformativeEmail
from app.services.situations.catalog import SITUATIONS

# Situations where an automatic data message could hurt: the tutor reviews it first.
HOLD_SITUATIONS = {SituationKind.GRIEF, SituationKind.HEALTH}

KIND_LABELS = {
    FamilyMessageKind.WEEKLY_ATTENDANCE: "Asistencia semanal",
    FamilyMessageKind.PERFECT_ATTENDANCE: "Asistencia perfecta del mes",
    FamilyMessageKind.PERIOD_GRADES: "Notas del bimestre",
}


class FamilyMessageService:
    def __init__(self, db: Session, sender: EmailSender) -> None:
        self.db = db
        self.sender = sender
        self.messages = MessagingRepository(db)
        self.situations = SituationRepository(db)
        self.policy = AccessPolicy(db)

    def publish(
        self,
        student: Student,
        *,
        kind: FamilyMessageKind,
        reference_date: date,
        subject: str,
        intro: str,
        rows: list[tuple[str, str]],
    ) -> FamilyMessage | None:
        """Create and send (or hold) a message. Returns None if it already existed."""
        if self.messages.exists(student_id=student.id, kind=kind, reference_date=reference_date):
            return None
        hold_reason = self._hold_reason(student)
        message = self.messages.add(
            FamilyMessage(
                student_id=student.id,
                kind=kind,
                reference_date=reference_date,
                status=FamilyMessageStatus.HELD if hold_reason else FamilyMessageStatus.SENT,
                subject=subject,
                content={"intro": intro, "rows": [list(row) for row in rows]},
                hold_reason=hold_reason,
            )
        )
        if hold_reason is None:
            self._send(message)
        return message

    # --- Revisión del tutor -----------------------------------------------------------

    def list_held(self, user: User) -> list[FamilyMessage]:
        classroom_ids = None if user.role == Role.DIRECTOR else self.policy.tutored_ids(user)
        return self.messages.list_for_review(
            user.institution_id, status=FamilyMessageStatus.HELD, classroom_ids=classroom_ids
        )

    def release(self, user: User, message_id: int) -> FamilyMessage:
        message = self._get_held(user, message_id)
        message.reviewed_by = user.id
        self._send(message)
        self.db.commit()
        return message

    def discard(self, user: User, message_id: int) -> FamilyMessage:
        message = self._get_held(user, message_id)
        message.reviewed_by = user.id
        message.status = FamilyMessageStatus.DISCARDED
        self.db.commit()
        return message

    # --- Internos -----------------------------------------------------------------------

    def _hold_reason(self, student: Student) -> str | None:
        for situation in self.situations.list_for_student(student.id, include_resolved=False):
            info = SITUATIONS[situation.kind]
            if situation.kind in HOLD_SITUATIONS or info.group == "TEAM":
                return f"Situación activa: {info.label}"
        return None

    def _send(self, message: FamilyMessage) -> None:
        student = message.student
        guardians = [guardian for guardian in student.guardians if guardian.is_active]
        institution = self.db.get(Institution, student.institution_id)
        content: dict[str, Any] = message.content
        delivered = bool(guardians)
        for guardian in guardians:
            email = InformativeEmail(
                guardian_name=guardian.full_name.split()[0],
                subject=message.subject,
                intro=content["intro"],
                rows=[(label, value) for label, value in content["rows"]],
                institution_name=institution.name if institution else "EduTrack",
                portal_url=get_settings().portal_url,
            )
            delivered &= deliver(
                self.sender,
                to=guardian.email,
                subject=email.subject,
                text=email.text(),
                html=email.html(),
            )
        message.status = FamilyMessageStatus.SENT if delivered else FamilyMessageStatus.FAILED
        message.sent_at = utcnow() if delivered else None

    def _get_held(self, user: User, message_id: int) -> FamilyMessage:
        message = self.messages.get(message_id)
        if message is None:
            raise NotFoundError("Message not found")
        self.policy.ensure_can_manage_commitments(user, message.student)
        if message.status != FamilyMessageStatus.HELD:
            raise ConflictError("The message was already reviewed")
        return message


def students_with_guardians(db: Session) -> list[Student]:
    query = (
        select(Student)
        .join(Guardianship, Guardianship.student_id == Student.id)
        .where(Student.status == StudentStatus.ENROLLED)
        .distinct()
        .order_by(Student.id)
    )
    return list(db.scalars(query))
