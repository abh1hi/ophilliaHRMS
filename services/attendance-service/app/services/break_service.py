"""Break management service.

Handles start/end of break sessions within an active attendance record.
Multiple breaks per shift are allowed; total break time is deducted from
work hours at clock-out. A soft warning is issued (HR notified) when a
break starts outside the schedule's break window.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance_break import AttendanceBreak
from app.models.attendance_record import AttendanceRecord
from app.repositories.attendance_repository import AttendanceRepository
from app.services.schedule_resolver import ScheduleResolver, to_ist

logger = logging.getLogger(__name__)

BREAK_AUTO_COMPLETE_MINUTES = 30


class BreakService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.attendance_repo = AttendanceRepository(db)
        self.schedule_resolver = ScheduleResolver(db)

    async def _get_open_record(self, employee_id: UUID) -> AttendanceRecord:
        from datetime import date
        record = await self.attendance_repo.get_open_record_today_for_update(employee_id, date.today())
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active clock-in found. Clock in before starting a break.",
            )
        return record

    async def _get_active_break(self, record_id: UUID) -> Optional[AttendanceBreak]:
        result = await self.db.execute(
            select(AttendanceBreak).where(
                and_(
                    AttendanceBreak.attendance_record_id == record_id,
                    AttendanceBreak.break_end.is_(None),
                )
            ).limit(1)
        )
        return result.scalar_one_or_none()

    async def start_break(self, employee_id: UUID) -> AttendanceBreak:
        record = await self._get_open_record(employee_id)

        # Block if already on break
        active = await self._get_active_break(record.id)
        if active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A break is already in progress. End the current break before starting a new one.",
            )

        now = datetime.now(timezone.utc)
        now_ist_time = to_ist(now).time()

        # Check if inside clock-in or clock-out windows (breaks not allowed there)
        is_outside_window = False
        if record.schedule_id:
            resolved = await self.schedule_resolver.resolve_by_schedule_id(record.schedule_id, record.date)

            ci_start = resolved.schedule.clock_in_start_time
            ci_end = resolved.schedule.clock_in_end_time
            co_start = resolved.schedule.clock_out_start_time
            co_end = resolved.schedule.clock_out_end_time

            from app.services.schedule_resolver import ScheduleResolver as _SR
            in_ci_window = _SR.is_within_window(None, now_ist_time, ci_start, ci_end)
            in_co_window = _SR.is_within_window(None, now_ist_time, co_start, co_end)

            if in_ci_window or in_co_window:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Breaks cannot be started during the clock-in or clock-out window.",
                )

            # Check break window (soft: allow but flag + notify HR)
            bw_start = resolved.schedule.break_window_start
            bw_end = resolved.schedule.break_window_end
            if bw_start and bw_end:
                in_break_window = _SR.is_within_window(None, now_ist_time, bw_start, bw_end)
                if not in_break_window:
                    is_outside_window = True
                    logger.info(
                        f"Break started outside window for employee={employee_id}. "
                        f"Break window: {bw_start}–{bw_end}, current IST: {now_ist_time}"
                    )

        company_id = self.attendance_repo.db.info.get("company_id")
        break_record = AttendanceBreak(
            id=uuid4(),
            company_id=company_id,
            attendance_record_id=record.id,
            break_start=now,
            is_outside_window=is_outside_window,
        )
        self.db.add(break_record)
        await self.db.commit()
        await self.db.refresh(break_record)

        if is_outside_window:
            # Emit event for notification system to alert HR
            try:
                from app.events.publisher import get_publisher
                publisher = await get_publisher()
                if publisher:
                    await publisher.publish("attendance.break_outside_window", {
                        "company_id": str(company_id) if company_id else None,
                        "employee_id": str(employee_id),
                        "record_id": str(record.id),
                        "break_id": str(break_record.id),
                        "break_start": now.isoformat(),
                    })
            except Exception:
                pass

        return break_record

    async def end_break(self, employee_id: UUID) -> AttendanceBreak:
        record = await self._get_open_record(employee_id)
        active = await self._get_active_break(record.id)
        if not active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active break found to end.",
            )

        now = datetime.now(timezone.utc)
        duration = (now - active.break_start).total_seconds() / 60

        active.break_end = now
        active.duration_minutes = round(duration, 2)

        # Update the attendance record's running break total
        new_total = (record.break_minutes_total or 0.0) + active.duration_minutes
        await self.attendance_repo.update(record, {"break_minutes_total": new_total})

        await self.db.commit()
        await self.db.refresh(active)
        return active

    async def get_active_break(self, employee_id: UUID) -> Optional[AttendanceBreak]:
        """Return the currently open break for this employee, or None."""
        from datetime import date
        record = await self.attendance_repo.get_open_record_today_for_update(employee_id, date.today())
        if not record:
            return None
        await self.db.rollback()  # release lock from get_open_record_today_for_update
        return await self._get_active_break(record.id)

    @staticmethod
    async def auto_complete_breaks(db: AsyncSession) -> int:
        """Scheduler task: auto-close breaks that have run for 30+ minutes.

        Returns the count of auto-completed breaks.
        """
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=BREAK_AUTO_COMPLETE_MINUTES)

        result = await db.execute(
            select(AttendanceBreak).where(
                and_(
                    AttendanceBreak.break_end.is_(None),
                    AttendanceBreak.break_start <= cutoff,
                )
            ).with_for_update(skip_locked=True)
        )
        breaks = result.scalars().all()

        completed = 0
        for b in breaks:
            b.break_end = b.break_start + timedelta(minutes=BREAK_AUTO_COMPLETE_MINUTES)
            b.duration_minutes = BREAK_AUTO_COMPLETE_MINUTES
            b.is_auto_completed = True

            # Update parent record break total
            rec_result = await db.execute(
                select(AttendanceRecord).where(AttendanceRecord.id == b.attendance_record_id)
            )
            record = rec_result.scalar_one_or_none()
            if record:
                record.break_minutes_total = (record.break_minutes_total or 0.0) + BREAK_AUTO_COMPLETE_MINUTES

            completed += 1

        if completed:
            await db.commit()
            logger.info(f"Auto-completed {completed} break(s)")

        return completed
