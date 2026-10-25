"""Automatic informative messages for families: attendance and grades."""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import previous_month_start, week_start
from app.domain import AcademicPeriod, AttendanceStatus, FamilyMessageKind
from app.repositories.academic_repository import AcademicRepository
from app.services.family_message_service import FamilyMessageService, students_with_guardians
from app.services.notifications.email_sender import EmailSender
from app.services.risk.features import PASSING_SCORE

WEEKDAYS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
# fmt: off
MONTHS = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
# fmt: on


def _day(value: date) -> str:
    return f"{WEEKDAYS[value.weekday()]} {value.day}"


def _days(values: list[date]) -> str:
    return ", ".join(_day(value) for value in sorted(values))


def weekly_attendance(db: Session, sender: EmailSender, today: date) -> int:
    """Saturday: families of students with absences or lateness during the week."""
    start = week_start(today)
    end = start + timedelta(days=5)
    academic = AcademicRepository(db)
    service = FamilyMessageService(db, sender)
    sent = 0

    for student in students_with_guardians(db):
        records = academic.attendance_records(student.id, start, end)
        absent = [r.date for r in records if r.status == AttendanceStatus.ABSENT]
        late = [r.date for r in records if r.status == AttendanceStatus.LATE]
        justified = [r.date for r in records if r.status == AttendanceStatus.JUSTIFIED]
        if not absent and not late:
            continue

        rows: list[tuple[str, str]] = []
        if absent:
            rows.append(("Faltas", f"{len(absent)} ({_days(absent)})"))
        if late:
            rows.append(("Tardanzas", f"{len(late)} ({_days(late)})"))
        if justified:
            rows.append(("Faltas justificadas", f"{len(justified)} ({_days(justified)})"))

        week = f"semana del {start.day} al {end.day} de {MONTHS[end.month - 1]}"
        message = service.publish(
            student,
            kind=FamilyMessageKind.WEEKLY_ATTENDANCE,
            reference_date=start,
            subject=f"Asistencia de {student.first_name}, {week}",
            intro=f"Le compartimos el resumen de asistencia de {student.first_name} de la {week}.",
            rows=rows,
        )
        sent += message is not None
    db.commit()
    return sent


def perfect_attendance(db: Session, sender: EmailSender, today: date) -> int:
    """First day of the month: recognition for students who never missed class last month."""
    start = previous_month_start(today)
    end = today.replace(day=1) - timedelta(days=1)
    month = MONTHS[start.month - 1]
    academic = AcademicRepository(db)
    service = FamilyMessageService(db, sender)
    sent = 0

    for student in students_with_guardians(db):
        records = academic.attendance_records(student.id, start, end)
        if not records or any(
            r.status in (AttendanceStatus.ABSENT, AttendanceStatus.LATE) for r in records
        ):
            continue
        message = service.publish(
            student,
            kind=FamilyMessageKind.PERFECT_ATTENDANCE,
            reference_date=start,
            subject=f"¡{student.first_name} tuvo asistencia perfecta en {month}!",
            intro=(
                f"{student.first_name} asistió a todas sus clases y llegó puntual durante {month}. "
                "¡Felicitaciones a toda la familia!"
            ),
            rows=[("Días de clase registrados", str(len(records)))],
        )
        sent += message is not None
    db.commit()
    return sent


def period_grades(db: Session, sender: EmailSender, today: date) -> int:
    """Daily: grade report for periods that ended during the last week."""
    periods = db.scalars(
        select(AcademicPeriod).where(
            AcademicPeriod.end_date < today,
            AcademicPeriod.end_date >= today - timedelta(days=7),
        )
    ).all()
    academic = AcademicRepository(db)
    service = FamilyMessageService(db, sender)
    sent = 0

    for period in periods:
        for student in students_with_guardians(db):
            if student.institution_id != period.institution_id:
                continue
            grades = academic.list_grades(student.id, period.id)
            if not grades:
                continue
            average = sum(grade.score for grade in grades) / len(grades)
            rows = [
                (
                    grade.subject.name,
                    f"{grade.score:.1f}"
                    + (" (desaprobado)" if grade.score < PASSING_SCORE else ""),
                )
                for grade in grades
            ]
            rows.append(("Promedio", f"{average:.1f}"))
            message = service.publish(
                student,
                kind=FamilyMessageKind.PERIOD_GRADES,
                reference_date=period.start_date,
                subject=f"Notas de {student.first_name}, bimestre {period.bimester}",
                intro=(
                    f"Terminó el bimestre {period.bimester}. Estas son las notas de "
                    f"{student.first_name}."
                ),
                rows=rows,
            )
            sent += message is not None
    db.commit()
    return sent
