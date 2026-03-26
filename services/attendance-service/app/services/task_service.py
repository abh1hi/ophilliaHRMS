import logging
from typing import Optional, List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance_task import AttendanceTask
from app.repositories.task_repository import TaskRepository
from app.repositories.attendance_repository import AttendanceRepository
from app.schemas.attendance import TaskCreate, TaskUpdate, TaskCompleteUpdate, TaskAssignRequest

logger = logging.getLogger(__name__)


class TaskService:
    """Business logic for daily attendance task management."""

    def __init__(self, db: AsyncSession):
        self.task_repo = TaskRepository(db)
        self.attendance_repo = AttendanceRepository(db)

    async def add_task(
        self,
        record_id: UUID,
        employee_id: UUID,
        data: TaskCreate,
        assigned_by: Optional[UUID] = None,
    ) -> AttendanceTask:
        """Add a task to an attendance record.

        The record must belong to the given employee (unless assigned_by is set,
        indicating a manager / admin is assigning on behalf of the employee).
        """
        record = await self.attendance_repo.get_by_id(record_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attendance record not found",
            )
        # Employees can only add tasks to their own record
        if assigned_by is None and record.employee_id != employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot add tasks to another employee's record",
            )

        task = AttendanceTask(
            attendance_record_id=record_id,
            employee_id=employee_id,
            assigned_by=assigned_by,
            title=data.title,
            details=data.details,
            estimated_finish_time=data.estimated_finish_time,
            expected_expenses=data.expected_expenses,
            status="pending",
        )
        task = await self.task_repo.create(task)
        logger.info(
            f"Task created: record={record_id}, employee={employee_id}, task={task.id}",
            extra={"user_id": str(employee_id), "service_task": "add_task"},
        )
        return task

    async def update_task(
        self,
        task_id: UUID,
        employee_id: UUID,
        data: TaskUpdate,
    ) -> AttendanceTask:
        """Update pre-completion fields of a task.

        Completed tasks have limited editing: only completion_notes can be updated
        within a time window (handled at completion level).
        """
        task = await self._get_task_for_employee(task_id, employee_id)

        # Completed tasks cannot have their core fields edited
        if task.status in ("completed", "partially_completed", "not_completed"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot edit task details after completion. Only completion notes can be updated.",
            )

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No fields to update",
            )
        return await self.task_repo.update(task, update_data)

    async def delete_task(self, task_id: UUID, employee_id: UUID) -> None:
        """Delete a task (employee can only delete their own tasks).

        Completed tasks cannot be deleted.
        """
        task = await self._get_task_for_employee(task_id, employee_id)
        if task.status in ("completed", "partially_completed", "not_completed"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Completed tasks cannot be deleted",
            )
        await self.task_repo.delete(task)

    async def complete_task(
        self,
        task_id: UUID,
        employee_id: UUID,
        data: TaskCompleteUpdate,
    ) -> AttendanceTask:
        """Mark a task's outcome at punch-out time."""
        task = await self._get_task_for_employee(task_id, employee_id)
        update_data = data.model_dump(exclude_unset=True)
        return await self.task_repo.update(task, update_data)

    async def assign_task_to_employee(
        self,
        data: TaskAssignRequest,
        assigned_by: UUID,
    ) -> AttendanceTask:
        """Assign a task to another employee's today attendance record.

        Any authenticated user (employee, manager, admin) can assign tasks to
        any colleague. The target employee must already be clocked in today.
        """
        from datetime import date as date_cls
        record = await self.attendance_repo.get_by_employee_and_date(
            data.target_employee_id, date_cls.today()
        )
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target employee has not clocked in today. Cannot assign task.",
            )
        task = AttendanceTask(
            attendance_record_id=record.id,
            employee_id=data.target_employee_id,
            assigned_by=assigned_by,
            title=data.title,
            details=data.details,
            estimated_finish_time=data.estimated_finish_time,
            expected_expenses=data.expected_expenses,
            status="pending",
        )
        task = await self.task_repo.create(task)
        logger.info(
            f"Task assigned: target={data.target_employee_id}, by={assigned_by}, task={task.id}",
            extra={"user_id": str(assigned_by), "service_task": "assign_task"},
        )
        return task

    async def list_tasks_for_record(self, record_id: UUID) -> List[AttendanceTask]:
        """Return all tasks for a given attendance record."""
        return await self.task_repo.get_by_record(record_id)

    # ── helpers ────────────────────────────────────────────────────
    async def _get_task_for_employee(
        self, task_id: UUID, employee_id: UUID
    ) -> AttendanceTask:
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found",
            )
        if task.employee_id != employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot modify another employee's task",
            )
        return task
