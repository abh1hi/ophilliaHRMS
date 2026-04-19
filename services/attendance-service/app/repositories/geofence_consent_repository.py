from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.geofence_consent import GeofenceConsent


class GeofenceConsentRepository:
    """CRUD for GDPR geofence consent records."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _company_id(self) -> UUID:
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session")
        return UUID(cid) if isinstance(cid, str) else cid

    async def get_for_employee(self, employee_id: UUID) -> Optional[GeofenceConsent]:
        result = await self.db.execute(
            select(GeofenceConsent).where(
                and_(
                    GeofenceConsent.company_id == self._company_id,
                    GeofenceConsent.employee_id == employee_id,
                )
            )
        )
        return result.scalars().first()

    async def give_consent(
        self,
        employee_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> GeofenceConsent:
        """Upsert: create or update consent record to consented=True."""
        existing = await self.get_for_employee(employee_id)
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        if existing:
            existing.consented = True
            existing.consent_given_at = now
            existing.consent_withdrawn_at = None
            existing.ip_address = ip_address
            existing.user_agent = user_agent
            await self.db.flush()
            return existing

        record = GeofenceConsent(
            company_id=self._company_id,
            employee_id=employee_id,
            consented=True,
            consent_given_at=now,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record

    async def withdraw_consent(self, employee_id: UUID) -> Optional[GeofenceConsent]:
        """Mark consent as withdrawn."""
        existing = await self.get_for_employee(employee_id)
        if not existing:
            return None
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        existing.consented = False
        existing.consent_withdrawn_at = now
        await self.db.flush()
        return existing
