from fastapi import APIRouter
from .endpoints import (
    leave_types, leave_balances, leave_requests, holidays, leave_calendar,
    leave_periods, holiday_lists, leave_policies, leave_allocations,
    leave_block_lists, compensatory_leave_requests, leave_encashments, leave_ledger,
    internal,
)

api_router = APIRouter()

# Existing routers
api_router.include_router(leave_types.router, prefix="/leave-types", tags=["leave-types"])
api_router.include_router(leave_balances.router, prefix="/leave-balances", tags=["leave-balances"])
api_router.include_router(leave_requests.router, prefix="/leave-requests", tags=["leave-requests"])
api_router.include_router(holidays.router, prefix="/holidays", tags=["holidays"])
api_router.include_router(leave_calendar.router, prefix="/leave-calendar", tags=["leave-calendar"])

# New routers
api_router.include_router(leave_periods.router, prefix="/leave-periods", tags=["leave-periods"])
api_router.include_router(holiday_lists.router, prefix="/holiday-lists", tags=["holiday-lists"])
api_router.include_router(leave_policies.router, prefix="/leave-policies", tags=["leave-policies"])
api_router.include_router(leave_allocations.router, prefix="/leave-allocations", tags=["leave-allocations"])
api_router.include_router(leave_block_lists.router, prefix="/leave-block-lists", tags=["leave-block-lists"])
api_router.include_router(compensatory_leave_requests.router, prefix="/compensatory-leave-requests", tags=["compensatory-leave"])
api_router.include_router(leave_encashments.router, prefix="/leave-encashments", tags=["leave-encashments"])
api_router.include_router(leave_ledger.router, prefix="/leave-ledger", tags=["leave-ledger"])
api_router.include_router(internal.router, prefix="/internal", tags=["internal"])
