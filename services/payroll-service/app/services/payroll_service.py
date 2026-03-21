"""Payroll Service — Core Business Logic.

TRANSACTIONAL: Payroll run creates PayrollRun + N Payslips atomically.
IDEMPOTENT: UniqueConstraint prevents duplicate runs for same period.
SNAPSHOT: Payslips freeze salary at processing time — never reference live salary.
"""
import logging
import uuid
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import PayrollStatus
from app.models.payroll import PayrollRun, Payslip, EmployeeSalary, SalaryStructure
from app.repositories.payroll_repository import PayrollRepository
from app.schemas.payroll import (
    SalaryStructureCreate, SalaryStructureUpdate, SalaryStructureResponse,
    EmployeeSalaryCreate, EmployeeSalaryResponse,
    PayrollRunCreate, PayrollRunResponse,
    PayslipResponse,
)
from app.services.calculators.base import BaseSalaryCalculator
from app.core.employee_validator import validate_employee_tenant

logger = logging.getLogger(__name__)
calculator = BaseSalaryCalculator()


class PayrollService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PayrollRepository(db)

    # ── Salary Structure ─────────────────────────────────────────────────

    async def create_structure(self, data: SalaryStructureCreate) -> SalaryStructureResponse:
        obj = await self.repo.create_salary_structure(data.model_dump())
        return SalaryStructureResponse.model_validate(obj)

    async def list_structures(self, skip: int = 0, limit: int = 100, include_inactive: bool = False) -> List[SalaryStructureResponse]:
        items = await self.repo.list_salary_structures(skip=skip, limit=limit, include_inactive=include_inactive)
        return [SalaryStructureResponse.model_validate(i) for i in items]

    async def get_structure(self, sid: UUID) -> Optional[SalaryStructureResponse]:
        obj = await self.repo.get_salary_structure(sid)
        return SalaryStructureResponse.model_validate(obj) if obj else None

    async def update_structure(self, sid: UUID, data: SalaryStructureUpdate) -> Optional[SalaryStructureResponse]:
        obj = await self.repo.get_salary_structure(sid)
        if not obj:
            return None
        updates = data.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(obj, field, value)
        obj = await self.repo.update_salary_structure(obj)
        return SalaryStructureResponse.model_validate(obj)

    async def soft_delete_structure(self, sid: UUID) -> Optional[SalaryStructureResponse]:
        obj = await self.repo.get_salary_structure(sid)
        if not obj:
            return None
        obj.is_active = 0
        obj = await self.repo.update_salary_structure(obj)
        return SalaryStructureResponse.model_validate(obj)

    # ── Employee Salary ──────────────────────────────────────────────────

    async def assign_salary(self, data: EmployeeSalaryCreate) -> EmployeeSalaryResponse:
        # Validate employee belongs to current tenant
        company_id = self.db.info.get("company_id")
        if company_id:
            await validate_employee_tenant(data.employee_id, company_id)

        # Deactivate any existing active salary for this employee
        existing = await self.repo.get_active_salary(data.employee_id)
        if existing:
            existing.is_active = 0
            existing.effective_to = data.effective_from
            self.db.add(existing)

        obj = await self.repo.assign_salary(data.model_dump())
        return EmployeeSalaryResponse.model_validate(obj)

    async def get_employee_salary(self, employee_id: UUID) -> Optional[EmployeeSalaryResponse]:
        obj = await self.repo.get_active_salary(employee_id)
        return EmployeeSalaryResponse.model_validate(obj) if obj else None

    async def get_employee_salary_history(self, employee_id: UUID) -> List[EmployeeSalaryResponse]:
        items = await self.repo.get_employee_salary_history(employee_id)
        return [EmployeeSalaryResponse.model_validate(i) for i in items]

    # ── Payroll Run ──────────────────────────────────────────────────────

    async def run_payroll(self, data: PayrollRunCreate, processed_by: UUID) -> PayrollRunResponse:
        """Execute a payroll run.

        TRANSACTION: All operations (PayrollRun + N Payslips) happen atomically.
        STATUS: DRAFT → PROCESSING → COMPLETED or FAILED.
        SNAPSHOT: Each payslip freezes salary at processing time.
        IDEMPOTENT: DB UniqueConstraint prevents duplicate runs for same period.
        """
        # 1. Create PayrollRun as DRAFT
        run_data = {
            "id": uuid.uuid4(),
            "period_start": data.period_start,
            "period_end": data.period_end,
            "status": PayrollStatus.DRAFT.value,
            "processed_by": processed_by,
        }

        try:
            run = await self.repo.create_payroll_run(run_data)
        except Exception as exc:
            if "uq_payroll_run_company_period" in str(exc).lower() or "unique" in str(exc).lower():
                raise ValueError(
                    f"Payroll already exists for period {data.period_start} to {data.period_end}"
                )
            raise

        # 2. Transition to PROCESSING
        run.status = PayrollStatus.PROCESSING.value
        await self.repo.update_payroll_run(run)

        try:
            # 3. Get all active employee salaries
            active_salaries = await self.repo.list_active_salaries()
            if not active_salaries:
                run.status = PayrollStatus.FAILED.value
                run.error_message = "No active employee salaries found"
                await self.repo.update_payroll_run(run)
                return PayrollRunResponse.model_validate(run)

            total_gross = Decimal("0.00")
            total_net = Decimal("0.00")
            total_deductions = Decimal("0.00")
            count = 0

            # 4. Process each employee — ATOMIC inside a single transaction
            async with self.db.begin_nested():
                for emp_salary in active_salaries:
                    # Fetch the salary structure for this employee
                    structure = await self.repo.get_salary_structure(emp_salary.salary_structure_id)
                    if not structure:
                        continue

                    # Calculate using the strategy calculator
                    breakdown = calculator.calculate(
                        ctc=Decimal(str(emp_salary.ctc)),
                        basic_pct=Decimal(str(structure.basic_pct)),
                        hra_pct=Decimal(str(structure.hra_pct)),
                        allowances_pct=Decimal(str(structure.allowances_pct)),
                        pf_pct=Decimal(str(structure.pf_pct)),
                        esi_pct=Decimal(str(structure.esi_pct)),
                        professional_tax=Decimal(str(structure.professional_tax)),
                    )

                    # 5. Create SNAPSHOT payslip — frozen salary components
                    payslip_data = {
                        "id": uuid.uuid4(),
                        "payroll_run_id": run.id,
                        "employee_id": emp_salary.employee_id,
                        "ctc": breakdown.ctc,
                        "basic": breakdown.basic,
                        "hra": breakdown.hra,
                        "allowances": breakdown.allowances,
                        "pf_deduction": breakdown.pf_deduction,
                        "esi_deduction": breakdown.esi_deduction,
                        "professional_tax": breakdown.professional_tax,
                        "other_deductions": breakdown.other_deductions,
                        "gross": breakdown.gross,
                        "total_deductions": breakdown.total_deductions,
                        "net": breakdown.net,
                        "period_start": data.period_start,
                        "period_end": data.period_end,
                    }
                    await self.repo.create_payslip(payslip_data)

                    total_gross += breakdown.gross
                    total_net += breakdown.net
                    total_deductions += breakdown.total_deductions
                    count += 1

            # 6. Update run totals and mark COMPLETED
            run.total_employees = count
            run.total_gross = total_gross
            run.total_net = total_net
            run.total_deductions = total_deductions
            run.status = PayrollStatus.COMPLETED.value
            run.error_message = None
            await self.repo.update_payroll_run(run)

            logger.info(
                "Payroll run completed",
                extra={
                    "service_task": "payroll_run",
                    "run_id": str(run.id),
                    "employees": count,
                    "total_net": str(total_net),
                },
            )

        except Exception as exc:
            # FAILED — roll back to failed status, preserve error
            run.status = PayrollStatus.FAILED.value
            run.error_message = str(exc)[:500]
            await self.repo.update_payroll_run(run)
            logger.error(
                f"Payroll run failed: {exc}",
                extra={"service_task": "payroll_run", "run_id": str(run.id)},
            )

        return PayrollRunResponse.model_validate(run)

    async def get_payroll_run(self, run_id: UUID) -> Optional[PayrollRunResponse]:
        obj = await self.repo.get_payroll_run(run_id)
        return PayrollRunResponse.model_validate(obj) if obj else None

    async def list_payroll_runs(self, skip: int = 0, limit: int = 100) -> List[PayrollRunResponse]:
        items = await self.repo.list_payroll_runs(skip=skip, limit=limit)
        return [PayrollRunResponse.model_validate(i) for i in items]

    async def get_payslips(self, run_id: UUID) -> List[PayslipResponse]:
        items = await self.repo.get_payslips_by_run(run_id)
        return [PayslipResponse.model_validate(i) for i in items]

    async def get_employee_payslips(self, employee_id: UUID) -> List[PayslipResponse]:
        items = await self.repo.get_payslips_by_employee(employee_id)
        return [PayslipResponse.model_validate(i) for i in items]
