"""Internal endpoints — service-to-service only.

Authenticated via X-Internal-Token header; no JWT required.
Used by calendar-service to fetch holidays for cross-service sync.
"""
from fastapi import APIRouter, Header, HTTPException, status
from sqlalchemy.future import select
from typing import Annotated, List, Optional
from uuid import UUID
from datetime import date

from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.models.leave import Holiday
from app.core.config import settings
from app.db.session import AsyncSessionLocal

router = APIRouter()


def _verify_internal_token(x_internal_token: Annotated[str, Header()]) -> None:
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
