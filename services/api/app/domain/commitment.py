from datetime import date, datetime

from sqlalchemy import BigInteger, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utcnow
from app.domain.enums import CommitmentStatus
from app.domain.types import BigIntPK


class Commitment(Base):
    __tablename__ = "commitments"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    tutor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    guardian_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    meeting_date: Mapped[date]
    agreements: Mapped[str] = mapped_column(Text)
    follow_up_date: Mapped[date | None]
    status: Mapped[CommitmentStatus] = mapped_column(
        Enum(CommitmentStatus, name="commitment_status"), default=CommitmentStatus.OPEN
    )
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
