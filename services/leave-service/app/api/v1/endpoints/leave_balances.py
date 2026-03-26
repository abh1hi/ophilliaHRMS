from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID
from datetime import datetime

from app.api.v1.dependencies import (
    get_current_user,
    require_role,
    TokenPayload,
    get_db_with_tenant
)
from app.core.constants import UserRole
from app.services import leave_service
from app.schemas.leave import (
    LeaveBalanceCreate,
    LeaveBalanceUpdate,
    LeaveBalanceResponse,
    BulkLeaveBalanceRequest,
    BulkLeaveBalanceResponse,
    BulkLeaveBalanceResult,
)
from app.schemas.response import APIResponse
from app.models.leave import LeaveBalance, LeaveType

router = APIRouter()

@router.get("/", response_model=APIResponse[List[LeaveBalanceResponse]])
async def list_all_leave_balances(
    year: int = datetime.utcnow().year,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: TokenPayload = Depends(require_role(UserRole.HR, UserRole.ADMIN, UserRole.SUPER_ADMIN))
):
    """List all leave balances for the company (admin/HR only)."""
    company_id = db.info.get("company_id")
    result = await db.execute(
        select(LeaveBalance)
        .options(selectinload(LeaveBalance.leave_type))
        .filter(
            LeaveBalance.company_id == company_id,
            LeaveBalance.year == year,
        )
    )
    return APIResponse(success=True, data=result.scalars().all())

@router.get("/{employee_id}", response_model=APIResponse[List[LeaveBalanceResponse]])
async def get_leave_balances(
    employee_id: UUID,
    year: int = datetime.utcnow().year,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: TokenPayload = Depends(get_current_user)
):
    if current_user.role == UserRole.EMPLOYEE.value and str(employee_id) != current_user.sub:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    company_id = db.info.get("company_id")
    result = await db.execute(
        select(LeaveBalance)
        .options(selectinload(LeaveBalance.leave_type))
        .filter(
            LeaveBalance.company_id == company_id,
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.year == year,
        )
    )
    return APIResponse(success=True, data=result.scalars().all())

@router.post("/", response_model=APIResponse[LeaveBalanceResponse], status_code=status.HTTP_201_CREATED)
async def create_leave_balance(
    *,
    db: AsyncSession = Depends(get_db_with_tenant),
    balance_in: LeaveBalanceCreate,
    current_user: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN))
):
    db_obj = await leave_service.create_leave_balance(db, obj_in=balance_in)
    
    # Reload with leave_type
    result = await db.execute(
        select(LeaveBalance)
        .options(selectinload(LeaveBalance.leave_type))
        .filter(LeaveBalance.id == db_obj.id)
    )
    return APIResponse(success=True, data=result.scalars().first())

@router.patch("/{balance_id}", response_model=APIResponse[LeaveBalanceResponse])
async def update_leave_balance(
    *,
    db: AsyncSession = Depends(get_db_with_tenant),
    balance_id: UUID,
    balance_in: LeaveBalanceUpdate,
    current_user: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN))
):
    company_id = db.info.get("company_id")
    result = await db.execute(
        select(LeaveBalance).filter(LeaveBalance.id == balance_id, LeaveBalance.company_id == company_id)
    )
    db_obj = result.scalars().first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Leave balance not found")

    update_data = balance_in.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    for field, value in update_data.items():
        setattr(db_obj, field, value)

    await db.commit()

    # Reload with leave_type
    result = await db.execute(
        select(LeaveBalance)
        .options(selectinload(LeaveBalance.leave_type))
        .filter(LeaveBalance.id == db_obj.id)
    )
    return APIResponse(success=True, data=result.scalars().first())


@router.post("/bulk", response_model=BulkLeaveBalanceResponse)
async def bulk_create_leave_balances(
    *,
    db: AsyncSession = Depends(get_db_with_tenant),
    data: BulkLeaveBalanceRequest,
    current_user: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN))
):
    """Allocate leave balances for multiple employees at once.
    Skips rows where a balance already exists for that employee+type+year.
    """
    company_id = db.info.get("company_id")

    # Verify leave type exists and belongs to tenant
    lt_result = await db.execute(
        select(LeaveType).filter(LeaveType.id == data.leave_type_id, LeaveType.company_id == company_id)
    )
    if not lt_result.scalars().first():
        raise HTTPException(status_code=404, detail="Leave type not found")

    results: List[BulkLeaveBalanceResult] = []
    for idx, item in enumerate(data.items):
        try:
            existing = await db.execute(
                select(LeaveBalance).filter(
                    LeaveBalance.company_id == company_id,
                    LeaveBalance.employee_id == item.employee_id,
                    LeaveBalance.leave_type_id == data.leave_type_id,
                    LeaveBalance.year == data.year,
                )
            )
            if existing.scalars().first():
                results.append(BulkLeaveBalanceResult(
                    index=idx, employee_id=item.employee_id, success=False,
                    error="Balance already exists for this employee/type/year"
                ))
                continue

            obj = LeaveBalance(
                company_id=company_id,
                employee_id=item.employee_id,
                leave_type_id=data.leave_type_id,
                total_days=item.total_days,
                year=data.year,
            )
            db.add(obj)
            await db.flush()
            results.append(BulkLeaveBalanceResult(
                index=idx, employee_id=item.employee_id, success=True
            ))
        except Exception as e:
            results.append(BulkLeaveBalanceResult(
                index=idx, employee_id=item.employee_id, success=False, error=str(e)
            ))

    await db.commit()
    succeeded = sum(1 for r in results if r.success)
    return BulkLeaveBalanceResponse(
        total=len(results), succeeded=succeeded, failed=len(results) - succeeded, results=results,
    )
