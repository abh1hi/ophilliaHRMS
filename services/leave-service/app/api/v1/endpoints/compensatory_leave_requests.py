from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.v1.dependencies import get_current_user, require_role, TokenPayload, get_db_with_tenant
from app.core.constants import UserRole
from app.schemas.compensatory_leave import (
    CompensatoryLeaveRequestCreate, CompensatoryLeaveReview,
    CompensatoryLeaveRequestResponse, CompensatoryLeaveListResponse,
)
from app.schemas.response import APIResponse
from app.services import compensatory_service

router = APIRouter()


@router.get("/", response_model=APIResponse[CompensatoryLeaveListResponse])
async def list_requests(
    employee_id: UUID | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(get_current_user),
):
    items, total = await compensatory_service.list_requests(db, employee_id, status, skip, limit)
    return APIResponse(success=True, data=CompensatoryLeaveListResponse(
        total=total, skip=skip, limit=limit, requests=items
    ))


@router.get("/{request_id}", response_model=APIResponse[CompensatoryLeaveRequestResponse])
async def get_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(get_current_user),
):
    item = await compensatory_service.get_request(db, request_id)
    return APIResponse(success=True, data=item)


@router.post("/", response_model=APIResponse[CompensatoryLeaveRequestResponse], status_code=201)
async def create_request(
    data: CompensatoryLeaveRequestCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: TokenPayload = Depends(get_current_user),
):
    item = await compensatory_service.create_request(db, data, UUID(current_user.sub))
    return APIResponse(success=True, data=item)


@router.patch("/{request_id}/review", response_model=APIResponse[CompensatoryLeaveRequestResponse])
async def review_request(
    request_id: UUID,
    data: CompensatoryLeaveReview,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    item = await compensatory_service.review_request(db, request_id, data, UUID(current_user.sub))
    return APIResponse(success=True, data=item)
