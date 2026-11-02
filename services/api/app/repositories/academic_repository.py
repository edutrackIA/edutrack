from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain import (
    AcademicPeriod,
    Attendance,
    AttendanceStatus,
    BehaviorRecord,
    Grade,
    Student,
    Subject,
)


class AcademicRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_periods(self, institution_id: int) -> list[AcademicPeriod]:
        query = (
            select(AcademicPeriod)
            .where(AcademicPeriod.institution_id == institution_id)
            .order_by(AcademicPeriod.start_date)
        )
        return list(self.db.scalars(query))

    def periods_with_grades(self, institution_id: int) -> set[int]:
        query = (
            select(Grade.period_id)
            .join(Student, Student.id == Grade.student_id)
            .where(Student.institution_id == institution_id)
            .distinct()
        )
        return set(self.db.scalars(query))

    def get_period(self, period_id: int) -> AcademicPeriod | None:
        return self.db.get(AcademicPeriod, period_id)

    def latest_period_with_grades(self, student_id: int) -> AcademicPeriod | None:
        return self.db.scalar(
            select(AcademicPeriod)
            .join(Grade, Grade.period_id == AcademicPeriod.id)
            .where(Grade.student_id == student_id)
            .order_by(AcademicPeriod.start_date.desc())
            .limit(1)
        )

    def attendance_counts(
        self, student_id: int, start: date, end: date
    ) -> dict[AttendanceStatus, int]:
        rows = self.db.execute(
            select(Attendance.status, func.count())
            .where(
                Attendance.student_id == student_id,
                Attendance.date >= start,
                Attendance.date <= end,
            )
            .group_by(Attendance.status)
        )
        return {status: count for status, count in rows}

    def previous_period(self, period: AcademicPeriod) -> AcademicPeriod | None:
        return self.db.scalar(
            select(AcademicPeriod)
            .where(
                AcademicPeriod.institution_id == period.institution_id,
                AcademicPeriod.start_date < period.start_date,
            )
            .order_by(AcademicPeriod.start_date.desc())
            .limit(1)
        )

    def latest_behavior_until(
        self, student_id: int, period: AcademicPeriod
    ) -> BehaviorRecord | None:
        return self.db.scalar(
            select(BehaviorRecord)
            .join(AcademicPeriod, AcademicPeriod.id == BehaviorRecord.period_id)
            .where(
                BehaviorRecord.student_id == student_id,
                AcademicPeriod.start_date <= period.start_date,
            )
            .order_by(AcademicPeriod.start_date.desc())
            .limit(1)
        )

    def get_subject(self, subject_id: int) -> Subject | None:
        return self.db.get(Subject, subject_id)

    def get_subject_by_name(self, institution_id: int, name: str) -> Subject | None:
        return self.db.scalar(
            select(Subject).where(
                Subject.institution_id == institution_id,
                func.lower(Subject.name) == name.strip().lower(),
            )
        )

    def list_subjects(self, institution_id: int) -> list[Subject]:
        query = select(Subject).where(Subject.institution_id == institution_id)
        return list(self.db.scalars(query.order_by(Subject.name)))

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

    def attendance_records(self, student_id: int, start: date, end: date) -> list[Attendance]:
        query = select(Attendance).where(
            Attendance.student_id == student_id,
            Attendance.date >= start,
            Attendance.date <= end,
        )
        return list(self.db.scalars(query))

    def add(self, entity: Grade | BehaviorRecord | Attendance) -> None:
        self.db.add(entity)
        self.db.flush()
