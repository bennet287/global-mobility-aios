"""AgentRun status lifecycle for background worker queue v4.5

Revision ID: 0004_agent_run_status
Revises: 0003_document_upload_minio
Create Date: 2026-07-10
"""

from alembic import op


revision = "0004_agent_run_status"
down_revision = "0003_document_upload_minio"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_agent_runs_status", "agent_runs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_agent_runs_status", table_name="agent_runs")
