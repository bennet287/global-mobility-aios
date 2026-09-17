"""Add governed organization agent lifecycle identity.

Revision ID: 0084_organization_agent_lifecycle
Revises: 0083_native_skill_registry
Create Date: 2026-09-17
"""

from alembic import op
import sqlalchemy as sa


revision = "0084_organization_agent_lifecycle"
down_revision = "0083_native_skill_registry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organization_agents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("agent_key", sa.String(), nullable=False),
        sa.Column("registry_key", sa.String(), nullable=False),
        sa.Column("registry_version", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("department", sa.String(), nullable=False),
        sa.Column("position_key", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("lifecycle_reason", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('created','onboarding','inactive','active','restricted','suspended','retired')",
            name="ck_organization_agent_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_key", name="uq_organization_agent_key"),
    )
    for column in (
        "id",
        "agent_key",
        "registry_key",
        "department",
        "position_key",
        "status",
        "created_by",
        "created_at",
    ):
        op.create_index(f"ix_organization_agents_{column}", "organization_agents", [column])


def downgrade() -> None:
    op.drop_table("organization_agents")
