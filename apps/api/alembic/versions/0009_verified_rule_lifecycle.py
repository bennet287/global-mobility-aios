"""Verified rule supersession and retirement lifecycle.

Revision ID: 0009_verified_rule_lifecycle
Revises: 0008_controlled_retrieval
Create Date: 2026-07-13
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_verified_rule_lifecycle"
down_revision = "0008_controlled_retrieval"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("verified_rules") as batch:
        batch.add_column(sa.Column("supersedes_rule_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("retired_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("retired_by", sa.String(), nullable=True))
        batch.add_column(sa.Column("retirement_reason", sa.String(), nullable=True))
        batch.create_foreign_key(
            "fk_verified_rules_supersedes",
            "verified_rules",
            ["supersedes_rule_id"],
            ["id"],
        )
        batch.create_index("ix_verified_rules_supersedes_rule_id", ["supersedes_rule_id"])


def downgrade() -> None:
    with op.batch_alter_table("verified_rules") as batch:
        batch.drop_index("ix_verified_rules_supersedes_rule_id")
        batch.drop_constraint("fk_verified_rules_supersedes", type_="foreignkey")
        batch.drop_column("retirement_reason")
        batch.drop_column("retired_by")
        batch.drop_column("retired_at")
        batch.drop_column("supersedes_rule_id")
