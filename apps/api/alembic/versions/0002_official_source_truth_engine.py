"""Official-source truth engine v3.4

Revision ID: 0002_official_source_truth_engine
Revises: 0001_mvp1_baseline
Create Date: 2026-07-09
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_official_source_truth_engine"
down_revision = "0001_mvp1_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "official_sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("country", sa.String(), nullable=False),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("authority", sa.String(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_official_sources_id", "official_sources", ["id"])
    op.create_index("ix_official_sources_country", "official_sources", ["country"])
    op.create_index("ix_official_sources_domain", "official_sources", ["domain"])
    op.create_index("ix_official_sources_url", "official_sources", ["url"])
    op.create_index("ix_official_sources_source_type", "official_sources", ["source_type"])
    op.create_index("ix_official_sources_active", "official_sources", ["active"])

    op.create_table(
        "source_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("official_source_id", sa.Uuid(), nullable=True),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("content_hash", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("metadata_json", sa.String(), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["official_source_id"], ["official_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_source_snapshots_id", "source_snapshots", ["id"])
    op.create_index("ix_source_snapshots_official_source_id", "source_snapshots", ["official_source_id"])
    op.create_index("ix_source_snapshots_url", "source_snapshots", ["url"])
    op.create_index("ix_source_snapshots_content_hash", "source_snapshots", ["content_hash"])
    op.create_index("ix_source_snapshots_status", "source_snapshots", ["status"])
    op.create_index("ix_source_snapshots_captured_at", "source_snapshots", ["captured_at"])

    op.create_table(
        "source_check_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("truth_claim_id", sa.Uuid(), nullable=True),
        sa.Column("country", sa.String(), nullable=True),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("claim", sa.String(), nullable=False),
        sa.Column("verdict", sa.String(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence_count", sa.Integer(), nullable=False),
        sa.Column("matched_sources_json", sa.String(), nullable=True),
        sa.Column("corrected_statement", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["truth_claim_id"], ["truth_claims.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_source_check_runs_id", "source_check_runs", ["id"])
    op.create_index("ix_source_check_runs_truth_claim_id", "source_check_runs", ["truth_claim_id"])
    op.create_index("ix_source_check_runs_country", "source_check_runs", ["country"])
    op.create_index("ix_source_check_runs_domain", "source_check_runs", ["domain"])
    op.create_index("ix_source_check_runs_verdict", "source_check_runs", ["verdict"])
    op.create_index("ix_source_check_runs_created_at", "source_check_runs", ["created_at"])

    op.create_table(
        "verified_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("country", sa.String(), nullable=False),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("rule_key", sa.String(), nullable=False),
        sa.Column("statement", sa.String(), nullable=False),
        sa.Column("official_source_id", sa.Uuid(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["official_source_id"], ["official_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_verified_rules_id", "verified_rules", ["id"])
    op.create_index("ix_verified_rules_country", "verified_rules", ["country"])
    op.create_index("ix_verified_rules_domain", "verified_rules", ["domain"])
    op.create_index("ix_verified_rules_rule_key", "verified_rules", ["rule_key"])
    op.create_index("ix_verified_rules_official_source_id", "verified_rules", ["official_source_id"])
    op.create_index("ix_verified_rules_active", "verified_rules", ["active"])

    op.create_table(
        "country_policies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("country", sa.String(), nullable=False),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("policy_json", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_country_policies_id", "country_policies", ["id"])
    op.create_index("ix_country_policies_country", "country_policies", ["country"])
    op.create_index("ix_country_policies_domain", "country_policies", ["domain"])
    op.create_index("ix_country_policies_status", "country_policies", ["status"])


def downgrade() -> None:
    op.drop_index("ix_country_policies_status", table_name="country_policies")
    op.drop_index("ix_country_policies_domain", table_name="country_policies")
    op.drop_index("ix_country_policies_country", table_name="country_policies")
    op.drop_index("ix_country_policies_id", table_name="country_policies")
    op.drop_table("country_policies")

    op.drop_index("ix_verified_rules_active", table_name="verified_rules")
    op.drop_index("ix_verified_rules_official_source_id", table_name="verified_rules")
    op.drop_index("ix_verified_rules_rule_key", table_name="verified_rules")
    op.drop_index("ix_verified_rules_domain", table_name="verified_rules")
    op.drop_index("ix_verified_rules_country", table_name="verified_rules")
    op.drop_index("ix_verified_rules_id", table_name="verified_rules")
    op.drop_table("verified_rules")

    op.drop_index("ix_source_check_runs_created_at", table_name="source_check_runs")
    op.drop_index("ix_source_check_runs_verdict", table_name="source_check_runs")
    op.drop_index("ix_source_check_runs_domain", table_name="source_check_runs")
    op.drop_index("ix_source_check_runs_country", table_name="source_check_runs")
    op.drop_index("ix_source_check_runs_truth_claim_id", table_name="source_check_runs")
    op.drop_index("ix_source_check_runs_id", table_name="source_check_runs")
    op.drop_table("source_check_runs")

    op.drop_index("ix_source_snapshots_captured_at", table_name="source_snapshots")
    op.drop_index("ix_source_snapshots_status", table_name="source_snapshots")
    op.drop_index("ix_source_snapshots_content_hash", table_name="source_snapshots")
    op.drop_index("ix_source_snapshots_url", table_name="source_snapshots")
    op.drop_index("ix_source_snapshots_official_source_id", table_name="source_snapshots")
    op.drop_index("ix_source_snapshots_id", table_name="source_snapshots")
    op.drop_table("source_snapshots")

    op.drop_index("ix_official_sources_active", table_name="official_sources")
    op.drop_index("ix_official_sources_source_type", table_name="official_sources")
    op.drop_index("ix_official_sources_url", table_name="official_sources")
    op.drop_index("ix_official_sources_domain", table_name="official_sources")
    op.drop_index("ix_official_sources_country", table_name="official_sources")
    op.drop_index("ix_official_sources_id", table_name="official_sources")
    op.drop_table("official_sources")
