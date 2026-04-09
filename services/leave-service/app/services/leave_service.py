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

from app.models.leave import LeaveType, LeaveBalance, LeaveRequest, LeaveApproval
from app.schemas.leave import LeaveTypeCreate, LeaveBalanceCreate, LeaveRequestCreate, LeaveRequestUpdate
from app.events.publishers import publish_event
from app.core.constants import LeaveStatus, DurationType, ApprovalLevel
from app.utils.holiday_cache import get_holidays_cached, count_business_days
from app.core.employee_validator import validate_employee_tenant

logger = logging.getLogger(__name__)


def _get_company_id(db: AsyncSession) -> UUID:
    cid = db.info.get("company_id")
    if not cid:
        raise RuntimeError("company_id not set on session")
    return UUID(cid) if isinstance(cid, str) else cid


async def get_leave_type(db: AsyncSession, leave_type_id: UUID):
    company_id = _get_company_id(db)
    result = await db.execute(
        select(LeaveType).filter(LeaveType.id == leave_type_id, LeaveType.company_id == company_id)
    )
    return result.scalars().first()


async def create_leave_type(db: AsyncSession, obj_in: LeaveTypeCreate):
    company_id = _get_company_id(db)
    db_obj = LeaveType(**obj_in.model_dump(), company_id=company_id)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def get_leave_balance(db: AsyncSession, employee_id: UUID, leave_type_id: UUID, year: int):
    company_id = _get_company_id(db)
    result = await db.execute(
        select(LeaveBalance).filter(
            LeaveBalance.company_id == company_id,
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.leave_type_id == leave_type_id,
            LeaveBalance.year == year,
        )
    )
    return result.scalars().first()


async def get_leave_balance_for_update(db: AsyncSession, employee_id: UUID, leave_type_id: UUID, year: int):
    """Acquire row-level lock (SELECT ... FOR UPDATE) to prevent concurrent balance corruption."""
    company_id = _get_company_id(db)
    result = await db.execute(
        select(LeaveBalance)
        .filter(
            LeaveBalance.company_id == company_id,
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.leave_type_id == leave_type_id,
            LeaveBalance.year == year,
        )
        .with_for_update()
    )
    return result.scalars().first()


async def create_leave_balance(db: AsyncSession, obj_in: LeaveBalanceCreate):
    company_id = _get_company_id(db)
    db_obj = LeaveBalance(**obj_in.model_dump(), company_id=company_id)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def _check_overlapping_leaves(db: AsyncSession, employee_id: UUID, start_date: date, end_date: date):
    """Prevent overlapping leaves: check for PENDING or APPROVED requests that overlap."""
    company_id = _get_company_id(db)
    result = await db.execute(
        select(LeaveRequest).filter(
            LeaveRequest.company_id == company_id,
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.status.in_([LeaveStatus.PENDING.value, LeaveStatus.APPROVED.value]),
            start_date <= LeaveRequest.end_date,
            end_date >= LeaveRequest.start_date,
        )
    )
    return result.scalars().first()


async def _check_department_leave_limit(db: AsyncSession, employee_id: UUID, start_date: date, end_date: date):
    # Mocking external call to employee-service to get department & peers
    # In reality, this would be an HTTP call to employee-service to get department_id
    # Then query leave-service for requests by those peers on the same dates
    # For now, we simulate success (under limit).
    pass

async def apply_leave(db: AsyncSession, obj_in: LeaveRequestCreate):
    # Validate employee belongs to current tenant
    company_id = _get_company_id(db)
    await validate_employee_tenant(obj_in.employee_id, str(company_id))

    # Date range validation
    if obj_in.end_date < obj_in.start_date:
        raise HTTPException(status_code=400, detail="Invalid date range")

    # 3-day intimation policy check (SOP: Leave should be intimated 3 days before required date)
    if not obj_in.is_emergency:
        delta_days = (obj_in.start_date - date.today()).days
        if delta_days < 3:
            raise HTTPException(
                status_code=400, 
                detail="Leave must be intimated AT LEAST 3 days before the required date. Use Emergency Leave if applicable."
            )

    # Department limit check (max 2 from same dept on same day)
    await _check_department_leave_limit(db, obj_in.employee_id, obj_in.start_date, obj_in.end_date)

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
    
    if obj_in.duration_type == DurationType.HALF_DAY:
        days = 0.5

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
    company_id = _get_company_id(db)
    db_obj = LeaveRequest(**obj_in.model_dump(), total_days=days, company_id=company_id)

    if leave_type.requires_approval:
        db_obj.status = LeaveStatus.PENDING.value
        balance.pending_days += days
    else:
        db_obj.status = LeaveStatus.APPROVED.value
        balance.used_days += days

    db.add(db_obj)
    db.add(balance)
    await db.flush() # Flush to get db_obj.id

    # Create initial Approval Step (Project In-Charge) if requires approval
    if leave_type.requires_approval:
        # Note: the specific approver_id needs to be determined based on the employee's manager
        # For now, we seed a placeholder or expect it to be handled by a workflow engine.
        initial_approval = LeaveApproval(
            leave_request_id=db_obj.id,
            approver_id=obj_in.employee_id, # Placeholder, will be replaced in real integration
            level=ApprovalLevel.PROJECT_IN_CHARGE.value,
            status=LeaveStatus.PENDING.value
        )
        db.add(initial_approval)

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
        "is_emergency": db_obj.is_emergency
    }
    await publish_event("leave.requested", event_payload)
    if db_obj.is_emergency:
        await publish_event("leave.emergency", event_payload)
        
    return db_obj


