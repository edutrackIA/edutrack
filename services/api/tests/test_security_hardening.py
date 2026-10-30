from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app import main
from app.core.config import Settings
from app.core.rate_limit import RateLimiter
from app.domain import User
from tests.conftest import DEFAULT_PASSWORD

LOGIN_URL = "/api/v1/auth/login"
EMAIL = "director@test.dev"


def login(client: TestClient, password: str, email: str = EMAIL):
    return client.post(LOGIN_URL, json={"email": email, "password": password})


# --- Límite de intentos -------------------------------------------------------------


def test_login_is_blocked_after_five_failures(
    client: TestClient, make_user: Callable[..., User]
) -> None:
    make_user(email=EMAIL)

    failures = [login(client, "Wrong123!").status_code for _ in range(5)]
    blocked = login(client, DEFAULT_PASSWORD)

    assert failures == [401] * 5
    assert blocked.status_code == 429
    assert blocked.json()["code"] == "TOO_MANY_ATTEMPTS"
    assert 0 < int(blocked.headers["Retry-After"]) <= 15 * 60


def test_the_block_is_per_account(client: TestClient, make_user: Callable[..., User]) -> None:
    make_user(email=EMAIL)
    make_user(email="otro@test.dev")
    for _ in range(5):
        login(client, "Wrong123!")

    assert login(client, DEFAULT_PASSWORD, email="otro@test.dev").status_code == 200


def test_a_successful_login_resets_the_counter(
    client: TestClient, make_user: Callable[..., User]
) -> None:
    make_user(email=EMAIL)
    for _ in range(4):
        login(client, "Wrong123!")
    assert login(client, DEFAULT_PASSWORD).status_code == 200

    for _ in range(4):
        login(client, "Wrong123!")

    assert login(client, DEFAULT_PASSWORD).status_code == 200


def test_many_accounts_from_one_address_are_blocked(client: TestClient) -> None:
    statuses = [login(client, "Wrong123!", f"user{i}@test.dev").status_code for i in range(31)]

    assert statuses[:30] == [401] * 30
    assert statuses[30] == 429


def test_invalid_invitation_links_are_limited(client: TestClient) -> None:
    statuses = [client.get(f"/api/v1/invitations/fake-{i}").status_code for i in range(21)]

    assert statuses[:20] == [404] * 20
    assert statuses[20] == 429


def test_failures_expire_after_the_window() -> None:
    now = [1000.0]
    limiter = RateLimiter(limit=2, window_seconds=60, clock=lambda: now[0])
    limiter.record_failure("k")
    limiter.record_failure("k")
    assert limiter.retry_after("k") == 60

    now[0] += 61

    assert limiter.retry_after("k") is None


# --- Cabeceras de seguridad ------------------------------------------------------------


def test_responses_carry_security_headers(client: TestClient) -> None:
    headers = client.get("/api/v1/health").headers

    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["Referrer-Policy"] == "no-referrer"
    assert headers["Cache-Control"] == "no-store"
    assert "Strict-Transport-Security" not in headers


# --- Configuración de producción ---------------------------------------------------


PRODUCTION = {
    "environment": "production",
    "jwt_secret": "x" * 48,
    "cors_origins": ["https://edutrack.example.com"],
    "portal_url": "https://edutrack.example.com",
}


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"jwt_secret": "dev-only-secret-change-me-in-env-file-0123456789"}, "API_JWT_SECRET"),
        ({"jwt_secret": "short"}, "API_JWT_SECRET"),
        ({"cors_origins": ["*"]}, "API_CORS_ORIGINS"),
        ({"portal_url": "http://edutrack.example.com"}, "API_PORTAL_URL"),
    ],
)
def test_production_refuses_development_defaults(override: dict, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        Settings(**(PRODUCTION | override))


def test_production_hides_docs_and_forces_https(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "get_settings", lambda: Settings(**PRODUCTION))

    production = TestClient(main.create_app())

    assert production.get("/api/docs").status_code == 404
    assert production.get("/api/openapi.json").status_code == 404
    assert (
        "max-age=31536000" in production.get("/api/v1/health").headers["Strict-Transport-Security"]
    )
