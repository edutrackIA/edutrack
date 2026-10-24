from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain import Guardianship, Student


class StudentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, student_id: int) -> Student | None:
        return self.db.get(Student, student_id)

    def get_by_code(self, code: str) -> Student | None:
        return self.db.scalar(select(Student).where(Student.code == code))

    def add(self, student: Student) -> Student:
        self.db.add(student)
        self.db.flush()
        return student

    def list_for_guardian(self, guardian_id: int) -> list[Student]:
        query = (
            select(Student)
            .join(Guardianship, Guardianship.student_id == Student.id)
            .where(Guardianship.guardian_id == guardian_id)
            .order_by(Student.last_name, Student.first_name)
        )
        return list(self.db.scalars(query))

    def is_guardian(self, *, guardian_id: int, student_id: int) -> bool:
        return self.db.get(Guardianship, (guardian_id, student_id)) is not None
