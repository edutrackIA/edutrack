from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain import AcademicPeriod, Attendance, BehaviorRecord, Grade, Subject


class AcademicRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_period(self, period_id: int) -> AcademicPeriod | None:
        return self.db.get(AcademicPeriod, period_id)

    def get_subject(self, subject_id: int) -> Subject | None:
        return self.db.get(Subject, subject_id)

    def get_subject_by_name(self, name: str) -> Subject | None:
        return self.db.scalar(select(Subject).where(func.lower(Subject.name) == name.lower()))

    def list_grades(self, student_id: int, period_id: int | None = None) -> list[Grade]:
        query = (
            select(Grade)
            .join(Grade.subject)
            .where(Grade.student_id == student_id)
            .order_by(Grade.period_id, Subject.name)
        )
        if period_id is not None:
            query = query.where(Grade.period_id == period_id)
        return list(self.db.scalars(query))

    def get_grade(self, *, student_id: int, subject_id: int, period_id: int) -> Grade | None:
        return self.db.scalar(
            select(Grade).where(
                Grade.student_id == student_id,
                Grade.subject_id == subject_id,
                Grade.period_id == period_id,
            )
        )

    def get_behavior(self, *, student_id: int, period_id: int) -> BehaviorRecord | None:
        return self.db.scalar(
            select(BehaviorRecord).where(
                BehaviorRecord.student_id == student_id,
                BehaviorRecord.period_id == period_id,
            )
        )

    def get_attendance(self, *, student_id: int, day: date) -> Attendance | None:
        return self.db.scalar(
            select(Attendance).where(Attendance.student_id == student_id, Attendance.date == day)
        )

    def add(self, entity: Grade | BehaviorRecord | Attendance) -> None:
        self.db.add(entity)
        self.db.flush()
