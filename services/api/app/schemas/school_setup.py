from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from app.domain import Classroom, CourseAssignment, Subject, User

StaffRole = Literal["DIRECTOR", "TEACHER", "ANALYST"]


class PeriodInput(BaseModel):
    year: int = Field(ge=2020, le=2100)
    bimester: int = Field(ge=1, le=4)
    start_date: date
    end_date: date


class PeriodDates(BaseModel):
    start_date: date
    end_date: date


class SubjectInput(BaseModel):
    name: str = Field(min_length=2, max_length=80)


class SubjectResponse(BaseModel):
    id: int
    name: str

    @classmethod
    def from_model(cls, subject: Subject) -> "SubjectResponse":
        return cls(id=subject.id, name=subject.name)


class ClassroomInput(BaseModel):
    year: int = Field(ge=2020, le=2100)
    grade: int = Field(ge=1, le=6)
    section: str = Field(min_length=1, max_length=2)
    tutor_id: int | None = None


class ClassroomTutor(BaseModel):
    tutor_id: int | None


class StaffInput(BaseModel):
    full_name: str = Field(min_length=3, max_length=150)
    email: str = Field(min_length=3, max_length=255)
    role: StaffRole


class StaffStatus(BaseModel):
    is_active: bool


class StaffResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: StaffRole
    is_active: bool
    has_access: bool
    # Only set right after an action that tried to email an invitation.
    invitation_sent: bool | None = None

    @classmethod
    def from_model(cls, user: User, *, invitation_sent: bool | None = None) -> "StaffResponse":
        return cls(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            role=user.role.value,  # type: ignore[arg-type]
            is_active=user.is_active,
            has_access=user.has_access,
            invitation_sent=invitation_sent,
        )


class AssignmentInput(BaseModel):
    classroom_id: int
    subject_id: int
    teacher_id: int


class AssignmentResponse(BaseModel):
    id: int
    classroom_id: int
    classroom: str
    subject_id: int
    subject: str
    teacher_id: int
    teacher: str

    @classmethod
    def from_model(
        cls, assignment: CourseAssignment, classroom: Classroom, subject: Subject, teacher: User
    ) -> "AssignmentResponse":
        return cls(
            id=assignment.id,
            classroom_id=classroom.id,
            classroom=classroom.label,
            subject_id=subject.id,
            subject=subject.name,
            teacher_id=teacher.id,
            teacher=teacher.full_name,
        )
