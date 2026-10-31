from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.api.routes import health, models, prediction
from app.core.config import get_settings
from app.model_store import load_active


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.model = load_active(Path(get_settings().model_dir))
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.version, lifespan=lifespan)
    app.state.model = None
    app.include_router(health.router)
    app.include_router(prediction.router)
    app.include_router(models.router)
    return app


app = create_app()
