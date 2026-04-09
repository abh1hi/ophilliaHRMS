"""Leave Allocation service — manage allocations and adjustments.

Idempotent: duplicate allocation for same employee/type/period is rejected.
Every allocation or adjustment writes a LeaveLedgerEntry.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.leave_allocation import LeaveAllocation
from app.models.leave_adjustment import LeaveAdjustment
from app.models.leave_ledger_entry import LeaveLedgerEntry
from app.schemas.leave_allocation import (
    LeaveAllocationCreate, LeaveAllocationUpdate, LeaveAdjustmentCreate,
)


def _cid(db: AsyncSession) -> UUID:
    cid = db.info.get("company_id")
    return UUID(cid) if isinstance(cid, str) else cid


async def _write_ledger(
    db: AsyncSession,
    company_id: UUID,
    employee_id: UUID,
    leave_type_id: UUID,
    leaves: float,
    from_date: date,
    to_date: date,
    transaction_type: str,
    transaction_name: Optional[str] = None,
    is_carry_forward: int = 0,
) -> None:
    entry = LeaveLedgerEntry(
        company_id=company_id,
        employee_id=employee_id,
        leave_type_id=leave_type_id,
        from_date=from_date,
        to_date=to_date,
        leaves=leaves,
        transaction_type=transaction_type,
        transaction_name=transaction_name,
        is_carry_forward=is_carry_forward,
    )
    db.add(entry)


# ── Leave Allocation CRUD ─────────────────────────────────────────────────────

async def list_allocations(
    db: AsyncSession,
    employee_id: Optional[UUID] = None,
    leave_type_id: Optional[UUID] = None,
    leave_period_id: Optional[UUID] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[List[LeaveAllocation], int]:
    cid = _cid(db)
    from sqlalchemy import func
    base = select(func.count(LeaveAllocation.id)).where(LeaveAllocation.company_id == cid)
    q = select(LeaveAllocation).where(LeaveAllocation.company_id == cid)

    for stmt, fil, val in [
        (employee_id, LeaveAllocation.employee_id, employee_id),
        (leave_type_id, LeaveAllocation.leave_type_id, leave_type_id),
        (leave_period_id, LeaveAllocation.leave_period_id, leave_period_id),
        (status_filter, LeaveAllocation.status, status_filter),
    ]:
        if stmt:
            base = base.where(fil == val)
            q = q.where(fil == val)

    total = (await db.execute(base)).scalar() or 0
    items = (await db.execute(q.order_by(LeaveAllocation.from_date.desc()).offset(skip).limit(limit))).scalars().all()
    return list(items), total


async def get_allocation(db: AsyncSession, allocation_id: UUID) -> LeaveAllocation:
    cid = _cid(db)
    obj = (await db.execute(
        select(LeaveAllocation).where(
            LeaveAllocation.id == allocation_id,
            LeaveAllocation.company_id == cid,
        )
    )).scalars().first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allocation not found")
    return obj


async def create_allocation(db: AsyncSession, data: LeaveAllocationCreate) -> LeaveAllocation:
    cid = _cid(db)
    total = data.new_leaves_allocated + data.carry_forward_days
    obj = LeaveAllocation(
        company_id=cid,
        employee_id=data.employee_id,
        leave_type_id=data.leave_type_id,
        leave_period_id=data.leave_period_id,
        from_date=data.from_date,
        to_date=data.to_date,
        new_leaves_allocated=data.new_leaves_allocated,
        carry_forward_days=data.carry_forward_days,
        total_leaves_allocated=total,
    )
    db.add(obj)
    await db.flush()

    await _write_ledger(
        db, cid, data.employee_id, data.leave_type_id,
        leaves=data.new_leaves_allocated,
        from_date=data.from_date, to_date=data.to_date,
        transaction_type="allocation", transaction_name=str(obj.id),
    )
    if data.carry_forward_days > 0:
        await _write_ledger(
            db, cid, data.employee_id, data.leave_type_id,
            leaves=data.carry_forward_days,
            from_date=data.from_date, to_date=data.to_date,
            transaction_type="allocation", transaction_name=str(obj.id),
            is_carry_forward=1,
        )
    await db.commit()
    await db.refresh(obj)
    return obj


async def update_allocation(
    db: AsyncSession, allocation_id: UUID, data: LeaveAllocationUpdate
) -> LeaveAllocation:
    obj = await get_allocation(db, allocation_id)
    updates = data.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(obj, k, v)
    if "new_leaves_allocated" in updates or "carry_forward_days" in updates:
        obj.total_leaves_allocated = obj.new_leaves_allocated + obj.carry_forward_days
    await db.commit()
    await db.refresh(obj)
    return obj


# ── Leave Adjustment ──────────────────────────────────────────────────────────

async def adjust_allocation(
    db: AsyncSession,
    data: LeaveAdjustmentCreate,
    adjusted_by: UUID,
) -> LeaveAdjustment:
    cid = _cid(db)
    alloc = await get_allocation(db, data.allocation_id)

    delta = data.adjustment_days if data.adjustment_type == "allocate" else -data.adjustment_days
    alloc.total_leaves_allocated = alloc.total_leaves_allocated + delta

    if alloc.total_leaves_allocated < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Adjustment would result in negative total allocation",
        )

    adj = LeaveAdjustment(
        company_id=cid,
        employee_id=alloc.employee_id,
        allocation_id=alloc.id,
        adjustment_type=data.adjustment_type,
        adjustment_days=data.adjustment_days,
        reason=data.reason,
        adjusted_by=adjusted_by,
        adjustment_date=date.today(),
    )
    db.add(adj)
    await db.flush()

    await _write_ledger(
        db, cid, alloc.employee_id, alloc.leave_type_id,
        leaves=delta,
        from_date=alloc.from_date, to_date=alloc.to_date,
        transaction_type="adjustment", transaction_name=str(adj.id),
    )
    await db.commit()
    await db.refresh(adj)
    return adj
