from datetime import date, datetime

from sqlalchemy import JSON, BigInteger, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.time import utcnow
from app.domain.enums import FamilyMood
from app.domain.student import Student
from app.domain.types import BigIntPK


class FamilyCheckin(Base):
    """Monthly note from the family: how they see the student and what changed at home."""

    __tablename__ = "family_checkins"
    __table_args__ = (UniqueConstraint("student_id", "month"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    guardian_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    month: Mapped[date]
    mood: Mapped[FamilyMood] = mapped_column(Enum(FamilyMood, name="family_mood"))
    home_changes: Mapped[list[str]] = mapped_column(JSON)
    peer_concern: Mapped[bool] = mapped_column(default=False)
    comment: Mapped[str | None] = mapped_column(String(500))
    submitted_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)
    reviewed_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None]

    student: Mapped[Student] = relationship()

    @property
    def needs_attention(self) -> bool:
        return bool(
            self.peer_concern
            or self.home_changes
            or self.mood == FamilyMood.WORRIED
            or self.comment
        )
