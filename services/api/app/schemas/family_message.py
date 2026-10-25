from datetime import date, datetime

from pydantic import BaseModel

from app.domain import FamilyMessage, FamilyMessageKind, FamilyMessageStatus
from app.schemas.student import StudentListItem
from app.services.family_message_service import KIND_LABELS


class FamilyMessageResponse(BaseModel):
    id: int
    student: StudentListItem
    kind: FamilyMessageKind
    kind_label: str
    reference_date: date
    status: FamilyMessageStatus
    subject: str
    intro: str
    rows: list[tuple[str, str]]
    hold_reason: str | None
    created_at: datetime
    sent_at: datetime | None

    @classmethod
    def from_model(cls, message: FamilyMessage) -> "FamilyMessageResponse":
        return cls(
            id=message.id,
            student=StudentListItem.from_model(message.student),
            kind=message.kind,
            kind_label=KIND_LABELS[message.kind],
            reference_date=message.reference_date,
            status=message.status,
            subject=message.subject,
            intro=message.content["intro"],
            rows=[(label, value) for label, value in message.content["rows"]],
            hold_reason=message.hold_reason,
            created_at=message.created_at,
            sent_at=message.sent_at,
        )
