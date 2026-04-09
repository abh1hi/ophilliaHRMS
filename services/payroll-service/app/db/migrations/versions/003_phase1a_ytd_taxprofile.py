"""Phase 1A: YTD, Tax Profile, Adjustments, Loans, and Audit Trail

Revision ID: 0003_phase1a
Revises: 0002_add_tenant_isolation
Create Date: 2026-04-07

Creates:
  - employee_tax_profiles (tax regime, investment declarations)
  - employee_ytd (year-to-date accumulation per financial year)
  - payroll_adjustments (one-time adjustments: bonus, arrears, etc.)
  - payroll_loans (salary advances and loans)
  - payroll_audit_logs (immutable audit trail)

Modifies:
  - payroll_runs: add run_type, idempotency_key, approval workflow, exception_report
  - payslips: add employer contributions, TDS, LOP, tax regime, immutability
"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from alembic import op

revision: str = "0003_phase1a"
down_revision: Union[str, None] = "0002_add_tenant_isolation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── employee_tax_profiles ────────────────────────────────────────────
    op.create_table(
        "employee_tax_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", UUID(as_uuid=True), nullable=False),
        sa.Column("financial_year", sa.Integer, nullable=False),
        sa.Column("tax_regime", sa.String(10), nullable=False, server_default="new"),
        sa.Column("investment_80c", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("investment_80d", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("hra_rent_paid", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("is_metro_city", sa.Boolean, nullable=False, server_default="False"),
        sa.Column("nps_voluntary", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("declared_at", sa.DateTime, nullable=True),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_employee_tax_profiles_company_id", "employee_tax_profiles", ["company_id"])
    op.create_index("ix_employee_tax_profiles_employee_id", "employee_tax_profiles", ["employee_id"])
    op.create_unique_constraint(
        "uq_employee_tax_profile_fy",
        "employee_tax_profiles",
        ["company_id", "employee_id", "financial_year"],
    )

    # ── employee_ytd ────────────────────────────────────────────────────
    op.create_table(
        "employee_ytd",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", UUID(as_uuid=True), nullable=False),
        sa.Column("financial_year", sa.Integer, nullable=False),
        sa.Column("ytd_gross", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("ytd_basic", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("ytd_hra", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("ytd_pf_employee", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("ytd_pf_employer", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("ytd_esi_employee", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("ytd_esi_employer", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("ytd_professional_tax", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("ytd_lwf_employee", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("ytd_tds", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("ytd_lop_days", sa.Integer, nullable=False, server_default="0"),
        sa.Column("ytd_bonus", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("ytd_arrears", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_employee_ytd_company_id", "employee_ytd", ["company_id"])
    op.create_index("ix_employee_ytd_employee_id", "employee_ytd", ["employee_id"])
    op.create_index("ix_employee_ytd_fy", "employee_ytd", ["financial_year"])
    op.create_unique_constraint(
        "uq_employee_ytd_fy",
        "employee_ytd",
        ["company_id", "employee_id", "financial_year"],
    )

    # ── payroll_adjustments ──────────────────────────────────────────────
    op.create_table(
        "payroll_adjustments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("payroll_run_id", UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", UUID(as_uuid=True), nullable=False),
        sa.Column("adjustment_type", sa.String(30), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("direction", sa.String(6), nullable=False, server_default="CREDIT"),
        sa.Column("taxable", sa.Boolean, nullable=False, server_default="True"),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("period_ref_start", sa.Date, nullable=True),
        sa.Column("period_ref_end", sa.Date, nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_payroll_adjustments_company_id", "payroll_adjustments", ["company_id"])
    op.create_index("ix_payroll_adjustments_run_id", "payroll_adjustments", ["payroll_run_id"])
    op.create_index("ix_payroll_adjustments_employee_id", "payroll_adjustments", ["employee_id"])

    # ── payroll_loans ───────────────────────────────────────────────────
    op.create_table(
        "payroll_loans",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", UUID(as_uuid=True), nullable=False),
        sa.Column("loan_type", sa.String(20), nullable=False),
        sa.Column("principal", sa.Numeric(12, 2), nullable=False),
        sa.Column("outstanding", sa.Numeric(12, 2), nullable=False),
        sa.Column("emi_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("start_month", sa.String(7), nullable=False),
        sa.Column("end_month", sa.String(7), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("closed_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_payroll_loans_company_id", "payroll_loans", ["company_id"])
    op.create_index("ix_payroll_loans_employee_id", "payroll_loans", ["employee_id"])
    op.create_index("ix_payroll_loans_status", "payroll_loans", ["status"])

    # ── payroll_audit_logs ──────────────────────────────────────────────
    op.create_table(
        "payroll_audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", UUID(as_uuid=True), nullable=True),
        sa.Column("payslip_id", UUID(as_uuid=True), nullable=True),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("performed_by", UUID(as_uuid=True), nullable=False),
        sa.Column("performed_at", sa.DateTime, nullable=False),
        sa.Column("before_state", JSONB, nullable=True),
        sa.Column("after_state", JSONB, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(255), nullable=True),
    )
    op.create_index("ix_payroll_audit_logs_company_id", "payroll_audit_logs", ["company_id"])
    op.create_index("ix_payroll_audit_logs_run_id", "payroll_audit_logs", ["run_id"])
    op.create_index("ix_payroll_audit_logs_entity", "payroll_audit_logs", ["company_id", "entity_type", "entity_id"])

    # ── Modify payroll_runs ──────────────────────────────────────────────
    # Add new columns
    op.add_column("payroll_runs", sa.Column("run_type", sa.String(20), nullable=False, server_default="REGULAR"))
    op.add_column("payroll_runs", sa.Column("idempotency_key", sa.String(64), nullable=True))
    op.add_column("payroll_runs", sa.Column("idempotency_endpoint", sa.String(100), nullable=True))
    op.add_column("payroll_runs", sa.Column("idempotency_expires_at", sa.DateTime, nullable=True))
    op.add_column("payroll_runs", sa.Column("approved_by", UUID(as_uuid=True), nullable=True))
    op.add_column("payroll_runs", sa.Column("approved_at", sa.DateTime, nullable=True))
    op.add_column("payroll_runs", sa.Column("locked_at", sa.DateTime, nullable=True))
    op.add_column("payroll_runs", sa.Column("exception_report", JSONB, nullable=True))

    # Drop old unique constraint and create new one (with run_type)
    op.drop_constraint("uq_payroll_run_company_period", "payroll_runs", type_="unique")
    op.create_unique_constraint(
        "uq_payroll_run_company_period_type",
        "payroll_runs",
        ["company_id", "period_start", "period_end", "run_type"],
    )

    # CRITICAL FIX: Scoped idempotency key (company_id, key, endpoint)
    # Prevents same key from being reused across different endpoints
    op.create_index(
        "ix_payroll_runs_idempotency",
        "payroll_runs",
        ["company_id", "idempotency_key", "idempotency_endpoint"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),  # Only index when key is present
    )

    # ── Modify payslips ──────────────────────────────────────────────────
    # Add new columns
    op.add_column("payslips", sa.Column("employer_pf", sa.Numeric(10, 2), nullable=False, server_default="0"))
    op.add_column("payslips", sa.Column("employer_esi", sa.Numeric(10, 2), nullable=False, server_default="0"))
    op.add_column("payslips", sa.Column("employer_lwf", sa.Numeric(8, 2), nullable=False, server_default="0"))
    op.add_column("payslips", sa.Column("tds_deduction", sa.Numeric(10, 2), nullable=False, server_default="0"))
    op.add_column("payslips", sa.Column("lwf_employee", sa.Numeric(8, 2), nullable=False, server_default="0"))
    op.add_column("payslips", sa.Column("lop_days", sa.Integer, nullable=False, server_default="0"))
    op.add_column("payslips", sa.Column("lop_amount", sa.Numeric(10, 2), nullable=False, server_default="0"))
    op.add_column("payslips", sa.Column("lop_fetch_status", sa.String(20), nullable=False, server_default="OK"))
    op.add_column("payslips", sa.Column("pro_rata_factor", sa.Numeric(5, 4), nullable=False, server_default="1.0000"))
    op.add_column("payslips", sa.Column("tax_regime", sa.String(10), nullable=False, server_default="new"))
    op.add_column("payslips", sa.Column("snapshot", JSONB, nullable=True))
    op.add_column("payslips", sa.Column("locked_at", sa.DateTime, nullable=True))
    op.add_column("payslips", sa.Column("updated_at", sa.DateTime, nullable=True))
    op.add_column("payslips", sa.Column("pdf_data", sa.Text, nullable=True))  # base64 encoded PDF
    op.add_column("payslips", sa.Column("pdf_generated_at", sa.DateTime, nullable=True))

    # Add index for locked payslips
    op.create_index("ix_payslips_locked", "payslips", ["locked_at"])

    # ── Create prevent_locked_payslip_update trigger ──────────────────────
    # CRITICAL FIX: Allow updates to pdf_data and pdf_generated_at even when locked
    # Only financial data (gross, net, deductions, etc.) is immutable
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_locked_payslip_update()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF OLD.locked_at IS NOT NULL THEN
            -- Allow updates to pdf_data and pdf_generated_at (for async PDF worker)
            -- Block updates to all financial fields
            IF (OLD.basic IS DISTINCT FROM NEW.basic OR
                OLD.hra IS DISTINCT FROM NEW.hra OR
                OLD.allowances IS DISTINCT FROM NEW.allowances OR
                OLD.gross IS DISTINCT FROM NEW.gross OR
                OLD.pf_deduction IS DISTINCT FROM NEW.pf_deduction OR
                OLD.esi_deduction IS DISTINCT FROM NEW.esi_deduction OR
                OLD.professional_tax IS DISTINCT FROM NEW.professional_tax OR
                OLD.tds_deduction IS DISTINCT FROM NEW.tds_deduction OR
                OLD.lwf_employee IS DISTINCT FROM NEW.lwf_employee OR
                OLD.total_deductions IS DISTINCT FROM NEW.total_deductions OR
                OLD.net IS DISTINCT FROM NEW.net OR
                OLD.employer_pf IS DISTINCT FROM NEW.employer_pf OR
                OLD.employer_esi IS DISTINCT FROM NEW.employer_esi OR
                OLD.lop_days IS DISTINCT FROM NEW.lop_days OR
                OLD.lop_amount IS DISTINCT FROM NEW.lop_amount OR
                OLD.snapshot IS DISTINCT FROM NEW.snapshot) THEN
              RAISE EXCEPTION 'payslip % is locked; financial data cannot be modified', OLD.id;
            END IF;
          END IF;
          RETURN NEW;
        END;
        $$;
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_prevent_locked_payslip_update
          BEFORE UPDATE OR DELETE ON payslips
          FOR EACH ROW EXECUTE FUNCTION prevent_locked_payslip_update();
        """
    )


