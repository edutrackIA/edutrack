"""Guards against N+1 queries: the busiest lists must cost the same number of SQL
statements whether the school has a few students or many."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.domain import (
    Alert,
    Guardianship,
    Recommendation,
    RiskAssessment,
    RiskLevel,
    Sex,
    Student,
    User,
)
from tests.conftest import School, auth, engine


@contextmanager
def counted() -> Iterator[list[str]]:
    statements: list[str] = []

    def record(conn, cursor, statement, parameters, context, executemany) -> None:  # noqa: ANN001
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", record)
    try:
        yield statements
    finally:
        event.remove(engine, "before_cursor_execute", record)


def add_students(db: Session, school: School, start: int, count: int) -> None:
    """Assessed students with a pending recommendation, an alert and a guardian each."""
    for index in range(start, start + count):
        student = Student(
            institution_id=school.classroom_a.institution_id,
            classroom_id=school.classroom_a.id,
            code=f"Q{index:03d}",
            first_name=f"Alumno{index}",
            last_name="Carga",
            birth_date=date(2012, 1, 1),
            sex=Sex.F,
        )
        db.add(student)
        db.flush()
        assessment = RiskAssessment(
            student_id=student.id,
            period_id=school.period.id,
            probability=0.8,
            level=RiskLevel.HIGH,
            model_version="rf-test",
            top_factors=[],
        )
        db.add(assessment)
        db.flush()
        db.add(
            Recommendation(
                assessment_id=assessment.id,
                student_id=student.id,
                period_id=school.period.id,
                parent_items=["Revisar la agenda cada noche."],
                teacher_items=["Conversar con el estudiante."],
            )
        )
        db.add(Alert(assessment_id=assessment.id, recipient_id=school.teacher.id))
        db.add(Guardianship(guardian_id=school.parent.id, student_id=student.id, kinship="Madre"))
    db.commit()


def queries(client: TestClient, db: Session, url: str, user: User) -> int:
    # A fresh identity map, as each real request has its own session.
    db.expunge_all()
    with counted() as statements:
        response = client.get(url, headers=auth(user))
    assert response.status_code == 200, response.text
    return len(statements)


ENDPOINTS: list[tuple[str, Callable[[School], str], Callable[[School], User]]] = [
    (
        "dashboard",
        lambda s: f"/api/v1/dashboard/summary?period_id={s.period.id}",
        lambda s: s.director,
    ),
    ("classroom", lambda s: f"/api/v1/classrooms/{s.classroom_a.id}/students", lambda s: s.teacher),
    ("recommendations", lambda s: "/api/v1/recommendations", lambda s: s.director),
    ("alerts", lambda s: "/api/v1/alerts", lambda s: s.teacher),
]


@pytest.mark.parametrize(("name", "url", "user"), ENDPOINTS, ids=[e[0] for e in ENDPOINTS])
def test_lists_do_not_query_once_per_student(
    client: TestClient,
    school: School,
    db_session: Session,
    name: str,
    url: Callable[[School], str],
    user: Callable[[School], User],
) -> None:
    add_students(db_session, school, 0, 3)
    few = queries(client, db_session, url(school), user(school))

    add_students(db_session, school, 3, 12)
    many = queries(client, db_session, url(school), user(school))

    assert many == few, f"{name}: {few} queries with 5 students, {many} with 17"
