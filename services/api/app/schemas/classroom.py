from pydantic import BaseModel

from app.domain import Classroom
from app.schemas.auth import UserResponse


class ClassroomResponse(BaseModel):
    id: int
    year: int
    grade: int
    section: str
    tutor: UserResponse | None
    student_count: int

    @classmethod
    def from_model(cls, classroom: Classroom) -> "ClassroomResponse":
        return cls(
            id=classroom.id,
            year=classroom.year,
            grade=classroom.grade,
            section=classroom.section,
            tutor=UserResponse.model_validate(classroom.tutor) if classroom.tutor else None,
            student_count=len(classroom.students),
        )
