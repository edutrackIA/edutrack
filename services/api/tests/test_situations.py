from collections.abc import Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_school_today
from app.domain import SituationAction, SituationEvent
from app.main import app
from tests.conftest import School, auth

WEDNESDAY = date(2026, 10, 28)
SUNDAY = date(2026, 11, 1)


@pytest.fixture
def today() -> Iterator[list[date]]:
    """Mutable clock: tests can move the school's date."""
    current = [WEDNESDAY]
    app.dependency_overrides[get_school_today] = lambda: current[0]
    yield current
    app.dependency_overrides.pop(get_school_today, None)


def situations_url(student_id: int) -> str:
    return f"/api/v1/students/{student_id}/situations"


def create(client: TestClient, school: School, **overrides: object) -> dict:
    payload = {"kind": "HEALTH", "note": "Hospitalizada una semana."} | overrides
    response = client.post(
        situations_url(school.student_a.id), json=payload, headers=auth(school.teacher)
    )
    assert response.status_code == 201, response.text
    return response.json()


# --- Catálogo -----------------------------------------------------------------


def test_catalog_lists_every_situation_with_its_group(client: TestClient, school: School) -> None:
    body = client.get("/api/v1/situations/catalog", headers=auth(school.teacher)).json()

    groups = {item["kind"]: item["group"] for item in body}
    assert len(body) == 16
    assert groups["GRIEF"] == "MESSAGE"
    assert groups["FAMILY_VIOLENCE"] == "TEAM"
    assert groups["BULLYING"] == "TEAM"


# --- Situaciones ----------------------------------------------------------------


def test_tutor_marks_a_situation(client: TestClient, school: School, today: list[date]) -> None:
    body = create(client, school)

    assert body["label"] == "Problema de salud"
    assert body["group"] == "MESSAGE"
    assert body["started_on"] == "2026-10-28"
    assert body["resolved_on"] is None


def test_situation_cannot_start_in_the_future(
    client: TestClient, school: School, today: list[date]
) -> None:
    response = client.post(
        situations_url(school.student_a.id),
        json={"kind": "GRIEF", "started_on": "2026-11-15"},
        headers=auth(school.teacher),
    )

    assert response.status_code == 422


def test_only_the_tutor_and_the_director_manage_situations(
    client: TestClient, school: School, today: list[date]
) -> None:
    payload = {"kind": "GRIEF"}
    url = situations_url(school.student_a.id)

    for user in (school.other_teacher, school.analyst, school.parent):
        assert client.post(url, json=payload, headers=auth(user)).status_code == 403
        assert client.get(url, headers=auth(user)).status_code == 403
    assert client.post(url, json=payload, headers=auth(school.director)).status_code == 201


def test_resolve_and_reopen_keep_an_audit_trail(
    client: TestClient, school: School, today: list[date], db_session: Session
) -> None:
    situation = create(client, school)
    url = f"/api/v1/situations/{situation['id']}"
    headers = auth(school.teacher)

    client.patch(url, json={"note": "Ya volvió a clases."}, headers=headers)
    resolved = client.patch(url, json={"resolved": True}, headers=headers).json()
    active = client.get(situations_url(school.student_a.id), headers=headers).json()
    history = client.get(
        f"{situations_url(school.student_a.id)}?include_resolved=true", headers=headers
    ).json()
    reopened = client.patch(url, json={"resolved": False}, headers=headers).json()

    assert resolved["resolved_on"] == "2026-10-28"
    assert resolved["note"] == "Ya volvió a clases."
    assert active == []
    assert len(history) == 1
    assert reopened["resolved_on"] is None
    actions = db_session.scalars(select(SituationEvent.action).order_by(SituationEvent.id)).all()
    assert actions == [
        SituationAction.CREATED,
        SituationAction.UPDATED,
        SituationAction.RESOLVED,
        SituationAction.REOPENED,
    ]


def test_blank_notes_are_stored_as_empty(
    client: TestClient, school: School, today: list[date]
) -> None:
    assert create(client, school, note="   ")["note"] is None


def test_unknown_situation_is_not_found(
    client: TestClient, school: School, today: list[date]
) -> None:
    response = client.patch(
        "/api/v1/situations/9999", json={"resolved": True}, headers=auth(school.teacher)
    )

    assert response.status_code == 404


def test_classroom_lists_active_situations_of_its_students(
    client: TestClient, school: School, today: list[date]
) -> None:
    create(client, school, kind="GRIEF")
    url = f"/api/v1/classrooms/{school.classroom_a.id}/situations"

    tutor = client.get(url, headers=auth(school.teacher)).json()
    other = client.get(url, headers=auth(school.other_teacher))

    assert [item["kind"] for item in tutor] == ["GRIEF"]
    assert other.status_code == 403


# --- Seguimiento semanal -----------------------------------------------------------


def test_tutor_completes_the_weekly_check_in(
    client: TestClient, school: School, today: list[date]
) -> None:
    url = f"/api/v1/classrooms/{school.classroom_a.id}/checkins/current"

    before = client.get(url, headers=auth(school.teacher)).json()
    after = client.post(f"{url}/complete", headers=auth(school.teacher)).json()
    again = client.post(f"{url}/complete", headers=auth(school.teacher))

    assert before == {
        "classroom_id": school.classroom_a.id,
        "week_start": "2026-10-26",
        "deadline": "2026-10-31",
        "editable": True,
        "completed": False,
        "completed_at": None,
    }
    assert after["completed"] is True
    assert again.status_code == 200


def test_check_in_closes_after_saturday(
    client: TestClient, school: School, today: list[date]
) -> None:
    today[0] = SUNDAY
    url = f"/api/v1/classrooms/{school.classroom_a.id}/checkins/current"

    status = client.get(url, headers=auth(school.teacher)).json()
    response = client.post(f"{url}/complete", headers=auth(school.teacher))

    assert status["editable"] is False
    assert response.status_code == 409


def test_only_the_tutor_completes_the_check_in(
    client: TestClient, school: School, today: list[date]
) -> None:
    url = f"/api/v1/classrooms/{school.classroom_a.id}/checkins/current"

    director = client.post(f"{url}/complete", headers=auth(school.director))
    other = client.post(f"{url}/complete", headers=auth(school.other_teacher))
    missing = client.get("/api/v1/classrooms/9999/checkins/current", headers=auth(school.teacher))

    assert director.status_code == 422
    assert other.status_code == 403
    assert missing.status_code == 404
