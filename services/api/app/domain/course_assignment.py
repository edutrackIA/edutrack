from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.domain.types import BigIntPK


class CourseAssignment(Base):
    __tablename__ = "course_assignments"
    __table_args__ = (UniqueConstraint("classroom_id", "subject_id"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    classroom_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("classrooms.id"))
    subject_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("subjects.id"))
    teacher_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
