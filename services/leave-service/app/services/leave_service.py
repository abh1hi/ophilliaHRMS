from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from uuid import UUID
from datetime import date

from app.models.leave import LeaveType, LeaveBalance, LeaveRequest
from app.schemas.leave import LeaveTypeCreate, LeaveBalanceCreate, LeaveRequestCreate, LeaveRequestUpdate
from app.events.publishers import publish_event
from app.core.constants import LeaveStatus

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
            LeaveBalance.year == year
        )
    )
    return result.scalars().first()

async def create_leave_balance(db: AsyncSession, obj_in: LeaveBalanceCreate):
    db_obj = LeaveBalance(**obj_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def apply_leave(db: AsyncSession, obj_in: LeaveRequestCreate):
    # Calculate days (dummy calculation for now, later integrate holiday calendar)
    days = (obj_in.end_date - obj_in.start_date).days + 1
    if days <= 0:
        raise HTTPException(status_code=400, detail="Invalid date range")

    # Overlapping date validation
    result = await db.execute(
        select(LeaveRequest).filter(
            LeaveRequest.employee_id == obj_in.employee_id,
            LeaveRequest.status.in_([LeaveStatus.PENDING.value, LeaveStatus.APPROVED.value]),
            # Overlap condition:
            # (NewStart <= ExistingEnd) AND (NewEnd >= ExistingStart)
            obj_in.start_date <= LeaveRequest.end_date,
            obj_in.end_date >= LeaveRequest.start_date
        )
    )
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Leave request dates overlap with an existing request")

    # Get Leave Type
    leave_type = await get_leave_type(db, obj_in.leave_type_id)
    if not leave_type:
        raise HTTPException(status_code=404, detail="Leave type not found")

    year = obj_in.start_date.year

    # Check Balance
    balance = await get_leave_balance(db, obj_in.employee_id, obj_in.leave_type_id, year)
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
    event_payload = {
        "leave_request_id": str(db_obj.id),
        "employee_id": str(db_obj.employee_id),
        "start_date": str(db_obj.start_date),
        "end_date": str(db_obj.end_date),
        "status": db_obj.status
    }
    await publish_event("leave.requested", event_payload)

    if db_obj.status == LeaveStatus.APPROVED.value:
        await publish_event("leave.approved", event_payload)

    return db_obj

async def update_leave_status(db: AsyncSession, request_id: UUID, obj_in: LeaveRequestUpdate, manager_id: UUID):
    result = await db.execute(select(LeaveRequest).filter(LeaveRequest.id == request_id))
    leave_req = result.scalars().first()
    
    if not leave_req:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if leave_req.status != LeaveStatus.PENDING.value:
        raise HTTPException(status_code=400, detail="Only pending requests can be updated")

    # Get Balance
    balance = await get_leave_balance(db, leave_req.employee_id, leave_req.leave_type_id, leave_req.start_date.year)
    if not balance:
        raise HTTPException(status_code=500, detail="Balance tracking error")

    leave_req.status = obj_in.status.value
    leave_req.manager_notes = obj_in.manager_notes
    leave_req.approved_by_id = manager_id

    if obj_in.status == LeaveStatus.APPROVED:
        balance.pending_days -= leave_req.total_days
        balance.used_days += leave_req.total_days
        await publish_event("leave.approved", {"leave_request_id": str(leave_req.id), "status": "APPROVED"})
    elif obj_in.status in [LeaveStatus.REJECTED, LeaveStatus.CANCELLED]:
        balance.pending_days -= leave_req.total_days
        event_name = "leave.rejected" if obj_in.status == LeaveStatus.REJECTED else "leave.cancelled"
        await publish_event(event_name, {"leave_request_id": str(leave_req.id), "status": obj_in.status.value})

    db.add(leave_req)
    db.add(balance)
    await db.commit()
    await db.refresh(leave_req)
    
    return leave_req
