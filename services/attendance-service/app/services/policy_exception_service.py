"""PolicyExceptionService: CRUD for temporary per-employee policy overrides."""
from typing import Optional, List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy_exception import PolicyException
from app.repositories.policy_exception_repository import PolicyExceptionRepository
from app.schemas.attendance import PolicyExceptionCreate, PolicyExceptionUpdate
from app.services.policy_service import _invalidate_policy_cache

_ERR_NOT_FOUND = "Policy exception not found"
_ERR_NO_FIELDS = "No fields to update"


def _geofence_ids_to_json(ids: Optional[List[UUID]]) -> Optional[list]:
    """Serialize UUID list to JSON-safe strings for JSONB storage."""
    if ids is None:
        return None
    return [str(gid) for gid in ids]


class PolicyExceptionService:
    """Business logic for temporary per-employee policy overrides."""

    def __init__(self, db: AsyncSession):
        self.repo = PolicyExceptionRepository(db)

    async def create_exception(
        self, data: PolicyExceptionCreate, approved_by: UUID
    ) -> PolicyException:
        exception = PolicyException(
            employee_id=data.employee_id,
            reason=data.reason,
            reason_category=data.reason_category,
            from_date=data.from_date,
            to_date=data.to_date,
            override_method=data.override_method,
            override_work_hours=data.override_work_hours,
            override_work_start_time=data.override_work_start_time,
            override_late_grace_minutes=data.override_late_grace_minutes,
            override_geofence_id=data.override_geofence_id,
            override_geofence_ids=_geofence_ids_to_json(data.override_geofence_ids),
            override_overtime_policy_id=data.override_overtime_policy_id,
            approved_by=approved_by,
        )
        exc = await self.repo.create(exception)
        await _invalidate_policy_cache(self.repo._company_id)
        return exc

    async def list_exceptions(
        self,
        skip: int = 0,
        limit: int = 100,
        employee_id: Optional[UUID] = None,
        include_inactive: bool = False,
    ) -> tuple[list, int]:
        return await self.repo.get_all(
            skip=skip, limit=limit, employee_id=employee_id, include_inactive=include_inactive
        )

    async def get_exception(self, exception_id: UUID) -> PolicyException:
        exc = await self.repo.get_by_id(exception_id)
        if not exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_NOT_FOUND)
        return exc

    async def update_exception(
        self, exception_id: UUID, data: PolicyExceptionUpdate
    ) -> PolicyException:
        exc = await self.repo.get_by_id(exception_id)
        if not exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_NOT_FOUND)

        updates = data.model_dump(exclude_unset=True)
        if not updates:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=_ERR_NO_FIELDS)

        # Serialize UUID list to JSON strings for JSONB column
        if "override_geofence_ids" in updates:
            updates["override_geofence_ids"] = _geofence_ids_to_json(updates["override_geofence_ids"])

        result = await self.repo.update(exc, updates)
        await _invalidate_policy_cache(self.repo._company_id)
        return result

    async def delete_exception(self, exception_id: UUID) -> None:
        exc = await self.repo.get_by_id(exception_id)
        if not exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_ERR_NOT_FOUND)
        company_id = self.repo._company_id
        await self.repo.delete(exc)
        await _invalidate_policy_cache(company_id)
