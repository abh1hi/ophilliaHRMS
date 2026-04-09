"""Leave Policy service — manage policies and auto-create allocations on assignment."""
from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.leave_policy import LeavePolicy, LeavePolicyItem
from app.models.leave_policy_assignment import LeavePolicyAssignment
from app.models.leave_allocation import LeaveAllocation
from app.schemas.leave_policy import (
    LeavePolicyCreate, LeavePolicyUpdate,
    LeavePolicyAssignmentCreate,
)


def _cid(db: AsyncSession) -> UUID:
    cid = db.info.get("company_id")
    return UUID(cid) if isinstance(cid, str) else cid


# ── Leave Policy CRUD ─────────────────────────────────────────────────────────

async def list_policies(db: AsyncSession, include_inactive: bool = False) -> List[LeavePolicy]:
    cid = _cid(db)
    q = select(LeavePolicy).where(LeavePolicy.company_id == cid)
    if not include_inactive:
        q = q.where(LeavePolicy.is_active == 1)
    return list((await db.execute(q.order_by(LeavePolicy.name))).scalars().all())


async def get_policy(db: AsyncSession, policy_id: UUID) -> LeavePolicy:
    cid = _cid(db)
    obj = (await db.execute(
        select(LeavePolicy).where(LeavePolicy.id == policy_id, LeavePolicy.company_id == cid)
    )).scalars().first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave policy not found")
    return obj


async def create_policy(db: AsyncSession, data: LeavePolicyCreate) -> LeavePolicy:
    cid = _cid(db)
    obj = LeavePolicy(name=data.name, description=data.description, company_id=cid)
    for item in data.items:
        obj.items.append(LeavePolicyItem(**item.model_dump()))
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def update_policy(db: AsyncSession, policy_id: UUID, data: LeavePolicyUpdate) -> LeavePolicy:
    obj = await get_policy(db, policy_id)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


async def delete_policy(db: AsyncSession, policy_id: UUID) -> LeavePolicy:
    obj = await get_policy(db, policy_id)
    obj.is_active = 0
    await db.commit()
    await db.refresh(obj)
    return obj


# ── Leave Policy Assignment ────────────────────────────────────────────────────

async def list_assignments(
    db: AsyncSession,
    employee_id: Optional[UUID] = None,
) -> List[LeavePolicyAssignment]:
    cid = _cid(db)
    q = select(LeavePolicyAssignment).where(LeavePolicyAssignment.company_id == cid)
    if employee_id:
        q = q.where(LeavePolicyAssignment.employee_id == employee_id)
    return list((await db.execute(q.order_by(LeavePolicyAssignment.effective_from.desc()))).scalars().all())


async def create_assignment(
    db: AsyncSession, data: LeavePolicyAssignmentCreate
) -> LeavePolicyAssignment:
    cid = _cid(db)
    policy = await get_policy(db, data.policy_id)

    assignment = LeavePolicyAssignment(
        **data.model_dump(),
        company_id=cid,
    )
    db.add(assignment)
    await db.flush()  # get assignment.id before creating allocations

    # Auto-create LeaveAllocation for each policy item (idempotent — skip if exists)
    for item in policy.items:
        alloc = LeaveAllocation(
            company_id=cid,
            employee_id=data.employee_id,
            leave_type_id=item.leave_type_id,
            assignment_id=assignment.id,
            leave_period_id=data.leave_period_id,
            from_date=data.effective_from,
            to_date=data.effective_to or date(data.effective_from.year, 12, 31),
            new_leaves_allocated=item.annual_allocation,
            carry_forward_days=0,
            total_leaves_allocated=item.annual_allocation,
        )
        db.add(alloc)

    await db.commit()
    await db.refresh(assignment)
    return assignment


async def cancel_assignment(
    db: AsyncSession, assignment_id: UUID
) -> LeavePolicyAssignment:
    cid = _cid(db)
    obj = (await db.execute(
        select(LeavePolicyAssignment).where(
            LeavePolicyAssignment.id == assignment_id,
            LeavePolicyAssignment.company_id == cid,
        )
    )).scalars().first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    obj.status = "cancelled"
    await db.commit()
    await db.refresh(obj)
    return obj
