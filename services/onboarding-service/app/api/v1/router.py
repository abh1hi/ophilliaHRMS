from fastapi import APIRouter

from app.api.v1.endpoints import onboarding_routes

api_router = APIRouter()
api_router.include_router(onboarding_routes.router, prefix="/onboarding", tags=["onboarding"])
