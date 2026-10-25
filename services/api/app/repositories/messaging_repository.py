from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain import (
    FamilyMessage,
    FamilyMessageKind,
    FamilyMessageStatus,
    NotificationLog,
    Student,
)


class MessagingRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, message_id: int) -> FamilyMessage | None:
        return self.db.get(FamilyMessage, message_id)

    def exists(self, *, student_id: int, kind: FamilyMessageKind, reference_date: date) -> bool:
        query = select(FamilyMessage.id).where(
            FamilyMessage.student_id == student_id,
            FamilyMessage.kind == kind,
            FamilyMessage.reference_date == reference_date,
        )
        return self.db.scalar(query) is not None

    def add(self, message: FamilyMessage) -> FamilyMessage:
        self.db.add(message)
        self.db.flush()
        return message

    def list_for_review(
        self,
        institution_id: int,
        *,
        status: FamilyMessageStatus,
        classroom_ids: set[int] | None,
    ) -> list[FamilyMessage]:
        query = (
            select(FamilyMessage)
            .join(Student, Student.id == FamilyMessage.student_id)
            .where(Student.institution_id == institution_id, FamilyMessage.status == status)
            .order_by(FamilyMessage.created_at.desc(), FamilyMessage.id.desc())
        )
        if classroom_ids is not None:
            query = query.where(Student.classroom_id.in_(classroom_ids))
        return list(self.db.scalars(query))

    def already_notified(self, *, kind: str, recipient_id: int, reference: str) -> bool:
        query = select(NotificationLog.id).where(
            NotificationLog.kind == kind,
            NotificationLog.recipient_id == recipient_id,
            NotificationLog.reference == reference,
        )
        return self.db.scalar(query) is not None

    def log_notice(self, *, kind: str, recipient_id: int, reference: str) -> None:
        self.db.add(NotificationLog(kind=kind, recipient_id=recipient_id, reference=reference))
        self.db.flush()
