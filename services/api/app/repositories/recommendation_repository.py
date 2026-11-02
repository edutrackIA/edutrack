from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.domain import Alert, Recommendation, RecommendationStatus, RiskAssessment, Student


class RecommendationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, recommendation_id: int) -> Recommendation | None:
        return self.db.get(Recommendation, recommendation_id)

    def get_for_assessment(self, assessment_id: int) -> Recommendation | None:
        return self.db.scalar(
            select(Recommendation).where(Recommendation.assessment_id == assessment_id)
        )

    def add(self, recommendation: Recommendation) -> Recommendation:
        self.db.add(recommendation)
        self.db.flush()
        return recommendation

    def list_for_student(self, student_id: int) -> list[Recommendation]:
        query = (
            select(Recommendation)
            .where(Recommendation.student_id == student_id)
            .order_by(Recommendation.created_at.desc(), Recommendation.id.desc())
        )
        return list(self.db.scalars(query))

    def latest_approved(self, student_id: int) -> Recommendation | None:
        return self.db.scalar(
            select(Recommendation)
            .where(
                Recommendation.student_id == student_id,
                Recommendation.status == RecommendationStatus.APPROVED,
            )
            .order_by(Recommendation.reviewed_at.desc(), Recommendation.id.desc())
            .limit(1)
        )

    def list_queue(
        self,
        institution_id: int,
        *,
        status: RecommendationStatus | None,
        classroom_ids: set[int] | None,
    ) -> list[Recommendation]:
        query = (
            select(Recommendation)
            .join(Student, Student.id == Recommendation.student_id)
            .where(Student.institution_id == institution_id)
            .order_by(Recommendation.created_at.desc(), Recommendation.id.desc())
            # Everything the response needs, in a fixed number of queries (no N+1).
            .options(
                selectinload(Recommendation.student).options(
                    joinedload(Student.classroom), selectinload(Student.guardians)
                ),
                selectinload(Recommendation.assessment),
            )
        )
        if status is not None:
            query = query.where(Recommendation.status == status)
        if classroom_ids is not None:
            query = query.where(Student.classroom_id.in_(classroom_ids))
        return list(self.db.scalars(query))


class AlertRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, alert_id: int) -> Alert | None:
        return self.db.get(Alert, alert_id)

    def exists(self, *, assessment_id: int, recipient_id: int) -> bool:
        query = select(Alert.id).where(
            Alert.assessment_id == assessment_id, Alert.recipient_id == recipient_id
        )
        return self.db.scalar(query) is not None

    def add(self, alert: Alert) -> Alert:
        self.db.add(alert)
        self.db.flush()
        return alert

    def list_for_recipient(
        self, recipient_id: int, *, unread: bool | None, offset: int, limit: int
    ) -> tuple[int, list[Alert]]:
        query = select(Alert).where(Alert.recipient_id == recipient_id)
        if unread is not None:
            query = query.where(Alert.is_read.is_(not unread))
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = self.db.scalars(
            query.order_by(Alert.created_at.desc(), Alert.id.desc())
            .offset(offset)
            .limit(limit)
            .options(
                selectinload(Alert.assessment)
                .selectinload(RiskAssessment.student)
                .joinedload(Student.classroom)
            )
        )
        return total, list(items)
