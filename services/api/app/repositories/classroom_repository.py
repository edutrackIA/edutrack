from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain import Classroom, CourseAssignment


class ClassroomRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, classroom_id: int) -> Classroom | None:
        return self.db.get(Classroom, classroom_id)

    def list_for_institution(
        self, institution_id: int, *, year: int | None = None, ids: set[int] | None = None
    ) -> list[Classroom]:
        query = (
            select(Classroom)
            .where(Classroom.institution_id == institution_id)
            .options(selectinload(Classroom.students), selectinload(Classroom.tutor))
            .order_by(Classroom.year.desc(), Classroom.grade, Classroom.section)
        )
        if year is not None:
            query = query.where(Classroom.year == year)
        if ids is not None:
            query = query.where(Classroom.id.in_(ids))
        return list(self.db.scalars(query))

    def find(self, *, institution_id: int, year: int, grade: int, section: str) -> Classroom | None:
        return self.db.scalar(
            select(Classroom).where(
                Classroom.institution_id == institution_id,
                Classroom.year == year,
                Classroom.grade == grade,
                Classroom.section == section,
            )
        )

    def tutored_classroom_ids(self, teacher_id: int) -> set[int]:
        return set(self.db.scalars(select(Classroom.id).where(Classroom.tutor_id == teacher_id)))

    def teacher_classroom_ids(self, teacher_id: int) -> set[int]:
        tutored = select(Classroom.id).where(Classroom.tutor_id == teacher_id)
        assigned = select(CourseAssignment.classroom_id).where(
            CourseAssignment.teacher_id == teacher_id
        )
        return set(self.db.scalars(tutored)) | set(self.db.scalars(assigned))

    def has_assignment(self, *, classroom_id: int, subject_id: int, teacher_id: int) -> bool:
        query = select(CourseAssignment.id).where(
            CourseAssignment.classroom_id == classroom_id,
            CourseAssignment.subject_id == subject_id,
            CourseAssignment.teacher_id == teacher_id,
        )
        return self.db.scalar(query) is not None
