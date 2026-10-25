from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain import SituationEvent, Student, StudentSituation, WeeklyCheckin


class SituationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, situation_id: int) -> StudentSituation | None:
        return self.db.get(StudentSituation, situation_id)

    def list_for_student(
        self, student_id: int, *, include_resolved: bool
    ) -> list[StudentSituation]:
        query = select(StudentSituation).where(StudentSituation.student_id == student_id)
        if not include_resolved:
            query = query.where(StudentSituation.resolved_on.is_(None))
        query = query.order_by(StudentSituation.started_on.desc(), StudentSituation.id.desc())
        return list(self.db.scalars(query))

    def active_for_classroom(self, classroom_id: int) -> list[StudentSituation]:
        query = (
            select(StudentSituation)
            .join(Student, Student.id == StudentSituation.student_id)
            .where(Student.classroom_id == classroom_id, StudentSituation.resolved_on.is_(None))
            .order_by(StudentSituation.started_on.desc(), StudentSituation.id.desc())
        )
        return list(self.db.scalars(query))

    def add(self, situation: StudentSituation) -> StudentSituation:
        self.db.add(situation)
        self.db.flush()
        return situation

    def log(self, event: SituationEvent) -> None:
        self.db.add(event)
        self.db.flush()

    def get_checkin(self, *, classroom_id: int, week_start: date) -> WeeklyCheckin | None:
        return self.db.scalar(
            select(WeeklyCheckin).where(
                WeeklyCheckin.classroom_id == classroom_id,
                WeeklyCheckin.week_start == week_start,
            )
        )

    def add_checkin(self, checkin: WeeklyCheckin) -> WeeklyCheckin:
        self.db.add(checkin)
        self.db.flush()
        return checkin
