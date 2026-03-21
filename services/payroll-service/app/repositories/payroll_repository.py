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

    @property
    def _company_id(self) -> UUID:
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session — use get_db_with_tenant dependency")
        return UUID(cid) if isinstance(cid, str) else cid

    # ── Salary Structure ─────────────────────────────────────────────────
    async def create_salary_structure(self, data: dict) -> SalaryStructure:
        data["company_id"] = self._company_id
        obj = SalaryStructure(**data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get_salary_structure(self, structure_id: UUID) -> Optional[SalaryStructure]:
        result = await self.db.execute(
            select(SalaryStructure).where(
                and_(SalaryStructure.id == structure_id, SalaryStructure.company_id == self._company_id)
            )
        )
        return result.scalar_one_or_none()

    async def list_salary_structures(self, skip: int = 0, limit: int = 100, include_inactive: bool = False) -> List[SalaryStructure]:
        conditions = [SalaryStructure.company_id == self._company_id]
        if not include_inactive:
            conditions.append(SalaryStructure.is_active == 1)
        result = await self.db.execute(
            select(SalaryStructure).where(and_(*conditions)).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def update_salary_structure(self, structure: SalaryStructure) -> SalaryStructure:
        self.db.add(structure)
        await self.db.commit()
        await self.db.refresh(structure)
        return structure

    # ── Employee Salary ──────────────────────────────────────────────────
    async def assign_salary(self, data: dict) -> EmployeeSalary:
        data["company_id"] = self._company_id
        obj = EmployeeSalary(**data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get_active_salary(self, employee_id: UUID) -> Optional[EmployeeSalary]:
        result = await self.db.execute(
            select(EmployeeSalary).where(
                and_(
                    EmployeeSalary.employee_id == employee_id,
                    EmployeeSalary.is_active == 1,
                    EmployeeSalary.company_id == self._company_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_active_salaries(self) -> List[EmployeeSalary]:
        result = await self.db.execute(
            select(EmployeeSalary).where(
                and_(EmployeeSalary.is_active == 1, EmployeeSalary.company_id == self._company_id)
            )
        )
        return list(result.scalars().all())

    async def get_employee_salary_history(self, employee_id: UUID) -> List[EmployeeSalary]:
        result = await self.db.execute(
            select(EmployeeSalary).where(
                and_(
                    EmployeeSalary.employee_id == employee_id,
                    EmployeeSalary.company_id == self._company_id,
                )
            )
            .order_by(EmployeeSalary.effective_from.desc())
        )
        return list(result.scalars().all())

    async def get_employee_salary(self, salary_id: UUID) -> Optional[EmployeeSalary]:
        result = await self.db.execute(
            select(EmployeeSalary).where(
                and_(EmployeeSalary.id == salary_id, EmployeeSalary.company_id == self._company_id)
            )
        )
        return result.scalar_one_or_none()

    # ── Payroll Run ──────────────────────────────────────────────────────
    async def create_payroll_run(self, data: dict) -> PayrollRun:
        data["company_id"] = self._company_id
        obj = PayrollRun(**data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get_payroll_run(self, run_id: UUID) -> Optional[PayrollRun]:
        result = await self.db.execute(
            select(PayrollRun).where(
                and_(PayrollRun.id == run_id, PayrollRun.company_id == self._company_id)
            )
        )
        return result.scalar_one_or_none()

    async def list_payroll_runs(self, skip: int = 0, limit: int = 100) -> List[PayrollRun]:
        result = await self.db.execute(
            select(PayrollRun).where(PayrollRun.company_id == self._company_id)
            .order_by(PayrollRun.created_at.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def update_payroll_run(self, run: PayrollRun) -> PayrollRun:
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        return run

    # ── Payslip ──────────────────────────────────────────────────────────
    async def create_payslip(self, data: dict) -> Payslip:
        data["company_id"] = self._company_id
        obj = Payslip(**data)
        self.db.add(obj)
        return obj  # Don't commit — caller manages transaction

    async def get_payslips_by_run(self, run_id: UUID) -> List[Payslip]:
        result = await self.db.execute(
            select(Payslip).where(
                and_(Payslip.payroll_run_id == run_id, Payslip.company_id == self._company_id)
            )
        )
        return list(result.scalars().all())

    async def get_payslips_by_employee(self, employee_id: UUID) -> List[Payslip]:
        result = await self.db.execute(
            select(Payslip).where(
                and_(Payslip.employee_id == employee_id, Payslip.company_id == self._company_id)
            )
            .order_by(Payslip.period_start.desc())
        )
        return list(result.scalars().all())
