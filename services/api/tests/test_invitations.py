import re
from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.domain import Invitation
from tests.conftest import Outbox, School, auth

LOGIN_URL = "/api/v1/auth/login"
EMAIL = "rosa@correo.com"


def invite(client: TestClient, school: School, outbox: Outbox) -> str:
    client.post(
        f"/api/v1/students/{school.student_a2.id}/guardians",
        json={"full_name": "Rosa Huamán", "email": EMAIL, "kinship": "Madre"},
        headers=auth(school.director),
    )
    text = outbox.messages[-1].get_body(("plain",)).get_content()
    match = re.search(r"/invitacion/(\S+)", text)
    assert match is not None
    return match.group(1)


def test_invited_guardian_cannot_log_in_before_accepting(
    client: TestClient, school: School, outbox: Outbox
) -> None:
    invite(client, school, outbox)

    response = client.post(LOGIN_URL, json={"email": EMAIL, "password": "cualquiera1"})

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"


def test_guardian_accepts_and_logs_in(client: TestClient, school: School, outbox: Outbox) -> None:
    token = invite(client, school, outbox)

    info = client.get(f"/api/v1/invitations/{token}").json()
    accepted = client.post(f"/api/v1/invitations/{token}/accept", json={"password": "Clave2026"})
    login = client.post(LOGIN_URL, json={"email": EMAIL, "password": "Clave2026"})
    reused = client.post(f"/api/v1/invitations/{token}/accept", json={"password": "Otra2026x"})

    assert info == {"full_name": "Rosa Huamán", "email": EMAIL}
    assert accepted.status_code == 204
    assert login.status_code == 200
    assert reused.status_code == 409
    assert reused.json()["code"] == "INVITATION_EXPIRED"


def test_weak_passwords_are_rejected(client: TestClient, school: School, outbox: Outbox) -> None:
    token = invite(client, school, outbox)

    response = client.post(f"/api/v1/invitations/{token}/accept", json={"password": "corta"})

    assert response.status_code == 422
    assert response.json()["code"] == "WEAK_PASSWORD"
    assert "al menos 8 caracteres" in response.json()["message"]
    assert "número" in response.json()["message"]


def test_expired_and_unknown_invitations(
    client: TestClient, school: School, outbox: Outbox, db_session: Session
) -> None:
    token = invite(client, school, outbox)
    invitation = db_session.scalar(select(Invitation))
    assert invitation is not None
    invitation.expires_at = utcnow() - timedelta(minutes=1)
    db_session.commit()

    expired = client.get(f"/api/v1/invitations/{token}")
    unknown = client.get("/api/v1/invitations/no-existe")

    assert expired.status_code == 409
    assert unknown.status_code == 404
    assert unknown.json()["code"] == "INVITATION_NOT_FOUND"


def test_only_the_hash_of_the_token_is_stored(
    client: TestClient, school: School, outbox: Outbox, db_session: Session
) -> None:
    token = invite(client, school, outbox)

    stored = db_session.scalar(select(Invitation.token_hash))

    assert stored is not None and stored != token and len(stored) == 64
