from datetime import datetime

from sqlalchemy import BigInteger, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.time import utcnow
from app.domain.enums import DataRequestKind, DataRequestStatus
from app.domain.student import Student
from app.domain.types import BigIntPK
from app.domain.user import User


class PrivacyConsent(Base):
    """A guardian accepted a given version of the privacy notice (Ley N.° 29733)."""

    __tablename__ = "privacy_consents"
    __table_args__ = (UniqueConstraint("user_id", "notice_version"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    notice_version: Mapped[str] = mapped_column(String(20))
    accepted_at: Mapped[datetime] = mapped_column(default=utcnow)


class DataRequest(Base):
    """A data subject rights request (access, rectification, cancellation, opposition)."""

    __tablename__ = "data_requests"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    institution_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("institutions.id"))
    requester_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[DataRequestKind] = mapped_column(Enum(DataRequestKind, name="data_request_kind"))
    details: Mapped[str] = mapped_column(Text)
    status: Mapped[DataRequestStatus] = mapped_column(
        Enum(DataRequestStatus, name="data_request_status"), default=DataRequestStatus.PENDING
    )
    response: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    resolved_at: Mapped[datetime | None]
    resolved_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))

    requester: Mapped[User] = relationship(foreign_keys=[requester_id])
    student: Mapped[Student] = relationship()
