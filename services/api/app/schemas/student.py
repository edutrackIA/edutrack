from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.domain import BehaviorRecord, Grade, Student
from app.domain.enums import Sex
from app.schemas.auth import UserResponse


class StudentListItem(BaseModel):
    id: int
    code: str
    full_name: str
    classroom: str
    risk_level: str | None = None
    probability: float | None = None

    @classmethod
    def from_model(cls, student: Student) -> "StudentListItem":
        return cls(
            id=student.id,
            code=student.code,
            full_name=student.full_name,
            classroom=student.classroom.label,
        )


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    first_name: str
    last_name: str
    birth_date: date
    sex: Sex
    classroom_id: int
    guardians: list[UserResponse]
    latest_risk: None = None


class StudentUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=80)
    last_name: str | None = Field(default=None, min_length=1, max_length=80)
    classroom_id: int | None = None


class GradeInput(BaseModel):
    subject_id: int
    period_id: int
    score: float = Field(ge=0, le=20)


class GradeResponse(BaseModel):
    subject_id: int
    subject: str
    period_id: int
    score: float

    @classmethod
    def from_model(cls, grade: Grade) -> "GradeResponse":
        return cls(
            subject_id=grade.subject_id,
            subject=grade.subject.name,
            period_id=grade.period_id,
            score=grade.score,
        )


class BehaviorInput(BaseModel):
    period_id: int
    rating: int = Field(ge=1, le=5)
    notes: str | None = Field(default=None, max_length=1000)


class BehaviorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    period_id: int
    rating: int
    notes: str | None

    @classmethod
    def from_model(cls, record: BehaviorRecord) -> "BehaviorResponse":
        return cls.model_validate(record)


class StudentSummary(BaseModel):
    student: StudentListItem
    period_id: int | None
    average_score: float | None
    attendance_rate: float | None
    grades: list[GradeResponse]
    parent_suggestions: list[str]
