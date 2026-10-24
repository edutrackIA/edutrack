from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain import FamilySurvey


class SurveyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_for_period(self, *, student_id: int, period_id: int) -> FamilySurvey | None:
        return self.db.scalar(
            select(FamilySurvey).where(
                FamilySurvey.student_id == student_id, FamilySurvey.period_id == period_id
            )
        )

    def list_for_student(self, student_id: int) -> list[FamilySurvey]:
        query = (
            select(FamilySurvey)
            .where(FamilySurvey.student_id == student_id)
            .order_by(FamilySurvey.period_id.desc())
        )
        return list(self.db.scalars(query))

    def add(self, survey: FamilySurvey) -> FamilySurvey:
        self.db.add(survey)
        self.db.flush()
        return survey
