"""Daily records a school keeps: grades per course, attendance per day, conduct per period.

The three sheets work the same way: load the classroom's students with what is already
recorded, then save the whole sheet at once. Every row must belong to the classroom.
"""

from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, UnprocessableError
from app.domain import (
    AcademicPeriod,
    Attendance,
    BehaviorRecord,
    Classroom,
    CourseAssignment,
    Grade,
    Student,
    Subject,
    User,
)
from app.repositories.academic_repository import AcademicRepository
from app.repositories.classroom_repository import ClassroomRepository
from app.schemas.class_register import (
    AttendanceInput,
    AttendanceRow,
    AttendanceSheet,
    BehaviorInput,
    BehaviorRow,
    BehaviorSheet,
    Gradebook,
    GradebookInput,
    GradebookRow,
    MyTeaching,
    TeachingClassroom,
    TeachingCourse,
)
from app.services.access_policy import AccessPolicy


def _invalid(message: str) -> UnprocessableError:
    return UnprocessableError(message, code="REGISTER_INVALID")


class ClassRegisterService:
    def __init__(self, db: Session, today: date) -> None:
        self.db = db
        self.today = today
        self.academic = AcademicRepository(db)
        self.classrooms = ClassroomRepository(db)
        self.policy = AccessPolicy(db)

    # --- Lo que dicta cada docente ---------------------------------------------------------

    def my_teaching(self, user: User) -> MyTeaching:
        rows = self.db.execute(
            select(Classroom, Subject)
            .join(CourseAssignment, CourseAssignment.classroom_id == Classroom.id)
            .join(Subject, Subject.id == CourseAssignment.subject_id)
            .where(CourseAssignment.teacher_id == user.id)
            .order_by(Classroom.year.desc(), Classroom.grade, Classroom.section, Subject.name)
        ).all()
        courses = [
            TeachingCourse(
                classroom_id=classroom.id,
                classroom=classroom.label,
                year=classroom.year,
                subject_id=subject.id,
                subject=subject.name,
            )
            for classroom, subject in rows
        ]
        ids = self.classrooms.teacher_classroom_ids(user.id)
        classrooms = self.db.scalars(
            select(Classroom)
            .where(Classroom.id.in_(ids))
            .order_by(Classroom.year.desc(), Classroom.grade, Classroom.section)
        ).all()
        return MyTeaching(
            courses=courses,
            classrooms=[
                TeachingClassroom(
                    classroom_id=classroom.id,
                    classroom=classroom.label,
                    year=classroom.year,
                    is_tutor=classroom.tutor_id == user.id,
                )
                for classroom in classrooms
            ],
        )

    # --- Notas -----------------------------------------------------------------------------

    def gradebook(
        self, user: User, classroom_id: int, subject_id: int, period_id: int
    ) -> Gradebook:
        classroom = self._classroom(user, classroom_id)
        self.policy.ensure_can_record_course(user, classroom, subject_id)
        self._subject(user, subject_id)
        self._period(user, period_id)
        students = self._students(classroom)
        grades = {
            grade.student_id: grade.score
            for grade in self.db.scalars(
                select(Grade).where(
                    Grade.subject_id == subject_id,
                    Grade.period_id == period_id,
                    Grade.student_id.in_([student.id for student in students]),
                )
            )
        }
        return Gradebook(
            classroom_id=classroom.id,
            subject_id=subject_id,
            period_id=period_id,
            rows=[
                GradebookRow(**self._identity(student), score=grades.get(student.id))
                for student in students
            ],
        )

    def save_grades(self, user: User, data: GradebookInput) -> Gradebook:
        classroom = self._classroom(user, data.classroom_id)
        self.policy.ensure_can_record_course(user, classroom, data.subject_id)
        self._subject(user, data.subject_id)
        self._period(user, data.period_id)
        self._belongs(classroom, [item.student_id for item in data.scores])

        for item in data.scores:
            grade = self.academic.get_grade(
                student_id=item.student_id, subject_id=data.subject_id, period_id=data.period_id
            )
            if item.score is None:
                if grade is not None:
                    self.db.delete(grade)
            elif grade is None:
                self.academic.add(
                    Grade(
                        student_id=item.student_id,
                        subject_id=data.subject_id,
                        period_id=data.period_id,
                        score=round(item.score, 1),
                    )
                )
            else:
                grade.score = round(item.score, 1)
        self.db.commit()
        return self.gradebook(user, classroom.id, data.subject_id, data.period_id)

    # --- Asistencia ------------------------------------------------------------------------

    def attendance(self, user: User, classroom_id: int, day: date) -> AttendanceSheet:
        classroom = self._classroom(user, classroom_id)
        self.policy.ensure_can_take_attendance(user, classroom)
        students = self._students(classroom)
        marks = {
            record.student_id: record.status
            for record in self.db.scalars(
                select(Attendance).where(
                    Attendance.date == day,
                    Attendance.student_id.in_([student.id for student in students]),
                )
            )
        }
        period = self._period_of(user, day)
        return AttendanceSheet(
            classroom_id=classroom.id,
            date=day,
            period_id=period.id if period else None,
            rows=[
                AttendanceRow(**self._identity(student), status=marks.get(student.id))
                for student in students
            ],
        )

    def save_attendance(
        self, user: User, classroom_id: int, data: AttendanceInput
    ) -> AttendanceSheet:
        classroom = self._classroom(user, classroom_id)
        self.policy.ensure_can_take_attendance(user, classroom)
        if data.date > self.today:
            raise _invalid("No se puede registrar asistencia de días futuros")
        if data.date.weekday() >= 5:
            raise _invalid("La asistencia se registra de lunes a viernes")
        if self._period_of(user, data.date) is None:
            raise _invalid("La fecha no pertenece a ningún bimestre")
        self._belongs(classroom, [item.student_id for item in data.records])

        for item in data.records:
            record = self.academic.get_attendance(student_id=item.student_id, day=data.date)
            if record is None:
                self.academic.add(
                    Attendance(student_id=item.student_id, date=data.date, status=item.status)
                )
            else:
                record.status = item.status
        self.db.commit()
        return self.attendance(user, classroom.id, data.date)

    # --- Conducta ------------------------------------------------------------------------

    def behavior(self, user: User, classroom_id: int, period_id: int) -> BehaviorSheet:
        classroom = self._classroom(user, classroom_id)
        self.policy.ensure_can_record_classroom_behavior(user, classroom)
        self._period(user, period_id)
        students = self._students(classroom)
        records = {
            record.student_id: record
            for record in self.db.scalars(
                select(BehaviorRecord).where(
                    BehaviorRecord.period_id == period_id,
                    BehaviorRecord.student_id.in_([student.id for student in students]),
                )
            )
        }
        return BehaviorSheet(
            classroom_id=classroom.id,
            period_id=period_id,
            rows=[
                BehaviorRow(
                    **self._identity(student),
                    rating=records[student.id].rating if student.id in records else None,
                    notes=records[student.id].notes if student.id in records else None,
                )
                for student in students
            ],
        )

    def save_behavior(self, user: User, classroom_id: int, data: BehaviorInput) -> BehaviorSheet:
        classroom = self._classroom(user, classroom_id)
        self.policy.ensure_can_record_classroom_behavior(user, classroom)
        self._period(user, data.period_id)
        self._belongs(classroom, [item.student_id for item in data.ratings])

        for item in data.ratings:
            if item.rating is None:
                self.db.execute(
                    delete(BehaviorRecord).where(
                        BehaviorRecord.student_id == item.student_id,
                        BehaviorRecord.period_id == data.period_id,
                    )
                )
                continue
            record = self.academic.get_behavior(
                student_id=item.student_id, period_id=data.period_id
            )
            notes = (item.notes or "").strip() or None
            if record is None:
                self.academic.add(
                    BehaviorRecord(
                        student_id=item.student_id,
                        period_id=data.period_id,
                        rating=item.rating,
                        notes=notes,
                    )
                )
            else:
                record.rating, record.notes = item.rating, notes
        self.db.commit()
        return self.behavior(user, classroom.id, data.period_id)

    # --- Internos ----------------------------------------------------------------------------

    def _classroom(self, user: User, classroom_id: int) -> Classroom:
        classroom = self.classrooms.get(classroom_id)
        if classroom is None or classroom.institution_id != user.institution_id:
            raise NotFoundError("Classroom not found")
        return classroom

    def _subject(self, user: User, subject_id: int) -> Subject:
        subject = self.academic.get_subject(subject_id)
        if subject is None or subject.institution_id != user.institution_id:
            raise NotFoundError("Subject not found")
        return subject

    def _period(self, user: User, period_id: int) -> AcademicPeriod:
        period = self.academic.get_period(period_id)
        if period is None or period.institution_id != user.institution_id:
            raise NotFoundError("Period not found")
        return period

    def _period_of(self, user: User, day: date) -> AcademicPeriod | None:
        return self.db.scalar(
            select(AcademicPeriod).where(
                AcademicPeriod.institution_id == user.institution_id,
                AcademicPeriod.start_date <= day,
                AcademicPeriod.end_date >= day,
            )
        )

    @staticmethod
    def _students(classroom: Classroom) -> list[Student]:
        return sorted(classroom.students, key=lambda s: (s.last_name, s.first_name))

    @staticmethod
    def _identity(student: Student) -> dict[str, object]:
        return {"student_id": student.id, "code": student.code, "full_name": student.full_name}

    @staticmethod
    def _belongs(classroom: Classroom, student_ids: list[int]) -> None:
        own = {student.id for student in classroom.students}
        if len(student_ids) != len(set(student_ids)):
            raise _invalid("Un estudiante aparece más de una vez")
        if not set(student_ids) <= own:
            raise _invalid("Hay estudiantes que no pertenecen a esta aula")
