import re
from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.domain import Invitation, TokenPurpose
from tests.conftest import DEFAULT_PASSWORD, Outbox, School, auth

LOGIN = "/api/v1/auth/login"
FORGOT = "/api/v1/auth/password/forgot"
EMAIL = "parent@school.dev"
NEW_PASSWORD = "NuevaClave2026"


def login(client: TestClient, password: str, email: str = EMAIL):
    return client.post(LOGIN, json={"email": email, "password": password})


def forgot(client: TestClient, email: str = EMAIL):
    return client.post(FORGOT, json={"email": email})


def link(outbox: Outbox, path: str) -> str:
    text = outbox.messages[-1].get_body(("plain",)).get_content()
    match = re.search(rf"/{path}/(\S+)", text)
    assert match is not None
    return match.group(1)


# --- Olvidé mi contraseña ------------------------------------------------------------


def test_reset_flow_changes_the_password_and_closes_sessions(
    client: TestClient, school: School, outbox: Outbox
) -> None:
    refresh = login(client, DEFAULT_PASSWORD).json()["refresh_token"]

    assert forgot(client).status_code == 202
    token = link(outbox, "restablecer")
    target = client.get(f"/api/v1/auth/password/reset/{token}")
    reset = client.post(f"/api/v1/auth/password/reset/{token}", json={"password": NEW_PASSWORD})
    reused = client.post(f"/api/v1/auth/password/reset/{token}", json={"password": "Otra2026x"})

    assert target.json() == {"email": EMAIL}
    assert reset.status_code == 204
    assert login(client, NEW_PASSWORD).status_code == 200
    assert login(client, DEFAULT_PASSWORD).status_code == 401
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": refresh}).status_code == 401
    assert reused.status_code == 409


def test_unknown_emails_get_the_same_answer_and_no_email(
    client: TestClient, school: School, outbox: Outbox
) -> None:
    response = forgot(client, "nadie@correo.com")

    assert response.status_code == 202
    assert outbox.messages == []


def test_invited_users_receive_a_new_invitation_instead(
    client: TestClient, school: School, outbox: Outbox
) -> None:
    client.post(
        f"/api/v1/students/{school.student_a2.id}/guardians",
        json={"full_name": "Rosa Huamán", "email": "rosa@correo.com", "kinship": "Madre"},
        headers=auth(school.director),
    )

    forgot(client, "rosa@correo.com")

    assert len(outbox.messages) == 2
    assert link(outbox, "invitacion")


def test_reset_links_are_not_invitations_and_expire_in_an_hour(
    client: TestClient, school: School, outbox: Outbox, db_session: Session
) -> None:
    forgot(client)
    token = link(outbox, "restablecer")
    stored = db_session.scalar(
        select(Invitation).where(Invitation.purpose == TokenPurpose.PASSWORD_RESET)
    )
    assert stored is not None

    as_invitation = client.get(f"/api/v1/invitations/{token}")
    stored.expires_at = utcnow() - timedelta(seconds=1)
    db_session.commit()
    expired = client.get(f"/api/v1/auth/password/reset/{token}")

    assert as_invitation.status_code == 404
    assert expired.status_code == 409


def test_weak_new_passwords_are_rejected(
    client: TestClient, school: School, outbox: Outbox
) -> None:
    forgot(client)
    token = link(outbox, "restablecer")

    response = client.post(f"/api/v1/auth/password/reset/{token}", json={"password": "corta"})

    assert response.status_code == 422
    assert response.json()["code"] == "WEAK_PASSWORD"


def test_requests_are_limited_per_email_and_per_address(
    client: TestClient, school: School, outbox: Outbox
) -> None:
    same_email = [forgot(client).status_code for _ in range(4)]
    others = [forgot(client, f"x{i}@correo.com").status_code for i in range(7)]

    assert same_email == [202] * 4
    assert len(outbox.messages) == 3
    assert others[:6] == [202] * 6
    assert others[6] == 429


# --- Cambiar contraseña ---------------------------------------------------------------


def change(client: TestClient, school: School, current: str, new: str):
    return client.post(
        "/api/v1/auth/password/change",
        json={"current_password": current, "new_password": new},
        headers=auth(school.parent),
    )


def test_change_password_requires_the_current_one(client: TestClient, school: School) -> None:
    refresh = login(client, DEFAULT_PASSWORD).json()["refresh_token"]

    wrong = change(client, school, "NoEsLaClave1", NEW_PASSWORD)
    same = change(client, school, DEFAULT_PASSWORD, DEFAULT_PASSWORD)
    changed = change(client, school, DEFAULT_PASSWORD, NEW_PASSWORD)

    assert wrong.status_code == 422
    assert wrong.json()["code"] == "WRONG_PASSWORD"
    assert same.json()["code"] == "WEAK_PASSWORD"
    assert changed.status_code == 204
    assert login(client, NEW_PASSWORD).status_code == 200
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": refresh}).status_code == 401
