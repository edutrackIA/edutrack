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


@lru_cache
def get_settings() -> Settings:
    return Settings()
