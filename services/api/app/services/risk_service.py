from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, UnprocessableError
from app.core.time import utcnow
from app.domain import RiskAssessment, RiskLevel, RiskThreshold, Student, User
from app.repositories.academic_repository import AcademicRepository
from app.repositories.classroom_repository import ClassroomRepository
from app.repositories.risk_repository import RiskRepository
from app.repositories.student_repository import StudentRepository
from app.schemas.risk import RiskThresholds, RunRiskResponse, SkippedStudent
from app.services.access_policy import AccessPolicy
from app.services.recommendation_service import RecommendationService
from app.services.risk.features import FeatureBuilder
from app.services.risk.ml_client import MlClient


class RiskService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.risk = RiskRepository(db)
        self.academic = AcademicRepository(db)
        self.classrooms = ClassroomRepository(db)
        self.students = StudentRepository(db)
        self.features = FeatureBuilder(db)
        self.policy = AccessPolicy(db)
        self.recommendations = RecommendationService(db)

    def run(
        self, user: User, ml: MlClient, *, period_id: int, classroom_id: int | None = None
    ) -> RunRiskResponse:
        period = self.academic.get_period(period_id)
        if period is None or period.institution_id != user.institution_id:
            raise UnprocessableError(f"Invalid period {period_id}")
        if classroom_id is not None:
            classroom = self.classrooms.get(classroom_id)
            if classroom is None or classroom.institution_id != user.institution_id:
                raise UnprocessableError(f"Invalid classroom {classroom_id}")

        requests: list[dict] = []
        skipped: list[SkippedStudent] = []
        students = {
            student.id: student
            for student in self.students.list_for_institution(user.institution_id, classroom_id)
        }
        for student in students.values():
            result = self.features.build(student, period)
            if result.features is None:
                skipped.append(SkippedStudent(student_id=student.id, reason=result.missing or ""))
            else:
                requests.append({"student_id": student.id, "features": result.features})

        by_level = dict.fromkeys(RiskLevel, 0)
        if not requests:
            return RunRiskResponse(
                evaluated=0,
                skipped=len(skipped),
                model_version=None,
                by_level=by_level,
                skipped_students=skipped,
            )

        version, predictions = ml.predict_batch(requests)
        thresholds = self.risk.get_thresholds(user.institution_id)
        for prediction in predictions:
            level = thresholds.classify(prediction["probability"])
            assessment = self._save(prediction, period.id, version, level)
            self.recommendations.refresh_for(students[prediction["student_id"]], assessment)
            by_level[level] += 1

        self.db.commit()
        return RunRiskResponse(
            evaluated=len(predictions),
            skipped=len(skipped),
            model_version=version,
            by_level=by_level,
            skipped_students=skipped,
        )

    def history(self, user: User, student_id: int) -> list[RiskAssessment]:
        student = self.students.get(student_id)
        if student is None:
            raise NotFoundError("Student not found")
        self.policy.ensure_can_view_risk(user, student)
        return self.risk.list_for_student(student.id)

    def latest_for(self, user: User, students: list[Student]) -> dict[int, RiskAssessment]:
        if not self.policy.can_see_risk(user):
            return {}
        return self.risk.latest_for_students([student.id for student in students])

    def get_thresholds(self, user: User) -> RiskThreshold:
        return self.risk.get_thresholds(user.institution_id)

    def update_thresholds(self, user: User, data: RiskThresholds) -> RiskThreshold:
        thresholds = self.risk.save_thresholds(
            RiskThreshold(
                institution_id=user.institution_id,
                medium_from=data.medium_from,
                high_from=data.high_from,
                updated_by=user.id,
                updated_at=utcnow(),
            )
        )
        self.db.commit()
        return thresholds

    def _save(
        self, prediction: dict, period_id: int, version: str, level: RiskLevel
    ) -> RiskAssessment:
        existing = self.risk.get_assessment(
            student_id=prediction["student_id"], period_id=period_id, model_version=version
        )
        if existing is None:
            return self.risk.add_assessment(
                RiskAssessment(
                    student_id=prediction["student_id"],
                    period_id=period_id,
                    probability=prediction["probability"],
                    level=level,
                    model_version=version,
                    top_factors=prediction["top_factors"],
                )
            )
        existing.probability = prediction["probability"]
        existing.level = level
        existing.top_factors = prediction["top_factors"]
        existing.created_at = utcnow()
        self.db.flush()
        return existing
