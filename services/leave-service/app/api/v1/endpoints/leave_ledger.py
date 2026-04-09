from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date

from app.api.v1.dependencies import get_current_user, TokenPayload, get_db_with_tenant
from app.schemas.leave_ledger import LeaveLedgerListResponse
from app.schemas.response import APIResponse
from app.services import leave_ledger_service

router = APIRouter()


@router.get("/", response_model=APIResponse[LeaveLedgerListResponse])
async def list_ledger_entries(
    employee_id: UUID | None = None,
    leave_type_id: UUID | None = None,
    transaction_type: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(get_current_user),
):
    items, total = await leave_ledger_service.list_ledger_entries(
        db, employee_id, leave_type_id, transaction_type, from_date, to_date, skip, limit
    )
    return APIResponse(success=True, data=LeaveLedgerListResponse(
        total=total, skip=skip, limit=limit, entries=items
    ))
