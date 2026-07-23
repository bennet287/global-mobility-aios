"""Corporate account and mobility-case foundation.

Revision ID: 0033_corporate_mobility_foundation
Revises: 0032_initial_rule_assertions
Create Date: 2026-07-23
"""
from alembic import op
import sqlalchemy as sa


revision = "0033_corporate_mobility_foundation"
down_revision = "0032_initial_rule_assertions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "corporate_accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("legal_name", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=True),
        sa.Column("account_status", sa.String(), nullable=False),
        sa.Column("primary_country", sa.String(), nullable=False),
        sa.Column("registration_number", sa.String(), nullable=True),
        sa.Column("contact_name", sa.String(), nullable=True),
        sa.Column("contact_email", sa.String(), nullable=True),
        sa.Column("compliance_owner", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("updated_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "id", "legal_name", "account_status", "primary_country", "registration_number",
        "contact_email", "created_by", "updated_by", "created_at",
    ):
        op.create_index(f"ix_corporate_accounts_{column}", "corporate_accounts", [column])

    op.create_table(
        "corporate_mobility_cases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("corporate_account_id", sa.Uuid(), nullable=False),
        sa.Column("employee_lead_id", sa.Uuid(), nullable=True),
        sa.Column("case_reference", sa.String(), nullable=False),
        sa.Column("case_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("origin_country", sa.String(), nullable=True),
        sa.Column("destination_country", sa.String(), nullable=False),
        sa.Column("sponsor_name", sa.String(), nullable=True),
        sa.Column("target_start_date", sa.DateTime(), nullable=True),
        sa.Column("compliance_due_date", sa.DateTime(), nullable=True),
        sa.Column("human_review_required", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("updated_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["corporate_account_id"], ["corporate_accounts.id"]),
        sa.ForeignKeyConstraint(["employee_lead_id"], ["leads.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_corporate_mobility_cases_case_reference", "corporate_mobility_cases", ["case_reference"], unique=True)
    for column in (
        "id", "corporate_account_id", "employee_lead_id", "case_type", "status",
        "origin_country", "destination_country", "target_start_date", "compliance_due_date",
        "created_by", "updated_by", "created_at",
    ):
        op.create_index(f"ix_corporate_mobility_cases_{column}", "corporate_mobility_cases", [column])


def downgrade() -> None:
    for column in (
        "created_at", "updated_by", "created_by", "compliance_due_date", "target_start_date",
        "destination_country", "origin_country", "status", "case_type", "employee_lead_id",
        "corporate_account_id", "id",
    ):
        op.drop_index(f"ix_corporate_mobility_cases_{column}", table_name="corporate_mobility_cases")
    op.drop_index("ix_corporate_mobility_cases_case_reference", table_name="corporate_mobility_cases")
    op.drop_table("corporate_mobility_cases")

    for column in (
        "created_at", "updated_by", "created_by", "contact_email", "registration_number",
        "primary_country", "account_status", "legal_name", "id",
    ):
        op.drop_index(f"ix_corporate_accounts_{column}", table_name="corporate_accounts")
    op.drop_table("corporate_accounts")

