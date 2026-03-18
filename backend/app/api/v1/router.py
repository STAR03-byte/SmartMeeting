"""API v1 路由聚合。"""

from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.meetings import router as meetings_router
from app.api.v1.endpoints.participants import router as participants_router
from app.api.v1.endpoints.tasks import router as tasks_router
from app.api.v1.endpoints.transcripts import router as transcripts_router
from app.api.v1.endpoints.users import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(meetings_router)
api_router.include_router(transcripts_router)
api_router.include_router(tasks_router)
api_router.include_router(participants_router)
