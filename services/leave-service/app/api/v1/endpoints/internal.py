"""Internal endpoints — service-to-service only.

Authenticated via X-Internal-Token header; no JWT required.
Used by calendar-service to fetch holidays for cross-service sync.
Used by onboarding-service for template application saga.
"""
from fastapi import APIRouter, Header, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy import delete
from typing import Annotated, List, Optional
from uuid import UUID
from datetime import date

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.models.leave import Holiday, LeaveType
from app.core.config import settings
from app.core.internal_auth import verify_service_jwt
from app.db.session import AsyncSessionLocal

router = APIRouter()


def _verify_internal_token(x_internal_token: Annotated[str, Header()]) -> None:
    """Legacy static-secret check — kept for backwards compat during transition."""
    if x_internal_token != settings.INTERNAL_SERVICE_TOKEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid internal token")


class HolidayInternalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    company_id: UUID
    name: str
    date: date
    description: Optional[str] = None


@router.get(
    "/holidays",
    response_model=List[HolidayInternalResponse],
    dependencies=[Depends(_verify_internal_token)],
)
async def list_all_holidays(year: Optional[int] = None):
    """Return all active holidays across all companies for a given year.

    Used by calendar-service holiday sync scheduler.
    """
    async with AsyncSessionLocal() as db:
        query = select(Holiday).where(Holiday.is_active == 1)
        if year:
            query = query.where(
                Holiday.date >= date(year, 1, 1),
                Holiday.date <= date(year, 12, 31),
            )
        result = await db.execute(query.order_by(Holiday.date))
        return result.scalars().all()


# ─── Onboarding template application ────────────────────────────────────────

class LeaveTypeSeedItem(BaseModel):
    name: str = Field(..., max_length=100)
    days_allowed: int = Field(..., ge=0)
    description: Optional[str] = None
    requires_approval: bool = True


class BulkSeedRequest(BaseModel):
    company_id: UUID
    leave_types: List[LeaveTypeSeedItem]


class BulkSeedResponse(BaseModel):
    created_ids: List[UUID]
    skipped: List[str]  # names that already existed


class BulkRollbackRequest(BaseModel):
    company_id: UUID
    leave_type_ids: List[UUID]


@router.post(
    "/leave-types/bulk-seed",
    response_model=BulkSeedResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_service_jwt)],
)
async def bulk_seed_leave_types(body: BulkSeedRequest):
    """Idempotent bulk create leave types for a company.

    Used by onboarding-service template application saga.
    Skips any leave type whose name already exists for the company.
    """
    created_ids: List[UUID] = []
    skipped: List[str] = []

    async with AsyncSessionLocal() as db:
        for item in body.leave_types:
            existing = await db.execute(
                select(LeaveType).where(
                    LeaveType.company_id == body.company_id,
                    LeaveType.name == item.name,
                )
            )
            if existing.scalars().first():
                skipped.append(item.name)
                continue

            lt = LeaveType(
                company_id=body.company_id,
                name=item.name,
                days_allowed=item.days_allowed,
                description=item.description,
                requires_approval=1 if item.requires_approval else 0,
                is_active=1,
            )
            db.add(lt)
            await db.flush()
            created_ids.append(lt.id)

        await db.commit()

    return BulkSeedResponse(created_ids=created_ids, skipped=skipped)


@router.delete(
    "/leave-types/bulk-rollback",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_service_jwt)],
)
async def bulk_rollback_leave_types(body: BulkRollbackRequest):
    """Delete specific leave types by ID for a company (saga compensation).

    Used by onboarding-service template application saga on failure.
    Only deletes IDs that belong to the given company_id (safety check).
    """
    if not body.leave_type_ids:
        return

    async with AsyncSessionLocal() as db:
        await db.execute(
            delete(LeaveType).where(
                LeaveType.id.in_(body.leave_type_ids),
                LeaveType.company_id == body.company_id,
            )
        )
        await db.commit()
