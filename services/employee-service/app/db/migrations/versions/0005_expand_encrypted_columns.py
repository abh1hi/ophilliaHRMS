"""Expand encrypted columns to accommodate AES-256-GCM ciphertext

The EncryptedString type produces base64(12-byte nonce + ciphertext + 16-byte tag),
which is ~56+ chars even for short plaintext. The original column sizes (VARCHAR 10-30)
are too small for encrypted values.

Revision ID: 0005_expand_encrypted_cols
Revises: 0004_dept_is_active
Create Date: 2026-03-26
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_expand_encrypted_cols"
down_revision = "0004_dept_is_active"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # All columns that use EncryptedString() need at least VARCHAR(512)
    op.alter_column(
        "employees", "aadhaar_number",
        type_=sa.String(512), existing_type=sa.String(12), existing_nullable=True,
    )
    op.alter_column(
        "employees", "pan_number",
        type_=sa.String(512), existing_type=sa.String(10), existing_nullable=True,
    )
    op.alter_column(
        "employees", "uan_number",
        type_=sa.String(512), existing_type=sa.String(12), existing_nullable=True,
    )
    op.alter_column(
        "employees", "esi_number",
        type_=sa.String(512), existing_type=sa.String(17), existing_nullable=True,
    )
    op.alter_column(
        "employees", "driving_license_number",
        type_=sa.String(512), existing_type=sa.String(50), existing_nullable=True,
    )
    op.alter_column(
        "employees", "bank_account_number",
        type_=sa.String(512), existing_type=sa.String(30), existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "employees", "bank_account_number",
        type_=sa.String(30), existing_type=sa.String(512), existing_nullable=True,
    )
    op.alter_column(
        "employees", "driving_license_number",
        type_=sa.String(50), existing_type=sa.String(512), existing_nullable=True,
    )
    op.alter_column(
        "employees", "esi_number",
        type_=sa.String(17), existing_type=sa.String(512), existing_nullable=True,
    )
    op.alter_column(
        "employees", "uan_number",
        type_=sa.String(12), existing_type=sa.String(512), existing_nullable=True,
    )
    op.alter_column(
        "employees", "pan_number",
        type_=sa.String(10), existing_type=sa.String(512), existing_nullable=True,
    )
    op.alter_column(
        "employees", "aadhaar_number",
        type_=sa.String(12), existing_type=sa.String(512), existing_nullable=True,
    )
