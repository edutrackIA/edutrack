from datetime import date

from pydantic import BaseModel, Field

from app.domain import AttendanceStatus


class TeachingCourse(BaseModel):
    classroom_id: int
    classroom: str
    year: int
    subject_id: int
    subject: str


class TeachingClassroom(BaseModel):
    classroom_id: int
    classroom: str
    year: int
    is_tutor: bool


class MyTeaching(BaseModel):
    """What a teacher records: grades of their courses, attendance and conduct of classrooms."""

    courses: list[TeachingCourse]
    classrooms: list[TeachingClassroom]


class RegisterStudent(BaseModel):
    student_id: int
    code: str
    full_name: str


# --- Notas ------------------------------------------------------------------------------


class GradebookRow(RegisterStudent):
    score: float | None


class Gradebook(BaseModel):
    classroom_id: int
    subject_id: int
    period_id: int
    rows: list[GradebookRow]


class ScoreInput(BaseModel):
    student_id: int
    # Null removes the grade (for example, a mistake typed in the wrong row).
    score: float | None = Field(default=None, ge=0, le=20)


class GradebookInput(BaseModel):
    classroom_id: int
    subject_id: int
    period_id: int
    scores: list[ScoreInput] = Field(max_length=200)


# --- Asistencia ---------------------------------------------------------------------------


class AttendanceRow(RegisterStudent):
    status: AttendanceStatus | None


class AttendanceSheet(BaseModel):
    classroom_id: int
    date: date
    period_id: int | None
    rows: list[AttendanceRow]


class AttendanceMark(BaseModel):
    student_id: int
    status: AttendanceStatus


class AttendanceInput(BaseModel):
    date: date
    records: list[AttendanceMark] = Field(max_length=200)


# --- Conducta -----------------------------------------------------------------------------


class BehaviorRow(RegisterStudent):
    rating: int | None
    notes: str | None


class BehaviorSheet(BaseModel):
    classroom_id: int
    period_id: int
    rows: list[BehaviorRow]


class BehaviorMark(BaseModel):
    student_id: int
    rating: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = Field(default=None, max_length=500)


class BehaviorInput(BaseModel):
    period_id: int
    ratings: list[BehaviorMark] = Field(max_length=200)
