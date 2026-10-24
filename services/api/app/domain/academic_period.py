from datetime import date

from sqlalchemy import BigInteger, ForeignKey, SmallInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.domain.types import BigIntPK


class AcademicPeriod(Base):
    __tablename__ = "academic_periods"
    __table_args__ = (UniqueConstraint("institution_id", "year", "bimester"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    institution_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("institutions.id"))
    year: Mapped[int] = mapped_column(SmallInteger)
    bimester: Mapped[int] = mapped_column(SmallInteger)
    start_date: Mapped[date]
    end_date: Mapped[date]
