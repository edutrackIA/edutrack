from fastapi import APIRouter

from app.api.routes import (
    auth,
    class_register,
    classrooms,
    commitments,
    dashboard,
    enrollment,
    family_checkins,
    family_messages,
    guardians,
    health,
    imports,
    invitations,
    model_monitoring,
    models,
    periods,
    recommendations,
    risk,
    school_setup,
    settings,
    situations,
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
api_router.include_router(periods.router)
api_router.include_router(situations.router)
api_router.include_router(family_messages.router)
api_router.include_router(family_checkins.router)
api_router.include_router(guardians.router)
api_router.include_router(invitations.router)
api_router.include_router(school_setup.router)
api_router.include_router(class_register.router)
api_router.include_router(enrollment.router)
api_router.include_router(model_monitoring.router)
api_router.include_router(models.router)
