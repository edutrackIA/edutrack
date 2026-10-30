from collections.abc import Callable, Hashable
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.domain import Attendance, AttendanceStatus, Grade, Sex, Student, Subject, User
from app.repositories.academic_repository import AcademicRepository
from app.repositories.classroom_repository import ClassroomRepository
from app.repositories.student_repository import StudentRepository
from app.services.guardian_links import GuardianLinkError, link_guardian

ATTENDANCE_ALIASES = {
    "PRESENT": AttendanceStatus.PRESENT,
    "PRESENTE": AttendanceStatus.PRESENT,
    "P": AttendanceStatus.PRESENT,
    "ABSENT": AttendanceStatus.ABSENT,
    "FALTA": AttendanceStatus.ABSENT,
    "AUSENTE": AttendanceStatus.ABSENT,
    "F": AttendanceStatus.ABSENT,
    "LATE": AttendanceStatus.LATE,
    "TARDANZA": AttendanceStatus.LATE,
    "T": AttendanceStatus.LATE,
    "JUSTIFIED": AttendanceStatus.JUSTIFIED,
    "JUSTIFICADA": AttendanceStatus.JUSTIFIED,
    "J": AttendanceStatus.JUSTIFIED,
}


class RowValidationError(Exception):
    def __init__(self, column: str | None, message: str) -> None:
        super().__init__(message)
        self.column = column
        self.message = message


class RowImporter:
    """Validates a whole row before writing, so a failing row never leaves partial changes."""

    required_columns: tuple[str, ...] = ()

    def __init__(self, db: Session, institution_id: int) -> None:
        self.institution_id = institution_id
        self.students = StudentRepository(db)
        self.classrooms = ClassroomRepository(db)
        self.academic = AcademicRepository(db)

    def key(self, row: dict[str, str]) -> Hashable:
        raise NotImplementedError

    def import_row(self, row: dict[str, str]) -> None:
        raise NotImplementedError

    def after_commit(self) -> None:
        """Side effects that must only happen once the rows are saved (e.g. emails)."""

    def _student(self, row: dict[str, str], column: str = "student_code") -> Student:
        code = _required(row, column)
        student = self.students.get_by_code(code)
        if student is None or student.institution_id != self.institution_id:
            raise RowValidationError(column, f"El estudiante {code} no existe")
        return student


class StudentImporter(RowImporter):
    required_columns = (
        "code",
        "first_name",
        "last_name",
        "birth_date",
        "sex",
        "year",
        "grade",
        "section",
    )

    def key(self, row: dict[str, str]) -> Hashable:
        return row.get("code", "")

    def import_row(self, row: dict[str, str]) -> None:
        code = _required(row, "code")
        first_name = _required(row, "first_name")
        last_name = _required(row, "last_name")
        birth_date = _parse_date(row, "birth_date")
        sex = _required(row, "sex").upper()
        if sex not in Sex.__members__:
            raise RowValidationError("sex", "El sexo debe ser M o F")
        year = _parse_int(row, "year", 2000, 2100)
        grade = _parse_int(row, "grade", 1, 5)
        section = _required(row, "section").upper()

        classroom = self.classrooms.find(
            institution_id=self.institution_id, year=year, grade=grade, section=section
        )
        if classroom is None:
            raise RowValidationError("section", f"No existe el aula {grade}° {section} ({year})")

        student = self.students.get_by_code(code)
        if student is not None and student.institution_id != self.institution_id:
            raise RowValidationError("code", f"El código {code} ya está en uso")

        if student is None:
            self.students.add(
                Student(
                    institution_id=self.institution_id,
                    classroom_id=classroom.id,
                    code=code,
                    first_name=first_name,
                    last_name=last_name,
                    birth_date=birth_date,
                    sex=Sex(sex),
                )
            )
        else:
            student.classroom_id = classroom.id
            student.first_name = first_name
            student.last_name = last_name
            student.birth_date = birth_date
            student.sex = Sex(sex)


