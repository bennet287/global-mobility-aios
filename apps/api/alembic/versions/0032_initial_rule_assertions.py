"""Controlled initial verified-rule assertions from approved baseline snapshots.

Revision ID: 0032_initial_rule_assertions
Revises: 0031_global_coverage_source_onboarding
Create Date: 2026-07-14
"""
from alembic import op
import sqlalchemy as sa

revision = "0032_initial_rule_assertions"
down_revision = "0031_global_coverage_source_onboarding"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "initial_rule_assertions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assertion_sha256", sa.String(), nullable=False),
        sa.Column("coverage_batch_item_id", sa.Uuid(), nullable=True),
        sa.Column("jurisdiction_id", sa.Uuid(), nullable=False),
        sa.Column("official_source_id", sa.Uuid(), nullable=False),
        sa.Column("source_snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("rule_key", sa.String(), nullable=False),
        sa.Column("statement", sa.String(), nullable=False),
        sa.Column("rationale", sa.String(), nullable=False),
        sa.Column("evidence_excerpt", sa.String(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("effective_from", sa.DateTime(), nullable=True),
        sa.Column("effective_to", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("proposed_by", sa.String(), nullable=False),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_notes", sa.String(), nullable=True),
        sa.Column("published_rule_id", sa.Uuid(), nullable=True),
        sa.Column("published_by", sa.String(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["coverage_batch_item_id"],
            ["jurisdiction_coverage_evidence_batch_items.id"],
            name="fk_initial_assertion_batch_item",
        ),
        sa.ForeignKeyConstraint(
            ["jurisdiction_id"],
            ["jurisdictions.id"],
            name="fk_initial_assertion_jurisdiction",
        ),
        sa.ForeignKeyConstraint(
            ["official_source_id"],
            ["official_sources.id"],
            name="fk_initial_assertion_source",
        ),
        sa.ForeignKeyConstraint(
            ["source_snapshot_id"],
            ["source_snapshots.id"],
            name="fk_initial_assertion_snapshot",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_initial_rule_assertions_id", "initial_rule_assertions", ["id"])
    op.create_index("ix_initial_rule_assertions_assertion_sha256", "initial_rule_assertions", ["assertion_sha256"], unique=True)
    op.create_index("ix_initial_rule_assertions_coverage_batch_item_id", "initial_rule_assertions", ["coverage_batch_item_id"])
    op.create_index("ix_initial_rule_assertions_jurisdiction_id", "initial_rule_assertions", ["jurisdiction_id"])
    op.create_index("ix_initial_rule_assertions_official_source_id", "initial_rule_assertions", ["official_source_id"])
    op.create_index("ix_initial_rule_assertions_source_snapshot_id", "initial_rule_assertions", ["source_snapshot_id"])
    op.create_index("ix_initial_rule_assertions_domain", "initial_rule_assertions", ["domain"])
    op.create_index("ix_initial_rule_assertions_rule_key", "initial_rule_assertions", ["rule_key"])
    op.create_index("ix_initial_rule_assertions_status", "initial_rule_assertions", ["status"])
    op.create_index("ix_initial_rule_assertions_proposed_by", "initial_rule_assertions", ["proposed_by"])
    op.create_index("ix_initial_rule_assertions_reviewed_by", "initial_rule_assertions", ["reviewed_by"])
    op.create_index("ix_initial_rule_assertions_reviewed_at", "initial_rule_assertions", ["reviewed_at"])
    op.create_index("ix_initial_rule_assertions_published_rule_id", "initial_rule_assertions", ["published_rule_id"])
    op.create_index("ix_initial_rule_assertions_published_by", "initial_rule_assertions", ["published_by"])
    op.create_index("ix_initial_rule_assertions_published_at", "initial_rule_assertions", ["published_at"])
    op.create_index("ix_initial_rule_assertions_created_at", "initial_rule_assertions", ["created_at"])

    with op.batch_alter_table("verified_rules") as batch:
        batch.add_column(sa.Column("initial_rule_assertion_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key(
            "fk_verified_rule_initial_assertion",
            "initial_rule_assertions",
            ["initial_rule_assertion_id"],
            ["id"],
        )
        batch.create_index("ix_verified_rules_initial_rule_assertion_id", ["initial_rule_assertion_id"])

    with op.batch_alter_table("regulatory_knowledge_edges") as batch:
        batch.alter_column("regulatory_change_id", existing_type=sa.Uuid(), nullable=True)
        batch.add_column(sa.Column("initial_rule_assertion_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key(
            "fk_graph_edge_initial_assertion",
            "initial_rule_assertions",
            ["initial_rule_assertion_id"],
            ["id"],
        )
        batch.create_index("ix_regulatory_knowledge_edges_initial_rule_assertion_id", ["initial_rule_assertion_id"])


def downgrade() -> None:
    with op.batch_alter_table("regulatory_knowledge_edges") as batch:
        batch.drop_index("ix_regulatory_knowledge_edges_initial_rule_assertion_id")
        batch.drop_constraint("fk_graph_edge_initial_assertion", type_="foreignkey")
        batch.drop_column("initial_rule_assertion_id")
        batch.alter_column("regulatory_change_id", existing_type=sa.Uuid(), nullable=False)

    with op.batch_alter_table("verified_rules") as batch:
        batch.drop_index("ix_verified_rules_initial_rule_assertion_id")
        batch.drop_constraint("fk_verified_rule_initial_assertion", type_="foreignkey")
        batch.drop_column("initial_rule_assertion_id")

    op.drop_index("ix_initial_rule_assertions_created_at", table_name="initial_rule_assertions")
    op.drop_index("ix_initial_rule_assertions_published_at", table_name="initial_rule_assertions")
    op.drop_index("ix_initial_rule_assertions_published_by", table_name="initial_rule_assertions")
    op.drop_index("ix_initial_rule_assertions_published_rule_id", table_name="initial_rule_assertions")
    op.drop_index("ix_initial_rule_assertions_reviewed_at", table_name="initial_rule_assertions")
    op.drop_index("ix_initial_rule_assertions_reviewed_by", table_name="initial_rule_assertions")
    op.drop_index("ix_initial_rule_assertions_proposed_by", table_name="initial_rule_assertions")
    op.drop_index("ix_initial_rule_assertions_status", table_name="initial_rule_assertions")
    op.drop_index("ix_initial_rule_assertions_rule_key", table_name="initial_rule_assertions")
    op.drop_index("ix_initial_rule_assertions_domain", table_name="initial_rule_assertions")
    op.drop_index("ix_initial_rule_assertions_source_snapshot_id", table_name="initial_rule_assertions")
    op.drop_index("ix_initial_rule_assertions_official_source_id", table_name="initial_rule_assertions")
    op.drop_index("ix_initial_rule_assertions_jurisdiction_id", table_name="initial_rule_assertions")
    op.drop_index("ix_initial_rule_assertions_coverage_batch_item_id", table_name="initial_rule_assertions")
    op.drop_index("ix_initial_rule_assertions_assertion_sha256", table_name="initial_rule_assertions")
    op.drop_index("ix_initial_rule_assertions_id", table_name="initial_rule_assertions")
    op.drop_table("initial_rule_assertions")
