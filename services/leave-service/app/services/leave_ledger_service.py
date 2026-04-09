"""Leave Ledger service — read-only queries on the leave ledger."""
from typing import List, Optional
from uuid import UUID
from datetime import date

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.leave_ledger_entry import LeaveLedgerEntry


def _cid(db: AsyncSession) -> UUID:
    cid = db.info.get("company_id")
    return UUID(cid) if isinstance(cid, str) else cid


async def list_ledger_entries(
    db: AsyncSession,
    employee_id: Optional[UUID] = None,
    leave_type_id: Optional[UUID] = None,
    transaction_type: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[List[LeaveLedgerEntry], int]:
    cid = _cid(db)
    conditions = [LeaveLedgerEntry.company_id == cid]
    if employee_id:
        conditions.append(LeaveLedgerEntry.employee_id == employee_id)
    if leave_type_id:
        conditions.append(LeaveLedgerEntry.leave_type_id == leave_type_id)
    if transaction_type:
        conditions.append(LeaveLedgerEntry.transaction_type == transaction_type)
    if from_date:
        conditions.append(LeaveLedgerEntry.from_date >= from_date)
    if to_date:
        conditions.append(LeaveLedgerEntry.to_date <= to_date)

    where_clause = and_(*conditions)
    total = (await db.execute(select(func.count(LeaveLedgerEntry.id)).where(where_clause))).scalar() or 0
    items = (await db.execute(
        select(LeaveLedgerEntry).where(where_clause)
        .order_by(LeaveLedgerEntry.created_at.desc())
        .offset(skip).limit(limit)
    )).scalars().all()
    return list(items), total
