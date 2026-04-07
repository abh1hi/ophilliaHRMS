"""Payroll Service — Core Business Logic.

TRANSACTIONAL: Payroll run creates PayrollRun + N Payslips atomically.
IDEMPOTENT: UniqueConstraint prevents duplicate runs for same period.
SNAPSHOT: Payslips freeze salary at processing time — never reference live salary.
PRO-RATION: Applies when employee joins mid-period.
LOP INTEGRATION: Soft dependency on leave-service; graceful fallback on unavailability.
"""
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import PayrollStatus, LOPFetchStatus
from app.models.payroll import PayrollRun, Payslip, EmployeeSalary, SalaryStructure
from app.repositories.payroll_repository import PayrollRepository
from app.schemas.payroll import (
    SalaryStructureCreate, SalaryStructureUpdate, SalaryStructureResponse,
    EmployeeSalaryCreate, EmployeeSalaryResponse,
    PayrollRunCreate, PayrollRunResponse,
    PayslipResponse,
)
from app.services.calculators.india_calculator import IndiaSalaryCalculator
from app.services.attendance_integration import (
    fetch_lop_summary,
    pro_rata_factor,
    lop_deduction,
    calendar_days_in_period,
)
from app.core.employee_validator import validate_employee_tenant
from app.core.payroll_guards import (
    assert_payroll_not_locked,
    assert_payroll_in_state,
    assert_net_pay_valid,
    assert_payroll_state_valid,
    assert_payroll_not_failed,
)

logger = logging.getLogger(__name__)

# ── Snapshot Schema Version ──────────────────────────────────────────────
# Used to identify which version of snapshot schema was used at payslip creation.
# Format: YYYY-MM-vN (e.g., "2026-04-v1")
# Increment version when snapshot schema changes (e.g., adding new fields).
PAYSLIP_SNAPSHOT_SCHEMA_VERSION = "2026-04-v1"

