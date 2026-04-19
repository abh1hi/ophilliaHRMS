"""OvertimeRequestRepository: data access for employee OT requests."""
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.overtime_request import OvertimeRequest


class OvertimeRequestRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _company_id(self) -> UUID:
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session")
        return UUID(cid) if isinstance(cid, str) else cid

    def _scoped(self, stmt):
        return stmt.where(OvertimeRequest.company_id == self._company_id)

    async def list_for_company(
        self,
        status: Optional[str] = None,
        employee_id: Optional[UUID] = None,
    ) -> list[OvertimeRequest]:
        stmt = self._scoped(select(OvertimeRequest)).order_by(OvertimeRequest.created_at.desc())
        if status:
            stmt = stmt.where(OvertimeRequest.status == status)
        if employee_id:
            stmt = stmt.where(OvertimeRequest.employee_id == employee_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_for_employee(self, employee_id: UUID) -> list[OvertimeRequest]:
        stmt = (
            self._scoped(select(OvertimeRequest))
            .where(OvertimeRequest.employee_id == employee_id)
            .order_by(OvertimeRequest.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, request_id: UUID) -> Optional[OvertimeRequest]:
        result = await self.db.execute(
            self._scoped(select(OvertimeRequest)).where(OvertimeRequest.id == request_id)
        )
        return result.scalars().first()

    async def create(
        self,
        employee_id: UUID,
        date,
        requested_hours: float,
        reason: str,
    ) -> OvertimeRequest:
        record = OvertimeRequest(
            company_id=self._company_id,
            employee_id=employee_id,
            date=date,
            requested_hours=requested_hours,
            reason=reason,
        )
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record

    async def review(
        self,
        request_id: UUID,
        status: str,
        reviewer_id: UUID,
        note: Optional[str],
    ) -> Optional[OvertimeRequest]:
        record = await self.get_by_id(request_id)
        if not record:
            return None
        record.status = status
        record.reviewed_by = reviewer_id
        record.review_note = note
        record.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.db.flush()
        return record

    async def delete(self, request_id: UUID) -> Optional[OvertimeRequest]:
        record = await self.get_by_id(request_id)
        if not record:
            return None
        await self.db.delete(record)
        await self.db.flush()
        return record
