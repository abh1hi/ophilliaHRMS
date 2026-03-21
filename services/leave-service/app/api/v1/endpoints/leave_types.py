from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from uuid import UUID

from app.api.v1.dependencies import (
    get_current_user,
    require_role,
    TokenPayload,
    get_db_with_tenant
)
from app.core.constants import UserRole
from app.schemas.leave import LeaveTypeCreate, LeaveTypeUpdate, LeaveTypeResponse
from app.schemas.response import APIResponse
from app.models.leave import LeaveType

router = APIRouter()

@router.get("/", response_model=APIResponse[List[LeaveTypeResponse]])
async def list_leave_types(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: TokenPayload = Depends(get_current_user)
):
    company_id = db.info.get("company_id")
    query = select(LeaveType).filter(LeaveType.company_id == company_id)
    if not include_inactive:
        query = query.filter(LeaveType.is_active == 1)
    result = await db.execute(query)
    return APIResponse(success=True, data=result.scalars().all())

@router.post("/", response_model=APIResponse[LeaveTypeResponse], status_code=status.HTTP_201_CREATED)
async def create_leave_type(
    *,
    db: AsyncSession = Depends(get_db_with_tenant),
    leave_type_in: LeaveTypeCreate,
    current_user: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN))
):
    # Check if exists within tenant
    company_id = db.info.get("company_id")
    result = await db.execute(
        select(LeaveType).filter(LeaveType.name == leave_type_in.name, LeaveType.company_id == company_id)
    )
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Leave type with this name already exists")

    db_obj = LeaveType(**leave_type_in.model_dump(), company_id=company_id)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return APIResponse(success=True, data=db_obj)

@router.patch("/{leave_type_id}", response_model=APIResponse[LeaveTypeResponse])
async def update_leave_type(
    *,
    db: AsyncSession = Depends(get_db_with_tenant),
    leave_type_id: UUID,
    leave_type_in: LeaveTypeUpdate,
    current_user: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN))
):
    company_id = db.info.get("company_id")
    result = await db.execute(
        select(LeaveType).filter(LeaveType.id == leave_type_id, LeaveType.company_id == company_id)
    )
    db_obj = result.scalars().first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Leave type not found")

    update_data = leave_type_in.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    # If renaming, check for duplicate name within tenant
    if "name" in update_data and update_data["name"] != db_obj.name:
        dup_result = await db.execute(
            select(LeaveType).filter(
                LeaveType.name == update_data["name"],
                LeaveType.company_id == company_id,
                LeaveType.id != leave_type_id,
            )
        )
        if dup_result.scalars().first():
            raise HTTPException(status_code=400, detail="Leave type with this name already exists")

    for field, value in update_data.items():
        setattr(db_obj, field, value)

    await db.commit()
    await db.refresh(db_obj)
    return APIResponse(success=True, data=db_obj)

@router.delete("/{leave_type_id}", response_model=APIResponse[LeaveTypeResponse])
async def delete_leave_type(
    *,
    db: AsyncSession = Depends(get_db_with_tenant),
    leave_type_id: UUID,
    current_user: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN))
):
    company_id = db.info.get("company_id")
    result = await db.execute(
        select(LeaveType).filter(LeaveType.id == leave_type_id, LeaveType.company_id == company_id)
    )
    db_obj = result.scalars().first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Leave type not found")

    db_obj.is_active = 0
    await db.commit()
    await db.refresh(db_obj)
    return APIResponse(success=True, data=db_obj)
