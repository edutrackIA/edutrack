from datetime import date, datetime

from sqlalchemy import BigInteger, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utcnow
from app.domain.enums import SituationAction, SituationKind
from app.domain.types import BigIntPK


class StudentSituation(Base):
    """Context known by the tutor that changes how the student should be supported."""

    __tablename__ = "student_situations"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[SituationKind] = mapped_column(Enum(SituationKind, name="situation_kind"))
    note: Mapped[str | None] = mapped_column(String(500))
    started_on: Mapped[date]
    resolved_on: Mapped[date | None]
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    @property
    def is_active(self) -> bool:
        return self.resolved_on is None


class SituationEvent(Base):
    """Audit trail: who created, edited or resolved each situation, and when."""

    __tablename__ = "situation_events"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    situation_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("student_situations.id", ondelete="CASCADE"), index=True
    )
    action: Mapped[SituationAction] = mapped_column(
        Enum(SituationAction, name="situation_action")
    )
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class WeeklyCheckin(Base):
    """The tutor's confirmation that the classroom was reviewed during a school week."""

    __tablename__ = "weekly_checkins"
    __table_args__ = (UniqueConstraint("classroom_id", "week_start"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    classroom_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("classrooms.id", ondelete="CASCADE")
    )
    week_start: Mapped[date]
    completed_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    completed_at: Mapped[datetime] = mapped_column(default=utcnow)