def downgrade() -> None:
    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS trg_prevent_locked_payslip_update ON payslips")
    op.execute("DROP FUNCTION IF EXISTS prevent_locked_payslip_update()")

    # Remove new indexes from payslips
    op.drop_index("ix_payslips_locked", "payslips")

    # Remove new columns from payslips
    op.drop_column("payslips", "pdf_generated_at")
    op.drop_column("payslips", "pdf_data")
    op.drop_column("payslips", "updated_at")
    op.drop_column("payslips", "locked_at")
    op.drop_column("payslips", "snapshot")
    op.drop_column("payslips", "tax_regime")
    op.drop_column("payslips", "pro_rata_factor")
    op.drop_column("payslips", "lop_fetch_status")
    op.drop_column("payslips", "lop_amount")
    op.drop_column("payslips", "lop_days")
    op.drop_column("payslips", "lwf_employee")
    op.drop_column("payslips", "tds_deduction")
    op.drop_column("payslips", "employer_lwf")
    op.drop_column("payslips", "employer_esi")
    op.drop_column("payslips", "employer_pf")

    # Restore old unique constraint on payroll_runs and remove new one
    op.drop_index("ix_payroll_runs_idempotency", "payroll_runs")
    op.drop_constraint("uq_payroll_run_company_period_type", "payroll_runs", type_="unique")
    op.create_unique_constraint(
        "uq_payroll_run_company_period",
        "payroll_runs",
        ["company_id", "period_start", "period_end"],
    )

    # Remove new columns from payroll_runs
    op.drop_column("payroll_runs", "exception_report")
    op.drop_column("payroll_runs", "locked_at")
    op.drop_column("payroll_runs", "approved_at")
    op.drop_column("payroll_runs", "approved_by")
    op.drop_column("payroll_runs", "idempotency_expires_at")
    op.drop_column("payroll_runs", "idempotency_endpoint")
    op.drop_column("payroll_runs", "idempotency_key")
    op.drop_column("payroll_runs", "run_type")

    # Drop new tables
    op.drop_table("payroll_audit_logs")
    op.drop_table("payroll_loans")
    op.drop_table("payroll_adjustments")
    op.drop_table("employee_ytd")
    op.drop_table("employee_tax_profiles")
