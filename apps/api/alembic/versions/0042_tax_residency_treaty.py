"""Tax residency and treaty intelligence controls.

Revision ID: 0042_tax_residency_treaty
Revises: 0041_family_office_mobility
Create Date: 2026-07-23
"""

from alembic import op
import sqlalchemy as sa


revision = "0042_tax_residency_treaty"
down_revision = "0041_family_office_mobility"
branch_labels = None
depends_on = None


def _indexes(table: str, columns: dict[str, str]) -> None:
    for column, suffix in columns.items():
        op.create_index(f"ix_{table}_{suffix}", table, [column])


def upgrade() -> None:
    op.create_table(
        "tax_treaty_evidence",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("evidence_key", sa.String(), nullable=False),
        sa.Column("jurisdiction_a", sa.String(), nullable=False),
        sa.Column("jurisdiction_b", sa.String(), nullable=False),
        sa.Column("topic", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("statement", sa.String(), nullable=False),
        sa.Column("official_source_id", sa.Uuid(), nullable=False),
        sa.Column("source_snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("effective_from", sa.DateTime(), nullable=True),
        sa.Column("effective_to", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("proposed_by", sa.String(), nullable=False),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["official_source_id"], ["official_sources.id"]),
        sa.ForeignKeyConstraint(["source_snapshot_id"], ["source_snapshots.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("evidence_key"),
    )
    _indexes("tax_treaty_evidence", {
        "id": "id", "evidence_key": "key", "jurisdiction_a": "jur_a",
        "jurisdiction_b": "jur_b", "topic": "topic", "official_source_id": "source",
        "source_snapshot_id": "snapshot", "effective_from": "from", "effective_to": "to",
        "status": "status", "proposed_by": "proposer", "reviewed_by": "reviewer",
        "reviewed_at": "reviewed_at", "created_at": "created_at",
    })

    op.create_table(
        "tax_treaty_evidence_decisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tax_treaty_evidence_id", sa.Uuid(), nullable=False),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("reviewer", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tax_treaty_evidence_id"], ["tax_treaty_evidence.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _indexes("tax_treaty_evidence_decisions", {
        "id": "id", "tax_treaty_evidence_id": "evidence", "decision": "decision",
        "reviewer": "reviewer", "created_at": "created_at",
    })

    op.create_table(
        "tax_residency_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=False),
        sa.Column("family_office_assessment_id", sa.Uuid(), nullable=True),
        sa.Column("business_advisory_assessment_id", sa.Uuid(), nullable=True),
        sa.Column("tax_year", sa.Integer(), nullable=False),
        sa.Column("input_json", sa.String(), nullable=False),
        sa.Column("readiness_score", sa.Float(), nullable=False),
        sa.Column("readiness_band", sa.String(), nullable=False),
        sa.Column("fact_completeness_score", sa.Float(), nullable=False),
        sa.Column("controlled_evidence_score", sa.Float(), nullable=False),
        sa.Column("treaty_grounding_score", sa.Float(), nullable=False),
        sa.Column("specialist_coordination_score", sa.Float(), nullable=False),
        sa.Column("issue_matrix_json", sa.String(), nullable=False),
        sa.Column("workstreams_json", sa.String(), nullable=False),
        sa.Column("blockers_json", sa.String(), nullable=False),
        sa.Column("next_actions_json", sa.String(), nullable=False),
        sa.Column("evidence_basis_json", sa.String(), nullable=False),
        sa.Column("treaty_evidence_ids_json", sa.String(), nullable=False),
        sa.Column("escalation_flags_json", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("human_review_required", sa.Boolean(), nullable=False),
        sa.Column("generated_by", sa.String(), nullable=False),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["family_office_assessment_id"], ["family_office_mobility_assessments.id"]),
        sa.ForeignKeyConstraint(["business_advisory_assessment_id"], ["business_mobility_advisory_assessments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _indexes("tax_residency_assessments", {
        "id": "id", "lead_id": "lead", "family_office_assessment_id": "family_office",
        "business_advisory_assessment_id": "advisory", "tax_year": "year",
        "readiness_band": "readiness", "status": "status", "generated_by": "generator",
        "reviewed_by": "reviewer", "reviewed_at": "reviewed_at", "created_at": "created_at",
    })

    op.create_table(
        "tax_residency_assessment_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assessment_id", sa.Uuid(), nullable=False),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("reviewer", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["tax_residency_assessments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _indexes("tax_residency_assessment_reviews", {
        "id": "id", "assessment_id": "assessment", "decision": "decision",
        "reviewer": "reviewer", "created_at": "created_at",
    })


def downgrade() -> None:
    op.drop_table("tax_residency_assessment_reviews")
    op.drop_table("tax_residency_assessments")
    op.drop_table("tax_treaty_evidence_decisions")
    op.drop_table("tax_treaty_evidence")
