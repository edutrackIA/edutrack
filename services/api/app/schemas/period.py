from datetime import date

from pydantic import BaseModel

from app.domain import AcademicPeriod


class PeriodResponse(BaseModel):
    id: int
    year: int
    bimester: int
    start_date: date
    end_date: date
    label: str

    @classmethod
    def from_model(cls, period: AcademicPeriod) -> "PeriodResponse":
        return cls(
            id=period.id,
            year=period.year,
            bimester=period.bimester,
            start_date=period.start_date,
            end_date=period.end_date,
            label=f"Bimestre {period.bimester}, {period.year}",
        )
