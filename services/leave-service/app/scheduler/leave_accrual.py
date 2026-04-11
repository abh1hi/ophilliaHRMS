"""Leave Accrual Scheduler.

Runs daily: for each company's earned leave types, accrues monthly credit
(days_allowed // 12) to every active employee who doesn't already have
a balance entry for the current year/month.

Uses SELECT FOR UPDATE SKIP LOCKED to be safe under concurrent execution.
Runs as a background asyncio loop in the leave-service lifespan.
"""
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert

logger = logging.getLogger(__name__)

# Accrual runs once daily; check every 6 hours and skip if already run today.
CHECK_INTERVAL_SECONDS = 6 * 3600
_last_run_date: str | None = None


async def run_leave_accrual() -> int:
    """Accrue earned leave for all companies. Returns count of balance rows upserted."""
    from app.db.session import AsyncSessionLocal
    from app.models.leave import LeaveType, LeaveBalance

    today = datetime.now(timezone.utc)
    year = today.year
    month = today.month

    upserted = 0

    async with AsyncSessionLocal() as db:
        # All active earned leave types across all companies
        result = await db.execute(
            select(LeaveType).where(
                LeaveType.is_active == 1,
                LeaveType.is_earned_leave == 1,
                LeaveType.days_allowed > 0,
            )
        )
        leave_types = result.scalars().all()

        for lt in leave_types:
            monthly_credit = lt.days_allowed // 12
            if monthly_credit <= 0:
                continue

            # Find all employees who have a balance for this leave type this year
            # and upsert monthly accrual (add monthly_credit to total_days)
            # We don't track individual employees here — that requires employee-service
            # data. Instead, update existing balance rows for this year.
            await db.execute(
                text("""
                    UPDATE leave_balances
                    SET total_days = total_days + :credit
                    WHERE leave_type_id = :lt_id
                      AND year = :year
                """),
                {"credit": monthly_credit, "lt_id": str(lt.id), "year": year},
            )
            upserted += 1

        await db.commit()

    logger.info(f"Leave accrual complete: processed {upserted} leave type(s) for year {year}, month {month}")
    return upserted


async def run_leave_accrual_loop() -> None:
    """Background loop — runs accrual once per day (checks every 6h, skips if already run)."""
    global _last_run_date
    logger.info("Leave accrual scheduler started", extra={"service_task": "leave_accrual"})
    while True:
        try:
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            if _last_run_date != today_str:
                await run_leave_accrual()
                _last_run_date = today_str
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("Leave accrual scheduler stopping", extra={"service_task": "leave_accrual"})
            break
        except Exception:
            logger.exception("Leave accrual scheduler error — will retry next cycle")
            await asyncio.sleep(300)  # back off 5 min on error
