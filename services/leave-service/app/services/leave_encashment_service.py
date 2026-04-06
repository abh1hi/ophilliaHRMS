"""Leave Encashment service — process encashment of unused encashable leaves."""
from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.leave_encashment import LeaveEncashment
from app.models.leave_allocation import LeaveAllocation
from app.models.leave_ledger_entry import LeaveLedgerEntry
from app.schemas.leave_encashment import LeaveEncashmentCreate


def _cid(db: AsyncSession) -> UUID:
    cid = db.info.get("company_id")
    return UUID(cid) if isinstance(cid, str) else cid


async def list_encashments(
    db: AsyncSession,
    employee_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[List[LeaveEncashment], int]:
    cid = _cid(db)
    from sqlalchemy import func
    base = select(func.count(LeaveEncashment.id)).where(LeaveEncashment.company_id == cid)
    q = select(LeaveEncashment).where(LeaveEncashment.company_id == cid)
    if employee_id:
        base = base.where(LeaveEncashment.employee_id == employee_id)
        q = q.where(LeaveEncashment.employee_id == employee_id)
    total = (await db.execute(base)).scalar() or 0
    items = (await db.execute(q.order_by(LeaveEncashment.created_at.desc()).offset(skip).limit(limit))).scalars().all()
    return list(items), total


async def get_encashment(db: AsyncSession, encashment_id: UUID) -> LeaveEncashment:
    cid = _cid(db)
    obj = (await db.execute(
        select(LeaveEncashment).where(
            LeaveEncashment.id == encashment_id, LeaveEncashment.company_id == cid
        )
    )).scalars().first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave encashment not found")
    return obj


async def create_encashment(db: AsyncSession, data: LeaveEncashmentCreate) -> LeaveEncashment:
    cid = _cid(db)

    # Resolve current allocation balance if allocation_id provided
    leave_balance = 0.0
    encashable_days = 0.0
    if data.leave_allocation_id:
        alloc = (await db.execute(
            select(LeaveAllocation).where(
                LeaveAllocation.id == data.leave_allocation_id,
                LeaveAllocation.company_id == cid,
            )
        )).scalars().first()
        if alloc:
            leave_balance = alloc.total_leaves_allocated - alloc.used_leaves
            encashable_days = max(0.0, leave_balance)

    obj = LeaveEncashment(
        company_id=cid,
        employee_id=data.employee_id,
        leave_type_id=data.leave_type_id,
        leave_period_id=data.leave_period_id,
        leave_allocation_id=data.leave_allocation_id,
        leave_balance=leave_balance,
        encashable_days=encashable_days,
        encashment_amount=data.encashment_amount,
        encashment_date=data.encashment_date,
    )
    db.add(obj)
    await db.flush()

    # Write ledger: encashment is a debit from the balance
    if encashable_days > 0:
        db.add(LeaveLedgerEntry(
            company_id=cid,
            employee_id=data.employee_id,
            leave_type_id=data.leave_type_id,
            from_date=data.encashment_date or date.today(),
            to_date=data.encashment_date or date.today(),
            leaves=-encashable_days,
            transaction_type="encashment",
            transaction_name=str(obj.id),
        ))

    await db.commit()
    await db.refresh(obj)
    return obj


async def cancel_encashment(db: AsyncSession, encashment_id: UUID) -> LeaveEncashment:
    obj = await get_encashment(db, encashment_id)
    if obj.status == "paid":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot cancel an already paid encashment",
        )
    obj.status = "cancelled"
    await db.commit()
    await db.refresh(obj)
    return obj
