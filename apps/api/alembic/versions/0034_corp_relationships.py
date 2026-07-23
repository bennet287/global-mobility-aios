"""Corporate sponsor, dependant, and compliance relationships.

Revision ID: 0034_corp_relationships
Revises: 0033_corporate_mobility_foundation
Create Date: 2026-07-23
"""
from alembic import op
import sqlalchemy as sa


revision = "0034_corp_relationships"
down_revision = "0033_corporate_mobility_foundation"
branch_labels = None
depends_on = None


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("updated_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    ]


def _indexes(table: str, columns: tuple[str, ...]) -> None:
    for column in columns:
        op.create_index(f"ix_{table}_{column}", table, [column])


def upgrade() -> None:
    op.create_table(
        "corporate_sponsor_entities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("corporate_account_id", sa.Uuid(), nullable=False),
        sa.Column("legal_name", sa.String(), nullable=False),
        sa.Column("sponsor_type", sa.String(), nullable=False),
        sa.Column("country", sa.String(), nullable=False),
        sa.Column("registration_number", sa.String(), nullable=True),
        sa.Column("contact_name", sa.String(), nullable=True),
        sa.Column("contact_email", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["corporate_account_id"], ["corporate_accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _indexes("corporate_sponsor_entities", (
        "id", "corporate_account_id", "legal_name", "sponsor_type", "country",
        "registration_number", "contact_email", "status", "created_by", "updated_by", "created_at",
    ))

    op.create_table(
        "corporate_case_sponsor_assignments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("corporate_mobility_case_id", sa.Uuid(), nullable=False),
        sa.Column("sponsor_entity_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["corporate_mobility_case_id"], ["corporate_mobility_cases.id"]),
        sa.ForeignKeyConstraint(["sponsor_entity_id"], ["corporate_sponsor_entities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_corp_case_sponsor_case_id",
        "corporate_case_sponsor_assignments",
        ["corporate_mobility_case_id"],
    )
    _indexes("corporate_case_sponsor_assignments", (
        "id", "sponsor_entity_id", "status", "created_by", "updated_by", "created_at",
    ))

    op.create_table(
        "corporate_case_dependants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("corporate_mobility_case_id", sa.Uuid(), nullable=False),
        sa.Column("dependant_lead_id", sa.Uuid(), nullable=False),
        sa.Column("relationship_to_employee", sa.String(), nullable=False),
        sa.Column("sponsorship_required", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["corporate_mobility_case_id"], ["corporate_mobility_cases.id"]),
        sa.ForeignKeyConstraint(["dependant_lead_id"], ["leads.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _indexes("corporate_case_dependants", (
        "id", "corporate_mobility_case_id", "dependant_lead_id", "relationship_to_employee",
        "status", "created_by", "updated_by", "created_at",
    ))

    op.create_table(
        "corporate_compliance_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("corporate_mobility_case_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("due_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("evidence_required", sa.Boolean(), nullable=False),
        sa.Column("human_review_required", sa.Boolean(), nullable=False),
        sa.Column("completion_notes", sa.String(), nullable=True),
        sa.Column("completed_by", sa.String(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["corporate_mobility_case_id"], ["corporate_mobility_cases.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _indexes("corporate_compliance_events", (
        "id", "corporate_mobility_case_id", "event_type", "due_at", "status", "completed_by",
        "completed_at", "created_by", "updated_by", "created_at",
    ))


def downgrade() -> None:
    for table in (
        "corporate_compliance_events", "corporate_case_dependants",
        "corporate_case_sponsor_assignments", "corporate_sponsor_entities",
    ):
        op.drop_table(table)
