from fastapi import APIRouter

from app.api.v1.endpoints.employees import router as employees_router
from app.api.v1.endpoints.departments import router as departments_router
from app.api.v1.endpoints.branches import router as branches_router
from app.api.v1.endpoints.designations import router as designations_router
from app.api.v1.endpoints.employment_types import router as employment_types_router
from app.api.v1.endpoints.employee_grades import router as employee_grades_router
from app.api.v1.endpoints.employee_groups import router as employee_groups_router
from app.api.v1.endpoints.shift_types import router as shift_types_router
from app.api.v1.endpoints.shift_locations import router as shift_locations_router

api_router = APIRouter()
api_router.include_router(employees_router)
api_router.include_router(departments_router)
api_router.include_router(branches_router)
api_router.include_router(designations_router)
api_router.include_router(employment_types_router)
api_router.include_router(employee_grades_router)
api_router.include_router(employee_groups_router)
api_router.include_router(shift_types_router)
api_router.include_router(shift_locations_router)
