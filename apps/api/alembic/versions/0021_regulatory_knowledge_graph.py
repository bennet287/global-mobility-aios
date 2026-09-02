"""Provenance-preserving regulatory knowledge graph projection.

Revision ID: 0021_regulatory_knowledge_graph
Revises: 0020_regulatory_classification_proposals
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "0021_regulatory_knowledge_graph"
down_revision = "0020_regulatory_classification_proposals"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "regulatory_knowledge_nodes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("node_key", sa.String(), nullable=False),
        sa.Column("node_type", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("properties_json", sa.String(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_from_verified_rule_id", sa.Uuid(), nullable=False),
        sa.Column("last_verified_rule_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_from_verified_rule_id"], ["verified_rules.id"]),
        sa.ForeignKeyConstraint(["last_verified_rule_id"], ["verified_rules.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "id", "node_type", "active", "created_from_verified_rule_id",
        "last_verified_rule_id", "created_at",
    ):
        op.create_index(f"ix_regulatory_knowledge_nodes_{column}", "regulatory_knowledge_nodes", [column])
    op.create_index(
        "ix_regulatory_knowledge_nodes_node_key",
        "regulatory_knowledge_nodes",
        ["node_key"],
        unique=True,
    )

    op.create_table(
        "regulatory_knowledge_edges",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("edge_key", sa.String(), nullable=False),
        sa.Column("source_node_id", sa.Uuid(), nullable=False),
        sa.Column("target_node_id", sa.Uuid(), nullable=False),
        sa.Column("relation_type", sa.String(), nullable=False),
        sa.Column("verified_rule_id", sa.Uuid(), nullable=False),
        sa.Column("source_snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("regulatory_change_id", sa.Uuid(), nullable=False),
        sa.Column("projection_version", sa.String(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("effective_from", sa.DateTime(), nullable=True),
        sa.Column("effective_to", sa.DateTime(), nullable=True),
        sa.Column("retired_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["source_node_id"], ["regulatory_knowledge_nodes.id"]),
        sa.ForeignKeyConstraint(["target_node_id"], ["regulatory_knowledge_nodes.id"]),
        sa.ForeignKeyConstraint(["verified_rule_id"], ["verified_rules.id"]),
        sa.ForeignKeyConstraint(["source_snapshot_id"], ["source_snapshots.id"]),
        sa.ForeignKeyConstraint(["regulatory_change_id"], ["regulatory_changes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "id", "source_node_id", "target_node_id", "relation_type",
        "verified_rule_id", "source_snapshot_id", "regulatory_change_id",
        "projection_version", "active", "retired_at", "created_at",
    ):
        op.create_index(f"ix_regulatory_knowledge_edges_{column}", "regulatory_knowledge_edges", [column])
    op.create_index(
        "ix_regulatory_knowledge_edges_edge_key",
        "regulatory_knowledge_edges",
        ["edge_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("regulatory_knowledge_edges")
    op.drop_table("regulatory_knowledge_nodes")
