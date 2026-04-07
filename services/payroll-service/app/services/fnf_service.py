"""Full & Final Settlement (FNF) Service.

Handles exit payroll calculations for employee separation:
- Pro-rated final salary for partial month
- Gratuity (₹20L private sector exemption, ₹10L public sector)
- Leave encashment (earned balance × basic/26, ₹25L exemption on exit)
- Outstanding loan recovery
- Final tax calculation (Section 192, pro-rata standard deduction)
- Form 16 for partial financial year
"""
import logging
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Dict, Any, Optional, List
from uuid import UUID
from dataclasses import dataclass, asdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import TaxRegime, PayrollStatus, AdjustmentDirection, AdjustmentType
from app.models.payroll import Payslip, PayrollRun, EmployeeYTD, EmployeeSalary, SalaryStructure
from app.repositories.payroll_repository import PayrollRepository
from app.services.tax.india.tds import compute_annual_tax_new_regime, round_to_nearest_ten
from app.services.form16_service import Form16Service
from app.services.loan_service import LoanService

logger = logging.getLogger(__name__)


@dataclass
class GratuityComponent:
    """Gratuity calculation breakdown."""
    eligible: bool  # >= 5 years service
    years_of_service: Decimal
    last_basic_da: Decimal
    gratuity_amount: Decimal
    exempt_amount: Decimal  # ₹20L for private, ₹10L for public
    taxable_amount: Decimal
    note: str


@dataclass
class LeaveEncashmentComponent:
    """Leave encashment calculation breakdown."""
    earned_leave_balance: int  # days
    basic_per_day: Decimal
    encashment_amount: Decimal
    exempt_amount: Decimal  # ₹25L on exit (new rule, Section 10(10)(AA))
    taxable_amount: Decimal
    note: str


@dataclass
class LoanRecoveryComponent:
    """Loan recovery summary."""
    loan_id: UUID
    loan_type: str
    principal: Decimal
    outstanding: Decimal
    recovery_amount: Decimal  # min(outstanding, available_fnf)
    note: str


@dataclass
class FNFSummary:
    """Complete Full & Final Settlement summary."""
    employee_id: UUID
    employee_name: str
    last_working_day: date
    years_of_service: Decimal
    service_end_date: date

    # Salary components
    final_salary_pro_rata: Decimal  # final month pro-rated
    gratuity: GratuityComponent
    leave_encashment: LeaveEncashmentComponent

    # Tax calculation (partial year)
    ytd_gross_to_lwd: Decimal  # YTD including final salary
    final_year_tax_liability: Decimal  # Full year tax at current CTC
    final_year_taxable_income: Decimal
    tds_deducted_so_far: Decimal
    final_tds_adjustment: Decimal  # TDS to deduct from FNF
    standard_deduction_prorata: Decimal  # Pro-rata standard deduction

    # Deductions & recoveries
    regular_deductions_final: Decimal  # PF, ESI, PT, LWF
    loan_recoveries: List[LoanRecoveryComponent]
    total_loan_recovery: Decimal

    # Final settlement
    gross_fnf: Decimal  # final salary + gratuity + encashment
    total_deductions_fnf: Decimal  # regular deductions + loan recovery + FNF TDS
    net_fnf: Decimal  # amount payable to employee

    # Validation & flags
    net_fnf_negative: bool  # flag if net < 0 (needs manual intervention)
    available_for_loan_recovery: Decimal  # amount available for loan deduction
    loan_recovery_shortfall: Decimal  # unrecovered loan amount
    warnings: List[str]


