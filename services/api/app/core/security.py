import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any

import bcrypt
import jwt

from app.core.config import get_settings

BCRYPT_MAX_BYTES = 72


def _encode_password(password: str) -> bytes:
    return password.encode("utf-8")[:BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=get_settings().bcrypt_rounds)
    return bcrypt.hashpw(_encode_password(password), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(_encode_password(password), password_hash.encode("utf-8"))


@lru_cache
def dummy_password_hash() -> str:
    """Hash used to keep login timing constant when the email does not exist."""
    return hash_password(secrets.token_urlsafe(16))


def create_access_token(*, user_id: int, role: str, institution_id: int) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "inst": institution_id,
        "type": "access",
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_ttl_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    payload = jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
        options={"require": ["exp", "sub", "type"]},
    )
    if payload["type"] != "access":
        raise jwt.InvalidTokenError("Unexpected token type")
    return payload


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


MIN_PASSWORD_LENGTH = 8


def password_problems(password: str) -> list[str]:
    """Rules for passwords people choose themselves. Empty list means it is acceptable."""
    problems = []
    if len(password) < MIN_PASSWORD_LENGTH:
        problems.append(f"Debe tener al menos {MIN_PASSWORD_LENGTH} caracteres")
    if not any(char.isalpha() for char in password):
        problems.append("Debe incluir al menos una letra")
    if not any(char.isdigit() for char in password):
        problems.append("Debe incluir al menos un número")
    return problems


def new_url_token() -> tuple[str, str]:
    """Random token for a link and the SHA-256 hash to store instead of it."""
    raw = secrets.token_urlsafe(32)
    return raw, hash_url_token(raw)


def hash_url_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
