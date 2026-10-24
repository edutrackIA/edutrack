from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain import RiskAssessment, RiskThreshold
from app.domain.risk import DEFAULT_HIGH_FROM, DEFAULT_MEDIUM_FROM


class RiskRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_thresholds(self, institution_id: int) -> RiskThreshold:
        """Stored thresholds, or the defaults (not persisted) if none were configured."""
        thresholds = self.db.get(RiskThreshold, institution_id)
        if thresholds is None:
            thresholds = RiskThreshold(
                institution_id=institution_id,
                medium_from=DEFAULT_MEDIUM_FROM,
                high_from=DEFAULT_HIGH_FROM,
            )
        return thresholds

    def save_thresholds(self, thresholds: RiskThreshold) -> RiskThreshold:
        merged = self.db.merge(thresholds)
        self.db.flush()
        return merged

    def get_assessment(
        self, *, student_id: int, period_id: int, model_version: str
    ) -> RiskAssessment | None:
        return self.db.scalar(
            select(RiskAssessment).where(
                RiskAssessment.student_id == student_id,
                RiskAssessment.period_id == period_id,
                RiskAssessment.model_version == model_version,
            )
        )

    def add_assessment(self, assessment: RiskAssessment) -> RiskAssessment:
        self.db.add(assessment)
        self.db.flush()
        return assessment

    def list_for_student(self, student_id: int) -> list[RiskAssessment]:
        query = (
            select(RiskAssessment)
            .where(RiskAssessment.student_id == student_id)
            .order_by(RiskAssessment.created_at.desc(), RiskAssessment.id.desc())
        )
        return list(self.db.scalars(query))

    def latest_for_students(self, student_ids: list[int]) -> dict[int, RiskAssessment]:
        if not student_ids:
            return {}
        query = (
            select(RiskAssessment)
            .where(RiskAssessment.student_id.in_(student_ids))
            .order_by(RiskAssessment.created_at, RiskAssessment.id)
        )
        latest: dict[int, RiskAssessment] = {}
        for assessment in self.db.scalars(query):
            latest[assessment.student_id] = assessment
        return latest
