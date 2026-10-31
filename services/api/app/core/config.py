from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_JWT_SECRET = "dev-only-secret-change-me-in-env-file-0123456789"
MIN_SECRET_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="API_", extra="ignore")

    app_name: str = "EduTrack API"
    version: str = "0.1.0"
    environment: str = "development"
    database_url: str = "mysql+pymysql://edutrack:edutrack@localhost:3306/edutrack"
    ml_service_url: str = "http://localhost:8001"
    # Shared secret with the ML service to train and activate models (ML_ADMIN_TOKEN there).
    ml_admin_token: str = ""
    cors_origins: list[str] = ["http://localhost:5173"]

    jwt_secret: str = DEV_JWT_SECRET
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

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @model_validator(mode="after")
    def safe_for_production(self) -> "Settings":
        """Refuse to start in production with development defaults."""
        if not self.is_production:
            return self
        problems = []
        if self.jwt_secret == DEV_JWT_SECRET or len(self.jwt_secret) < MIN_SECRET_LENGTH:
            problems.append(f"API_JWT_SECRET must be a random value of {MIN_SECRET_LENGTH}+ chars")
        if "*" in self.cors_origins:
            problems.append("API_CORS_ORIGINS cannot be '*'")
        if not self.portal_url.startswith("https://"):
            problems.append("API_PORTAL_URL must use https")
        if problems:
            raise ValueError("; ".join(problems))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
