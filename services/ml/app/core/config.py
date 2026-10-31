from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="ML_", extra="ignore")

    app_name: str = "EduTrack ML Service"
    version: str = "0.1.0"
    model_dir: str = "models"
    # Shared secret the API sends to train and activate models. Empty disables those actions.
    admin_token: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
