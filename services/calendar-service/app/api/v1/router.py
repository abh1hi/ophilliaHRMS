from fastapi import APIRouter

from app.api.v1.endpoints import (
    workspaces,
    calendars,
    events,
    tasks,
    search,
    audit,
    internal,
    google,
)

api_router = APIRouter()

api_router.include_router(workspaces.router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(calendars.router, prefix="/calendars", tags=["calendars"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(audit.router, prefix="/audit-logs", tags=["audit"])
api_router.include_router(internal.router, prefix="/internal", tags=["internal"])
api_router.include_router(google.router, prefix="/google", tags=["google"])
