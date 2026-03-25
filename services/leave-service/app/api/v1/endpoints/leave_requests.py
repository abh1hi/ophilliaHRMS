from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID

from app.models.leave import LeaveRequest
from app.schemas.leave import LeaveRequestCreate, LeaveRequestResponse, LeaveRequestUpdate
from app.schemas.response import APIResponse, PaginatedAPIResponse, PaginatedMeta
from app.api.v1.dependencies import (
    get_current_user,
    require_role,
    TokenPayload,
    get_db_with_tenant
)
from app.core.constants import UserRole
from app.services import leave_service
from app.core.rate_limit import limiter

router = APIRouter()

@router.post("/", response_model=APIResponse[LeaveRequestResponse], status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def apply_for_leave(
    request: Request,
    *,
    db: AsyncSession = Depends(get_db_with_tenant),
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
    return APIResponse(success=True, data=result.scalars().first())

@router.get("/", response_model=PaginatedAPIResponse[LeaveRequestResponse])
async def list_leave_requests(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: TokenPayload = Depends(get_current_user),
    page: int = 1,
    page_size: int = 20
):
    company_id = db.info.get("company_id")
    query = select(LeaveRequest).options(selectinload(LeaveRequest.leave_type)).filter(
        LeaveRequest.company_id == company_id
    )

    if current_user.role == UserRole.EMPLOYEE.value:
        query = query.filter(LeaveRequest.employee_id == UUID(current_user.sub))

    # Standard DB Pagination (Simple)
    query = query.offset((page - 1) * page_size).limit(page_size)

    # Count query for accurate pagination
    count_query = select(func.count(LeaveRequest.id)).filter(LeaveRequest.company_id == company_id)
    if current_user.role == UserRole.EMPLOYEE.value:
        count_query = count_query.filter(LeaveRequest.employee_id == UUID(current_user.sub))
    count_result = await db.execute(count_query)
    total_items = count_result.scalar()

    result = await db.execute(query)
    items = result.scalars().all()

    meta = PaginatedMeta(page=page, page_size=page_size, total_items=total_items, total_pages=max(1, (total_items + page_size - 1) // page_size))
    
    return PaginatedAPIResponse(success=True, data=items, meta=meta)

@router.put("/{request_id}/status", response_model=APIResponse[LeaveRequestResponse])
async def update_leave_status(
    *,
    db: AsyncSession = Depends(get_db_with_tenant),
    request_id: UUID,
    status_in: LeaveRequestUpdate,
    current_user: TokenPayload = Depends(require_role(UserRole.HR, UserRole.MANAGER, UserRole.SUPER_ADMIN, UserRole.ADMIN))
):
    db_obj = await leave_service.update_leave_status(
        db, 
        request_id=request_id, 
        obj_in=status_in, 
        manager_id=UUID(current_user.sub),
        role=current_user.role
    )
    
    result = await db.execute(
        select(LeaveRequest)
        .options(selectinload(LeaveRequest.leave_type))
        .filter(LeaveRequest.id == db_obj.id)
    )
    return APIResponse(success=True, data=result.scalars().first())
