"""Compensatory Leave Request service.

On approval, increments total_leaves_allocated of the matching active LeaveAllocation.
Also writes a LeaveLedgerEntry.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime, timezone, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compensatory_leave_request import CompensatoryLeaveRequest
from app.models.leave_allocation import LeaveAllocation
from app.models.leave_ledger_entry import LeaveLedgerEntry
from app.schemas.compensatory_leave import (
    CompensatoryLeaveRequestCreate, CompensatoryLeaveReview,
)


def _cid(db: AsyncSession) -> UUID:
    cid = db.info.get("company_id")
    return UUID(cid) if isinstance(cid, str) else cid


def _naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def list_requests(
    db: AsyncSession,
    employee_id: Optional[UUID] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[List[CompensatoryLeaveRequest], int]:
    cid = _cid(db)
    from sqlalchemy import func
    base = select(func.count(CompensatoryLeaveRequest.id)).where(
        CompensatoryLeaveRequest.company_id == cid
    )
    q = select(CompensatoryLeaveRequest).where(CompensatoryLeaveRequest.company_id == cid)
    if employee_id:
        base = base.where(CompensatoryLeaveRequest.employee_id == employee_id)
        q = q.where(CompensatoryLeaveRequest.employee_id == employee_id)
    if status_filter:
        base = base.where(CompensatoryLeaveRequest.status == status_filter)
        q = q.where(CompensatoryLeaveRequest.status == status_filter)
    total = (await db.execute(base)).scalar() or 0
    items = (await db.execute(q.order_by(CompensatoryLeaveRequest.created_at.desc()).offset(skip).limit(limit))).scalars().all()
    return list(items), total


async def get_request(db: AsyncSession, request_id: UUID) -> CompensatoryLeaveRequest:
    cid = _cid(db)
    obj = (await db.execute(
        select(CompensatoryLeaveRequest).where(
            CompensatoryLeaveRequest.id == request_id,
            CompensatoryLeaveRequest.company_id == cid,
        )
    )).scalars().first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compensatory leave request not found")
    return obj


async def create_request(
    db: AsyncSession,
    data: CompensatoryLeaveRequestCreate,
    employee_id: UUID,
) -> CompensatoryLeaveRequest:
    cid = _cid(db)
    obj = CompensatoryLeaveRequest(
        company_id=cid,
        employee_id=employee_id,
        **data.model_dump(),
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def review_request(
    db: AsyncSession,
    request_id: UUID,
    data: CompensatoryLeaveReview,
    reviewed_by: UUID,
) -> CompensatoryLeaveRequest:
    cid = _cid(db)
    obj = await get_request(db, request_id)
    if obj.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot review a request with status '{obj.status}'",
        )

    obj.status = data.status
    obj.reviewed_by = reviewed_by
    obj.reviewed_at = _naive_utcnow()
    obj.review_note = data.review_note

    if data.status == "approved":
        # Count working days between work_from_date and work_end_date
        days = (obj.work_end_date - obj.work_from_date).days + 1

        # Find active allocation for this leave type
        alloc = (await db.execute(
            select(LeaveAllocation).where(
                and_(
                    LeaveAllocation.company_id == cid,
                    LeaveAllocation.employee_id == obj.employee_id,
                    LeaveAllocation.leave_type_id == obj.leave_type_id,
                    LeaveAllocation.status == "active",
                )
            ).order_by(LeaveAllocation.from_date.desc()).limit(1)
        )).scalars().first()

        if alloc:
            alloc.total_leaves_allocated += days
            obj.leave_allocation_id = alloc.id

            # Write ledger entry
            db.add(LeaveLedgerEntry(
                company_id=cid,
                employee_id=obj.employee_id,
                leave_type_id=obj.leave_type_id,
                from_date=obj.work_from_date,
                to_date=obj.work_end_date,
                leaves=float(days),
                transaction_type="allocation",
                transaction_name=str(obj.id),
            ))

    await db.commit()
    await db.refresh(obj)
    return obj
