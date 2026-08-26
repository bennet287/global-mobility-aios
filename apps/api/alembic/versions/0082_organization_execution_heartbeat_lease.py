"""Add durable AIOS execution-checkpoint heartbeat leases.

Revision ID: 0082_organization_execution_heartbeat_lease
Revises: 0081_capability_autonomy_evidence_evaluation_policy
Create Date: 2026-08-26
"""

from alembic import op
import sqlalchemy as sa


revision = "0082_organization_execution_heartbeat_lease"
down_revision = "0081_capability_autonomy_evidence_evaluation_policy"
branch_labels = None
depends_on = None


def _uuid() -> sa.Uuid:
    return sa.Uuid()


def upgrade() -> None:
    op.create_table(
        "organization_execution_heartbeats",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("heartbeat_key", sa.String(), nullable=False),
        sa.Column("tenant_key", sa.String(), nullable=False),
        sa.Column("position_key", sa.String(), nullable=False),
        sa.Column("work_item_id", _uuid(), nullable=False),
        sa.Column("execution_attempt_id", _uuid(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("checkpoint", sa.String(), nullable=False),
        sa.Column("writer", sa.String(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fresh_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "sequence >= 1",
            name="ck_org_execution_heartbeat_sequence_positive",
        ),
        sa.CheckConstraint(
            "fresh_until > observed_at",
            name="ck_org_execution_heartbeat_fresh_after_observed",
        ),
        sa.ForeignKeyConstraint(
            ["work_item_id"],
            ["organizational_work_items.id"],
            name="fk_org_execution_heartbeat_work_item",
        ),
        sa.ForeignKeyConstraint(
            ["execution_attempt_id"],
            ["organization_execution_attempts.id"],
            name="fk_org_execution_heartbeat_attempt",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "heartbeat_key",
            name="uq_org_execution_heartbeat_key",
        ),
        sa.UniqueConstraint(
            "execution_attempt_id",
            "sequence",
            name="uq_org_execution_heartbeat_attempt_sequence",
        ),
    )
    op.create_index(
        "ix_org_execution_heartbeat_tenant_position_observed",
        "organization_execution_heartbeats",
        ["tenant_key", "position_key", "observed_at"],
    )
    op.create_index(
        "ix_org_execution_heartbeat_attempt_sequence",
        "organization_execution_heartbeats",
        ["execution_attempt_id", "sequence"],
    )
    op.create_index(
        "ix_organization_execution_heartbeats_id",
        "organization_execution_heartbeats",
        ["id"],
    )
    op.create_index(
        "ix_organization_execution_heartbeats_heartbeat_key",
        "organization_execution_heartbeats",
        ["heartbeat_key"],
    )
    op.create_index(
        "ix_organization_execution_heartbeats_tenant_key",
        "organization_execution_heartbeats",
        ["tenant_key"],
    )
    op.create_index(
        "ix_organization_execution_heartbeats_position_key",
        "organization_execution_heartbeats",
        ["position_key"],
    )
    op.create_index(
        "ix_organization_execution_heartbeats_work_item_id",
        "organization_execution_heartbeats",
        ["work_item_id"],
    )
    op.create_index(
        "ix_organization_execution_heartbeats_execution_attempt_id",
        "organization_execution_heartbeats",
        ["execution_attempt_id"],
    )
    op.create_index(
        "ix_organization_execution_heartbeats_checkpoint",
        "organization_execution_heartbeats",
        ["checkpoint"],
    )
    op.create_index(
        "ix_organization_execution_heartbeats_writer",
        "organization_execution_heartbeats",
        ["writer"],
    )
    op.create_index(
        "ix_organization_execution_heartbeats_observed_at",
        "organization_execution_heartbeats",
        ["observed_at"],
    )
    op.create_index(
        "ix_organization_execution_heartbeats_fresh_until",
        "organization_execution_heartbeats",
        ["fresh_until"],
    )
    op.create_index(
        "ix_organization_execution_heartbeats_created_at",
        "organization_execution_heartbeats",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_table("organization_execution_heartbeats")
