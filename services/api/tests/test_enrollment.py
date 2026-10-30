from collections.abc import Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_school_today
from app.domain import Classroom, Recommendation, RecommendationStatus, StudentStatus
from app.main import app
from tests.conftest import School, auth


@pytest.fixture(autouse=True)
def today() -> Iterator[None]:
    app.dependency_overrides[get_school_today] = lambda: date(2026, 10, 28)
    yield
    app.dependency_overrides.pop(get_school_today, None)


def withdraw(client: TestClient, school: School, user=None, **body: object):
    payload = {"exit_date": "2026-10-20", "reason": "WORK", "note": "Trabaja con su papá."}
    return client.post(
        f"/api/v1/students/{school.student_a.id}/withdrawal",
        json=payload | body,
        headers=auth(user or school.director),
    )


# --- Retiros y traslados --------------------------------------------------------------


def test_withdrawn_students_leave_classroom_lists(client: TestClient, school: School) -> None:
    response = withdraw(client, school)
    classroom = client.get(
        f"/api/v1/classrooms/{school.classroom_a.id}/students", headers=auth(school.teacher)
    ).json()
    children = client.get("/api/v1/me/children", headers=auth(school.parent)).json()
    record = client.get(f"/api/v1/students/{school.student_a.id}", headers=auth(school.director))

    assert response.json()["status"] == "WITHDRAWN"
    assert response.json()["exit_reason"] == "WORK"
    assert [student["code"] for student in classroom] == ["A002"]
    assert children == []
    assert record.status_code == 200


def test_transfers_are_not_dropouts(client: TestClient, school: School) -> None:
    response = withdraw(client, school, reason="TRANSFER")

    assert response.json()["status"] == "TRANSFERRED"


def test_withdrawal_discards_pending_recommendations(
    client: TestClient, assessed_school: School, db_session: Session
) -> None:
    withdraw(client, assessed_school)

    statuses = db_session.scalars(
        select(Recommendation.status).where(
            Recommendation.student_id == assessed_school.student_a.id
        )
    ).all()
    assert statuses and set(statuses) == {RecommendationStatus.DISCARDED}


def test_withdrawal_rules(client: TestClient, school: School) -> None:
    future = withdraw(client, school, exit_date="2026-11-15")
    graduation = withdraw(client, school, reason="GRADUATION")
    teacher = withdraw(client, school, user=school.teacher)
    first = withdraw(client, school)
    again = withdraw(client, school)

    assert future.status_code == 422
    assert graduation.status_code == 422
    assert teacher.status_code == 403
    assert first.status_code == 200
    assert again.status_code == 409


def test_reinstating_undoes_a_withdrawal(client: TestClient, school: School) -> None:
    withdraw(client, school)
    url = f"/api/v1/students/{school.student_a.id}/reinstatement"

    reinstated = client.post(url, headers=auth(school.analyst)).json()
    again = client.post(url, headers=auth(school.analyst))

    assert reinstated["status"] == "ENROLLED"
    assert reinstated["exit_reason"] is None
    assert again.status_code == 409


# --- Cierre del año -----------------------------------------------------------------------


def promote(client: TestClient, school: School, **body: object):
    return client.post(
        "/api/v1/school-years/2026/promotion", json=body, headers=auth(school.director)
    )


def test_promotion_preview_changes_nothing(
    client: TestClient, school: School, db_session: Session
) -> None:
    plan = promote(client, school, repeating_codes=["A002", "ZZZ9"]).json()

    assert plan["applied"] is False
    assert (plan["promoted"], plan["repeating"], plan["graduated"]) == (2, 1, 0)
    assert plan["unknown_codes"] == ["ZZZ9"]
    assert {(m["source"], m["target"], m["students"]) for m in plan["moves"]} == {
        ("3° A (2026)", "4° A (2027)", 1),
        ("3° A (2026)", "3° A (2027)", 1),
        ("3° B (2026)", "4° B (2027)", 1),
    }
    assert db_session.scalars(select(Classroom).where(Classroom.year == 2027)).all() == []


def test_promotion_moves_students_to_next_year_classrooms(
    client: TestClient, school: School, db_session: Session
) -> None:
    plan = promote(client, school, repeating_codes=["A002"], dry_run=False).json()

    db_session.refresh(school.student_a)
    db_session.refresh(school.student_a2)
    assert plan["applied"] is True
    assert (school.student_a.classroom.year, school.student_a.classroom.label) == (2027, "4° A")
    assert (school.student_a2.classroom.year, school.student_a2.classroom.label) == (2027, "3° A")
    again = promote(client, school, dry_run=False).json()
    assert again["promoted"] == 0


def test_students_in_the_final_grade_graduate(
    client: TestClient, school: School, db_session: Session
) -> None:
    plan = promote(client, school, final_grade=3, dry_run=False).json()

    db_session.refresh(school.student_b)
    assert plan["graduated"] == 3
    assert school.student_b.status == StudentStatus.GRADUATED


def test_promotion_needs_classrooms_and_the_director(client: TestClient, school: School) -> None:
    empty = client.post(
        "/api/v1/school-years/2030/promotion", json={}, headers=auth(school.director)
    )
    analyst = client.post(
        "/api/v1/school-years/2026/promotion", json={}, headers=auth(school.analyst)
    )

    assert empty.status_code == 422
    assert analyst.status_code == 403
