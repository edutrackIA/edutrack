from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.core.time import utcnow
from app.domain import (
    Alert,
    Recommendation,
    RecommendationStatus,
    RiskAssessment,
    RiskLevel,
    Role,
    Student,
    User,
)
from app.repositories.recommendation_repository import AlertRepository, RecommendationRepository
from app.repositories.student_repository import StudentRepository
from app.services.access_policy import AccessPolicy
from app.services.recommendations.generator import RecommendationGenerator

ALERT_LEVELS = {RiskLevel.MEDIUM, RiskLevel.HIGH}


class RecommendationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.recommendations = RecommendationRepository(db)
        self.alerts = AlertRepository(db)
        self.students = StudentRepository(db)
        self.generator = RecommendationGenerator(db)
        self.policy = AccessPolicy(db)

    # --- Generación (llamada desde la evaluación de riesgo) ---------------------

    def refresh_for(self, student: Student, assessment: RiskAssessment) -> None:
        """Create or regenerate the recommendation and alert the tutor if needed.

        Recommendations already reviewed by the tutor are never overwritten.
        """
        generated = self.generator.generate(student, assessment)
        recommendation = self.recommendations.get_for_assessment(assessment.id)
        if recommendation is None:
            self.recommendations.add(
                Recommendation(
                    assessment_id=assessment.id,
                    student_id=student.id,
                    period_id=assessment.period_id,
                    parent_items=generated.parent_items,
                    teacher_items=generated.teacher_items,
                )
            )
        elif recommendation.status == RecommendationStatus.PENDING_REVIEW:
            recommendation.parent_items = generated.parent_items
            recommendation.teacher_items = generated.teacher_items

        tutor_id = student.classroom.tutor_id
        if (
            assessment.level in ALERT_LEVELS
            and tutor_id is not None
            and not self.alerts.exists(assessment_id=assessment.id, recipient_id=tutor_id)
        ):
            self.alerts.add(Alert(assessment_id=assessment.id, recipient_id=tutor_id))

    # --- Revisión del tutor ----------------------------------------------------

    def queue(self, user: User, status: RecommendationStatus | None) -> list[Recommendation]:
        classroom_ids = None if user.role == Role.DIRECTOR else self.policy.tutored_ids(user)
        return self.recommendations.list_queue(
            user.institution_id, status=status, classroom_ids=classroom_ids
        )

    def list_for_student(self, user: User, student_id: int) -> list[Recommendation]:
        student = self._get_student(student_id)
        self.policy.ensure_can_view_risk(user, student)
        return self.recommendations.list_for_student(student.id)

    def update_items(self, user: User, recommendation_id: int, items: list[str]) -> Recommendation:
        recommendation = self._get_reviewable(user, recommendation_id)
        recommendation.parent_items = items
        self.db.commit()
        return recommendation

    def approve(self, user: User, recommendation_id: int) -> Recommendation:
        return self._review(user, recommendation_id, RecommendationStatus.APPROVED)

    def discard(self, user: User, recommendation_id: int) -> Recommendation:
        return self._review(user, recommendation_id, RecommendationStatus.DISCARDED)

    def latest_for_family(self, student: Student) -> Recommendation | None:
        return self.recommendations.latest_approved(student.id)

    # --- Alertas ---------------------------------------------------------------

    def list_alerts(
        self, user: User, *, unread: bool | None, page: int, size: int
    ) -> tuple[int, list[Alert]]:
        return self.alerts.list_for_recipient(
            user.id, unread=unread, offset=(page - 1) * size, limit=size
        )

    def mark_alert(self, user: User, alert_id: int, *, is_read: bool) -> Alert:
        alert = self.alerts.get(alert_id)
        if alert is None or alert.recipient_id != user.id:
            raise NotFoundError("Alert not found")
        alert.is_read = is_read
        self.db.commit()
        return alert

    # --- Internos --------------------------------------------------------------

    def _review(
        self, user: User, recommendation_id: int, status: RecommendationStatus
    ) -> Recommendation:
        recommendation = self._get_reviewable(user, recommendation_id)
        recommendation.status = status
        recommendation.reviewed_by = user.id
        recommendation.reviewed_at = utcnow()
        self.db.commit()
        return recommendation

    def _get_reviewable(self, user: User, recommendation_id: int) -> Recommendation:
        recommendation = self.recommendations.get(recommendation_id)
        if recommendation is None:
            raise NotFoundError("Recommendation not found")
        self.policy.ensure_can_manage_commitments(user, recommendation.student)
        if recommendation.status != RecommendationStatus.PENDING_REVIEW:
            raise ConflictError("The recommendation was already reviewed")
        return recommendation

    def _get_student(self, student_id: int) -> Student:
        student = self.students.get(student_id)
        if student is None:
            raise NotFoundError("Student not found")
        return student
