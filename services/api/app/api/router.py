from fastapi import APIRouter

from app.api.routes import (
    auth,
    classrooms,
    commitments,
    dashboard,
    health,
    imports,
    recommendations,
    risk,
    settings,
    students,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(classrooms.router)
api_router.include_router(students.router)
api_router.include_router(commitments.router)
api_router.include_router(imports.router)
api_router.include_router(risk.router)
api_router.include_router(recommendations.router)
api_router.include_router(settings.router)
api_router.include_router(dashboard.router)
