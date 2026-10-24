import jwt
import pytest

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("Secret123!")

    assert hashed != "Secret123!"
    assert verify_password("Secret123!", hashed)
    assert not verify_password("Other123!", hashed)


def test_passwords_longer_than_bcrypt_limit_are_supported() -> None:
    long_password = "a" * 100

    assert verify_password(long_password, hash_password(long_password))


def test_access_token_contains_expected_claims() -> None:
    token = create_access_token(user_id=7, role="ANALYST", institution_id=3)

    payload = decode_access_token(token)

    assert payload["sub"] == "7"
    assert payload["role"] == "ANALYST"
    assert payload["inst"] == 3
    assert payload["type"] == "access"


def test_decode_rejects_tokens_signed_with_another_key() -> None:
    forged = jwt.encode(
        {"sub": "1", "type": "access", "exp": 9999999999},
        "another-secret-key-that-is-at-least-32-bytes",
        algorithm="HS256",
    )

    with pytest.raises(jwt.PyJWTError):
        decode_access_token(forged)


def test_decode_rejects_non_access_tokens() -> None:
    settings = get_settings()
    token = jwt.encode(
        {"sub": "1", "type": "refresh", "exp": 9999999999},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(jwt.PyJWTError):
        decode_access_token(token)
