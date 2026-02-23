from fastapi import APIRouter

from app.api.v1.endpoints.employees import router as employees_router
from app.api.v1.endpoints.departments import router as departments_router

api_router = APIRouter()
api_router.include_router(employees_router)
api_router.include_router(departments_router)
