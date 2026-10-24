from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, UnprocessableError
from app.domain import AcademicPeriod, AttendanceStatus, BehaviorRecord, Grade, Student, User
from app.repositories.academic_repository import AcademicRepository
from app.repositories.classroom_repository import ClassroomRepository
from app.repositories.student_repository import StudentRepository
from app.schemas.student import (
    BehaviorInput,
    GradeInput,
    GradeResponse,
    StudentListItem,
    StudentSummary,
    StudentUpdate,
)
from app.services.access_policy import AccessPolicy


class StudentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.students = StudentRepository(db)
        self.classrooms = ClassroomRepository(db)
        self.academic = AcademicRepository(db)
        self.policy = AccessPolicy(db)

    def get(self, user: User, student_id: int) -> Student:
        student = self._get_student(student_id)
        self.policy.ensure_can_view_student(user, student)
        return student

    def update(self, user: User, student_id: int, data: StudentUpdate) -> Student:
        student = self._get_student(student_id)
        self.policy.ensure_can_edit_student(user, student)

        changes = data.model_dump(exclude_unset=True, exclude_none=True)
        if "classroom_id" in changes:
            classroom = self.classrooms.get(changes["classroom_id"])
            if classroom is None or classroom.institution_id != user.institution_id:
                raise UnprocessableError("Invalid classroom")
        for field, value in changes.items():
            setattr(student, field, value)

        self.db.commit()
        self.db.refresh(student)
        return student

    def list_grades(self, user: User, student_id: int, period_id: int | None) -> list[Grade]:
        student = self.get(user, student_id)
        return self.academic.list_grades(student.id, period_id)

    def upsert_grades(self, user: User, student_id: int, items: list[GradeInput]) -> list[Grade]:
        student = self._get_student(student_id)
        keys = [(item.subject_id, item.period_id) for item in items]
        if len(keys) != len(set(keys)):
            raise UnprocessableError("Duplicated subject and period in request")

        saved: list[Grade] = []
        for item in items:
            if self.academic.get_subject(item.subject_id) is None:
                raise UnprocessableError(f"Invalid subject {item.subject_id}")
            self._get_period(user, item.period_id)
            self.policy.ensure_can_record_grade(user, student, item.subject_id)

            grade = self.academic.get_grade(
                student_id=student.id, subject_id=item.subject_id, period_id=item.period_id
            )
            if grade is None:
                grade = Grade(
                    student_id=student.id,
                    subject_id=item.subject_id,
                    period_id=item.period_id,
                    score=item.score,
                )
                self.academic.add(grade)
            else:
                grade.score = item.score
            saved.append(grade)

        self.db.commit()
        return saved

    def record_behavior(self, user: User, student_id: int, data: BehaviorInput) -> BehaviorRecord:
        student = self._get_student(student_id)
        self.policy.ensure_can_record_behavior(user, student)
        self._get_period(user, data.period_id)

        record = self.academic.get_behavior(student_id=student.id, period_id=data.period_id)
        if record is None:
            record = BehaviorRecord(
                student_id=student.id,
                period_id=data.period_id,
                rating=data.rating,
                notes=data.notes,
            )
            self.academic.add(record)
        else:
            record.rating = data.rating
            record.notes = data.notes

        self.db.commit()
        return record

    def summary(self, user: User, student_id: int, period_id: int | None) -> StudentSummary:
        student = self.get(user, student_id)
        if period_id is None:
            period = self.academic.latest_period_with_grades(student.id)
        else:
            period = self._get_period(user, period_id)

        grades: list[Grade] = []
        attendance_rate: float | None = None
        if period is not None:
            grades = self.academic.list_grades(student.id, period.id)
            counts = self.academic.attendance_counts(student.id, period.start_date, period.end_date)
            total = sum(counts.values())
            if total:
                attended = total - counts.get(AttendanceStatus.ABSENT, 0)
                attendance_rate = round(attended / total, 4)

        average = round(sum(g.score for g in grades) / len(grades), 2) if grades else None
        return StudentSummary(
            student=StudentListItem.from_model(student),
            period_id=period.id if period else None,
            average_score=average,
            attendance_rate=attendance_rate,
            grades=[GradeResponse.from_model(grade) for grade in grades],
            parent_suggestions=[],
        )

    def list_children(self, user: User) -> list[Student]:
        return self.students.list_for_guardian(user.id)

    def _get_student(self, student_id: int) -> Student:
        student = self.students.get(student_id)
        if student is None:
            raise NotFoundError("Student not found")
        return student

    def _get_period(self, user: User, period_id: int) -> AcademicPeriod:
        period = self.academic.get_period(period_id)
        if period is None or period.institution_id != user.institution_id:
            raise UnprocessableError(f"Invalid period {period_id}")
        return period
