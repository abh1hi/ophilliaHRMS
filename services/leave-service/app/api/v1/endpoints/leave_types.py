from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.api.v1.dependencies import (
    get_current_user,
    require_role,
    TokenPayload,
    get_db_with_tenant
)
from app.core.constants import UserRole

router = APIRouter()

@router.get("/", response_model=List[LeaveTypeResponse])
async def list_leave_types(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: TokenPayload = Depends(get_current_user)
):
    result = await db.execute(select(LeaveType).filter(LeaveType.is_active == 1))
    return result.scalars().all()

@router.post("/", response_model=LeaveTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_leave_type(
    *,
    db: AsyncSession = Depends(get_db_with_tenant),
    leave_type_in: LeaveTypeCreate,
    current_user: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN))
):
    # Check if exists
    result = await db.execute(select(LeaveType).filter(LeaveType.name == leave_type_in.name))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Leave type with this name already exists")
    
    db_obj = LeaveType(**leave_type_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj
