"""Geofence consent endpoints — GDPR consent management for location-based attendance."""
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, require_role, TokenPayload, get_db_with_tenant
from app.core.constants import UserRole
from app.core.responses import ok
from app.services.geofence_consent_service import GeofenceConsentService
from app.schemas.attendance import (
    GeofenceConsentResponse, GeofenceConsentStatusResponse, GeofenceConsentListResponse,
)

router = APIRouter(prefix="/attendance/geofence/consent", tags=["geofence-consent"])

_HR_ROLES = require_role(UserRole.HR, UserRole.ADMIN, UserRole.SUPER_ADMIN)


def _svc(db: AsyncSession = Depends(get_db_with_tenant)) -> GeofenceConsentService:
    return GeofenceConsentService(db)


@router.get("/me")
async def get_my_consent(
    current_user: TokenPayload = Depends(get_current_user),
    svc: GeofenceConsentService = Depends(_svc),
):
    status_dict = await svc.get_consent_status(UUID(current_user.sub))
    return ok(GeofenceConsentStatusResponse(**status_dict).model_dump(mode="json"))


@router.post("")
async def give_consent(
    request: Request,
    current_user: TokenPayload = Depends(get_current_user),
    svc: GeofenceConsentService = Depends(_svc),
):
    ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    record = await svc.give_consent(
        UUID(current_user.sub), ip_address=ip, user_agent=user_agent
    )
    return ok(GeofenceConsentResponse.model_validate(record).model_dump(mode="json"))


@router.delete("")
async def withdraw_consent(
    current_user: TokenPayload = Depends(get_current_user),
    svc: GeofenceConsentService = Depends(_svc),
):
    record = await svc.withdraw_consent(UUID(current_user.sub))
    return ok(GeofenceConsentResponse.model_validate(record).model_dump(mode="json"))


@router.get("")
async def list_all_consents(
    _: TokenPayload = Depends(_HR_ROLES),
    db: AsyncSession = Depends(get_db_with_tenant),
    svc: GeofenceConsentService = Depends(_svc),
):
    from sqlalchemy import select
    from app.models.geofence_consent import GeofenceConsent

    cid = db.info.get("company_id")
    company_id = UUID(cid) if isinstance(cid, str) else cid
    result = await db.execute(
        select(GeofenceConsent).where(GeofenceConsent.company_id == company_id)
    )
    items = result.scalars().all()
    return ok(GeofenceConsentListResponse(
        items=[GeofenceConsentResponse.model_validate(r).model_dump(mode="json") for r in items],
        total=len(items),
    ).model_dump(mode="json"))
