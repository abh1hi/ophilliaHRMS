from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.models.leave import LeaveBalance
from app.schemas.leave import LeaveBalanceResponse, LeaveBalanceCreate
from app.api.v1.dependencies import get_current_user, require_role, TokenPayload
from app.core.constants import UserRole
from app.services import leave_service

router = APIRouter()

@router.get("/{employee_id}", response_model=List[LeaveBalanceResponse])
async def get_leave_balances(
    employee_id: UUID,
    year: int = datetime.utcnow().year,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user)
):
    if current_user.role == UserRole.EMPLOYEE.value and str(employee_id) != current_user.sub:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    result = await db.execute(
        select(LeaveBalance)
        .options(selectinload(LeaveBalance.leave_type))
        .filter(LeaveBalance.employee_id == employee_id, LeaveBalance.year == year)
    )
    return result.scalars().all()

@router.post("/", response_model=LeaveBalanceResponse, status_code=status.HTTP_201_CREATED)
async def create_leave_balance(
    *,
    db: AsyncSession = Depends(get_db),
    balance_in: LeaveBalanceCreate,
    current_user: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN))
):
    db_obj = await leave_service.create_leave_balance(db, obj_in=balance_in)
    
    # Reload with leave_type
    result = await db.execute(
        select(LeaveBalance)
        .options(selectinload(LeaveBalance.leave_type))
        .filter(LeaveBalance.id == db_obj.id)
    )
    return result.scalars().first()
