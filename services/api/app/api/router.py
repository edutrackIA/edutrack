from fastapi import APIRouter

from app.api.routes import auth, classrooms, health, students

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(classrooms.router)
api_router.include_router(students.router)
