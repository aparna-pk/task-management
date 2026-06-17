from fastapi import APIRouter

from app.api.v1 import auth, tasks, teams

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(teams.router, prefix="/teams", tags=["Teams"])
