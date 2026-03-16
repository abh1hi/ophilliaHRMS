"""Expand employee table with full HR profile fields

Revision ID: 0003_expand_employee_fields
Revises: 0002_multi_tenancy
Create Date: 2026-03-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0003_expand_employee_fields"
down_revision = "0002_multi_tenancy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Address ──────────────────────────────────────────────────────────
    op.add_column("employees", sa.Column("door_no", sa.String(50), nullable=True))
    op.add_column("employees", sa.Column("street", sa.String(200), nullable=True))
    op.add_column("employees", sa.Column("village_town", sa.String(150), nullable=True))
    op.add_column("employees", sa.Column("pin_code", sa.String(10), nullable=True))

    # ── Contact ───────────────────────────────────────────────────────────
    op.add_column("employees", sa.Column("phone_2", sa.String(20), nullable=True))
    op.add_column("employees", sa.Column("personal_email", sa.String(255), nullable=True))

    # ── Government IDs ────────────────────────────────────────────────────
    op.add_column("employees", sa.Column("driving_license_number", sa.String(50), nullable=True))
    op.add_column("employees", sa.Column("aadhaar_number", sa.String(12), nullable=True))
    op.add_column("employees", sa.Column("uan_number", sa.String(12), nullable=True))
    op.add_column("employees", sa.Column("esi_number", sa.String(17), nullable=True))
    op.add_column("employees", sa.Column("pan_number", sa.String(10), nullable=True))

    # ── Banking ───────────────────────────────────────────────────────────
    op.add_column("employees", sa.Column("bank_account_number", sa.String(30), nullable=True))
    op.add_column("employees", sa.Column("bank_name", sa.String(150), nullable=True))
    op.add_column("employees", sa.Column("bank_branch", sa.String(150), nullable=True))
    op.add_column("employees", sa.Column("ifsc_code", sa.String(11), nullable=True))

    # ── Emergency Contact ─────────────────────────────────────────────────
    op.add_column("employees", sa.Column("emergency_contact_name", sa.String(150), nullable=True))
    op.add_column("employees", sa.Column("emergency_contact_number", sa.String(20), nullable=True))
    op.add_column("employees", sa.Column("emergency_contact_relation", sa.String(100), nullable=True))

    # ── Education ─────────────────────────────────────────────────────────
    op.add_column("employees", sa.Column("highest_qualification", sa.String(200), nullable=True))
    op.add_column("employees", sa.Column("year_of_passing", sa.String(4), nullable=True))
    op.add_column("employees", sa.Column("percentage", sa.String(10), nullable=True))
    op.add_column("employees", sa.Column("institute_name", sa.String(300), nullable=True))

    # ── Work History ──────────────────────────────────────────────────────
    op.add_column("employees", sa.Column("last_firm_name", sa.String(300), nullable=True))
    op.add_column("employees", sa.Column("years_of_experience", sa.String(10), nullable=True))
    op.add_column("employees", sa.Column("last_designation", sa.String(100), nullable=True))
    op.add_column("employees", sa.Column("last_drawn_salary", sa.Numeric(12, 2), nullable=True))
    op.add_column("employees", sa.Column("reason_to_quit", sa.Text, nullable=True))
    op.add_column("employees", sa.Column("referred_by", sa.String(200), nullable=True))

    # ── Health ────────────────────────────────────────────────────────────
    op.add_column("employees", sa.Column("health_issues", sa.Text, nullable=True))
    op.add_column("employees", sa.Column("allergies", sa.Text, nullable=True))

    # ── Job Info ──────────────────────────────────────────────────────────
    op.add_column("employees", sa.Column("project", sa.String(200), nullable=True))
    op.add_column("employees", sa.Column("joining_salary", sa.Numeric(12, 2), nullable=True))
    op.add_column("employees", sa.Column("role", sa.String(50), nullable=True))

    # ── File Uploads ──────────────────────────────────────────────────────
    op.add_column("employees", sa.Column("staff_photo_url", sa.String(500), nullable=True))
    op.add_column("employees", sa.Column("staff_documents_urls", sa.Text, nullable=True))


def downgrade() -> None:
    # File Uploads
    op.drop_column("employees", "staff_documents_urls")
    op.drop_column("employees", "staff_photo_url")

    # Job Info
    op.drop_column("employees", "role")
    op.drop_column("employees", "joining_salary")
    op.drop_column("employees", "project")

    # Health
    op.drop_column("employees", "allergies")
    op.drop_column("employees", "health_issues")

    # Work History
    op.drop_column("employees", "referred_by")
    op.drop_column("employees", "reason_to_quit")
    op.drop_column("employees", "last_drawn_salary")
    op.drop_column("employees", "last_designation")
    op.drop_column("employees", "years_of_experience")
    op.drop_column("employees", "last_firm_name")

    # Education
    op.drop_column("employees", "institute_name")
    op.drop_column("employees", "percentage")
    op.drop_column("employees", "year_of_passing")
    op.drop_column("employees", "highest_qualification")

    # Emergency Contact
    op.drop_column("employees", "emergency_contact_relation")
    op.drop_column("employees", "emergency_contact_number")
    op.drop_column("employees", "emergency_contact_name")

    # Banking
    op.drop_column("employees", "ifsc_code")
    op.drop_column("employees", "bank_branch")
    op.drop_column("employees", "bank_name")
    op.drop_column("employees", "bank_account_number")

    # Government IDs
    op.drop_column("employees", "pan_number")
    op.drop_column("employees", "esi_number")
    op.drop_column("employees", "uan_number")
    op.drop_column("employees", "aadhaar_number")
    op.drop_column("employees", "driving_license_number")

    # Contact
    op.drop_column("employees", "personal_email")
    op.drop_column("employees", "phone_2")

    # Address
    op.drop_column("employees", "pin_code")
    op.drop_column("employees", "village_town")
    op.drop_column("employees", "street")
    op.drop_column("employees", "door_no")
