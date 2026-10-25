from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain import (
    Attendance,
    AttendanceStatus,
    FamilyMessage,
    FamilyMessageStatus,
    Grade,
    SituationKind,
    StudentSituation,
    WeeklyCheckin,
)
from app.services.jobs.family_reports import perfect_attendance, period_grades, weekly_attendance
from app.services.jobs.tutor_reminders import remind_pending_checkins, report_missed_checkins
from app.worker import JOBS
from tests.conftest import Outbox, School, auth

MONDAY = date(2026, 3, 9)
SATURDAY = date(2026, 3, 14)


def attend(db: Session, student_id: int, statuses: list[AttendanceStatus], start: date = MONDAY):
    db.add_all(
        Attendance(student_id=student_id, date=start + timedelta(days=i), status=status)
        for i, status in enumerate(statuses)
    )
    db.commit()


def recipients(outbox: Outbox) -> list[str]:
    return [message["To"] for message in outbox.messages]


# --- Asistencia semanal ---------------------------------------------------------------


def test_weekly_attendance_reports_absences_and_lateness(
    school: School, db_session: Session, outbox: Outbox
) -> None:
    attend(
        db_session,
        school.student_a.id,
        [AttendanceStatus.ABSENT, AttendanceStatus.LATE, AttendanceStatus.PRESENT],
    )

    sent = weekly_attendance(db_session, outbox, SATURDAY)
    again = weekly_attendance(db_session, outbox, SATURDAY)

    assert (sent, again) == (1, 0)
    assert recipients(outbox) == ["parent@school.dev"]
    email = outbox.messages[0]
    assert email["Subject"] == "Asistencia de Lucía, semana del 9 al 14 de marzo"
    text = email.get_body(preferencelist=("plain",)).get_content()
    assert "Faltas: 1 (lunes 9)" in text
    assert "Tardanzas: 1 (martes 10)" in text
    assert "Mensaje automático de EduTrack" in text


def test_weekly_attendance_skips_perfect_weeks(
    school: School, db_session: Session, outbox: Outbox
) -> None:
    attend(db_session, school.student_a.id, [AttendanceStatus.PRESENT] * 5)

    assert weekly_attendance(db_session, outbox, SATURDAY) == 0
    assert outbox.messages == []


# --- Retención por situaciones sensibles -------------------------------------------------


def hold_message(school: School, db: Session, outbox: Outbox) -> FamilyMessage:
    db.add(
        StudentSituation(
            student_id=school.student_a.id,
            kind=SituationKind.HEALTH,
            started_on=MONDAY,
            created_by=school.teacher.id,
        )
    )
    db.commit()
    attend(db, school.student_a.id, [AttendanceStatus.ABSENT] * 3)
    weekly_attendance(db, outbox, SATURDAY)
    message = db.scalar(select(FamilyMessage))
    assert message is not None
    return message


def test_sensitive_situations_hold_the_message_for_the_tutor(
    client: TestClient, school: School, db_session: Session, outbox: Outbox
) -> None:
    message = hold_message(school, db_session, outbox)

    held = client.get("/api/v1/family-messages/held", headers=auth(school.teacher)).json()
    other = client.get("/api/v1/family-messages/held", headers=auth(school.other_teacher)).json()

    assert message.status == FamilyMessageStatus.HELD
    assert outbox.messages == []
    assert [item["hold_reason"] for item in held] == ["Situación activa: Problema de salud"]
    assert held[0]["kind_label"] == "Asistencia semanal"
    assert held[0]["rows"][0][0] == "Faltas"
    assert other == []


def test_tutor_releases_a_held_message(
    client: TestClient, school: School, db_session: Session, outbox: Outbox
) -> None:
    message = hold_message(school, db_session, outbox)
    url = f"/api/v1/family-messages/{message.id}"

    released = client.post(f"{url}/release", headers=auth(school.teacher))
    again = client.post(f"{url}/release", headers=auth(school.teacher))

    assert released.json()["status"] == "SENT"
    assert recipients(outbox) == ["parent@school.dev"]
    assert again.status_code == 409


