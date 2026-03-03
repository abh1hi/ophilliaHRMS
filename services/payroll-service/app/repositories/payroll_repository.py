import logging
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payroll import SalaryStructure, EmployeeSalary, PayrollRun, Payslip

logger = logging.getLogger(__name__)


class PayrollRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Salary Structure ─────────────────────────────────────────────────
    async def create_salary_structure(self, data: dict) -> SalaryStructure:
        obj = SalaryStructure(**data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get_salary_structure(self, structure_id: UUID) -> Optional[SalaryStructure]:
        result = await self.db.execute(select(SalaryStructure).where(SalaryStructure.id == structure_id))
        return result.scalar_one_or_none()

    async def list_salary_structures(self) -> List[SalaryStructure]:
        result = await self.db.execute(select(SalaryStructure).where(SalaryStructure.is_active == 1))
        return list(result.scalars().all())

    # ── Employee Salary ──────────────────────────────────────────────────
    async def assign_salary(self, data: dict) -> EmployeeSalary:
        obj = EmployeeSalary(**data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get_active_salary(self, employee_id: UUID) -> Optional[EmployeeSalary]:
        result = await self.db.execute(
            select(EmployeeSalary).where(
                and_(EmployeeSalary.employee_id == employee_id, EmployeeSalary.is_active == 1)
            )
        )
        return result.scalar_one_or_none()

    async def list_active_salaries(self) -> List[EmployeeSalary]:
        result = await self.db.execute(select(EmployeeSalary).where(EmployeeSalary.is_active == 1))
        return list(result.scalars().all())

    async def get_employee_salary(self, salary_id: UUID) -> Optional[EmployeeSalary]:
        result = await self.db.execute(select(EmployeeSalary).where(EmployeeSalary.id == salary_id))
        return result.scalar_one_or_none()

    # ── Payroll Run ──────────────────────────────────────────────────────
    async def create_payroll_run(self, data: dict) -> PayrollRun:
        obj = PayrollRun(**data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get_payroll_run(self, run_id: UUID) -> Optional[PayrollRun]:
        result = await self.db.execute(select(PayrollRun).where(PayrollRun.id == run_id))
        return result.scalar_one_or_none()

    async def list_payroll_runs(self) -> List[PayrollRun]:
        result = await self.db.execute(select(PayrollRun).order_by(PayrollRun.created_at.desc()))
        return list(result.scalars().all())

    async def update_payroll_run(self, run: PayrollRun) -> PayrollRun:
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        return run

    # ── Payslip ──────────────────────────────────────────────────────────
    async def create_payslip(self, data: dict) -> Payslip:
        obj = Payslip(**data)
        self.db.add(obj)
        return obj  # Don't commit — caller manages transaction

    async def get_payslips_by_run(self, run_id: UUID) -> List[Payslip]:
        result = await self.db.execute(select(Payslip).where(Payslip.payroll_run_id == run_id))
        return list(result.scalars().all())

    async def get_payslips_by_employee(self, employee_id: UUID) -> List[Payslip]:
        result = await self.db.execute(
            select(Payslip).where(Payslip.employee_id == employee_id).order_by(Payslip.period_start.desc())
        )
        return list(result.scalars().all())
