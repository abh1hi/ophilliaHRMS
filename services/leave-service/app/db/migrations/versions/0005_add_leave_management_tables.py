"""Add leave management tables: periods, holiday lists, policies, allocations, ledger, etc.

Revision ID: 0005_add_leave_management_tables
Revises: 0004_leave_approval_cid
Create Date: 2026-04-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_add_leave_management_tables"
down_revision = "0004_leave_approval_cid"
branch_labels = None
depends_on = None

UUID = postgresql.UUID


def upgrade() -> None:
    # ── LeaveType extended columns ────────────────────────────────────────────
    op.add_column("leave_types", sa.Column("is_carry_forward", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("leave_types", sa.Column("is_leave_without_pay", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("leave_types", sa.Column("is_compensatory", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("leave_types", sa.Column("is_optional_leave", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("leave_types", sa.Column("allow_negative_balance", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("leave_types", sa.Column("allow_over_allocation", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("leave_types", sa.Column("include_holidays_in_leaves", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("leave_types", sa.Column("is_partially_paid", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("leave_types", sa.Column("fraction_of_daily_salary", sa.Float(), nullable=True))
    op.add_column("leave_types", sa.Column("is_earned_leave", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("leave_types", sa.Column("earned_leave_frequency", sa.String(20), nullable=True))
    op.add_column("leave_types", sa.Column("allow_encashment", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("leave_types", sa.Column("non_encashable_leaves", sa.Float(), nullable=True, server_default="0"))
    op.add_column("leave_types", sa.Column("max_consecutive_days", sa.Integer(), nullable=True))
    op.add_column("leave_types", sa.Column("applicable_after_working_days", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("leave_types", sa.Column("max_leaves_allowed", sa.Float(), nullable=True))

    # ── leave_periods ─────────────────────────────────────────────────────────
    op.create_table(
        "leave_periods",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("from_date", sa.Date(), nullable=False),
        sa.Column("to_date", sa.Date(), nullable=False),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("optional_holiday_list_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # ── holiday_lists ─────────────────────────────────────────────────────────
    op.create_table(
        "holiday_lists",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("from_date", sa.Date(), nullable=False),
        sa.Column("to_date", sa.Date(), nullable=False),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "holiday_list_entries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("holiday_list_id", UUID(as_uuid=True), sa.ForeignKey("holiday_lists.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_holiday_list_entries_list_id", "holiday_list_entries", ["holiday_list_id"])

    # ── holiday_list_assignments ───────────────────────────────────────────────
    op.create_table(
        "holiday_list_assignments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("applicable_for", sa.String(20), nullable=False),
        sa.Column("employee_id", UUID(as_uuid=True), nullable=True),
        sa.Column("holiday_list_id", UUID(as_uuid=True), sa.ForeignKey("holiday_lists.id"), nullable=False),
        sa.Column("assignment_from", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # ── leave_policies ────────────────────────────────────────────────────────
    op.create_table(
        "leave_policies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "leave_policy_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("policy_id", UUID(as_uuid=True), sa.ForeignKey("leave_policies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("leave_type_id", UUID(as_uuid=True), nullable=False),
        sa.Column("annual_allocation", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_leave_policy_items_policy_id", "leave_policy_items", ["policy_id"])

    # ── leave_policy_assignments ──────────────────────────────────────────────
    op.create_table(
        "leave_policy_assignments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("employee_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("policy_id", UUID(as_uuid=True), sa.ForeignKey("leave_policies.id"), nullable=False),
        sa.Column("leave_period_id", UUID(as_uuid=True), nullable=True),
        sa.Column("assignment_based_on", sa.String(50), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # ── leave_allocations ─────────────────────────────────────────────────────
    op.create_table(
        "leave_allocations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("employee_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("leave_type_id", UUID(as_uuid=True), nullable=False),
        sa.Column("assignment_id", UUID(as_uuid=True), sa.ForeignKey("leave_policy_assignments.id"), nullable=True),
        sa.Column("leave_period_id", UUID(as_uuid=True), nullable=True),
        sa.Column("from_date", sa.Date(), nullable=False),
        sa.Column("to_date", sa.Date(), nullable=False),
        sa.Column("new_leaves_allocated", sa.Float(), nullable=False, server_default="0"),
        sa.Column("carry_forward_days", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total_leaves_allocated", sa.Float(), nullable=False, server_default="0"),
        sa.Column("used_leaves", sa.Float(), nullable=False, server_default="0"),
        sa.Column("leaves_pending_approval", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_leave_allocations_employee_type", "leave_allocations", ["company_id", "employee_id", "leave_type_id"])

    # ── leave_adjustments ─────────────────────────────────────────────────────
    op.create_table(
        "leave_adjustments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("employee_id", UUID(as_uuid=True), nullable=False),
        sa.Column("allocation_id", UUID(as_uuid=True), sa.ForeignKey("leave_allocations.id"), nullable=False),
        sa.Column("adjustment_type", sa.String(20), nullable=False),
        sa.Column("adjustment_days", sa.Float(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("adjusted_by", UUID(as_uuid=True), nullable=True),
        sa.Column("adjustment_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # ── leave_block_lists ─────────────────────────────────────────────────────
    op.create_table(
        "leave_block_lists",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("applies_to_company", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "leave_block_list_dates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("block_list_id", UUID(as_uuid=True), sa.ForeignKey("leave_block_lists.id", ondelete="CASCADE"), nullable=False),
        sa.Column("block_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_leave_block_list_dates_list_id", "leave_block_list_dates", ["block_list_id"])

    op.create_table(
        "leave_block_list_allowed",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("block_list_id", UUID(as_uuid=True), sa.ForeignKey("leave_block_lists.id", ondelete="CASCADE"), nullable=False),
        sa.Column("approver_employee_id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # ── compensatory_leave_requests ───────────────────────────────────────────
    op.create_table(
        "compensatory_leave_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("employee_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("leave_type_id", UUID(as_uuid=True), nullable=False),
        sa.Column("work_from_date", sa.Date(), nullable=False),
        sa.Column("work_end_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("leave_allocation_id", UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_by", UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_note", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # ── leave_encashments ─────────────────────────────────────────────────────
    op.create_table(
        "leave_encashments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("employee_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("leave_type_id", UUID(as_uuid=True), nullable=False),
        sa.Column("leave_period_id", UUID(as_uuid=True), nullable=True),
        sa.Column("leave_allocation_id", UUID(as_uuid=True), nullable=True),
        sa.Column("leave_balance", sa.Float(), nullable=False, server_default="0"),
        sa.Column("encashable_days", sa.Float(), nullable=False, server_default="0"),
        sa.Column("encashment_amount", sa.Float(), nullable=True),
        sa.Column("encashment_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="submitted"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # ── leave_ledger_entries ──────────────────────────────────────────────────
    op.create_table(
        "leave_ledger_entries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("employee_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("leave_type_id", UUID(as_uuid=True), nullable=False),
        sa.Column("from_date", sa.Date(), nullable=False),
        sa.Column("to_date", sa.Date(), nullable=False),
        sa.Column("leaves", sa.Float(), nullable=False),
        sa.Column("transaction_type", sa.String(30), nullable=False),
        sa.Column("transaction_name", sa.String(200), nullable=True),
        sa.Column("is_carry_forward", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_expired", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_lwp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("holiday_list_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_leave_ledger_employee_type", "leave_ledger_entries", ["company_id", "employee_id", "leave_type_id"])


def downgrade() -> None:
    op.drop_table("leave_ledger_entries")
    op.drop_table("leave_encashments")
    op.drop_table("compensatory_leave_requests")
    op.drop_table("leave_block_list_allowed")
    op.drop_table("leave_block_list_dates")
    op.drop_table("leave_block_lists")
    op.drop_table("leave_adjustments")
    op.drop_index("ix_leave_allocations_employee_type", table_name="leave_allocations")
    op.drop_table("leave_allocations")
    op.drop_table("leave_policy_assignments")
    op.drop_index("ix_leave_policy_items_policy_id", table_name="leave_policy_items")
    op.drop_table("leave_policy_items")
    op.drop_table("leave_policies")
    op.drop_table("holiday_list_assignments")
    op.drop_index("ix_holiday_list_entries_list_id", table_name="holiday_list_entries")
    op.drop_table("holiday_list_entries")
    op.drop_table("holiday_lists")
    op.drop_table("leave_periods")

    # Remove extended columns from leave_types
    for col in [
        "is_carry_forward", "is_leave_without_pay", "is_compensatory", "is_optional_leave",
        "allow_negative_balance", "allow_over_allocation", "include_holidays_in_leaves",
        "is_partially_paid", "fraction_of_daily_salary", "is_earned_leave",
        "earned_leave_frequency", "allow_encashment", "non_encashable_leaves",
        "max_consecutive_days", "applicable_after_working_days", "max_leaves_allowed",
    ]:
        op.drop_column("leave_types", col)
