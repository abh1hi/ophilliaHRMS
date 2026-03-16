from fastapi import APIRouter
from .endpoints import leave_types, leave_balances, leave_requests, holidays, leave_calendar

api_router = APIRouter()

api_router.include_router(leave_types.router, prefix="/leave-types", tags=["leave-types"])
api_router.include_router(leave_balances.router, prefix="/leave-balances", tags=["leave-balances"])
api_router.include_router(leave_requests.router, prefix="/leave-requests", tags=["leave-requests"])
api_router.include_router(holidays.router, prefix="/holidays", tags=["holidays"])
api_router.include_router(leave_calendar.router, prefix="/leave-calendar", tags=["leave-calendar"])
