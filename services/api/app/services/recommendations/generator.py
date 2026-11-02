from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.domain import AcademicPeriod, AttendanceStatus, RiskAssessment, RiskLevel, Student
from app.repositories.academic_repository import AcademicRepository
from app.repositories.risk_repository import RiskRepository
from app.repositories.situation_repository import SituationRepository
from app.services.recommendations.catalog import TEACHER_ROUTINE
from app.services.recommendations.engine import Facts, compose, load_rules
from app.services.risk.features import PASSING_SCORE, FeatureBuilder

BEST_SUBJECT_SCORE = 16
WEEKEND_ADJACENT_DAYS = {0, 4}  # Monday and Friday
LEVEL_RANK = {RiskLevel.LOW: 0, RiskLevel.MEDIUM: 1, RiskLevel.HIGH: 2}


@dataclass
class GeneratedRecommendation:
    parent_items: list[str]
    teacher_items: list[str]


class RecommendationGenerator:
    def __init__(self, db: Session) -> None:
        self.academic = AcademicRepository(db)
        self.risk = RiskRepository(db)
        self.situations = SituationRepository(db)
        self.features = FeatureBuilder(db)

    def generate(self, student: Student, assessment: RiskAssessment) -> GeneratedRecommendation:
        composition = compose(load_rules(), self.facts(student, assessment))
        return GeneratedRecommendation(
            parent_items=composition.parent_items,
            teacher_items=composition.teacher_items or [TEACHER_ROUTINE],
        )

    def facts(self, student: Student, assessment: RiskAssessment) -> Facts:
        period = self.academic.get_period(assessment.period_id)
        values: dict[str, Any] = {
            factor["feature"]: factor["value"] for factor in assessment.top_factors
        }
        values["top_factors"] = [factor["feature"] for factor in assessment.top_factors]
        failing: list[str] = []
        best_subject: str | None = None
        risk_periods = 0

        if period is not None:
            built = self.features.build(student, period)
            if built.features:
                values.update(built.features)
            failing, best_subject = self._subjects(student, period)
            values.update(self._attendance(student, period))
            values.update(self._history(student, assessment, period))
            risk_periods = values["consecutive_risk_periods"]

        values["failing_subjects"] = failing
        values["has_best_subject"] = best_subject is not None
        tutor = student.classroom.tutor

        return Facts(
            level=assessment.level,
            values=values,
            situations={
                situation.kind
                for situation in self.situations.list_for_student(
                    student.id, include_resolved=False
                )
            },
            placeholders={
                "name": student.first_name,
                "subjects": ", ".join(failing) or "los cursos con notas más bajas",
                "best_subject": best_subject or "",
                "tutor": tutor.full_name if tutor else "el tutor",
                "risk_periods": str(risk_periods),
            },
            seed=student.id * 31 + assessment.period_id,
        )

    def _subjects(self, student: Student, period: AcademicPeriod) -> tuple[list[str], str | None]:
        grades = self.academic.list_grades(student.id, period.id)
        failing = [grade.subject.name for grade in grades if grade.score < PASSING_SCORE]
        best = max(grades, key=lambda grade: grade.score, default=None)
        best_subject = best.subject.name if best and best.score >= BEST_SUBJECT_SCORE else None
        return failing, best_subject

    def _attendance(self, student: Student, period: AcademicPeriod) -> dict[str, Any]:
        records = self.academic.attendance_records(student.id, period.start_date, period.end_date)
        absences = [record for record in records if record.status == AttendanceStatus.ABSENT]
        justified = [record for record in records if record.status == AttendanceStatus.JUSTIFIED]
        weekend_adjacent = [
            record for record in absences if record.date.weekday() in WEEKEND_ADJACENT_DAYS
        ]
        return {
            "absences": len(absences),
            "justified_absences": len(justified),
            "monday_friday_absence_share": (
                len(weekend_adjacent) / len(absences) if absences else 0.0
            ),
        }

    def _history(
        self, student: Student, assessment: RiskAssessment, period: AcademicPeriod
    ) -> dict[str, Any]:
        latest_by_period: dict[int, RiskAssessment] = {}
        for item in self.risk.list_for_student(student.id):  # newest first
            latest_by_period.setdefault(item.period_id, item)
        latest_by_period[period.id] = assessment

        previous_period = self.academic.previous_period(period)
        previous = latest_by_period.get(previous_period.id) if previous_period else None

        consecutive = 0
        cursor: AcademicPeriod | None = period
        while cursor is not None:
            item = latest_by_period.get(cursor.id)
            if item is None or item.level == RiskLevel.LOW:
                break
            consecutive += 1
            cursor = self.academic.previous_period(cursor)

        previous_average = None
        if previous_period is not None:
            grades = self.academic.list_grades(student.id, previous_period.id)
            if grades:
                previous_average = sum(grade.score for grade in grades) / len(grades)

        return {
            "previous_level": previous.level.value if previous else None,
            "improved": previous is not None
            and LEVEL_RANK[assessment.level] < LEVEL_RANK[previous.level],
            "consecutive_risk_periods": consecutive,
            "previous_avg_score": previous_average,
        }
