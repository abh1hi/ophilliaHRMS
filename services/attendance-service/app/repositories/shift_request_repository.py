from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shift_request import ShiftRequest


class ShiftRequestRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _company_id(self) -> UUID:
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session — use get_db_with_tenant")
        return UUID(cid) if isinstance(cid, str) else cid

    def _scoped(self, stmt):
        return stmt.where(ShiftRequest.company_id == self._company_id)

    async def create(self, request: ShiftRequest) -> ShiftRequest:
        request.company_id = self._company_id
        self.db.add(request)
        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def get_by_id(self, request_id: UUID) -> Optional[ShiftRequest]:
        result = await self.db.execute(
            self._scoped(select(ShiftRequest).where(ShiftRequest.id == request_id))
        )
        return result.scalars().first()

    async def get_all(
        self,
        employee_id: Optional[UUID] = None,
        status: Optional[str] = None,
    ) -> tuple[List[ShiftRequest], int]:
        base = self._scoped(select(func.count(ShiftRequest.id)))
        query = self._scoped(select(ShiftRequest).order_by(ShiftRequest.created_at.desc()))
        if employee_id:
            base = base.where(ShiftRequest.employee_id == employee_id)
            query = query.where(ShiftRequest.employee_id == employee_id)
        if status:
            base = base.where(ShiftRequest.status == status)
            query = query.where(ShiftRequest.status == status)
        total = (await self.db.execute(base)).scalar() or 0
        items = (await self.db.execute(query)).scalars().all()
        return list(items), total

    async def update(self, request: ShiftRequest, data: dict) -> ShiftRequest:
        for k, v in data.items():
            setattr(request, k, v)
        await self.db.commit()
        await self.db.refresh(request)
        return request
