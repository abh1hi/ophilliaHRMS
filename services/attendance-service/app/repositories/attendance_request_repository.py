from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance_request import AttendanceRequest


class AttendanceRequestRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _company_id(self) -> UUID:
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session — use get_db_with_tenant")
        return UUID(cid) if isinstance(cid, str) else cid

    def _scoped(self, stmt):
        return stmt.where(AttendanceRequest.company_id == self._company_id)

    async def create(self, request: AttendanceRequest) -> AttendanceRequest:
        request.company_id = self._company_id
        self.db.add(request)
        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def get_by_id(self, request_id: UUID) -> Optional[AttendanceRequest]:
        result = await self.db.execute(
            self._scoped(select(AttendanceRequest).where(AttendanceRequest.id == request_id))
        )
        return result.scalars().first()

    async def get_all(
        self,
        employee_id: Optional[UUID] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[AttendanceRequest], int]:
        base = self._scoped(select(func.count(AttendanceRequest.id)))
        query = self._scoped(
            select(AttendanceRequest).order_by(AttendanceRequest.created_at.desc())
        )
        if employee_id:
            base = base.where(AttendanceRequest.employee_id == employee_id)
            query = query.where(AttendanceRequest.employee_id == employee_id)
        if status:
            base = base.where(AttendanceRequest.status == status)
            query = query.where(AttendanceRequest.status == status)
        total = (await self.db.execute(base)).scalar() or 0
        items = (await self.db.execute(query.offset(skip).limit(limit))).scalars().all()
        return list(items), total

    async def update(self, request: AttendanceRequest, data: dict) -> AttendanceRequest:
        for k, v in data.items():
            setattr(request, k, v)
        await self.db.commit()
        await self.db.refresh(request)
        return request
