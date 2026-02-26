from fastapi import APIRouter
from .endpoints import logs, preferences

api_router = APIRouter()

api_router.include_router(preferences.router, prefix="/preferences", tags=["preferences"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
