from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.privacy import PRIVACY_NOTICE_VERSION
from app.core.security import hash_password
from app.domain import Guardianship, Role, User
from app.services.privacy_service import add_business_days
from tests.conftest import DEFAULT_PASSWORD, Outbox, School, auth


@pytest.fixture
def new_parent(school: School, db_session: Session) -> User:
    """A guardian who has not accepted the privacy notice yet."""
    parent = User(
        institution_id=school.classroom_a.institution_id,
        email="nuevo@familia.pe",
        full_name="Rosa Huamán",
        role=Role.PARENT,
        password_hash=hash_password(DEFAULT_PASSWORD),
    )
    db_session.add(parent)
    db_session.flush()
    db_session.add(
        Guardianship(guardian_id=parent.id, student_id=school.student_a2.id, kinship="Madre")
    )
    db_session.commit()
    return parent


# --- Consentimiento ---------------------------------------------------------------------


def test_guardians_accept_the_current_notice(client: TestClient, new_parent: User) -> None:
    before = client.get("/api/v1/me/privacy", headers=auth(new_parent)).json()
    outdated = client.post(
        "/api/v1/me/privacy/acceptance", json={"version": "2020-01"}, headers=auth(new_parent)
    )
    accepted = client.post(
        "/api/v1/me/privacy/acceptance",
        json={"version": PRIVACY_NOTICE_VERSION},
        headers=auth(new_parent),
    )
    again = client.post(
        "/api/v1/me/privacy/acceptance",
        json={"version": PRIVACY_NOTICE_VERSION},
        headers=auth(new_parent),
    )

    assert before == {"version": PRIVACY_NOTICE_VERSION, "accepted_at": None}
    assert outdated.status_code == 409
    assert outdated.json()["code"] == "NOTICE_OUTDATED"
    assert accepted.json()["accepted_at"] is not None
    assert again.json()["accepted_at"] == accepted.json()["accepted_at"]


def test_guardians_send_no_data_before_consenting(
    client: TestClient, school: School, new_parent: User
) -> None:
    url = f"/api/v1/students/{school.student_a2.id}/family-checkins/current"
    body = {"mood": "OK"}

    blocked = client.put(url, json=body, headers=auth(new_parent))
    client.post(
        "/api/v1/me/privacy/acceptance",
        json={"version": PRIVACY_NOTICE_VERSION},
        headers=auth(new_parent),
    )
    allowed = client.put(url, json=body, headers=auth(new_parent))

    assert blocked.status_code == 403
    assert blocked.json()["code"] == "CONSENT_REQUIRED"
    assert allowed.status_code == 200


# --- Solicitudes ARCO ----------------------------------------------------------------


def request_access(client: TestClient, school: School, student_id: int | None = None):
    return client.post(
        "/api/v1/data-requests",
        json={
            "student_id": student_id or school.student_a.id,
            "kind": "ACCESS",
            "details": "Quiero una copia de todos los datos de mi hija.",
        },
        headers=auth(school.parent),
    )


def test_guardian_requests_access_and_direction_answers(
    client: TestClient, school: School, outbox: Outbox
) -> None:
    created = request_access(client, school).json()
    directors_inbox = [message["To"] for message in outbox.messages]
    listed = client.get("/api/v1/data-requests", headers=auth(school.director)).json()
    resolved = client.post(
        f"/api/v1/data-requests/{created['id']}/resolution",
        json={"status": "RESOLVED", "response": "Le enviamos el expediente por correo."},
        headers=auth(school.director),
    ).json()
    again = client.post(
        f"/api/v1/data-requests/{created['id']}/resolution",
        json={"status": "REJECTED", "response": "Respuesta duplicada de prueba."},
        headers=auth(school.director),
    )
    mine = client.get("/api/v1/data-requests", headers=auth(school.parent)).json()

    assert created["status"] == "PENDING"
    assert date.fromisoformat(created["due_date"]) > date.fromisoformat(created["created_at"][:10])
    assert directors_inbox == ["director@school.dev"]
    assert [item["id"] for item in listed] == [created["id"]]
    assert resolved["status"] == "RESOLVED"
    assert outbox.messages[-1]["To"] == "parent@school.dev"
    assert again.status_code == 409
    assert mine[0]["response"] == "Le enviamos el expediente por correo."


def test_requests_are_limited_to_own_children_and_direction(
    client: TestClient, school: School
) -> None:
    other_child = request_access(client, school, school.student_a2.id)
    teacher = client.get("/api/v1/data-requests", headers=auth(school.teacher))
    created = request_access(client, school).json()
    pending = client.post(
        f"/api/v1/data-requests/{created['id']}/resolution",
        json={"status": "PENDING", "response": "Sigue pendiente de revisión."},
        headers=auth(school.director),
    )

    assert other_child.status_code == 403
    assert teacher.status_code == 403
    assert pending.status_code == 422


def test_direction_exports_everything_kept_about_a_student(
    client: TestClient, evaluated_school: School
) -> None:
    school = evaluated_school
    url = f"/api/v1/students/{school.student_a.id}/data-export"

    response = client.get(url, headers=auth(school.director))
    teacher = client.get(url, headers=auth(school.teacher))

    data = response.json()
    assert 'filename="expediente-A001.json"' in response.headers["content-disposition"]
    assert data["student"]["code"] == "A001"
    assert {grade["subject"] for grade in data["grades"]} == {"Comunicación", "Matemática"}
    assert data["guardians"][0]["email"] == "parent@school.dev"
    assert len(data["attendance"]) == 10
    assert teacher.status_code == 403


def test_business_days_skip_weekends() -> None:
    friday = date(2026, 10, 30)

    assert add_business_days(friday, 1) == date(2026, 11, 2)
    assert add_business_days(friday, 20) == date(2026, 11, 27)
