"""Add durable public-intake submission idempotency.

Revision ID: 0072_intake_submission_idempotency
Revises: 0071_structured_shortage_occupation_evidence
Create Date: 2026-08-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0072_intake_submission_idempotency"
down_revision = "0071_structured_shortage_occupation_evidence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("intake_sessions", sa.Column("submission_key", sa.String(), nullable=True))
    op.add_column("intake_sessions", sa.Column("submission_fingerprint", sa.String(), nullable=True))
    op.create_index(
        "ix_intake_sessions_submission_key",
        "intake_sessions",
        ["submission_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_intake_sessions_submission_key", table_name="intake_sessions")
    op.drop_column("intake_sessions", "submission_fingerprint")
    op.drop_column("intake_sessions", "submission_key")
