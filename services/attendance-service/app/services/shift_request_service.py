import logging
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shift_request import ShiftRequest
from app.repositories.shift_request_repository import ShiftRequestRepository
from app.schemas.shift_request import ShiftRequestCreate, ShiftRequestUpdate, ShiftRequestReview

logger = logging.getLogger(__name__)


class ShiftRequestService:
    def __init__(self, db: AsyncSession):
        self.repo = ShiftRequestRepository(db)

    async def create(self, data: ShiftRequestCreate) -> ShiftRequest:
        request = ShiftRequest(
            employee_id=data.employee_id,
            request_type=data.request_type,
            from_date=data.from_date,
            to_date=data.to_date,
            requested_shift_type_id=data.requested_shift_type_id,
            reason=data.reason,
            status="pending",
        )
        result = await self.repo.create(request)
        logger.info("ShiftRequest created: %s", result.id)
        return result

    async def get(self, request_id: UUID) -> ShiftRequest:
        obj = await self.repo.get_by_id(request_id)
        if not obj:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Shift request {request_id} not found")
        return obj

    async def list_all(self, employee_id: Optional[UUID] = None, status_filter: Optional[str] = None):
        return await self.repo.get_all(employee_id=employee_id, status=status_filter)

    async def update(self, request_id: UUID, data: ShiftRequestUpdate) -> ShiftRequest:
        obj = await self.get(request_id)
        if obj.status != "pending":
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Only pending requests can be edited")
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No fields to update")
        return await self.repo.update(obj, update_data)

    async def review(self, request_id: UUID, data: ShiftRequestReview, reviewed_by: UUID) -> ShiftRequest:
        obj = await self.get(request_id)
        if obj.status != "pending":
            raise HTTPException(status.HTTP_409_CONFLICT, detail=f"Request is already {obj.status}")
        return await self.repo.update(obj, {
            "status": data.status,
            "reviewed_by": reviewed_by,
            "reviewed_at": datetime.now(timezone.utc).replace(tzinfo=None),
            "review_note": data.review_note,
        })

    async def cancel(self, request_id: UUID) -> ShiftRequest:
        obj = await self.get(request_id)
        if obj.status != "pending":
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Only pending requests can be cancelled")
        return await self.repo.update(obj, {"status": "cancelled"})
