from collections import Counter
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.errors import UnprocessableError
from app.domain import AcademicPeriod, RiskAssessment, RiskLevel, Student, User
from app.repositories.academic_repository import AcademicRepository
from app.repositories.classroom_repository import ClassroomRepository
from app.repositories.risk_repository import RiskRepository
from app.repositories.student_repository import StudentRepository
from app.schemas.dashboard import ClassroomRiskSummary, DashboardSummary, FactorFrequency
from app.services.risk.features import FEATURE_LABELS

FACTORS_PER_STUDENT = 3
RISK_LEVELS_WITH_FACTORS = {RiskLevel.MEDIUM, RiskLevel.HIGH}
TOP_FACTORS = 5


def period_label(period: AcademicPeriod) -> str:
    return f"{period.year} · Bimestre {period.bimester}"


@dataclass
class EvaluatedStudents:
    period: AcademicPeriod | None
    students: list[Student]
    assessments: dict[int, RiskAssessment]


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.risk = RiskRepository(db)
        self.academic = AcademicRepository(db)
        self.classrooms = ClassroomRepository(db)
        self.students = StudentRepository(db)

    def load(
        self, user: User, period_id: int | None, classroom_id: int | None = None
    ) -> EvaluatedStudents:
        """Students of the institution and their latest assessment for the period.

        Without a period, the most recent period that has assessments is used.
        """
        if period_id is None:
            period = self.risk.latest_evaluated_period(user.institution_id)
        else:
            period = self.academic.get_period(period_id)
            if period is None or period.institution_id != user.institution_id:
                raise UnprocessableError(f"Invalid period {period_id}")
        if classroom_id is not None:
            classroom = self.classrooms.get(classroom_id)
            if classroom is None or classroom.institution_id != user.institution_id:
                raise UnprocessableError(f"Invalid classroom {classroom_id}")

        students = self.students.list_for_institution(user.institution_id, classroom_id)
        assessments = (
            self.risk.latest_for_period([s.id for s in students], period.id) if period else {}
        )
        return EvaluatedStudents(period=period, students=students, assessments=assessments)

    def summary(self, user: User, period_id: int | None) -> DashboardSummary:
        data = self.load(user, period_id)
        by_level = dict.fromkeys(RiskLevel, 0)
        classrooms: dict[int, ClassroomRiskSummary] = {}
        factors: Counter[str] = Counter()

        for student in data.students:
            summary = classrooms.setdefault(
                student.classroom_id,
                ClassroomRiskSummary(
                    classroom_id=student.classroom_id,
                    label=student.classroom.label,
                    evaluated=0,
                    low=0,
                    medium=0,
                    high=0,
                ),
            )
            assessment = data.assessments.get(student.id)
            if assessment is None:
                continue
            by_level[assessment.level] += 1
            summary.evaluated += 1
            level_field = assessment.level.value.lower()
            setattr(summary, level_field, getattr(summary, level_field) + 1)
            # Factors only explain something when there is risk to explain.
            if assessment.level in RISK_LEVELS_WITH_FACTORS:
                factors.update(
                    factor["feature"] for factor in assessment.top_factors[:FACTORS_PER_STUDENT]
                )

        return DashboardSummary(
            period_id=data.period.id if data.period else None,
            period_label=period_label(data.period) if data.period else None,
            total_students=len(data.students),
            evaluated_students=len(data.assessments),
            by_level=by_level,
            by_classroom=sorted(classrooms.values(), key=lambda item: item.label),
            top_factors=[
                FactorFrequency(
                    feature=feature, label=FEATURE_LABELS.get(feature, feature), frequency=count
                )
                for feature, count in factors.most_common(TOP_FACTORS)
            ],
        )
