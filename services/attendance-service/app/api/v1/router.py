from fastapi import APIRouter

from app.api.v1.endpoints.attendance import router as attendance_router
from app.api.v1.endpoints.shift_schedules import router as shift_schedules_router
from app.api.v1.endpoints.shift_schedule_assignments import router as shift_schedule_assignments_router
from app.api.v1.endpoints.shift_assignments import router as shift_assignments_router
from app.api.v1.endpoints.shift_requests import router as shift_requests_router
from app.api.v1.endpoints.roster import router as roster_router
from app.api.v1.endpoints.employee_checkins import router as checkins_router
from app.api.v1.endpoints.attendance_requests import router as att_requests_router
from app.api.v1.endpoints.shift_types import router as shift_types_router
from app.api.v1.endpoints.overtime_policies import router as ot_policies_router
from app.api.v1.endpoints.overtime_requests import router as ot_requests_router
from app.api.v1.endpoints.holiday_calendar import router as holiday_calendar_router
from app.api.v1.endpoints.geofence_consent import router as geofence_consent_router

api_router = APIRouter()
# Specific sub-routers MUST come before the general attendance_router
# because attendance_router has GET /attendance/{record_id} which would
# otherwise shadow /attendance/checkins, /attendance/requests, and
# /attendance/geofence/consent.
api_router.include_router(geofence_consent_router)
api_router.include_router(checkins_router)
api_router.include_router(att_requests_router)
api_router.include_router(attendance_router)
api_router.include_router(shift_types_router)
api_router.include_router(shift_schedules_router)
api_router.include_router(shift_schedule_assignments_router)
api_router.include_router(shift_assignments_router)
api_router.include_router(shift_requests_router)
api_router.include_router(roster_router)
api_router.include_router(ot_policies_router)
api_router.include_router(ot_requests_router)
api_router.include_router(holiday_calendar_router)
