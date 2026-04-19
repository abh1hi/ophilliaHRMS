"""Shift type CRUD endpoints — define named shift patterns used in rosters and OT thresholds."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, require_role, TokenPayload, get_db_with_tenant
from app.core.constants import UserRole
from app.core.responses import ok
from app.models.shift_type import ShiftType
from app.schemas.shift_type import ShiftTypeCreate, ShiftTypeUpdate, ShiftTypeResponse

router = APIRouter(prefix="/shift-types", tags=["shift-types"])

_HR_ROLES = require_role(UserRole.HR, UserRole.ADMIN, UserRole.SUPER_ADMIN)


def _company_id(db: AsyncSession) -> UUID:
    cid = db.info.get("company_id")
    if not cid:
        raise RuntimeError("company_id not set on session")
    return UUID(cid) if isinstance(cid, str) else cid


@router.get("")
async def list_shift_types(
    include_inactive: bool = Query(False),
    _: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    stmt = select(ShiftType).where(ShiftType.company_id == _company_id(db))
    if not include_inactive:
        stmt = stmt.where(ShiftType.is_active.is_(True))
    stmt = stmt.order_by(ShiftType.name)
    result = await db.execute(stmt)
    items = result.scalars().all()
    return ok([ShiftTypeResponse.model_validate(x).model_dump(mode="json") for x in items])


@router.post("", status_code=201)
async def create_shift_type(
    data: ShiftTypeCreate,
    current_user: TokenPayload = Depends(_HR_ROLES),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    record = ShiftType(company_id=_company_id(db), **data.model_dump())
    db.add(record)
    await db.flush()
    await db.refresh(record)
    await db.commit()
    return ok(ShiftTypeResponse.model_validate(record).model_dump(mode="json"))


@router.patch("/{shift_type_id}")
async def update_shift_type(
    shift_type_id: UUID,
    data: ShiftTypeUpdate,
    current_user: TokenPayload = Depends(_HR_ROLES),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    result = await db.execute(
        select(ShiftType).where(
            ShiftType.company_id == _company_id(db),
            ShiftType.id == shift_type_id,
        )
    )
    record = result.scalars().first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift type not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(record, field, value)
    await db.flush()
    await db.commit()
    return ok(ShiftTypeResponse.model_validate(record).model_dump(mode="json"))


@router.delete("/{shift_type_id}")
async def delete_shift_type(
    shift_type_id: UUID,
    current_user: TokenPayload = Depends(_HR_ROLES),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    result = await db.execute(
        select(ShiftType).where(
            ShiftType.company_id == _company_id(db),
            ShiftType.id == shift_type_id,
        )
    )
    record = result.scalars().first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift type not found")
    record.is_active = False
    await db.flush()
    await db.commit()
    return ok(ShiftTypeResponse.model_validate(record).model_dump(mode="json"))
