"""Add external Truth Engine/pathway validation framework.

Revision ID: 0068_external_validation_framework
Revises: 0067_marketing_runtime_contract
Create Date: 2026-08-08
"""

from alembic import op
import sqlalchemy as sa


revision = "0068_external_validation_framework"
down_revision = "0067_marketing_runtime_contract"
branch_labels = None
depends_on = None


def _uuid() -> sa.Uuid:
    return sa.Uuid()


def upgrade() -> None:
    op.create_table(
        "external_validation_scenarios",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("scenario_key", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("jurisdiction_code", sa.String(), nullable=False),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("persona_json", sa.String(), nullable=False),
        sa.Column("objectives_json", sa.String(), nullable=False),
        sa.Column("required_evidence_types_json", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("source_fixture", sa.String(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scenario_key", name="uq_external_validation_scenario_key"),
    )
    for column in ("scenario_key", "jurisdiction_code", "domain", "status", "created_by", "created_at"):
        op.create_index(
            f"ix_external_validation_scenario_{column}",
            "external_validation_scenarios",
            [column],
        )

    op.create_table(
        "external_validation_runs",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("run_key", sa.String(), nullable=False),
        sa.Column("scenario_id", _uuid(), nullable=False),
        sa.Column("lead_id", _uuid(), nullable=False),
        sa.Column("pathway_comparison_assessment_id", _uuid(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("gate_status", sa.String(), nullable=False),
        sa.Column("gate_reasons_json", sa.String(), nullable=False),
        sa.Column("founder_intervention_count", sa.Integer(), nullable=False),
        sa.Column("workflow_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("workflow_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["scenario_id"], ["external_validation_scenarios.id"]),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(
            ["pathway_comparison_assessment_id"],
            ["pathway_comparison_assessments.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_key", name="uq_external_validation_run_key"),
    )
    for column in (
        "run_key",
        "scenario_id",
        "lead_id",
        "pathway_comparison_assessment_id",
        "status",
        "gate_status",
        "workflow_started_at",
        "workflow_completed_at",
        "evaluated_at",
        "created_by",
        "created_at",
    ):
        op.create_index(
            f"ix_external_validation_run_{column}",
            "external_validation_runs",
            [column],
        )

    op.create_table(
        "external_validation_reviews",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("run_id", _uuid(), nullable=False),
        sa.Column("reviewer_type", sa.String(), nullable=False),
        sa.Column("reviewer_name", sa.String(), nullable=False),
        sa.Column("reviewer_organization", sa.String(), nullable=True),
        sa.Column("reviewer_origin", sa.String(), nullable=False),
        sa.Column("external_human_attestation", sa.Boolean(), nullable=False),
        sa.Column("workflow_completed", sa.Boolean(), nullable=False),
        sa.Column("understanding_rating", sa.Integer(), nullable=True),
        sa.Column("usefulness_rating", sa.Integer(), nullable=True),
        sa.Column("jurisdiction_pathway_correct", sa.Boolean(), nullable=True),
        sa.Column("material_rule_traceability_percent", sa.Float(), nullable=True),
        sa.Column("unsupported_legal_certainty_count", sa.Integer(), nullable=True),
        sa.Column("missing_critical_document_count", sa.Integer(), nullable=True),
        sa.Column("feedback", sa.String(), nullable=False),
        sa.Column("submitted_by", sa.String(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["external_validation_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "run_id",
            "reviewer_type",
            name="uq_external_validation_run_reviewer_type",
        ),
    )
    for column in ("run_id", "reviewer_type", "reviewer_name", "reviewer_origin", "submitted_by", "submitted_at"):
        op.create_index(
            f"ix_external_validation_review_{column}",
            "external_validation_reviews",
            [column],
        )

    op.create_table(
        "external_validation_findings",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("run_id", _uuid(), nullable=False),
        sa.Column("review_id", _uuid(), nullable=True),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("remediation_notes", sa.String(), nullable=True),
        sa.Column("resolved_by", sa.String(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("board_acceptance_reason", sa.String(), nullable=True),
        sa.Column("board_accepted_by", sa.String(), nullable=True),
        sa.Column("board_accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["external_validation_runs.id"]),
        sa.ForeignKeyConstraint(["review_id"], ["external_validation_reviews.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "run_id",
        "review_id",
        "severity",
        "category",
        "status",
        "resolved_by",
        "resolved_at",
        "board_accepted_by",
        "board_accepted_at",
        "created_by",
        "created_at",
    ):
        op.create_index(
            f"ix_external_validation_finding_{column}",
            "external_validation_findings",
            [column],
        )

    op.create_table(
        "external_validation_evidence",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("run_id", _uuid(), nullable=False),
        sa.Column("finding_id", _uuid(), nullable=True),
        sa.Column("evidence_type", sa.String(), nullable=False),
        sa.Column("entity_id", _uuid(), nullable=True),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("metadata_json", sa.String(), nullable=False),
        sa.Column("added_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["external_validation_runs.id"]),
        sa.ForeignKeyConstraint(["finding_id"], ["external_validation_findings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("run_id", "finding_id", "evidence_type", "entity_id", "added_by", "created_at"):
        op.create_index(
            f"ix_external_validation_evidence_{column}",
            "external_validation_evidence",
            [column],
        )


def downgrade() -> None:
    op.drop_table("external_validation_evidence")
    op.drop_table("external_validation_findings")
    op.drop_table("external_validation_reviews")
    op.drop_table("external_validation_runs")
    op.drop_table("external_validation_scenarios")
