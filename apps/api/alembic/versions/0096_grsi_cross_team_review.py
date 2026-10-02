"""Add GRSI.D candidate-bound cross-team review packages.

Revision ID: 0096_grsi_cross_team_review
Revises: 0095_grsi_independent_evaluation
"""
from alembic import op
import sqlalchemy as sa


revision = "0096_grsi_cross_team_review"
down_revision = "0095_grsi_independent_evaluation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organization_improvement_review_packages",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("tenant_key", sa.String(), nullable=False),
        sa.Column("package_key", sa.String(), nullable=False),
        sa.Column("package_version", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("proposal_id", sa.Uuid(), nullable=False),
        sa.Column("evaluation_campaign_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("risk_class", sa.String(), nullable=False),
        sa.Column("risk_basis_reference_ids_json", sa.String(), nullable=False),
        sa.Column("review_policy_key", sa.String(), nullable=False),
        sa.Column("review_policy_version", sa.Integer(), nullable=False),
        sa.Column("review_policy_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("required_review_kinds_json", sa.String(), nullable=False),
        sa.Column("review_bindings_json", sa.String(), nullable=False),
        sa.Column("supersedes_package_id", sa.Uuid(), nullable=True),
        sa.Column("record_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "tenant_key",
            "id",
            name="uq_org_improvement_review_package_tenant_id",
        ),
        sa.UniqueConstraint(
            "tenant_key",
            "package_key",
            name="uq_org_improvement_review_package_tenant_key",
        ),
        sa.UniqueConstraint(
            "tenant_key",
            "candidate_id",
            "package_version",
            name="uq_org_improvement_review_package_candidate_version",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "candidate_id"],
            ["organization_improvement_candidates.tenant_key", "organization_improvement_candidates.id"],
            name="fk_org_improvement_review_package_candidate_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "proposal_id"],
            ["organization_improvement_proposals.tenant_key", "organization_improvement_proposals.id"],
            name="fk_org_improvement_review_package_proposal_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "evaluation_campaign_id"],
            [
                "organization_improvement_evaluation_campaigns.tenant_key",
                "organization_improvement_evaluation_campaigns.id",
            ],
            name="fk_org_improvement_review_package_campaign_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "supersedes_package_id"],
            ["organization_improvement_review_packages.tenant_key", "organization_improvement_review_packages.id"],
            name="fk_org_improvement_review_package_supersedes_tenant",
        ),
        sa.CheckConstraint(
            "package_version >= 1",
            name="ck_org_improvement_review_package_version",
        ),
        sa.CheckConstraint(
            "risk_class IN ('low','medium','high','critical')",
            name="ck_org_improvement_review_package_risk_class",
        ),
        sa.CheckConstraint(
            "length(candidate_fingerprint) = 64",
            name="ck_org_improvement_review_package_candidate_fp",
        ),
        sa.CheckConstraint(
            "length(review_policy_fingerprint) = 64",
            name="ck_org_improvement_review_package_policy_fp",
        ),
        sa.CheckConstraint(
            "length(record_fingerprint) = 64",
            name="ck_org_improvement_review_package_record_fp",
        ),
        sa.CheckConstraint(
            "supersedes_package_id IS NULL OR supersedes_package_id <> id",
            name="ck_org_improvement_review_package_not_self",
        ),
    )
    op.create_index(
        "ix_org_improvement_review_package_tenant_candidate",
        "organization_improvement_review_packages",
        ["tenant_key", "candidate_id", "created_at"],
    )
    op.create_index(
        "ix_org_improvement_review_package_tenant_risk",
        "organization_improvement_review_packages",
        ["tenant_key", "risk_class", "created_at"],
    )


def downgrade() -> None:
    connection = op.get_bind()
    if connection.execute(
        sa.text("SELECT COUNT(*) FROM organization_improvement_review_packages")
    ).scalar_one():
        raise RuntimeError("Cannot discard governed improvement review package lineage")
    op.drop_index(
        "ix_org_improvement_review_package_tenant_risk",
        table_name="organization_improvement_review_packages",
    )
    op.drop_index(
        "ix_org_improvement_review_package_tenant_candidate",
        table_name="organization_improvement_review_packages",
    )
    op.drop_table("organization_improvement_review_packages")
