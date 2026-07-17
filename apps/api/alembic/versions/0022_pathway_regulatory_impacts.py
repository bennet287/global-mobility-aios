"""Review-gated pathway impact links from regulatory graph updates.

Revision ID: 0022_pathway_regulatory_impacts
Revises: 0021_regulatory_knowledge_graph
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "0022_pathway_regulatory_impacts"
down_revision = "0021_regulatory_knowledge_graph"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pathway_regulatory_impacts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("impact_key", sa.String(), nullable=False),
        sa.Column("pathway_id", sa.Uuid(), nullable=False),
        sa.Column("pathway_version_id", sa.Uuid(), nullable=False),
        sa.Column("verified_rule_id", sa.Uuid(), nullable=False),
        sa.Column("superseded_rule_id", sa.Uuid(), nullable=True),
        sa.Column("regulatory_change_id", sa.Uuid(), nullable=False),
        sa.Column("source_snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("graph_rule_node_id", sa.Uuid(), nullable=True),
        sa.Column("graph_projection_version", sa.String(), nullable=False),
        sa.Column("impact_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("materiality", sa.String(), nullable=False),
        sa.Column("match_basis_json", sa.String(), nullable=False),
        sa.Column("impact_context_json", sa.String(), nullable=False),
        sa.Column("client_assessment_count_at_detection", sa.Integer(), nullable=False),
        sa.Column("timeline_count_at_detection", sa.Integer(), nullable=False),
        sa.Column("human_review_required", sa.Boolean(), nullable=False),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_notes", sa.String(), nullable=True),
        sa.Column("replacement_pathway_version_id", sa.Uuid(), nullable=True),
        sa.Column("event_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["pathway_id"], ["mobility_pathways.id"]),
        sa.ForeignKeyConstraint(["pathway_version_id"], ["mobility_pathway_versions.id"]),
        sa.ForeignKeyConstraint(["verified_rule_id"], ["verified_rules.id"]),
        sa.ForeignKeyConstraint(["superseded_rule_id"], ["verified_rules.id"]),
        sa.ForeignKeyConstraint(["regulatory_change_id"], ["regulatory_changes.id"]),
        sa.ForeignKeyConstraint(["source_snapshot_id"], ["source_snapshots.id"]),
        sa.ForeignKeyConstraint(["graph_rule_node_id"], ["regulatory_knowledge_nodes.id"]),
        sa.ForeignKeyConstraint(["replacement_pathway_version_id"], ["mobility_pathway_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "id",
        "pathway_id",
        "pathway_version_id",
        "verified_rule_id",
        "superseded_rule_id",
        "regulatory_change_id",
        "source_snapshot_id",
        "graph_rule_node_id",
        "graph_projection_version",
        "impact_type",
        "status",
        "materiality",
        "reviewed_by",
        "reviewed_at",
        "replacement_pathway_version_id",
        "event_at",
        "created_at",
    ):
        op.create_index(
            f"ix_pathway_regulatory_impacts_{column}",
            "pathway_regulatory_impacts",
            [column],
        )
    op.create_index(
        "ix_pathway_regulatory_impacts_impact_key",
        "pathway_regulatory_impacts",
        ["impact_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("pathway_regulatory_impacts")
