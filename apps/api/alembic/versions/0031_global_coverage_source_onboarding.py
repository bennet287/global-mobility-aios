"""Bulk source onboarding inside global coverage evidence batches.

Revision ID: 0031_global_coverage_source_onboarding
Revises: 0030_global_coverage_evidence_batches
Create Date: 2026-07-14
"""
from alembic import op
import sqlalchemy as sa

revision = "0031_global_coverage_source_onboarding"
down_revision = "0030_global_coverage_evidence_batches"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("jurisdiction_coverage_evidence_batches") as batch:
        batch.add_column(
            sa.Column("source_onboarding_count", sa.Integer(), nullable=False, server_default="0")
        )

    with op.batch_alter_table("jurisdiction_coverage_evidence_batch_items") as batch:
        batch.add_column(sa.Column("regulatory_authority_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("official_source_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("source_monitor_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key(
            "fk_cov_item_authority",
            "regulatory_authorities",
            ["regulatory_authority_id"],
            ["id"],
        )
        batch.create_foreign_key(
            "fk_cov_item_source",
            "official_sources",
            ["official_source_id"],
            ["id"],
        )
        batch.create_foreign_key(
            "fk_cov_item_monitor",
            "source_monitors",
            ["source_monitor_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("jurisdiction_coverage_evidence_batch_items") as batch:
        batch.drop_constraint("fk_cov_item_monitor", type_="foreignkey")
        batch.drop_constraint("fk_cov_item_source", type_="foreignkey")
        batch.drop_constraint("fk_cov_item_authority", type_="foreignkey")
        batch.drop_column("source_monitor_id")
        batch.drop_column("official_source_id")
        batch.drop_column("regulatory_authority_id")

    with op.batch_alter_table("jurisdiction_coverage_evidence_batches") as batch:
        batch.drop_column("source_onboarding_count")
