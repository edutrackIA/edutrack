from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.domain import RiskAssessment, RiskLevel, Student
from app.repositories.academic_repository import AcademicRepository
from app.services.recommendations import catalog
from app.services.risk.features import PASSING_SCORE


@dataclass
class GeneratedRecommendation:
    parent_items: list[str]
    teacher_items: list[str]


class RecommendationGenerator:
    def __init__(self, db: Session) -> None:
        self.academic = AcademicRepository(db)

    def generate(self, student: Student, assessment: RiskAssessment) -> GeneratedRecommendation:
        name = student.first_name
        if assessment.level == RiskLevel.LOW:
            return GeneratedRecommendation(
                parent_items=[item.format(name=name) for item in catalog.PARENT_POSITIVE],
                teacher_items=[catalog.TEACHER_ROUTINE],
            )

        subjects = self._failing_subjects(student, assessment.period_id)
        values = {"name": name, "subjects": subjects or "los cursos con notas más bajas"}
        factors = [
            factor["feature"]
            for factor in assessment.top_factors
            if factor["feature"] in catalog.PARENT_ACTIONS
        ]

        parent_items = [
            catalog.PARENT_ACTIONS[feature].format(**values)
            for feature in factors[: catalog.MAX_PARENT_ACTIONS]
        ]
        tutor = student.classroom.tutor.full_name if student.classroom.tutor else "el tutor"
        parent_items.append(catalog.PARENT_FOLLOW_UP.format(tutor=tutor, name=name))

        teacher_items = list(
            dict.fromkeys(catalog.TEACHER_ACTIONS[feature].format(**values) for feature in factors)
        )
        return GeneratedRecommendation(
            parent_items=parent_items,
            teacher_items=teacher_items or [catalog.TEACHER_ROUTINE],
        )

    def _failing_subjects(self, student: Student, period_id: int) -> str:
        grades = self.academic.list_grades(student.id, period_id)
        return ", ".join(grade.subject.name for grade in grades if grade.score < PASSING_SCORE)
