"""Controlled official-source retrieval worker state.

Revision ID: 0008_controlled_retrieval
Revises: 0007_regulatory_intelligence
Create Date: 2026-07-13
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_controlled_retrieval"
down_revision = "0007_regulatory_intelligence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("source_monitors") as batch:
        batch.add_column(sa.Column("allowed_domains_json", sa.String(), nullable=True))
        batch.add_column(sa.Column("max_redirects", sa.Integer(), nullable=False, server_default="3"))

    op.create_table(
        "source_retrieval_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("monitor_id", sa.Uuid(), nullable=False),
        sa.Column("official_source_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("requested_url", sa.String(), nullable=False),
        sa.Column("final_url", sa.String(), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("content_type", sa.String(), nullable=True),
        sa.Column("bytes_received", sa.Integer(), nullable=False),
        sa.Column("snapshot_id", sa.Uuid(), nullable=True),
        sa.Column("regulatory_change_id", sa.Uuid(), nullable=True),
        sa.Column("error_code", sa.String(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["monitor_id"], ["source_monitors.id"]),
        sa.ForeignKeyConstraint(["official_source_id"], ["official_sources.id"]),
        sa.ForeignKeyConstraint(["snapshot_id"], ["source_snapshots.id"]),
        sa.ForeignKeyConstraint(["regulatory_change_id"], ["regulatory_changes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "id",
        "monitor_id",
        "official_source_id",
        "status",
        "snapshot_id",
        "regulatory_change_id",
        "error_code",
        "started_at",
        "completed_at",
    ):
        op.create_index(f"ix_source_retrieval_runs_{column}", "source_retrieval_runs", [column])


def downgrade() -> None:
    op.drop_table("source_retrieval_runs")
    with op.batch_alter_table("source_monitors") as batch:
        batch.drop_column("max_redirects")
        batch.drop_column("allowed_domains_json")