class FNFService:
    """Service for computing Full & Final Settlement payroll."""

    def __init__(self, db: AsyncSession = None):
        """Initialize FNF service with database session.

        Args:
            db: AsyncSession for database operations (optional for unit tests)
        """
        self.db = db
        self.repo = PayrollRepository(db) if db else None
        self.loan_service = LoanService(db) if db else None
        self.form16_service = Form16Service(db) if db else None

    def calculate_gratuity(self, basic_da: Decimal, years: Decimal) -> Decimal:
        """Calculate gratuity: (basic+DA) × (15/26) × years.

        India statutory rules:
        - Minimum service: 5 years
        - Private sector exemption: ₹20L (Section 10(10)(ii))
        - Formula: (last_basic_da × 15/26) × years_of_service

        Args:
            basic_da: Basic + Dearness Allowance
            years: Years of completed service

        Returns:
            Gratuity amount (₹0 if < 5 years)
        """
        if years < Decimal("5"):
            return Decimal("0.00")
        gratuity = (basic_da * Decimal("15") / Decimal("26") * years).quantize(Decimal("0.01"))
        return gratuity

    def calculate_leave_encashment(self, basic_da: Decimal, earned_days: int) -> Decimal:
        """Calculate leave encashment: earned_days × (basic/26).

        India statutory rules:
        - Earned leave valuation: basic_salary / 26 per day
        - Exit exemption: ₹25L (Section 10(10)(AA))

        Args:
            basic_da: Basic salary
            earned_days: Number of earned leave days

        Returns:
            Leave encashment amount
        """
        if earned_days <= 0:
            return Decimal("0.00")
        encashment = (Decimal(earned_days) * basic_da / Decimal("26")).quantize(Decimal("0.01"))
        return encashment

    def calculate_pro_rata_factor(self, last_working_day: date, period_start: date, period_end: date) -> Decimal:
        """Calculate pro-rata factor for partial month.

        Pro-rata = days_worked / calendar_days_in_period (inclusive)

        Args:
            last_working_day: Employee's last working day
            period_start: Pay period start date
            period_end: Pay period end date

        Returns:
            Pro-rata factor (0.0 to 1.0)
        """
        if last_working_day >= period_end:
            return Decimal("1.0")
        if last_working_day < period_start:
            return Decimal("0.0")

        # Days worked inclusive of both start and end
        days_worked = (last_working_day - period_start).days + 1
        total_days = (period_end - period_start).days + 1

        factor = (Decimal(days_worked) / Decimal(total_days)).quantize(Decimal("0.0001"))
        return factor

    def apply_pro_rata(self, monthly_gross: Decimal, factor: Decimal) -> Decimal:
        """Apply pro-rata factor to gross salary.

        Args:
            monthly_gross: Full month gross salary
            factor: Pro-rata factor (0.0 to 1.0)

        Returns:
            Pro-rated gross salary
        """
        prorated = (monthly_gross * factor).quantize(Decimal("0.01"))
        return prorated

    def calculate_final_month_tds(self, annual_gross: Decimal, std_deduction: Decimal) -> Decimal:
        """Calculate TDS for final month (Section 288B rounded).

        Applies progressive slab taxation with 4% cess, rounded to nearest ₹10.

        Args:
            annual_gross: Total gross for partial financial year
            std_deduction: Standard deduction (₹75K for new regime)

        Returns:
            Final month TDS amount (rounded to nearest ₹10)
        """
        taxable = max(Decimal("0"), annual_gross - std_deduction)
        annual_tax = compute_annual_tax_new_regime(taxable)
        with_cess = (annual_tax * Decimal("1.04")).quantize(Decimal("0.01"))
        tds_rounded = round_to_nearest_ten(with_cess)
        return tds_rounded

    async def compute_fnf(
        self,
        employee_id: UUID,
        company_id: UUID,
        last_working_day: date,
        joining_date: date,
    ) -> FNFSummary:
        """Compute Full & Final Settlement for an employee.

        Args:
            employee_id: UUID of employee exiting
            company_id: Company UUID
            last_working_day: Last day of employment
            joining_date: Joining date (for gratuity eligibility)

        Returns:
            FNFSummary with all calculations and components

        Raises:
            ValueError: If employee not found or invalid dates
        """
        # Get employee and current salary structure
        employee_salary = await self.repo.get_employee_salary(employee_id, company_id)
        if not employee_salary:
            raise ValueError(f"Employee {employee_id} not found in company {company_id}")

        employee = employee_salary.employee
        if not employee:
            raise ValueError(f"Employee record not found for {employee_id}")

        salary_structure = employee_salary.salary_structure
        if not salary_structure:
            raise ValueError(f"No active salary structure for {employee_id}")

        # Calculate years of service (for gratuity)
        years_of_service = self._calculate_years_of_service(joining_date, last_working_day)

        # Get YTD data for current FY (up to LWD)
        fy = last_working_day.year if last_working_day.month >= 4 else last_working_day.year - 1
        ytd = await self.repo.get_employee_ytd(employee_id, fy)

        # Get active loans for recovery
        active_loans = await self.loan_service.get_active_loans_for_employee(employee_id, company_id)

        # ── Pro-rated Final Salary ──────────────────────────────────────────
        # Calculate for the partial month (joining_date to last_working_day)
        period_start = date(last_working_day.year, last_working_day.month, 1)
        period_end = last_working_day

        # Basic salary + DA from structure
        basic_monthly = salary_structure.basic
        dearness_allowance = salary_structure.dearness_allowance or Decimal("0")
        hra_monthly = salary_structure.hra or Decimal("0")
        allowances_monthly = salary_structure.allowances or Decimal("0")

        # Pro-rata factor (days worked / calendar days in month)
        from app.services.attendance_integration import pro_rata_factor
        prf = pro_rata_factor(period_start, period_start, period_end)

        final_gross = (basic_monthly + dearness_allowance + hra_monthly + allowances_monthly) * prf
        final_salary_pro_rata = final_gross

        logger.info(
            f"FNF: Employee {employee_id} final salary pro-rata {final_salary_pro_rata}",
            extra={"employee_id": str(employee_id), "pro_rata_factor": str(prf)},
        )

        # ── Gratuity Calculation ────────────────────────────────────────────
        # Private sector: (Last basic+DA × 15/26 × years of service), exempt ₹20L
        # Public sector: Similar, exempt ₹10L
        # Eligibility: >= 5 years continuous service

        gratuity_eligible = years_of_service >= Decimal("5")
        gratuity_amount = Decimal("0")
        gratuity_taxable = Decimal("0")

        if gratuity_eligible:
            last_basic_da = basic_monthly + dearness_allowance
            # 15/26 is daily wage formula for 26-day month
            gratuity_gross = last_basic_da * (Decimal("15") / Decimal("26")) * years_of_service
            gratuity_gross = gratuity_gross.quantize(Decimal("0.01"))

            # Private sector exemption (default ₹20L), public ₹10L
            exempt_limit = Decimal("2000000")  # ₹20 lakh private sector
            gratuity_taxable = max(Decimal("0"), gratuity_gross - exempt_limit)
            gratuity_amount = gratuity_gross

        gratuity_component = GratuityComponent(
            eligible=gratuity_eligible,
            years_of_service=years_of_service,
            last_basic_da=basic_monthly + dearness_allowance,
            gratuity_amount=gratuity_amount,
            exempt_amount=gratuity_amount - gratuity_taxable,
            taxable_amount=gratuity_taxable,
            note=f"Gratuity for {years_of_service.quantize(Decimal('0.01'))} years of service; ₹20L exemption applied (private sector)"
            if gratuity_eligible
            else "No gratuity: < 5 years service",
        )

        logger.info(
            f"FNF: Gratuity {gratuity_amount} (taxable: {gratuity_taxable})",
            extra={"employee_id": str(employee_id), "gratuity": str(gratuity_amount)},
        )

        # ── Leave Encashment ────────────────────────────────────────────────
        # Earned leave balance × (basic / 26)
        # Exempt up to ₹25L on exit (Section 10(10)(AA), new rule FY 2023-24)

        # TODO: Integrate with leave-service to fetch earned_leave_balance
        earned_leave_balance = 0  # Placeholder — fetch from leave-service
        basic_per_day = basic_monthly / Decimal("26")
        encashment_gross = basic_per_day * Decimal(str(earned_leave_balance))
        encashment_gross = encashment_gross.quantize(Decimal("0.01"))

        exempt_limit_encashment = Decimal("2500000")  # ₹25 lakh
        encashment_taxable = max(Decimal("0"), encashment_gross - exempt_limit_encashment)

        leave_encashment_component = LeaveEncashmentComponent(
            earned_leave_balance=earned_leave_balance,
            basic_per_day=basic_per_day,
            encashment_amount=encashment_gross,
            exempt_amount=encashment_gross - encashment_taxable,
            taxable_amount=encashment_taxable,
            note=f"Leave encashment for {earned_leave_balance} earned days @ ₹{basic_per_day}/day; ₹25L exemption applied",
        )

        logger.info(
            f"FNF: Leave encashment {encashment_gross} (taxable: {encashment_taxable})",
            extra={"employee_id": str(employee_id), "encashment": str(encashment_gross)},
        )

        # ── YTD Gross (Including Final Salary) ───────────────────────────────
        ytd_gross_so_far = ytd.ytd_gross if ytd else Decimal("0")
        ytd_gross_to_lwd = ytd_gross_so_far + final_salary_pro_rata

        # Taxable income for partial year FNF
        # Gratuity + encashment taxable amounts added
        taxable_gross_fnf = final_salary_pro_rata + gratuity_taxable + encashment_taxable

        # ── Final Tax Calculation (Partial Year) ─────────────────────────────
        # Pro-rata standard deduction based on months worked
        months_worked = self._months_worked_in_fy(joining_date, last_working_day)
        standard_deduction_full_year = Decimal("75000")
        standard_deduction_prorata = (standard_deduction_full_year / Decimal("12")) * Decimal(str(months_worked))
        standard_deduction_prorata = standard_deduction_prorata.quantize(Decimal("0.01"))

        # Taxable income for final FY
        final_year_taxable = taxable_gross_fnf - standard_deduction_prorata
        final_year_taxable = max(Decimal("0"), final_year_taxable)

        # Tax liability for full year (with 4% cess + Section 288B rounding)
        from app.services.tax.india.tds import apply_cess
        annual_tax_liability = compute_annual_tax_new_regime(final_year_taxable)
        annual_tax_with_cess = apply_cess(annual_tax_liability)
        # CRITICAL FIX: Section 288B rounding (round to nearest ₹10)
        annual_tax_liability = round_to_nearest_ten(annual_tax_with_cess)

        # TDS deducted so far (from YTD)
        tds_deducted = ytd.ytd_tds if ytd else Decimal("0")

        # Final TDS adjustment (balance to be deducted from FNF)
        final_tds_adjustment = max(Decimal("0"), annual_tax_liability - tds_deducted)
        final_tds_adjustment = final_tds_adjustment.quantize(Decimal("0.01"))

        logger.info(
            f"FNF: Tax liability {annual_tax_liability}, TDS deducted {tds_deducted}, final adjustment {final_tds_adjustment}",
            extra={
                "employee_id": str(employee_id),
                "tax_liability": str(annual_tax_liability),
                "tds_deducted": str(tds_deducted),
            },
        )

        # ── Regular Deductions (Final Month) ────────────────────────────────
        pf_deduction_final = (basic_monthly * Decimal("0.12")) * prf  # 12% employee PF
        pf_deduction_final = pf_deduction_final.quantize(Decimal("0.01"))

        esi_threshold = Decimal("21000")
        if final_gross <= esi_threshold:
            esi_deduction_final = (final_gross * Decimal("0.0075")).quantize(Decimal("0.01"))
        else:
            esi_deduction_final = Decimal("0")

        # PT and LWF similarly calculated
        pt_deduction_final = Decimal("200") * prf  # Placeholder: MH flat ₹200, pro-rated
        pt_deduction_final = pt_deduction_final.quantize(Decimal("0.01"))

        lwf_deduction_final = Decimal("0")  # Placeholder: state-wise

        regular_deductions_final = pf_deduction_final + esi_deduction_final + pt_deduction_final + lwf_deduction_final

        logger.info(
            f"FNF: Regular deductions {regular_deductions_final} (PF: {pf_deduction_final}, ESI: {esi_deduction_final})",
            extra={"employee_id": str(employee_id), "deductions": str(regular_deductions_final)},
        )

        # ── Loan Recovery ───────────────────────────────────────────────────
        loan_recovery_components: List[LoanRecoveryComponent] = []
        total_loan_recovery = Decimal("0")
        available_for_recovery = final_salary_pro_rata - regular_deductions_final - final_tds_adjustment

        for loan in active_loans:
            recovery_amt = min(Decimal(str(loan.outstanding)), available_for_recovery - total_loan_recovery)
            if recovery_amt > 0:
                total_loan_recovery += recovery_amt
                loan_recovery_components.append(
                    LoanRecoveryComponent(
                        loan_id=loan.id,
                        loan_type=loan.loan_type,
                        principal=Decimal(str(loan.principal)),
                        outstanding=Decimal(str(loan.outstanding)),
                        recovery_amount=recovery_amt,
                        note=f"Loan {loan.id}: ₹{loan.outstanding} outstanding, recovering ₹{recovery_amt}",
                    )
                )

        loan_recovery_shortfall = sum(Decimal(str(loan.outstanding)) for loan in active_loans) - total_loan_recovery

        logger.info(
            f"FNF: Loan recovery ₹{total_loan_recovery}, shortfall ₹{loan_recovery_shortfall}",
            extra={"employee_id": str(employee_id), "total_recovery": str(total_loan_recovery)},
        )

        # ── Final Settlement Amounts ────────────────────────────────────────
        gross_fnf = final_salary_pro_rata + gratuity_amount + encashment_gross
        gross_fnf = gross_fnf.quantize(Decimal("0.01"))

        total_deductions_fnf = (
            regular_deductions_final + final_tds_adjustment + total_loan_recovery
        ).quantize(Decimal("0.01"))

        net_fnf = gross_fnf - total_deductions_fnf
        net_fnf = net_fnf.quantize(Decimal("0.01"))

        net_fnf_negative = net_fnf < Decimal("0")
        available_for_loan_recovery = gross_fnf - regular_deductions_final - final_tds_adjustment
        available_for_loan_recovery = max(Decimal("0"), available_for_loan_recovery)

        logger.info(
            f"FNF: Gross {gross_fnf}, deductions {total_deductions_fnf}, net {net_fnf}",
            extra={"employee_id": str(employee_id), "net_fnf": str(net_fnf)},
        )

        # ── Warnings ────────────────────────────────────────────────────────
        warnings: List[str] = []
        if net_fnf_negative:
            warnings.append(
                f"⚠ Net FNF is NEGATIVE: ₹{abs(net_fnf)}. Total deductions exceed gross. "
                "Manual HR review required; recovery may not be possible."
            )
        if loan_recovery_shortfall > Decimal("0"):
            warnings.append(
                f"⚠ Loan recovery shortfall: ₹{loan_recovery_shortfall} unrecovered. "
                "Employee owes this amount; follow up post-exit."
            )
        if earned_leave_balance > 0 and encashment_gross == Decimal("0"):
            warnings.append(
                f"⚠ Employee has {earned_leave_balance} earned leave days but encashment is ₹0. "
                "Verify basic salary or leave-service integration."
            )
        if gratuity_eligible and years_of_service < Decimal("5.5"):
            warnings.append(
                f"⚠ Gratuity eligibility marginal: {years_of_service} years (5+ required). Verify exact dates."
            )

        # ── Build Summary ───────────────────────────────────────────────────
        summary = FNFSummary(
            employee_id=employee_id,
            employee_name=employee.full_name or employee.first_name or "N/A",
            last_working_day=last_working_day,
            years_of_service=years_of_service,
            service_end_date=last_working_day,
            final_salary_pro_rata=final_salary_pro_rata,
            gratuity=gratuity_component,
            leave_encashment=leave_encashment_component,
            ytd_gross_to_lwd=ytd_gross_to_lwd,
            final_year_tax_liability=annual_tax_liability,
            final_year_taxable_income=final_year_taxable,
            tds_deducted_so_far=tds_deducted,
            final_tds_adjustment=final_tds_adjustment,
            standard_deduction_prorata=standard_deduction_prorata,
            regular_deductions_final=regular_deductions_final,
            loan_recoveries=loan_recovery_components,
            total_loan_recovery=total_loan_recovery,
            gross_fnf=gross_fnf,
            total_deductions_fnf=total_deductions_fnf,
            net_fnf=net_fnf,
            net_fnf_negative=net_fnf_negative,
            available_for_loan_recovery=available_for_loan_recovery,
            loan_recovery_shortfall=loan_recovery_shortfall,
            warnings=warnings,
        )

        logger.info(
            f"FNF computation complete for {employee_id}",
            extra={"employee_id": str(employee_id), "net_fnf": str(net_fnf), "warnings": len(warnings)},
        )

        return summary

    async def create_fnf_payroll_run(
        self,
        company_id: UUID,
        employee_id: UUID,
        last_working_day: date,
        joining_date: date,
        approved_by: UUID,
    ) -> tuple[PayrollRun, FNFSummary]:
        """Create and process FNF payroll run for an employee.

        Args:
            company_id: Company UUID
            employee_id: Employee UUID
            last_working_day: Last day of employment
            joining_date: Employee joining date
            approved_by: UUID of approver

        Returns:
            Tuple of (PayrollRun, FNFSummary)
        """
        # Compute FNF
        fnf_summary = await self.compute_fnf(employee_id, company_id, last_working_day, joining_date)

        # Create FNF payroll run
        period_start = date(last_working_day.year, last_working_day.month, 1)
        period_end = last_working_day

        payroll_run = PayrollRun(
            id=str(uuid.uuid4()),
            company_id=str(company_id),
            period_start=period_start,
            period_end=period_end,
            run_type="FNF",
            status=PayrollStatus.COMPLETED.value,
            approved_by=str(approved_by),
            approved_at=datetime.now(timezone.utc),
            locked_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        self.db.add(payroll_run)

        # Create FNF payslip
        payslip = Payslip(
            id=str(uuid.uuid4()),
            payroll_run_id=str(payroll_run.id),
            company_id=str(company_id),
            employee_id=str(employee_id),
            period_start=period_start,
            period_end=period_end,
            basic=fnf_summary.final_salary_pro_rata * Decimal("0.4"),  # Approx 40% basic
            hra=fnf_summary.final_salary_pro_rata * Decimal("0.2"),  # Approx 20% HRA
            allowances=fnf_summary.final_salary_pro_rata * Decimal("0.4"),  # Remainder
            gross=fnf_summary.final_salary_pro_rata,
            pf_deduction=Decimal("0"),  # No PF on FNF
            esi_deduction=Decimal("0"),  # No ESI on FNF
            professional_tax=Decimal("0"),
            tds_deduction=fnf_summary.final_tds_adjustment,
            lwf_employee=Decimal("0"),
            total_deductions=fnf_summary.final_tds_adjustment + fnf_summary.total_loan_recovery,
            net=fnf_summary.net_fnf,
            employer_pf=Decimal("0"),
            employer_esi=Decimal("0"),
            lwf_employer=Decimal("0"),
            pro_rata_factor=Decimal("1.0"),
            lop_days=0,
            lop_amount=Decimal("0"),
            lop_fetch_status="SKIPPED",  # No LOP in FNF
            tax_regime="new",
            snapshot={
                # ── Guard: Snapshot Schema Versioning ───────────────────────
                "schema_version": "2026-04-v1",
                "version": 1,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                # ────────────────────────────────────────────────────────────
                "fnf_type": "full_and_final",
                "final_salary_pro_rata": str(fnf_summary.final_salary_pro_rata),
                "gratuity": str(fnf_summary.gratuity.gratuity_amount),
                "leave_encashment": str(fnf_summary.leave_encashment.encashment_amount),
                "gross_fnf": str(fnf_summary.gross_fnf),
                "net_fnf": str(fnf_summary.net_fnf),
            },
            locked_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        self.db.add(payslip)

        # Mark loans as CLOSED
        for loan_component in fnf_summary.loan_recoveries:
            loan = await self.loan_service.get_loan(loan_component.loan_id)
            if loan:
                loan.status = "CLOSED"
                loan.closed_at = datetime.now(timezone.utc)
                self.db.add(loan)

        await self.db.commit()

        logger.info(
            f"FNF payroll run created: {payroll_run.id}",
            extra={
                "company_id": str(company_id),
                "employee_id": str(employee_id),
                "run_id": str(payroll_run.id),
            },
        )

        return payroll_run, fnf_summary

    @staticmethod
    def _calculate_years_of_service(joining_date: date, last_working_day: date) -> Decimal:
        """Calculate years of service between joining and exit.

        Args:
            joining_date: Date joined
            last_working_day: Last day of employment

        Returns:
            Years of service (decimal, e.g., 5.25 for 5 years 3 months)
        """
        days_worked = (last_working_day - joining_date).days
        years = Decimal(str(days_worked)) / Decimal("365.25")
        return years.quantize(Decimal("0.01"))

    @staticmethod
    def _months_worked_in_fy(joining_date: date, last_working_day: date) -> int:
        """Calculate full months worked in current financial year.

        Args:
            joining_date: Joining date
            last_working_day: Last day worked

        Returns:
            Number of full months in FY (1-12)
        """
        # FY = April 1 - March 31
        fy_start = date(last_working_day.year if last_working_day.month >= 4 else last_working_day.year - 1, 4, 1)
        fy_end = last_working_day

        months = (fy_end.year - fy_start.year) * 12 + (fy_end.month - fy_start.month) + 1
        return max(1, min(12, months))