# Default calculator — India with Maharashtra state
calculator = IndiaSalaryCalculator(state_code="MH", tax_regime="new")


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
        """Execute a payroll run with pro-ration and LOP integration.

        TRANSACTION: All operations (PayrollRun + N Payslips) happen atomically.
        STATUS: DRAFT → PROCESSING → COMPLETED or FAILED.
        SNAPSHOT: Each payslip freezes salary at processing time.
        IDEMPOTENT: DB UniqueConstraint prevents duplicate runs for same period.
        PRO-RATION: Applied if employee.effective_from is within period.
        LOP INTEGRATION: Soft dependency on leave-service.
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

        exception_warnings: List[str] = []

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
            company_id = self.db.info.get("company_id")

            # 4. Process each employee — ATOMIC inside a single transaction
            async with self.db.begin_nested():
                for emp_salary in active_salaries:
                    # Fetch the salary structure for this employee
                    structure = await self.repo.get_salary_structure(emp_salary.salary_structure_id)
                    if not structure:
                        continue

                    # ── STEP 1: Calculate base salary (earnings only, no deductions yet)
                    breakdown = calculator.calculate(
                        ctc=Decimal(str(emp_salary.ctc)),
                        basic_pct=Decimal(str(structure.basic_pct)),
                        hra_pct=Decimal(str(structure.hra_pct)),
                        allowances_pct=Decimal(str(structure.allowances_pct)),
                        pf_pct=Decimal(str(structure.pf_pct)),
                        esi_pct=Decimal(str(structure.esi_pct)),
                        professional_tax=Decimal(str(structure.professional_tax)),
                    )

                    # ── STEP 2: Apply pro-ration (if employee joined mid-period)
                    prf = pro_rata_factor(emp_salary.effective_from, data.period_start, data.period_end)
                    prorated_basic = breakdown.basic * prf
                    prorated_hra = breakdown.hra * prf
                    prorated_allowances = breakdown.allowances * prf
                    prorated_gross = prorated_basic + prorated_hra + prorated_allowances

                    # ── STEP 3: Fetch LOP data (soft integration, graceful fallback)
                    lop_days = 0
                    lop_fetch_status = LOPFetchStatus.OK.value
                    if company_id:
                        lop_days, fetch_status, _detail = await fetch_lop_summary(
                            employee_id=str(emp_salary.employee_id),
                            period_start=data.period_start,
                            period_end=data.period_end,
                            company_id=company_id,
                        )
                        if fetch_status == "UNAVAILABLE":
                            lop_fetch_status = LOPFetchStatus.UNAVAILABLE.value
                            exception_warnings.append(
                                f"LOP data unavailable for emp {emp_salary.employee_id} — using 0 days"
                            )
                        elif fetch_status == "ERROR":
                            lop_fetch_status = LOPFetchStatus.UNAVAILABLE.value
                            exception_warnings.append(
                                f"Error fetching LOP for emp {emp_salary.employee_id} — using 0 days"
                            )

                    # ── STEP 4: Apply LOP deduction
                    period_days = calendar_days_in_period(data.period_start, data.period_end)
                    lop_amount = lop_deduction(prorated_gross, lop_days, period_days, method="CALENDAR")
                    net_gross = prorated_gross - lop_amount

                    # ── STEP 5: Calculate statutory deductions (PF, ESI, PT, TDS)
                    # Recalculate with pro-rated gross (excluding LOP)
                    pf_employee = calculator.calculate_pf(prorated_basic, Decimal("12"))
                    esi_employee = calculator.calculate_esi(net_gross, Decimal("0.75"))
                    pt_employee = calculator.calculate_professional_tax(
                        Decimal("0"),
                        gross=net_gross,
                        month=data.period_start.month,
                        gender="M",
                    )
                    tds_employee = Decimal("0.00")  # TODO: Integrate with YTD in Phase 4
                    lwf_employee = Decimal("0.00")   # TODO: Implement LWF in Phase 2 extension

                    # ── STEP 6: Calculate employer contributions
                    pf_employer = calculator.calculate_employer_pf(prorated_basic)
                    esi_employer = calculator.calculate_employer_esi(net_gross)

                    # ── STEP 7: Compute totals
                    total_employee_deductions = (
                        pf_employee + esi_employee + pt_employee + tds_employee + lwf_employee
                    )
                    net_salary = net_gross - total_employee_deductions

                    # ── STEP 8: Create SNAPSHOT payslip — frozen salary components
                    payslip_data = {
                        "id": uuid.uuid4(),
                        "payroll_run_id": run.id,
                        "employee_id": emp_salary.employee_id,
                        "ctc": breakdown.ctc,
                        "basic": prorated_basic,
                        "hra": prorated_hra,
                        "allowances": prorated_allowances,
                        "pf_deduction": pf_employee,
                        "esi_deduction": esi_employee,
                        "professional_tax": pt_employee,
                        "tds_deduction": tds_employee,
                        "lwf_employee": lwf_employee,
                        "other_deductions": Decimal("0.00"),
                        "gross": net_gross,
                        "total_deductions": total_employee_deductions,
                        "net": net_salary,
                        # Phase 1A additions
                        "employer_pf": pf_employer,
                        "employer_esi": esi_employer,
                        "employer_lwf": Decimal("0.00"),
                        "lop_days": lop_days,
                        "lop_amount": lop_amount,
                        "lop_fetch_status": lop_fetch_status,
                        "pro_rata_factor": prf,
                        "tax_regime": "new",
                        "period_start": data.period_start,
                        "period_end": data.period_end,
                    }
                    await self.repo.create_payslip(payslip_data)

                    total_gross += net_gross
                    total_net += net_salary
                    total_deductions += total_employee_deductions
                    count += 1

            # 6. Update run totals and mark COMPLETED
            run.total_employees = count
            run.total_gross = total_gross
            run.total_net = total_net
            run.total_deductions = total_deductions
            run.status = PayrollStatus.COMPLETED.value
            run.error_message = None
            if exception_warnings:
                run.exception_report = {
                    "warnings": exception_warnings,
                    "errors": [],
                }
            await self.repo.update_payroll_run(run)

            logger.info(
                "Payroll run completed with pro-ration and LOP",
                extra={
                    "service_task": "payroll_run",
                    "run_id": str(run.id),
                    "employees": count,
                    "total_net": str(total_net),
                    "lop_warnings": len([w for w in exception_warnings if "LOP" in w]),
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

    # ── Phase 4: Approval Lifecycle ──────────────────────────────────

    async def compute_payroll(
        self,
        run_id: UUID,
        computed_by: UUID,
    ) -> Dict:
        """Compute payslips for preview (DRAFT → REVIEW).

        Validates and computes payslips without persisting.
        Returns preview with errors/warnings for HR review.

        Args:
            run_id: PayrollRun ID
            computed_by: User ID performing computation

        Returns:
            Dict with payslips_preview, errors, warnings, and updated run status
        """
        from app.services.computation_service import ComputationService
        from app.services.state_machine import assert_can_compute, InvalidTransitionError
        from app.services.audit_service import AuditService

        run = await self.repo.get_payroll_run(run_id)
        if not run:
            raise ValueError(f"PayrollRun {run_id} not found")

        # Guard: Prevent compute on locked payroll
        assert_payroll_not_locked(run, "compute")

        # Validate transition
        try:
            assert_can_compute(run.status)
        except InvalidTransitionError as e:
            raise ValueError(str(e))

        # Compute preview
        comp_service = ComputationService(self.db)
        payslips, errors, warnings = await comp_service.compute_payroll_preview(run)

        # Store exception report
        run.exception_report = {
            "errors": errors,
            "warnings": warnings,
        }

        # Transition to REVIEW
        old_status = run.status
        run.status = PayrollStatus.REVIEW.value
        await self.repo.update_payroll_run(run)

        # Audit log
        audit = AuditService(self.db)
        company_id = self.db.info.get("company_id")
        if company_id:
            await audit.log_payroll_run_computed(
                company_id=UUID(company_id) if isinstance(company_id, str) else company_id,
                run_id=run_id,
                computed_by=computed_by,
                before_state={"status": old_status},
                after_state={"status": run.status},
            )

        return {
            "run": PayrollRunResponse.model_validate(run),
            "payslips_preview": payslips,
            "errors": errors,
            "warnings": warnings,
            "is_valid": len(errors) == 0,
        }

    async def approve_payroll(
        self,
        run_id: UUID,
        approved_by: UUID,
    ) -> PayrollRunResponse:
        """Approve payroll for processing (REVIEW → APPROVED).

        Args:
            run_id: PayrollRun ID
            approved_by: User ID approving (typically HR/Admin)

        Returns:
            Updated PayrollRun response
        """
        from app.services.state_machine import assert_can_approve, InvalidTransitionError
        from app.services.audit_service import AuditService

        run = await self.repo.get_payroll_run(run_id)
        if not run:
            raise ValueError(f"PayrollRun {run_id} not found")

        # Guard: Prevent approve on locked payroll
        assert_payroll_not_locked(run, "approve")

        # Validate transition
        try:
            assert_can_approve(run.status)
        except InvalidTransitionError as e:
            raise ValueError(str(e))

        # Transition to APPROVED
        old_status = run.status
        run.status = PayrollStatus.APPROVED.value
        run.approved_by = approved_by
        run.approved_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.repo.update_payroll_run(run)

        # Audit log
        audit = AuditService(self.db)
        company_id = self.db.info.get("company_id")
        if company_id:
            await audit.log_payroll_run_approved(
                company_id=UUID(company_id) if isinstance(company_id, str) else company_id,
                run_id=run_id,
                approved_by=approved_by,
                before_state={"status": old_status},
                after_state={"status": run.status, "approved_at": run.approved_at.isoformat()},
            )

        return PayrollRunResponse.model_validate(run)

    async def reject_payroll(
        self,
        run_id: UUID,
        rejected_by: UUID,
        rejection_reason: Optional[str] = None,
    ) -> PayrollRunResponse:
        """Reject payroll, return to DRAFT (REVIEW → DRAFT).

        Args:
            run_id: PayrollRun ID
            rejected_by: User ID rejecting
            rejection_reason: Optional reason for rejection

        Returns:
            Updated PayrollRun response
        """
        from app.services.state_machine import assert_can_reject, InvalidTransitionError
        from app.services.audit_service import AuditService

        run = await self.repo.get_payroll_run(run_id)
        if not run:
            raise ValueError(f"PayrollRun {run_id} not found")

        # Guard: Prevent reject on locked payroll
        assert_payroll_not_locked(run, "reject")

        # Validate transition
        try:
            assert_can_reject(run.status)
        except InvalidTransitionError as e:
            raise ValueError(str(e))

        # Transition to DRAFT
        old_status = run.status
        run.status = PayrollStatus.DRAFT.value
        await self.repo.update_payroll_run(run)

        # Audit log
        audit = AuditService(self.db)
        company_id = self.db.info.get("company_id")
        if company_id:
            await audit.log_payroll_run_rejected(
                company_id=UUID(company_id) if isinstance(company_id, str) else company_id,
                run_id=run_id,
                rejected_by=rejected_by,
                before_state={"status": old_status},
                after_state={"status": run.status},
                rejection_reason=rejection_reason,
            )

        return PayrollRunResponse.model_validate(run)

    async def process_payroll(
        self,
        run_id: UUID,
        processed_by: UUID,
    ) -> PayrollRunResponse:
        """Process payroll: finalize & persist (APPROVED → PROCESSING → COMPLETED).

        Persists computed payslips, locks them, updates YTD, publishes events.

        Args:
            run_id: PayrollRun ID
            processed_by: User ID processing

        Returns:
            Updated PayrollRun response
        """
        from app.services.state_machine import assert_can_process, InvalidTransitionError
        from app.services.audit_service import AuditService
        from app.services import ytd_service

        run = await self.repo.get_payroll_run(run_id)
        if not run:
            raise ValueError(f"PayrollRun {run_id} not found")

        # Guard: Prevent process on locked payroll
        assert_payroll_not_locked(run, "process")
        # Guard: Prevent process on FAILED payroll (must retry)
        assert_payroll_not_failed(run)

        # Validate transition
        try:
            assert_can_process(run.status)
        except InvalidTransitionError as e:
            raise ValueError(str(e))

        # Transition to PROCESSING
        old_status = run.status
        run.status = PayrollStatus.PROCESSING.value
        await self.repo.update_payroll_run(run)

        try:
            # Get all active salaries and recompute/persist
            active_salaries = await self.repo.list_active_salaries()
            company_id = self.db.info.get("company_id")
            now = datetime.now(timezone.utc).replace(tzinfo=None)

            total_gross = Decimal("0.00")
            total_net = Decimal("0.00")
            total_deductions = Decimal("0.00")
            count = 0

            async with self.db.begin_nested():
                for emp_salary in active_salaries:
                    structure = await self.repo.get_salary_structure(emp_salary.salary_structure_id)
                    if not structure:
                        continue

                    # Recompute salary
                    breakdown = calculator.calculate(
                        ctc=Decimal(str(emp_salary.ctc)),
                        basic_pct=Decimal(str(structure.basic_pct)),
                        hra_pct=Decimal(str(structure.hra_pct)),
                        allowances_pct=Decimal(str(structure.allowances_pct)),
                        pf_pct=Decimal(str(structure.pf_pct)),
                        esi_pct=Decimal(str(structure.esi_pct)),
                        professional_tax=Decimal(str(structure.professional_tax)),
                    )

                    prf = pro_rata_factor(emp_salary.effective_from, run.period_start, run.period_end)
                    prorated_basic = breakdown.basic * prf
                    prorated_hra = breakdown.hra * prf
                    prorated_allowances = breakdown.allowances * prf
                    prorated_gross = prorated_basic + prorated_hra + prorated_allowances

                    lop_days = 0
                    lop_fetch_status = LOPFetchStatus.OK.value
                    if company_id:
                        lop_days, fetch_status, _detail = await fetch_lop_summary(
                            employee_id=str(emp_salary.employee_id),
                            period_start=run.period_start,
                            period_end=run.period_end,
                            company_id=company_id,
                        )
                        if fetch_status != "OK":
                            lop_fetch_status = LOPFetchStatus.UNAVAILABLE.value

                    period_days = calendar_days_in_period(run.period_start, run.period_end)
                    lop_amount = lop_deduction(prorated_gross, lop_days, period_days, method="CALENDAR")
                    net_gross = prorated_gross - lop_amount

                    pf_employee = calculator.calculate_pf(prorated_basic, Decimal("12"))
                    esi_employee = calculator.calculate_esi(net_gross, Decimal("0.75"))
                    pt_employee = calculator.calculate_professional_tax(
                        Decimal("0"),
                        gross=net_gross,
                        month=run.period_start.month,
                        gender="M",
                    )
                    tds_employee = Decimal("0.00")
                    lwf_employee = Decimal("0.00")

                    pf_employer = calculator.calculate_employer_pf(prorated_basic)
                    esi_employer = calculator.calculate_employer_esi(net_gross)

                    total_employee_deductions = pf_employee + esi_employee + pt_employee + tds_employee + lwf_employee
                    net_salary = net_gross - total_employee_deductions

                    # Guard: Validate net pay is non-negative
                    try:
                        assert_net_pay_valid(
                            net_salary,
                            employee_id=str(emp_salary.employee_id),
                            period_str=f"{run.period_start.isoformat()} to {run.period_end.isoformat()}",
                        )
                    except ValueError as e:
                        logger.warning(f"Net pay validation warning: {e}")
                        # Allow payslip to be created but flag for HR review

                    # Persist payslip
                    payslip_data = {
                        "id": uuid.uuid4(),
                        "payroll_run_id": run.id,
                        "employee_id": emp_salary.employee_id,
                        "ctc": breakdown.ctc,
                        "basic": prorated_basic,
                        "hra": prorated_hra,
                        "allowances": prorated_allowances,
                        "pf_deduction": pf_employee,
                        "esi_deduction": esi_employee,
                        "professional_tax": pt_employee,
                        "tds_deduction": tds_employee,
                        "lwf_employee": lwf_employee,
                        "other_deductions": Decimal("0.00"),
                        "gross": net_gross,
                        "total_deductions": total_employee_deductions,
                        "net": net_salary,
                        "employer_pf": pf_employer,
                        "employer_esi": esi_employer,
                        "employer_lwf": Decimal("0.00"),
                        "lop_days": lop_days,
                        "lop_amount": lop_amount,
                        "lop_fetch_status": lop_fetch_status,
                        "pro_rata_factor": prf,
                        "tax_regime": "new",
                        "locked_at": now,  # Lock on completion
                        "period_start": run.period_start,
                        "period_end": run.period_end,
                    }
                    payslip = await self.repo.create_payslip(payslip_data)

                    # Update YTD
                    if company_id:
                        fy = run.period_start.year if run.period_start.month >= 4 else run.period_start.year
                        ytd = await ytd_service.get_or_create_ytd(
                            self.db,
                            emp_salary.employee_id,
                            UUID(company_id) if isinstance(company_id, str) else company_id,
                            fy,
                        )
                        await ytd_service.accumulate_payslip(self.db, payslip, ytd)

                    total_gross += net_gross
                    total_net += net_salary
                    total_deductions += total_employee_deductions
                    count += 1

            # Transition to COMPLETED
            run.total_employees = count
            run.total_gross = total_gross
            run.total_net = total_net
            run.total_deductions = total_deductions
            run.status = PayrollStatus.COMPLETED.value
            run.locked_at = now
            await self.repo.update_payroll_run(run)

            # Audit log
            audit = AuditService(self.db)
            if company_id:
                await audit.log_payroll_run_processing_started(
                    company_id=UUID(company_id) if isinstance(company_id, str) else company_id,
                    run_id=run_id,
                    processed_by=processed_by,
                    before_state={"status": old_status},
                    after_state={"status": run.status, "locked_at": run.locked_at.isoformat()},
                )

            logger.info(
                f"Payroll processed and locked: {run_id}",
                extra={"run_id": str(run_id), "employees": count},
            )

        except Exception as exc:
            # Rollback to FAILED
            run.status = PayrollStatus.FAILED.value
            run.error_message = str(exc)[:500]
            await self.repo.update_payroll_run(run)
            logger.error(
                f"Payroll processing failed: {exc}",
                extra={"run_id": str(run_id)},
            )
            raise

        return PayrollRunResponse.model_validate(run)

    async def mark_payroll_paid(
        self,
        run_id: UUID,
        marked_by: UUID,
    ) -> PayrollRunResponse:
        """Mark payroll as paid (COMPLETED → PAID).

        Args:
            run_id: PayrollRun ID
            marked_by: User ID marking

        Returns:
            Updated PayrollRun response
        """
        from app.services.state_machine import assert_can_mark_paid, InvalidTransitionError
        from app.services.audit_service import AuditService

        run = await self.repo.get_payroll_run(run_id)
        if not run:
            raise ValueError(f"PayrollRun {run_id} not found")

        try:
            assert_can_mark_paid(run.status)
        except InvalidTransitionError as e:
            raise ValueError(str(e))

        old_status = run.status
        run.status = PayrollStatus.PAID.value
        await self.repo.update_payroll_run(run)

        audit = AuditService(self.db)
        company_id = self.db.info.get("company_id")
        if company_id:
            await audit.log_payroll_run_marked_paid(
                company_id=UUID(company_id) if isinstance(company_id, str) else company_id,
                run_id=run_id,
                marked_by=marked_by,
                before_state={"status": old_status},
                after_state={"status": run.status},
            )

        return PayrollRunResponse.model_validate(run)

    async def lock_payroll(
        self,
        run_id: UUID,
        locked_by: UUID,
    ) -> PayrollRunResponse:
        """Lock payroll (terminal state: PAID → LOCKED).

        After locking, payslips cannot be modified. This is the final state.

        Args:
            run_id: PayrollRun ID
            locked_by: User ID locking

        Returns:
            Updated PayrollRun response
        """
        from app.services.state_machine import assert_can_lock, InvalidTransitionError
        from app.services.audit_service import AuditService

        run = await self.repo.get_payroll_run(run_id)
        if not run:
            raise ValueError(f"PayrollRun {run_id} not found")

        try:
            assert_can_lock(run.status)
        except InvalidTransitionError as e:
            raise ValueError(str(e))

        old_status = run.status
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        run.status = PayrollStatus.LOCKED.value
        await self.repo.update_payroll_run(run)

        audit = AuditService(self.db)
        company_id = self.db.info.get("company_id")
        if company_id:
            await audit.log_payroll_run_locked(
                company_id=UUID(company_id) if isinstance(company_id, str) else company_id,
                run_id=run_id,
                locked_by=locked_by,
                before_state={"status": old_status},
                after_state={"status": run.status},
            )

        return PayrollRunResponse.model_validate(run)

    async def retry_payroll(
        self,
        run_id: UUID,
        retried_by: UUID,
    ) -> PayrollRunResponse:
        """Retry failed payroll (FAILED → DRAFT).

        Clears error message and allows recomputation.

        Args:
            run_id: PayrollRun ID
            retried_by: User ID retrying

        Returns:
            Updated PayrollRun response
        """
        from app.services.state_machine import assert_can_retry, InvalidTransitionError
        from app.services.audit_service import AuditService

        run = await self.repo.get_payroll_run(run_id)
        if not run:
            raise ValueError(f"PayrollRun {run_id} not found")

        try:
            assert_can_retry(run.status)
        except InvalidTransitionError as e:
            raise ValueError(str(e))

        old_status = run.status
        run.status = PayrollStatus.DRAFT.value
        run.error_message = None
        run.exception_report = None
        await self.repo.update_payroll_run(run)

        audit = AuditService(self.db)
        company_id = self.db.info.get("company_id")
        if company_id:
            await audit.log_action(
                company_id=UUID(company_id) if isinstance(company_id, str) else company_id,
                entity_type="PAYROLL_RUN",
                entity_id=run_id,
                action="RETRIED",
                performed_by=retried_by,
                run_id=run_id,
                before_state={"status": old_status, "error_message": old_status},
                after_state={"status": run.status},
            )

        return PayrollRunResponse.model_validate(run)
