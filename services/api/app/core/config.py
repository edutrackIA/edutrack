from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="API_", extra="ignore")

    app_name: str = "EduTrack API"
    version: str = "0.1.0"
    environment: str = "development"
    database_url: str = "mysql+pymysql://edutrack:edutrack@localhost:3306/edutrack"
    ml_service_url: str = "http://localhost:8001"
    cors_origins: list[str] = ["http://localhost:5173"]

    jwt_secret: str = "dev-only-secret-change-me-in-env-file-0123456789"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 7
    refresh_reuse_grace_seconds: int = 30
    bcrypt_rounds: int = 12

    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = False
    mail_from: str = "EduTrack <no-reply@edutrack.dev>"
    portal_url: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()
