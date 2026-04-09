"""API v1 路由聚合。"""

from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.hotwords import router as hotwords_router
from app.api.v1.endpoints.meeting_shares import router as meeting_shares_router
from app.api.v1.endpoints.meetings import router as meetings_router
from app.api.v1.endpoints.shared_meetings import router as shared_meetings_router
from app.api.v1.endpoints.participants import router as participants_router
from app.api.v1.endpoints.team_invitations import router as team_invitations_router
from app.api.v1.endpoints.tasks import router as tasks_router
from app.api.v1.endpoints.teams import router as teams_router
from app.api.v1.endpoints.transcripts import router as transcripts_router
from app.api.v1.endpoints.users import router as users_router, open_router as register_router

api_router = APIRouter()
api_router.include_router(register_router)
api_router.include_router(auth_router)
api_router.include_router(health_router)
api_router.include_router(hotwords_router)
api_router.include_router(users_router)
api_router.include_router(meetings_router)
api_router.include_router(meeting_shares_router)
api_router.include_router(shared_meetings_router)
api_router.include_router(transcripts_router)
api_router.include_router(tasks_router)
api_router.include_router(participants_router)
api_router.include_router(teams_router)
api_router.include_router(team_invitations_router)