def test_tutor_discards_a_held_message(
    client: TestClient, school: School, db_session: Session, outbox: Outbox
) -> None:
    message = hold_message(school, db_session, outbox)
    url = f"/api/v1/family-messages/{message.id}"

    other = client.post(f"{url}/discard", headers=auth(school.other_teacher))
    discarded = client.post(f"{url}/discard", headers=auth(school.teacher))
    missing = client.post("/api/v1/family-messages/9999/discard", headers=auth(school.teacher))

    assert other.status_code == 403
    assert discarded.json()["status"] == "DISCARDED"
    assert outbox.messages == []
    assert missing.status_code == 404


def test_failed_delivery_is_recorded(school: School, db_session: Session, outbox: Outbox) -> None:
    outbox.fail = True
    attend(db_session, school.student_a.id, [AttendanceStatus.ABSENT])

    weekly_attendance(db_session, outbox, SATURDAY)

    message = db_session.scalar(select(FamilyMessage))
    assert message is not None and message.status == FamilyMessageStatus.FAILED


# --- Asistencia perfecta y notas ------------------------------------------------------------


def test_perfect_attendance_is_recognized_once_a_month(
    school: School, db_session: Session, outbox: Outbox
) -> None:
    attend(db_session, school.student_a.id, [AttendanceStatus.PRESENT] * 5, date(2026, 3, 2))
    attend(db_session, school.student_b.id, [AttendanceStatus.ABSENT], date(2026, 3, 2))

    assert perfect_attendance(db_session, outbox, date(2026, 4, 1)) == 1
    assert outbox.messages[0]["Subject"] == "¡Lucía tuvo asistencia perfecta en marzo!"


def test_period_grades_are_sent_after_the_period_ends(
    school: School, db_session: Session, outbox: Outbox
) -> None:
    db_session.add_all(
        [
            Grade(
                student_id=school.student_a.id,
                subject_id=school.math.id,
                period_id=school.period.id,
                score=9,
            ),
            Grade(
                student_id=school.student_a.id,
                subject_id=school.language.id,
                period_id=school.period.id,
                score=15,
            ),
        ]
    )
    db_session.commit()

    late = period_grades(db_session, outbox, date(2026, 5, 20))
    sent = period_grades(db_session, outbox, date(2026, 5, 10))

    assert (late, sent) == (0, 1)
    text = outbox.messages[0].get_body(preferencelist=("plain",)).get_content()
    assert "Matemática: 9.0 (desaprobado)" in text
    assert "Promedio: 12.0" in text


# --- Recordatorios al tutor ---------------------------------------------------------------


FRIDAY = date(2026, 10, 30)
SUNDAY = date(2026, 11, 1)
WEEK = date(2026, 10, 26)


def checkin(db: Session, school: School, week: date) -> None:
    db.add(
        WeeklyCheckin(
            classroom_id=school.classroom_a.id, week_start=week, completed_by=school.teacher.id
        )
    )
    db.commit()


def test_friday_reminds_tutors_with_pending_follow_up(
    school: School, db_session: Session, outbox: Outbox
) -> None:
    checkin(db_session, school, WEEK)

    sent = remind_pending_checkins(db_session, outbox, FRIDAY)
    again = remind_pending_checkins(db_session, outbox, FRIDAY)

    assert (sent, again) == (1, 0)
    assert recipients(outbox) == ["teacher2@school.dev"]
    assert "sábado 31 de octubre" in outbox.messages[0].get_body(("plain",)).get_content()


def test_sunday_escalates_to_the_director_after_two_missed_weeks(
    school: School, db_session: Session, outbox: Outbox
) -> None:
    checkin(db_session, school, WEEK - timedelta(days=7))

    report_missed_checkins(db_session, outbox, SUNDAY)

    assert sorted(recipients(outbox)) == [
        "director@school.dev",
        "teacher2@school.dev",
        "teacher@school.dev",
    ]
    escalation = next(m for m in outbox.messages if m["To"] == "director@school.dev")
    assert escalation["Subject"] == "Dos semanas sin seguimiento en 3° B"


def test_every_job_is_scheduled() -> None:
    assert set(JOBS) == {
        "checkin-reminders",
        "missed-checkins",
        "weekly-attendance",
        "perfect-attendance",
        "period-grades",
    }
