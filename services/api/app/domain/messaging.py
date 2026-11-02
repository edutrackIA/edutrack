from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.time import utcnow
from app.domain.enums import FamilyMessageKind, FamilyMessageStatus
from app.domain.student import Student
from app.domain.types import BigIntPK


class FamilyMessage(Base):
    """Automatic informative message (attendance, grades). Only data, never advice."""

    __tablename__ = "family_messages"
    __table_args__ = (UniqueConstraint("student_id", "kind", "reference_date"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[FamilyMessageKind] = mapped_column(
        Enum(FamilyMessageKind, name="family_message_kind")
    )
    # Week, month or period the message is about; with `kind` it makes sending idempotent.
    reference_date: Mapped[date]
    status: Mapped[FamilyMessageStatus] = mapped_column(
        Enum(FamilyMessageStatus, name="family_message_status")
    )
    subject: Mapped[str] = mapped_column(String(200))
    content: Mapped[dict[str, Any]] = mapped_column(JSON)
    hold_reason: Mapped[str | None] = mapped_column(String(200))
    reviewed_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    sent_at: Mapped[datetime | None]

    student: Mapped[Student] = relationship()


class NotificationLog(Base):
    """Notices already sent to staff, so a job that runs twice never repeats an email."""

    __tablename__ = "notification_log"
    __table_args__ = (UniqueConstraint("kind", "recipient_id", "reference"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    kind: Mapped[str] = mapped_column(String(40))
    recipient_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    reference: Mapped[str] = mapped_column(String(100))
    sent_at: Mapped[datetime] = mapped_column(default=utcnow)
