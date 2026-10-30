"""How the risk model performs against what really happened to students.

Each assessment (latest one per student and period) gets a real outcome once it is known:

- dropout (positive): the student withdrew, not transferred, within the observation
  window after the period ended;
- no dropout (negative): the window passed and the student is still enrolled or graduated;
- excluded: transfers (not a dropout) and assessments whose window has not passed yet.

A prediction counts as an alert when the assessed level was moderate or high.
"""

import csv
import io
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain import (
    AcademicPeriod,
    RiskAssessment,
    RiskLevel,
    Student,
    StudentStatus,
    User,
)
from app.schemas.model_monitoring import (
    DropoutCase,
    ModelPerformance,
    PerformanceMetrics,
)
from app.services.risk.features import FeatureBuilder

OUTCOME_WINDOW_DAYS = 180
# Below these numbers the percentages would say more about chance than about the model.
MIN_LABELED = 20
MIN_DROPOUTS = 3
ALERT_LEVELS = {RiskLevel.MEDIUM, RiskLevel.HIGH}


@dataclass
class LabeledAssessment:
    assessment: RiskAssessment
    student: Student
    period: AcademicPeriod
    dropout: bool


class ModelMonitoringService:
    def __init__(self, db: Session, today: date) -> None:
        self.db = db
        self.today = today
        self.window = timedelta(days=OUTCOME_WINDOW_DAYS)

    def performance(self, user: User) -> ModelPerformance:
        rows = self._latest_assessments(user.institution_id)
        labeled: list[LabeledAssessment] = []
        pending = 0
        for assessment, student, period in rows:
            outcome = self._outcome(student, period)
            if outcome is None:
                pending += student.status != StudentStatus.TRANSFERRED
                continue
            labeled.append(LabeledAssessment(assessment, student, period, outcome))

        dropouts = [row for row in labeled if row.dropout]
        return ModelPerformance(
            window_days=OUTCOME_WINDOW_DAYS,
            model_versions=sorted({row[0].model_version for row in rows}),
            labeled=len(labeled),
            dropouts=len(dropouts),
            pending=pending,
            min_labeled=MIN_LABELED,
            min_dropouts=MIN_DROPOUTS,
            metrics=self._metrics(labeled)
            if len(labeled) >= MIN_LABELED and len(dropouts) >= MIN_DROPOUTS
            else None,
            cases=self._cases(dropouts),
        )

    def dataset_csv(self, user: User) -> str:
        """Anonymized training rows: model features and the real outcome, no identifiers."""
        builder = FeatureBuilder(self.db)
        output = io.StringIO()
        writer: csv.DictWriter[str] | None = None
        for _, student, period in self._latest_assessments(user.institution_id):
            outcome = self._outcome(student, period)
            if outcome is None:
                continue
            built = builder.build(student, period)
            if built.features is None:
                continue
            row = {**built.features, "dropout": int(outcome)}
            if writer is None:
                writer = csv.DictWriter(output, fieldnames=list(row))
                writer.writeheader()
            writer.writerow(row)
        return output.getvalue()

    # --- Internos ------------------------------------------------------------------------

    def _latest_assessments(
        self, institution_id: int
    ) -> list[tuple[RiskAssessment, Student, AcademicPeriod]]:
        rows = self.db.execute(
            select(RiskAssessment, Student, AcademicPeriod)
            .join(Student, Student.id == RiskAssessment.student_id)
            .join(AcademicPeriod, AcademicPeriod.id == RiskAssessment.period_id)
            .where(Student.institution_id == institution_id)
            .order_by(RiskAssessment.created_at.desc(), RiskAssessment.id.desc())
        ).all()
        latest: dict[tuple[int, int], tuple[RiskAssessment, Student, AcademicPeriod]] = {}
        for assessment, student, period in rows:
            latest.setdefault((student.id, period.id), (assessment, student, period))
        return list(latest.values())

    def _outcome(self, student: Student, period: AcademicPeriod) -> bool | None:
        deadline = period.end_date + self.window
        if student.status == StudentStatus.TRANSFERRED:
            return None
        if student.status == StudentStatus.WITHDRAWN and student.exit_date is not None:
            if student.exit_date < period.start_date:
                return None  # Assessed after leaving: nothing to predict.
            if student.exit_date <= deadline:
                return True
        return False if self.today > deadline else None

    @staticmethod
    def _metrics(rows: list[LabeledAssessment]) -> PerformanceMetrics:
        tp = sum(row.dropout and row.assessment.level in ALERT_LEVELS for row in rows)
        fn = sum(row.dropout and row.assessment.level not in ALERT_LEVELS for row in rows)
        fp = sum(not row.dropout and row.assessment.level in ALERT_LEVELS for row in rows)
        tn = len(rows) - tp - fn - fp
        return PerformanceMetrics(
            true_positives=tp,
            false_negatives=fn,
            false_positives=fp,
            true_negatives=tn,
            recall=round(tp / (tp + fn), 3) if tp + fn else None,
            precision=round(tp / (tp + fp), 3) if tp + fp else None,
        )

    @staticmethod
    def _cases(dropouts: list[LabeledAssessment]) -> list[DropoutCase]:
        """One row per student who left: the last assessment before leaving."""
        by_student: dict[int, LabeledAssessment] = {}
        for row in sorted(dropouts, key=lambda item: item.period.end_date):
            by_student[row.student.id] = row
        return [
            DropoutCase(
                student_id=row.student.id,
                code=row.student.code,
                full_name=row.student.full_name,
                exit_date=row.student.exit_date,
                exit_reason=row.student.exit_reason,
                last_level=row.assessment.level,
                last_probability=row.assessment.probability,
                alerted=row.assessment.level in ALERT_LEVELS,
            )
            for row in sorted(
                by_student.values(),
                key=lambda item: (item.student.exit_date or date.min, item.student.code),
            )
        ]