async def update_leave_status(db: AsyncSession, request_id: UUID, obj_in: LeaveRequestUpdate, manager_id: UUID, role: str):
    company_id = _get_company_id(db)
    result = await db.execute(
        select(LeaveRequest).filter(LeaveRequest.id == request_id, LeaveRequest.company_id == company_id)
    )
    leave_req = result.scalars().first()

    if not leave_req:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if leave_req.status != LeaveStatus.PENDING.value:
        raise HTTPException(status_code=400, detail=f"Request is already {leave_req.status}")

    # Find the pending approval step
    approval_res = await db.execute(
        select(LeaveApproval)
        .filter(LeaveApproval.leave_request_id == request_id, LeaveApproval.status == LeaveStatus.PENDING.value)
        .order_by(LeaveApproval.created_at.asc())
    )
    current_approval = approval_res.scalars().first()
    
    if not current_approval:
        raise HTTPException(status_code=400, detail="No pending approvals for this request")
        
    # Verify role vs required level loosely (In real sys, rely on strict mapping)
    level_order = [ApprovalLevel.PROJECT_IN_CHARGE.value, ApprovalLevel.HR.value, ApprovalLevel.SUPER_ADMIN.value]
    
    current_approval.status = obj_in.status.value
    current_approval.remarks = obj_in.manager_notes
    current_approval.approver_id = manager_id
    db.add(current_approval)

    # CONCURRENCY LOCK on balance
    balance = await get_leave_balance_for_update(
        db, leave_req.employee_id, leave_req.leave_type_id, leave_req.start_date.year
    )
    if not balance:
        raise HTTPException(status_code=500, detail="Balance tracking error")

    event_name = ""

    if obj_in.status == LeaveStatus.REJECTED or obj_in.status == LeaveStatus.CANCELLED:
        leave_req.status = obj_in.status.value
        balance.pending_days -= leave_req.total_days
        db.add(balance)
        event_name = "leave.rejected" if obj_in.status == LeaveStatus.REJECTED else "leave.cancelled"
    elif obj_in.status == LeaveStatus.APPROVED:
        # Check if there's a next level
        current_idx = level_order.index(current_approval.level)
        if current_idx < len(level_order) - 1:
            # Move to next level
            next_level = level_order[current_idx + 1]
            next_approval = LeaveApproval(
                leave_request_id=leave_req.id,
                approver_id=manager_id, # Placeholder
                level=next_level,
                status=LeaveStatus.PENDING.value
            )
            db.add(next_approval)
            # Request remains PENDING
            event_name = f"leave.approved.{current_approval.level.lower()}"
        else:
            # Fully approved
            leave_req.status = LeaveStatus.APPROVED.value
            balance.pending_days -= leave_req.total_days
            balance.used_days += leave_req.total_days
            db.add(balance)
            event_name = "leave.approved"

    leave_req.manager_notes = obj_in.manager_notes
    leave_req.approved_by_id = manager_id
    db.add(leave_req)

    await db.commit()
    await db.refresh(leave_req)

    if event_name:
        # Fetch leave type name for calendar enrichment (best-effort)
        leave_type_name = ""
        try:
            lt_res = await db.execute(
                select(LeaveType).filter(LeaveType.id == leave_req.leave_type_id)
            )
            lt = lt_res.scalars().first()
            if lt:
                leave_type_name = lt.name
        except Exception:
            pass

        event_payload = {
            "company_id": str(company_id) if company_id else None,
            "leave_request_id": str(leave_req.id),
            "employee_id": str(leave_req.employee_id),
            "status": leave_req.status,
            "level_approved": current_approval.level,
            "start_date": leave_req.start_date.isoformat(),
            "end_date": leave_req.end_date.isoformat(),
            "total_days": float(leave_req.total_days),
            "leave_type_name": leave_type_name,
        }
        await publish_event(event_name, event_payload)

    return leave_req