class GradeImporter(RowImporter):
    required_columns = ("student_code", "subject", "score")

    def __init__(self, db: Session, institution_id: int, period_id: int) -> None:
        super().__init__(db, institution_id)
        self.period_id = period_id
        self._subjects: dict[str, Subject | None] = {}

    def key(self, row: dict[str, str]) -> Hashable:
        return row.get("student_code", ""), row.get("subject", "").lower()

    def import_row(self, row: dict[str, str]) -> None:
        student = self._student(row)
        subject = self._subject(_required(row, "subject"))
        score = _parse_score(row, "score")

        grade = self.academic.get_grade(
            student_id=student.id, subject_id=subject.id, period_id=self.period_id
        )
        if grade is None:
            self.academic.add(
                Grade(
                    student_id=student.id,
                    subject_id=subject.id,
                    period_id=self.period_id,
                    score=score,
                )
            )
        else:
            grade.score = score

    def _subject(self, name: str) -> Subject:
        key = name.lower()
        if key not in self._subjects:
            self._subjects[key] = self.academic.get_subject_by_name(name)
        subject = self._subjects[key]
        if subject is None:
            raise RowValidationError("subject", f"El curso {name} no existe")
        return subject


class AttendanceImporter(RowImporter):
    required_columns = ("student_code", "date", "status")

    def key(self, row: dict[str, str]) -> Hashable:
        return row.get("student_code", ""), row.get("date", "")

    def import_row(self, row: dict[str, str]) -> None:
        student = self._student(row)
        day = _parse_date(row, "date")
        status = ATTENDANCE_ALIASES.get(_required(row, "status").upper())
        if status is None:
            raise RowValidationError(
                "status", "El estado debe ser PRESENT, ABSENT, LATE o JUSTIFIED"
            )

        record = self.academic.get_attendance(student_id=student.id, day=day)
        if record is None:
            self.academic.add(Attendance(student_id=student.id, date=day, status=status))
        else:
            record.status = status


def _required(row: dict[str, str], column: str) -> str:
    value = row.get(column, "").strip()
    if not value:
        raise RowValidationError(column, "Falta el valor")
    return value


def _parse_int(row: dict[str, str], column: str, minimum: int, maximum: int) -> int:
    raw = _required(row, column)
    try:
        value = int(raw)
    except ValueError as exc:
        raise RowValidationError(column, f"{raw} no es un número entero") from exc
    if not minimum <= value <= maximum:
        raise RowValidationError(column, f"Debe estar entre {minimum} y {maximum}")
    return value


def _parse_score(row: dict[str, str], column: str) -> float:
    raw = _required(row, column)
    try:
        value = float(raw.replace(",", "."))
    except ValueError as exc:
        raise RowValidationError(column, f"{raw} no es un número") from exc
    if not 0 <= value <= 20:
        raise RowValidationError(column, "La nota debe estar entre 0 y 20")
    return value


def _parse_date(row: dict[str, str], column: str) -> date:
    raw = _required(row, column)
    for pattern in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw, pattern).date()
        except ValueError:
            continue
    raise RowValidationError(column, f"{raw} no es una fecha válida (AAAA-MM-DD o DD/MM/AAAA)")


class GuardianImporter(RowImporter):
    """Creates parent accounts without password and invites them after the import is saved."""

    required_columns = ("student_code", "full_name", "email")

    def __init__(self, db: Session, institution_id: int, invite: Callable[[User], bool]) -> None:
        super().__init__(db, institution_id)
        self.db = db
        self.invite = invite
        self.to_invite: dict[int, User] = {}

    def key(self, row: dict[str, str]) -> Hashable:
        return (row.get("student_code", "").strip(), row.get("email", "").strip().lower())

    def import_row(self, row: dict[str, str]) -> None:
        student = self._student(row)
        try:
            link = link_guardian(
                self.db,
                student,
                full_name=_required(row, "full_name"),
                email=_required(row, "email"),
                kinship=row.get("kinship", ""),
            )
        except GuardianLinkError as exc:
            raise RowValidationError(exc.column, exc.message) from exc
        if not link.user.has_access:
            self.to_invite[link.user.id] = link.user

    def after_commit(self) -> None:
        for user in self.to_invite.values():
            self.invite(user)
