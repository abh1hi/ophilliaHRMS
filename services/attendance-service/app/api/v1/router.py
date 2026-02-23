from fastapi import APIRouter

from app.api.v1.endpoints.attendance import router as attendance_router

api_router = APIRouter()
api_router.include_router(attendance_router)
