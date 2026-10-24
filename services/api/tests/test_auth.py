from collections.abc import Callable
from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_token
from app.core.time import utcnow
from app.domain import RefreshToken, Role, User

LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"
LOGOUT_URL = "/api/v1/auth/logout"
ME_URL = "/api/v1/auth/me"


def auth_header(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def test_login_returns_token_pair(
    client: TestClient, make_user: Callable[..., User], login: Callable[..., dict]
) -> None:
    make_user()

    body = login()

    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 900
    assert body["access_token"]
    assert body["refresh_token"]


def test_login_is_case_insensitive_for_email(
    make_user: Callable[..., User], login: Callable[..., dict]
) -> None:
    make_user()

    assert login(email="DIRECTOR@test.dev")["access_token"]


def test_login_rejects_wrong_password(client: TestClient, make_user: Callable[..., User]) -> None:
    make_user()

    response = client.post(LOGIN_URL, json={"email": "director@test.dev", "password": "Wrong123!"})

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"
    assert response.headers["www-authenticate"] == "Bearer"


def test_login_rejects_unknown_email(client: TestClient) -> None:
    response = client.post(LOGIN_URL, json={"email": "nobody@test.dev", "password": "Secret123!"})

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"


def test_login_rejects_inactive_user(client: TestClient, make_user: Callable[..., User]) -> None:
    make_user(is_active=False)

    response = client.post(LOGIN_URL, json={"email": "director@test.dev", "password": "Secret123!"})

    assert response.status_code == 401


def test_me_returns_authenticated_user(
    client: TestClient, make_user: Callable[..., User], login: Callable[..., dict]
) -> None:
    user = make_user(role=Role.TEACHER, email="teacher@test.dev")
    tokens = login(email="teacher@test.dev")

    response = client.get(ME_URL, headers=auth_header(tokens["access_token"]))

    assert response.status_code == 200
    assert response.json() == {
        "id": user.id,
        "email": "teacher@test.dev",
        "full_name": "Test User",
        "role": "TEACHER",
        "institution_id": user.institution_id,
    }


def test_me_requires_token(client: TestClient) -> None:
    response = client.get(ME_URL)

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"


def test_me_rejects_invalid_token(client: TestClient) -> None:
    response = client.get(ME_URL, headers=auth_header("not-a-jwt"))

    assert response.status_code == 401


def test_me_rejects_deactivated_user(
    client: TestClient,
    db_session: Session,
    make_user: Callable[..., User],
    login: Callable[..., dict],
) -> None:
    user = make_user()
    tokens = login()
    user.is_active = False
    db_session.commit()

    response = client.get(ME_URL, headers=auth_header(tokens["access_token"]))

    assert response.status_code == 401


def test_refresh_rotates_tokens(
    client: TestClient, make_user: Callable[..., User], login: Callable[..., dict]
) -> None:
    make_user()
    first = login()

    response = client.post(REFRESH_URL, json={"refresh_token": first["refresh_token"]})

    assert response.status_code == 200
    second = response.json()
    assert second["refresh_token"] != first["refresh_token"]
    assert client.get(ME_URL, headers=auth_header(second["access_token"])).status_code == 200


def test_reusing_a_rotated_refresh_token_revokes_all_sessions(
    client: TestClient, make_user: Callable[..., User], login: Callable[..., dict]
) -> None:
    make_user()
    first = login()
    second = client.post(REFRESH_URL, json={"refresh_token": first["refresh_token"]}).json()

    reuse = client.post(REFRESH_URL, json={"refresh_token": first["refresh_token"]})
    after_reuse = client.post(REFRESH_URL, json={"refresh_token": second["refresh_token"]})

    assert reuse.status_code == 401
    assert reuse.json()["code"] == "INVALID_REFRESH_TOKEN"
    assert after_reuse.status_code == 401


def test_refresh_rejects_unknown_token(client: TestClient) -> None:
    response = client.post(REFRESH_URL, json={"refresh_token": "unknown"})

    assert response.status_code == 401


def test_refresh_rejects_expired_token(
    client: TestClient,
    db_session: Session,
    make_user: Callable[..., User],
    login: Callable[..., dict],
) -> None:
    make_user()
    tokens = login()
    stored = db_session.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(tokens["refresh_token"]))
    )
    assert stored is not None
    stored.expires_at = utcnow() - timedelta(minutes=1)
    db_session.commit()

    response = client.post(REFRESH_URL, json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 401


def test_logout_revokes_refresh_token(
    client: TestClient, make_user: Callable[..., User], login: Callable[..., dict]
) -> None:
    make_user()
    tokens = login()

    logout = client.post(
        LOGOUT_URL,
        json={"refresh_token": tokens["refresh_token"]},
        headers=auth_header(tokens["access_token"]),
    )
    refresh = client.post(REFRESH_URL, json={"refresh_token": tokens["refresh_token"]})

    assert logout.status_code == 204
    assert refresh.status_code == 401
