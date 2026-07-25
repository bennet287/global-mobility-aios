"""External agency assignment SLA tracking.

Revision ID: 0052_external_agency_assignment_sla
Revises: 0051_authority_submission_checklist
Create Date: 2026-07-24
"""

from alembic import op
import sqlalchemy as sa


revision = "0052_external_agency_assignment_sla"
down_revision = "0051_authority_submission_checklist"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "external_agencies",
        sa.Column(
            "sla_due_hours",
            sa.Integer(),
            nullable=False,
            server_default="72",
        ),
    )
    op.create_index("ix_external_agencies_sla_due_hours", "external_agencies", ["sla_due_hours"])

    op.add_column(
        "external_agency_assignments",
        sa.Column("sla_due_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "external_agency_assignments",
        sa.Column(
            "sla_status",
            sa.String(),
            nullable=False,
            server_default="on_track",
        ),
    )
    op.add_column(
        "external_agency_assignments",
        sa.Column("sla_breached_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_external_agency_assignments_sla_due_at",
        "external_agency_assignments",
        ["sla_due_at"],
    )
    op.create_index(
        "ix_external_agency_assignments_sla_status",
        "external_agency_assignments",
        ["sla_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_external_agency_assignments_sla_status", table_name="external_agency_assignments")
    op.drop_index("ix_external_agency_assignments_sla_due_at", table_name="external_agency_assignments")
    op.drop_column("external_agency_assignments", "sla_breached_at")
    op.drop_column("external_agency_assignments", "sla_status")
    op.drop_column("external_agency_assignments", "sla_due_at")

    op.drop_index("ix_external_agencies_sla_due_hours", table_name="external_agencies")
    op.drop_column("external_agencies", "sla_due_hours")
