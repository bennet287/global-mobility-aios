"""Add GRSI.C independent improvement evaluation campaigns.

Revision ID: 0095_grsi_independent_evaluation
Revises: 0094_grsi_improvement_lineage
"""
from alembic import op
import sqlalchemy as sa

revision = "0095_grsi_independent_evaluation"
down_revision = "0094_grsi_improvement_lineage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organization_improvement_evaluation_campaigns",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("tenant_key", sa.String(), nullable=False),
        sa.Column("campaign_key", sa.String(), nullable=False),
        sa.Column("campaign_version", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("proposal_id", sa.Uuid(), nullable=False),
        sa.Column("target_type", sa.String(), nullable=False),
        sa.Column("target_reference", sa.String(), nullable=False),
        sa.Column("baseline_version", sa.String(), nullable=False),
        sa.Column("baseline_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("candidate_version", sa.String(), nullable=False),
        sa.Column("candidate_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("candidate_author_identities_json", sa.String(), nullable=False),
        sa.Column("candidate_author_evidence_reference_ids_json", sa.String(), nullable=False),
        sa.Column("evaluation_set_key", sa.String(), nullable=False),
        sa.Column("evaluation_set_version", sa.String(), nullable=False),
        sa.Column("evaluation_set_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("evaluation_set_reference_ids_json", sa.String(), nullable=False),
        sa.Column("regression_constraints_json", sa.String(), nullable=False),
        sa.Column("required_structurally_separate_evaluators", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("comparison_conclusion", sa.String(), nullable=False),
        sa.Column("record_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("closed_by", sa.String(), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("tenant_key", "id", name="uq_org_improvement_eval_campaign_tenant_id"),
        sa.UniqueConstraint("tenant_key", "campaign_key", name="uq_org_improvement_eval_campaign_tenant_key"),
        sa.UniqueConstraint(
            "tenant_key",
            "candidate_id",
            "campaign_version",
            name="uq_org_improvement_eval_campaign_candidate_version",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "candidate_id"],
            ["organization_improvement_candidates.tenant_key", "organization_improvement_candidates.id"],
            name="fk_org_improvement_eval_campaign_candidate_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "proposal_id"],
            ["organization_improvement_proposals.tenant_key", "organization_improvement_proposals.id"],
            name="fk_org_improvement_eval_campaign_proposal_tenant",
        ),
        sa.CheckConstraint("campaign_version >= 1", name="ck_org_improvement_eval_campaign_version"),
        sa.CheckConstraint(
            "required_structurally_separate_evaluators >= 1",
            name="ck_org_improvement_eval_campaign_required_evaluators",
        ),
        sa.CheckConstraint("status IN ('open','closed')", name="ck_org_improvement_eval_campaign_status"),
        sa.CheckConstraint(
            "comparison_conclusion IN ('not_assessed','constraints_met','constraints_not_met')",
            name="ck_org_improvement_eval_campaign_conclusion",
        ),
        sa.CheckConstraint("length(baseline_fingerprint) = 64", name="ck_org_improvement_eval_campaign_baseline_fp"),
        sa.CheckConstraint("length(candidate_fingerprint) = 64", name="ck_org_improvement_eval_campaign_candidate_fp"),
        sa.CheckConstraint("length(evaluation_set_fingerprint) = 64", name="ck_org_improvement_eval_campaign_set_fp"),
        sa.CheckConstraint("length(record_fingerprint) = 64", name="ck_org_improvement_eval_campaign_record_fp"),
    )
    op.create_index(
        "ix_org_improvement_eval_campaign_tenant_candidate",
        "organization_improvement_evaluation_campaigns",
        ["tenant_key", "candidate_id", "created_at"],
    )
    op.create_index(
        "ix_org_improvement_eval_campaign_tenant_status",
        "organization_improvement_evaluation_campaigns",
        ["tenant_key", "status", "created_at"],
    )

    op.create_table(
        "organization_improvement_evaluation_reports",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("tenant_key", sa.String(), nullable=False),
        sa.Column("report_key", sa.String(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("evaluator_actor_type", sa.String(), nullable=False),
        sa.Column("evaluator_identity", sa.String(), nullable=False),
        sa.Column("evaluator_independence_group", sa.String(), nullable=False),
        sa.Column("independence_evidence_reference_ids_json", sa.String(), nullable=False),
        sa.Column("baseline_measurements_json", sa.String(), nullable=False),
        sa.Column("candidate_measurements_json", sa.String(), nullable=False),
        sa.Column("constraint_results_json", sa.String(), nullable=False),
        sa.Column("evaluation_evidence_reference_ids_json", sa.String(), nullable=False),
        sa.Column("reproducibility_reference_ids_json", sa.String(), nullable=False),
        sa.Column("constraints_satisfied", sa.Boolean(), nullable=False),
        sa.Column("record_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("recorded_by", sa.String(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("tenant_key", "id", name="uq_org_improvement_eval_report_tenant_id"),
        sa.UniqueConstraint("tenant_key", "report_key", name="uq_org_improvement_eval_report_tenant_key"),
        sa.ForeignKeyConstraint(
            ["tenant_key", "campaign_id"],
            ["organization_improvement_evaluation_campaigns.tenant_key", "organization_improvement_evaluation_campaigns.id"],
            name="fk_org_improvement_eval_report_campaign_tenant",
        ),
        sa.CheckConstraint(
            "evaluator_actor_type IN ('human','agent','worker','system','external_human')",
            name="ck_org_improvement_eval_report_actor_type",
        ),
        sa.CheckConstraint("length(record_fingerprint) = 64", name="ck_org_improvement_eval_report_record_fp"),
    )
    op.create_index(
        "ix_org_improvement_eval_report_tenant_campaign",
        "organization_improvement_evaluation_reports",
        ["tenant_key", "campaign_id", "recorded_at"],
    )
    op.create_index(
        "ix_org_improvement_eval_report_tenant_evaluator",
        "organization_improvement_evaluation_reports",
        ["tenant_key", "evaluator_identity", "recorded_at"],
    )


def downgrade() -> None:
    connection = op.get_bind()
    if connection.execute(sa.text("SELECT COUNT(*) FROM organization_improvement_evaluation_reports")).scalar_one():
        raise RuntimeError("Cannot discard governed improvement evaluation report lineage")
    if connection.execute(sa.text("SELECT COUNT(*) FROM organization_improvement_evaluation_campaigns")).scalar_one():
        raise RuntimeError("Cannot discard governed improvement evaluation campaign lineage")
    op.drop_index(
        "ix_org_improvement_eval_report_tenant_evaluator",
        table_name="organization_improvement_evaluation_reports",
    )
    op.drop_index(
        "ix_org_improvement_eval_report_tenant_campaign",
        table_name="organization_improvement_evaluation_reports",
    )
    op.drop_table("organization_improvement_evaluation_reports")
    op.drop_index(
        "ix_org_improvement_eval_campaign_tenant_status",
        table_name="organization_improvement_evaluation_campaigns",
    )
    op.drop_index(
        "ix_org_improvement_eval_campaign_tenant_candidate",
        table_name="organization_improvement_evaluation_campaigns",
    )
    op.drop_table("organization_improvement_evaluation_campaigns")
