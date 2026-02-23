from fastapi import APIRouter
from .endpoints import health

api_router = APIRouter()
# api_router.include_router(some_module.router, prefix="/module", tags=["module"])
