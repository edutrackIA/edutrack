from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.domain import Classroom, Student, User
from app.repositories.classroom_repository import ClassroomRepository
from app.services.access_policy import AccessPolicy


class ClassroomService:
    def __init__(self, db: Session) -> None:
        self.classrooms = ClassroomRepository(db)
        self.policy = AccessPolicy(db)

    def list_visible(self, user: User, year: int | None = None) -> list[Classroom]:
        ids = self.policy.visible_classroom_ids(user)
        return self.classrooms.list_for_institution(user.institution_id, year=year, ids=ids)

    def list_students(self, user: User, classroom_id: int) -> list[Student]:
        classroom = self.classrooms.get(classroom_id)
        if classroom is None:
            raise NotFoundError("Classroom not found")
        self.policy.ensure_can_view_classroom(user, classroom)
        return sorted(classroom.students, key=lambda s: (s.last_name, s.first_name))
