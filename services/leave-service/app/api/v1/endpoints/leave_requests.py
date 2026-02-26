from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.models.leave import LeaveRequest
from app.schemas.leave import LeaveRequestCreate, LeaveRequestResponse, LeaveRequestUpdate
from app.api.v1.dependencies import get_current_user, require_role, TokenPayload
from app.core.constants import UserRole
from app.services import leave_service

router = APIRouter()

@router.post("/", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
async def apply_for_leave(
    *,
    db: AsyncSession = Depends(get_db),
    request_in: LeaveRequestCreate,
    current_user: TokenPayload = Depends(get_current_user)
):
    if current_user.role == UserRole.EMPLOYEE.value and str(request_in.employee_id) != current_user.sub:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db_obj = await leave_service.apply_leave(db, obj_in=request_in)
    
    result = await db.execute(
        select(LeaveRequest)
        .options(selectinload(LeaveRequest.leave_type))
        .filter(LeaveRequest.id == db_obj.id)
    )
    return result.scalars().first()

@router.get("/", response_model=List[LeaveRequestResponse])
async def list_leave_requests(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user)
):
    query = select(LeaveRequest).options(selectinload(LeaveRequest.leave_type))
    
    if current_user.role == UserRole.EMPLOYEE.value:
        query = query.filter(LeaveRequest.employee_id == UUID(current_user.sub))
        
    result = await db.execute(query)
    return result.scalars().all()

@router.put("/{request_id}/status", response_model=LeaveRequestResponse)
async def update_leave_status(
    *,
    db: AsyncSession = Depends(get_db),
    request_id: UUID,
    status_in: LeaveRequestUpdate,
    current_user: TokenPayload = Depends(require_role(UserRole.HR, UserRole.MANAGER, UserRole.SUPER_ADMIN))
):
    db_obj = await leave_service.update_leave_status(db, request_id=request_id, obj_in=status_in, manager_id=UUID(current_user.sub))
    
    result = await db.execute(
        select(LeaveRequest)
        .options(selectinload(LeaveRequest.leave_type))
        .filter(LeaveRequest.id == db_obj.id)
    )
    return result.scalars().first()
