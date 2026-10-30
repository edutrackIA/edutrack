"""Builds the model's feature vector for a student and period from EduTrack data."""

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.domain import AcademicPeriod, AttendanceStatus, Student
from app.repositories.academic_repository import AcademicRepository
from app.repositories.survey_repository import SurveyRepository

PASSING_SCORE = 11
NEUTRAL_BEHAVIOR = 3

FEATURE_LABELS = {
    "avg_score": "Promedio",
    "failed_subjects": "Cursos desaprobados",
    "score_trend": "Tendencia de notas",
    "attendance_rate": "Asistencia",
    "late_count": "Tardanzas",
    "behavior_rating": "Conducta",
    "study_hours_week": "Horas de estudio",
    "parent_education": "Educación de los padres",
    "home_internet": "Internet en casa",
    "has_study_device": "Dispositivo de estudio",
    "family_communication": "Comunicación familiar",
    "student_works": "Trabajo del estudiante",
    "household_size": "Tamaño del hogar",
}


@dataclass
class FeatureResult:
    features: dict[str, Any] | None = None
    missing: str | None = None


class FeatureBuilder:
    def __init__(self, db: Session) -> None:
        self.academic = AcademicRepository(db)
        self.surveys = SurveyRepository(db)

    def build(self, student: Student, period: AcademicPeriod) -> FeatureResult:
        grades = self.academic.list_grades(student.id, period.id)
        if not grades:
            return FeatureResult(missing="Sin notas en el bimestre")

        counts = self.academic.attendance_counts(student.id, period.start_date, period.end_date)
        total_days = sum(counts.values())
        if not total_days:
            return FeatureResult(missing="Sin asistencia registrada en el bimestre")

        survey = self.surveys.latest_until(student.id, period)
        if survey is None:
            return FeatureResult(missing="Sin encuesta familiar")

        scores = [grade.score for grade in grades]
        average = sum(scores) / len(scores)
        behavior = self.academic.latest_behavior_until(student.id, period)

        return FeatureResult(
            features={
                "avg_score": round(average, 2),
                "failed_subjects": sum(score < PASSING_SCORE for score in scores),
                "score_trend": round(average - self._previous_average(student, period, average), 2),
                "attendance_rate": round(
                    (total_days - counts.get(AttendanceStatus.ABSENT, 0)) / total_days, 4
                ),
                "late_count": counts.get(AttendanceStatus.LATE, 0),
                "behavior_rating": behavior.rating if behavior else NEUTRAL_BEHAVIOR,
                "study_hours_week": survey.study_hours_week,
                "parent_education": survey.parent_education.value,
                "home_internet": survey.home_internet,
                "has_study_device": survey.has_study_device,
                "family_communication": survey.family_communication,
                "student_works": survey.student_works,
                "household_size": survey.household_size,
            }
        )

    def _previous_average(self, student: Student, period: AcademicPeriod, current: float) -> float:
        """Average of the previous period; the current one if there is no history (trend 0)."""
        previous = self.academic.previous_period(period)
        if previous is None:
            return current
        grades = self.academic.list_grades(student.id, previous.id)
        if not grades:
            return current
        return sum(grade.score for grade in grades) / len(grades)
