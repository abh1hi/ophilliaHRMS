"""Leave Service — Business Logic Layer.

Enterprise additions:
- SELECT ... FOR UPDATE on balance rows to prevent concurrent corruption
- Overlapping leave detection enforced at service level
- Holiday-aware day calculation
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from fastapi import HTTPException, status
from uuid import UUID
from datetime import date
import logging

from app.models.leave import LeaveType, LeaveBalance, LeaveRequest
from app.schemas.leave import LeaveTypeCreate, LeaveBalanceCreate, LeaveRequestCreate, LeaveRequestUpdate
from app.events.publishers import publish_event
from app.core.constants import LeaveStatus
from app.utils.holiday_cache import get_holidays_cached, count_business_days

logger = logging.getLogger(__name__)


async def get_leave_type(db: AsyncSession, leave_type_id: UUID):
    result = await db.execute(select(LeaveType).filter(LeaveType.id == leave_type_id))
    return result.scalars().first()


async def create_leave_type(db: AsyncSession, obj_in: LeaveTypeCreate):
    db_obj = LeaveType(**obj_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def get_leave_balance(db: AsyncSession, employee_id: UUID, leave_type_id: UUID, year: int):
    result = await db.execute(
        select(LeaveBalance).filter(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.leave_type_id == leave_type_id,
            LeaveBalance.year == year,
        )
    )
    return result.scalars().first()


async def get_leave_balance_for_update(db: AsyncSession, employee_id: UUID, leave_type_id: UUID, year: int):
    """Acquire row-level lock (SELECT ... FOR UPDATE) to prevent concurrent balance corruption."""
    result = await db.execute(
        select(LeaveBalance)
        .filter(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.leave_type_id == leave_type_id,
            LeaveBalance.year == year,
        )
        .with_for_update()
    )
    return result.scalars().first()


async def create_leave_balance(db: AsyncSession, obj_in: LeaveBalanceCreate):
    db_obj = LeaveBalance(**obj_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def _check_overlapping_leaves(db: AsyncSession, employee_id: UUID, start_date: date, end_date: date):
    """Prevent overlapping leaves: check for PENDING or APPROVED requests that overlap."""
    result = await db.execute(
        select(LeaveRequest).filter(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.status.in_([LeaveStatus.PENDING.value, LeaveStatus.APPROVED.value]),
            start_date <= LeaveRequest.end_date,
            end_date >= LeaveRequest.start_date,
        )
    )
    return result.scalars().first()


async def apply_leave(db: AsyncSession, obj_in: LeaveRequestCreate):
    # Date range validation
    if obj_in.end_date < obj_in.start_date:
        raise HTTPException(status_code=400, detail="Invalid date range")

    # Overlapping leave check
    overlap = await _check_overlapping_leaves(db, obj_in.employee_id, obj_in.start_date, obj_in.end_date)
    if overlap:
        raise HTTPException(status_code=400, detail="Leave request dates overlap with an existing request")

    # Get Leave Type
    leave_type = await get_leave_type(db, obj_in.leave_type_id)
    if not leave_type:
        raise HTTPException(status_code=404, detail="Leave type not found")

    # Calculate business days (holiday-aware)
    holidays = await get_holidays_cached(db)
    days = count_business_days(obj_in.start_date, obj_in.end_date, holidays)
    if days <= 0:
        raise HTTPException(status_code=400, detail="No business days in the selected range")

    year = obj_in.start_date.year

    # CONCURRENCY LOCK: SELECT ... FOR UPDATE on balance row
    balance = await get_leave_balance_for_update(db, obj_in.employee_id, obj_in.leave_type_id, year)
    if not balance:
        raise HTTPException(status_code=400, detail="No leave balance found for this year")

    if balance.total_days - balance.used_days - balance.pending_days < days:
        raise HTTPException(status_code=400, detail="Insufficient leave balance")

    # Create Request
    db_obj = LeaveRequest(**obj_in.model_dump(), total_days=days)

    if leave_type.requires_approval:
        db_obj.status = LeaveStatus.PENDING.value
        balance.pending_days += days
    else:
        db_obj.status = LeaveStatus.APPROVED.value
        balance.used_days += days

    db.add(db_obj)
    db.add(balance)
    await db.commit()
    await db.refresh(db_obj)

    # Publish Event
    company_id = db.info.get("company_id")
    event_payload = {
        "company_id": str(company_id) if company_id else None,
        "leave_request_id": str(db_obj.id),
        "employee_id": str(db_obj.employee_id),
        "start_date": db_obj.start_date.isoformat(),
        "end_date": db_obj.end_date.isoformat(),
        "status": db_obj.status,
    }
    await publish_event("leave.requested", event_payload)
    return db_obj


async def update_leave_status(db: AsyncSession, request_id: UUID, obj_in: LeaveRequestUpdate, manager_id: UUID):
    result = await db.execute(select(LeaveRequest).filter(LeaveRequest.id == request_id))
    leave_req = result.scalars().first()

    if not leave_req:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if leave_req.status != LeaveStatus.PENDING.value:
        raise HTTPException(status_code=400, detail="Only pending requests can be updated")

    # CONCURRENCY LOCK on balance
    balance = await get_leave_balance_for_update(
        db, leave_req.employee_id, leave_req.leave_type_id, leave_req.start_date.year
    )
    if not balance:
        raise HTTPException(status_code=500, detail="Balance tracking error")

    leave_req.status = obj_in.status.value
    leave_req.manager_notes = obj_in.manager_notes
    leave_req.approved_by_id = manager_id
    db.add(leave_req)

    company_id = db.info.get("company_id")
    event_payload = {
        "company_id": str(company_id) if company_id else None,
        "leave_request_id": str(leave_req.id),
        "employee_id": str(leave_req.employee_id),
        "status": obj_in.status.value,
    }

    event_name = ""
    if obj_in.status == LeaveStatus.APPROVED:
        balance.pending_days -= leave_req.total_days
        balance.used_days += leave_req.total_days
        db.add(balance)
        event_name = "leave.approved"
    elif obj_in.status in [LeaveStatus.REJECTED, LeaveStatus.CANCELLED]:
        balance.pending_days -= leave_req.total_days
        db.add(balance)
        event_name = "leave.rejected" if obj_in.status == LeaveStatus.REJECTED else "leave.cancelled"

    await db.commit()
    await db.refresh(leave_req)

    if event_name:
        await publish_event(event_name, event_payload)

    return leave_req
