"""GeofenceConsentService: GDPR consent management for geofence tracking."""
import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.geofence_consent_repository import GeofenceConsentRepository
from app.models.geofence_consent import GeofenceConsent

logger = logging.getLogger(__name__)

_CONSENT_REQUIRED_MSG = (
    "Geofence-based attendance requires your explicit consent to collect location data. "
    "Please submit consent at POST /api/v1/attendance/geofence/consent before clocking in."
)


class GeofenceConsentService:
    """Give, withdraw, and check GDPR consent for geofence location tracking."""

    def __init__(self, db: AsyncSession):
        self.repo = GeofenceConsentRepository(db)
        self._db = db

    async def give_consent(
        self,
        employee_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> GeofenceConsent:
        record = await self.repo.give_consent(employee_id, ip_address, user_agent)
        await self._db.commit()
        logger.info(
            f"Geofence consent given: employee={employee_id}",
            extra={"user_id": str(employee_id), "service_task": "gdpr_consent"},
        )
        return record

    async def withdraw_consent(self, employee_id: UUID) -> GeofenceConsent:
        record = await self.repo.withdraw_consent(employee_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No consent record found for this employee.",
            )
        await self._db.commit()
        logger.info(
            f"Geofence consent withdrawn: employee={employee_id}",
            extra={"user_id": str(employee_id), "service_task": "gdpr_consent"},
        )
        return record

    async def get_consent_status(self, employee_id: UUID) -> dict:
        record = await self.repo.get_for_employee(employee_id)
        if not record:
            return {"consented": False, "consent_given_at": None, "consent_withdrawn_at": None}
        return {
            "consented": record.consented,
            "consent_given_at": record.consent_given_at,
            "consent_withdrawn_at": record.consent_withdrawn_at,
        }

    async def assert_consent(self, employee_id: UUID) -> None:
        """Raise HTTP 451 if the employee has not consented to geofence tracking."""
        record = await self.repo.get_for_employee(employee_id)
        if not record or not record.consented:
            raise HTTPException(
                status_code=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS,
                detail=_CONSENT_REQUIRED_MSG,
            )
