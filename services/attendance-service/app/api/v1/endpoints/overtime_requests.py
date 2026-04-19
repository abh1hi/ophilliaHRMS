"""Overtime request workflow — employees submit, HR/managers approve or reject."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, require_role, TokenPayload, get_db_with_tenant
from app.core.constants import UserRole
from app.core.responses import ok
from app.repositories.overtime_request_repository import OvertimeRequestRepository
from app.schemas.overtime import OvertimeRequestCreate, OvertimeRequestReview, OvertimeRequestResponse

router = APIRouter(prefix="/overtime/requests", tags=["overtime"])

_HR_ROLES = require_role(UserRole.HR, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.MANAGER)


def _repo(db: AsyncSession = Depends(get_db_with_tenant)) -> OvertimeRequestRepository:
    return OvertimeRequestRepository(db)


@router.get("")
async def list_overtime_requests(
    employee_id: UUID | None = Query(None),
    request_status: str | None = Query(None, alias="status"),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_with_tenant),
    repo: OvertimeRequestRepository = Depends(_repo),
):
    is_hr = UserRole(current_user.role) in (
        UserRole.HR, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.MANAGER
    )
    if is_hr:
        items = await repo.list_for_company(status=request_status, employee_id=employee_id)
    else:
        items = await repo.list_for_employee(UUID(current_user.user_id))
    return ok([OvertimeRequestResponse.model_validate(r).model_dump(mode="json") for r in items])


@router.post("", status_code=201)
async def submit_overtime_request(
    data: OvertimeRequestCreate,
    current_user: TokenPayload = Depends(get_current_user),
    repo: OvertimeRequestRepository = Depends(_repo),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    record = await repo.create(
        employee_id=UUID(current_user.user_id),
        date=data.date,
        requested_hours=data.requested_hours,
        reason=data.reason,
    )
    await db.commit()
    return ok(OvertimeRequestResponse.model_validate(record).model_dump(mode="json"))


@router.patch("/{request_id}/review")
async def review_overtime_request(
    request_id: UUID,
    data: OvertimeRequestReview,
    current_user: TokenPayload = Depends(_HR_ROLES),
    repo: OvertimeRequestRepository = Depends(_repo),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    record = await repo.get_by_id(request_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Overtime request not found")
    if record.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Request is already {record.status} and cannot be reviewed again",
        )
    updated = await repo.review(
        request_id=request_id,
        status=data.status,
        reviewer_id=UUID(current_user.user_id),
        note=data.review_note,
    )
    await db.commit()
    return ok(OvertimeRequestResponse.model_validate(updated).model_dump(mode="json"))


@router.delete("/{request_id}", status_code=204)
async def cancel_overtime_request(
    request_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    repo: OvertimeRequestRepository = Depends(_repo),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    record = await repo.get_by_id(request_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Overtime request not found")

    is_hr = UserRole(current_user.role) in (
        UserRole.HR, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.MANAGER
    )
    if not is_hr and str(record.employee_id) != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your request")
    if record.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only pending requests can be cancelled",
        )
    await repo.delete(request_id)
    await db.commit()
