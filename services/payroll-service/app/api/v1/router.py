from fastapi import APIRouter
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.salary import router as salary_router
from app.api.v1.endpoints.payroll import router as payroll_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(salary_router)
api_router.include_router(payroll_router)
