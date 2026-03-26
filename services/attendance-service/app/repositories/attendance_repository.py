from typing import Optional, List
from uuid import UUID
from datetime import date, timedelta

from sqlalchemy import select, func, and_, extract, case, literal_column
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance_record import AttendanceRecord
from app.models.attendance_task import AttendanceTask


class AttendanceRepository:
    """Data access layer for attendance records — async CRUD."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _company_id(self) -> UUID:
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session — use get_db_with_tenant dependency")
        return UUID(cid) if isinstance(cid, str) else cid

    def _scoped(self, stmt):
        return stmt.where(AttendanceRecord.company_id == self._company_id)

    async def create(self, record: AttendanceRecord) -> AttendanceRecord:
        record.company_id = self._company_id
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def get_by_id(self, record_id: UUID) -> Optional[AttendanceRecord]:
        result = await self.db.execute(
            self._scoped(select(AttendanceRecord)).where(AttendanceRecord.id == record_id)
        )
        return result.scalars().first()

    async def get_by_employee_and_date(
        self, employee_id: UUID, record_date: date
    ) -> Optional[AttendanceRecord]:
        """Get the latest shift record for an employee on a given date."""
        result = await self.db.execute(
            self._scoped(select(AttendanceRecord)).where(
                and_(
                    AttendanceRecord.employee_id == employee_id,
                    AttendanceRecord.date == record_date,
                )
            ).order_by(AttendanceRecord.shift_number.desc())
        )
        return result.scalars().first()

    async def get_employee_records(
        self,
        employee_id: UUID,
        skip: int = 0,
        limit: int = 20,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> tuple[List[AttendanceRecord], int]:
        query = self._scoped(select(AttendanceRecord)).where(
            AttendanceRecord.employee_id == employee_id
        )
        count_query = self._scoped(select(func.count(AttendanceRecord.id))).where(
            AttendanceRecord.employee_id == employee_id
        )

        if date_from:
            query = query.where(AttendanceRecord.date >= date_from)
            count_query = count_query.where(AttendanceRecord.date >= date_from)
        if date_to:
            query = query.where(AttendanceRecord.date <= date_to)
            count_query = count_query.where(AttendanceRecord.date <= date_to)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(AttendanceRecord.date.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        employee_id: Optional[UUID] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        status: Optional[str] = None,
    ) -> tuple[List[AttendanceRecord], int]:
        query = self._scoped(select(AttendanceRecord))
        count_query = self._scoped(select(func.count(AttendanceRecord.id)))

        if employee_id:
            query = query.where(AttendanceRecord.employee_id == employee_id)
            count_query = count_query.where(AttendanceRecord.employee_id == employee_id)
        if date_from:
            query = query.where(AttendanceRecord.date >= date_from)
            count_query = count_query.where(AttendanceRecord.date >= date_from)
        if date_to:
            query = query.where(AttendanceRecord.date <= date_to)
            count_query = count_query.where(AttendanceRecord.date <= date_to)
        if status:
            query = query.where(AttendanceRecord.status == status)
            count_query = count_query.where(AttendanceRecord.status == status)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(AttendanceRecord.date.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def update(self, record: AttendanceRecord, update_data: dict) -> AttendanceRecord:
        for field, value in update_data.items():
            if value is not None:
                setattr(record, field, value)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def get_missed_punchout_today(self) -> List[AttendanceRecord]:
        """Return attendance records for today that have no clock_out."""
        today = date.today()
        result = await self.db.execute(
            self._scoped(select(AttendanceRecord)).where(
                and_(
                    AttendanceRecord.date == today,
                    AttendanceRecord.clock_out.is_(None),
                )
            )
        )
        return list(result.scalars().all())

    async def get_late_count_today(self) -> int:
        """Return count of late clock-ins for today."""
        today = date.today()
        result = await self.db.execute(
            self._scoped(select(func.count(AttendanceRecord.id))).where(
                and_(
                    AttendanceRecord.date == today,
                    AttendanceRecord.status == "late",
                )
            )
        )
        return result.scalar() or 0

    async def get_open_record_today(
        self, employee_id: UUID, record_date: date
    ) -> Optional[AttendanceRecord]:
        """Get the most recent open (not clocked out) record for today."""
        result = await self.db.execute(
            self._scoped(select(AttendanceRecord)).where(
                and_(
                    AttendanceRecord.employee_id == employee_id,
                    AttendanceRecord.date == record_date,
                    AttendanceRecord.clock_out.is_(None),
                )
            ).order_by(AttendanceRecord.shift_number.desc())
        )
        return result.scalars().first()

    async def get_all_shifts_today(
        self, employee_id: UUID, record_date: date
    ) -> List[AttendanceRecord]:
        """Get all shift records for an employee on a given date, ordered by shift_number."""
        result = await self.db.execute(
            self._scoped(select(AttendanceRecord)).where(
                and_(
                    AttendanceRecord.employee_id == employee_id,
                    AttendanceRecord.date == record_date,
                )
            ).order_by(AttendanceRecord.shift_number.asc())
        )
        return list(result.scalars().all())

    async def get_shift_count_today(self, employee_id: UUID, record_date: date) -> int:
        """Count how many shifts an employee has today."""
        result = await self.db.execute(
            self._scoped(select(func.count(AttendanceRecord.id))).where(
                and_(
                    AttendanceRecord.employee_id == employee_id,
                    AttendanceRecord.date == record_date,
                )
            )
        )
        return result.scalar() or 0

    async def get_admin_kpi(self, target_date: date) -> dict:
        """Aggregate KPI data for admin dashboard."""
        from app.schemas.attendance import AdminKPIResponse

        base = self._scoped(select(AttendanceRecord)).where(AttendanceRecord.date == target_date)

        # Attendance counts
        result = await self.db.execute(
            self._scoped(select(
                func.count(AttendanceRecord.id).label("total"),
                func.sum(case((AttendanceRecord.status.in_(["present", "late", "half_day"]), 1), else_=0)).label("present"),
                func.sum(case((AttendanceRecord.status == "late", 1), else_=0)).label("late"),
                func.sum(case((AttendanceRecord.status == "absent", 1), else_=0)).label("absent"),
                func.sum(case((AttendanceRecord.clock_out.is_(None), 1), else_=0)).label("missed"),
                func.sum(case((AttendanceRecord.status == "auto_closed", 1), else_=0)).label("auto_closed"),
                func.avg(AttendanceRecord.work_hours).label("avg_hours"),
            )).where(AttendanceRecord.date == target_date)
        )
        row = result.mappings().first()

        # Task counts for today
        task_result = await self.db.execute(
            self._scoped(select(
                func.count(AttendanceTask.id).label("total_tasks"),
                func.sum(case((AttendanceTask.status == "completed", 1), else_=0)).label("completed_tasks"),
            ))
            .join(AttendanceRecord, AttendanceTask.attendance_record_id == AttendanceRecord.id)
            .where(AttendanceRecord.date == target_date)
        )
        task_row = task_result.mappings().first()

        total_tasks = task_row["total_tasks"] or 0
        completed_tasks = task_row["completed_tasks"] or 0

        return AdminKPIResponse(
            date=target_date,
            total_employees_present=row["present"] or 0,
            late_checkins=row["late"] or 0,
            absent_employees=row["absent"] or 0,
            missed_punchouts=row["missed"] or 0,
            auto_closed_count=row["auto_closed"] or 0,
            avg_working_hours=round(float(row["avg_hours"]), 1) if row["avg_hours"] else None,
            total_tasks_today=total_tasks,
            completed_tasks_today=completed_tasks,
            task_completion_rate=round((completed_tasks / total_tasks * 100), 1) if total_tasks else None,
        )

    async def get_attendance_trend(self, days: int = 7) -> list:
        """Get attendance trend for the last N days."""
        from app.schemas.attendance import AttendanceTrendItem
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        result = await self.db.execute(
            self._scoped(select(
                AttendanceRecord.date,
                func.sum(case((AttendanceRecord.status.in_(["present"]), 1), else_=0)).label("present"),
                func.sum(case((AttendanceRecord.status == "late", 1), else_=0)).label("late"),
                func.sum(case((AttendanceRecord.status == "absent", 1), else_=0)).label("absent"),
                func.sum(case((AttendanceRecord.status == "half_day", 1), else_=0)).label("half_day"),
                func.sum(case((AttendanceRecord.status == "auto_closed", 1), else_=0)).label("auto_closed"),
                func.avg(AttendanceRecord.work_hours).label("avg_hours"),
            ))
            .where(and_(
                AttendanceRecord.date >= start_date,
                AttendanceRecord.date <= end_date,
            ))
            .group_by(AttendanceRecord.date)
            .order_by(AttendanceRecord.date)
        )
        rows = result.mappings().all()
        return [
            AttendanceTrendItem(
                date=row["date"],
                present=row["present"] or 0,
                late=row["late"] or 0,
                absent=row["absent"] or 0,
                half_day=row["half_day"] or 0,
                auto_closed=row["auto_closed"] or 0,
                avg_hours=round(float(row["avg_hours"]), 1) if row["avg_hours"] else None,
            )
            for row in rows
        ]

    async def get_daily_status_breakdown(self, target_date: date) -> dict:
        """Get status counts for a single day."""
        from app.schemas.attendance import DailyStatusBreakdown

        result = await self.db.execute(
            self._scoped(select(
                func.sum(case((AttendanceRecord.status == "present", 1), else_=0)).label("present"),
                func.sum(case((AttendanceRecord.status == "late", 1), else_=0)).label("late"),
                func.sum(case((AttendanceRecord.status == "half_day", 1), else_=0)).label("half_day"),
                func.sum(case((AttendanceRecord.status == "absent", 1), else_=0)).label("absent"),
                func.sum(case((AttendanceRecord.status == "auto_closed", 1), else_=0)).label("auto_closed"),
            )).where(AttendanceRecord.date == target_date)
        )
        row = result.mappings().first()
        return DailyStatusBreakdown(
            date=target_date,
            present=row["present"] or 0,
            late=row["late"] or 0,
            half_day=row["half_day"] or 0,
            absent=row["absent"] or 0,
            auto_closed=row["auto_closed"] or 0,
        )

    async def get_performers(self, year: int, month: int, limit: int = 5) -> dict:
        """Get top and low performers for a month based on productivity score."""
        from app.schemas.attendance import EmployeeProductivitySummary, PerformersResponse

        base_query = (
            self._scoped(select(
                AttendanceRecord.employee_id,
                func.avg(AttendanceRecord.productivity_score).label("productivity_score"),
                func.avg(AttendanceRecord.day_rating).label("avg_rating"),
            ))
            .where(and_(
                extract("year", AttendanceRecord.date) == year,
                extract("month", AttendanceRecord.date) == month,
                AttendanceRecord.productivity_score.isnot(None),
            ))
            .group_by(AttendanceRecord.employee_id)
        )

        # Task stats per employee for the month
        task_query = (
            self._scoped(select(
                AttendanceRecord.employee_id,
                func.count(AttendanceTask.id).label("total_tasks"),
                func.sum(case((AttendanceTask.status == "completed", 1), else_=0)).label("completed_tasks"),
            ))
            .join(AttendanceRecord, AttendanceTask.attendance_record_id == AttendanceRecord.id)
            .where(and_(
                extract("year", AttendanceRecord.date) == year,
                extract("month", AttendanceRecord.date) == month,
            ))
            .group_by(AttendanceRecord.employee_id)
        )
        task_result = await self.db.execute(task_query)
        task_map = {row["employee_id"]: row for row in task_result.mappings().all()}

        # Top performers
        top_result = await self.db.execute(
            base_query.order_by(func.avg(AttendanceRecord.productivity_score).desc()).limit(limit)
        )
        top_rows = top_result.mappings().all()

        # Low performers
        low_result = await self.db.execute(
            base_query.order_by(func.avg(AttendanceRecord.productivity_score).asc()).limit(limit)
        )
        low_rows = low_result.mappings().all()

        def _build_summary(row):
            emp_id = row["employee_id"]
            task_data = task_map.get(emp_id, {})
            total_tasks = task_data.get("total_tasks", 0) or 0
            completed = task_data.get("completed_tasks", 0) or 0
            return EmployeeProductivitySummary(
                employee_id=emp_id,
                total_tasks=total_tasks,
                completed_tasks=completed,
                completion_rate=round((completed / total_tasks * 100), 1) if total_tasks else 0.0,
                avg_rating=round(float(row["avg_rating"]), 1) if row["avg_rating"] else None,
                productivity_score=round(float(row["productivity_score"]), 1) if row["productivity_score"] else None,
            )

        return PerformersResponse(
            top_performers=[_build_summary(r) for r in top_rows],
            low_performers=[_build_summary(r) for r in low_rows],
        )

    async def get_productivity_data(
        self,
        year: int,
        month: int,
        employee_id: Optional[UUID] = None,
    ) -> List[dict]:
        """Aggregate per-employee productivity stats for a given month.

        Returns a list of dicts with employee_id and aggregated attendance/task counts.
        """
        # Build attendance aggregation
        att_query = (
            self._scoped(select(
                AttendanceRecord.employee_id,
                func.count(AttendanceRecord.id).label("total_days"),
                func.sum(
                    func.cast(AttendanceRecord.status.in_(["present", "late"]), func.Integer())
                ).label("present_days"),
                func.sum(
                    func.cast(AttendanceRecord.status == "late", func.Integer())
                ).label("late_days"),
                func.sum(
                    func.cast(AttendanceRecord.status == "half_day", func.Integer())
                ).label("half_days"),
                func.avg(AttendanceRecord.day_rating).label("avg_rating"),
                func.sum(AttendanceRecord.work_hours).label("total_work_hours"),
            ))
            .where(
                and_(
                    extract("year", AttendanceRecord.date) == year,
                    extract("month", AttendanceRecord.date) == month,
                )
            )
            .group_by(AttendanceRecord.employee_id)
        )
        if employee_id:
            att_query = att_query.where(AttendanceRecord.employee_id == employee_id)

        att_result = await self.db.execute(att_query)
        att_rows = att_result.mappings().all()

        # Build task aggregation joined via attendance record
        task_query = (
            self._scoped(select(
                AttendanceRecord.employee_id,
                func.count(AttendanceTask.id).label("total_tasks"),
                func.sum(
                    func.cast(AttendanceTask.status == "completed", func.Integer())
                ).label("completed_tasks"),
                func.sum(
                    func.cast(AttendanceTask.status == "partially_completed", func.Integer())
                ).label("partial_tasks"),
                func.sum(
                    func.cast(AttendanceTask.status == "not_completed", func.Integer())
                ).label("not_completed_tasks"),
                func.sum(
                    func.cast(AttendanceTask.status == "pending", func.Integer())
                ).label("pending_tasks"),
                func.sum(AttendanceTask.expected_expenses).label("total_expected_expenses"),
                func.sum(AttendanceTask.actual_expenses).label("total_actual_expenses"),
            ))
            .join(AttendanceRecord, AttendanceTask.attendance_record_id == AttendanceRecord.id)
            .where(
                and_(
                    extract("year", AttendanceRecord.date) == year,
                    extract("month", AttendanceRecord.date) == month,
                )
            )
            .group_by(AttendanceRecord.employee_id)
        )
        if employee_id:
            task_query = task_query.where(AttendanceRecord.employee_id == employee_id)

        task_result = await self.db.execute(task_query)
        task_rows = {row["employee_id"]: row for row in task_result.mappings().all()}

        # Merge
        results = []
        for row in att_rows:
            emp_id = row["employee_id"]
            task_data = task_rows.get(emp_id, {})
            total_tasks = task_data.get("total_tasks") or 0
            completed = task_data.get("completed_tasks") or 0
            results.append({
                "employee_id": emp_id,
                "month": month,
                "year": year,
                "total_days": row["total_days"] or 0,
                "present_days": row["present_days"] or 0,
                "late_days": row["late_days"] or 0,
                "half_days": row["half_days"] or 0,
                "total_tasks": total_tasks,
                "completed_tasks": completed,
                "partial_tasks": task_data.get("partial_tasks") or 0,
                "not_completed_tasks": task_data.get("not_completed_tasks") or 0,
                "pending_tasks": task_data.get("pending_tasks") or 0,
                "completion_rate": round((completed / total_tasks * 100), 1) if total_tasks else 0.0,
                "avg_rating": float(row["avg_rating"]) if row["avg_rating"] else None,
                "total_expected_expenses": task_data.get("total_expected_expenses"),
                "total_actual_expenses": task_data.get("total_actual_expenses"),
            })
        return results
