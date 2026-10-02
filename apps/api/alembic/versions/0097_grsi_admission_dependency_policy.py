"""Add Board-governed GRSI admission dependency policy.

Revision ID: 0097_grsi_admission_dependency_policy
Revises: 0096_grsi_cross_team_review
"""
from alembic import op
import sqlalchemy as sa


revision = "0097_grsi_admission_dependency_policy"
down_revision = "0096_grsi_cross_team_review"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organization_improvement_admission_dependency_policies",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("tenant_key", sa.String(), nullable=False),
        sa.Column("target_type", sa.String(), nullable=False),
        sa.Column("execution_mode", sa.String(), nullable=False),
        sa.Column("candidate_risk_class", sa.String(), nullable=False),
        sa.Column("policy_version", sa.Integer(), nullable=False),
        sa.Column("phase_requirements_json", sa.String(), nullable=False),
        sa.Column("policy_reason", sa.String(), nullable=False),
        sa.Column("supersedes_policy_id", sa.Uuid(), nullable=True),
        sa.Column("decision_activity_id", sa.Uuid(), nullable=False),
        sa.Column("decision_activity_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key", sa.String(), nullable=False),
        sa.Column("record_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "tenant_key",
            "id",
            name="uq_org_improv_adm_policy_tenant_id",
        ),
        sa.UniqueConstraint(
            "tenant_key",
            "idempotency_key",
            name="uq_org_improv_adm_policy_idempotency",
        ),
        sa.UniqueConstraint(
            "tenant_key",
            "target_type",
            "execution_mode",
            "candidate_risk_class",
            "policy_version",
            name="uq_org_improv_adm_policy_scope_version",
        ),
        sa.UniqueConstraint(
            "tenant_key",
            "supersedes_policy_id",
            name="uq_org_improv_adm_policy_supersedes",
        ),
        sa.CheckConstraint(
            "target_type = 'code_configuration'",
            name="ck_org_improv_adm_policy_target",
        ),
        sa.CheckConstraint(
            "execution_mode = 'shadow'",
            name="ck_org_improv_adm_policy_mode",
        ),
        sa.CheckConstraint(
            "candidate_risk_class IN ('low','medium','high','critical')",
            name="ck_org_improv_adm_policy_risk",
        ),
        sa.CheckConstraint(
            "policy_version >= 1",
            name="ck_org_improv_adm_policy_version",
        ),
        sa.CheckConstraint(
            "supersedes_policy_id IS NULL OR supersedes_policy_id <> id",
            name="ck_org_improv_adm_policy_not_self",
        ),
        sa.CheckConstraint(
            "length(decision_activity_fingerprint) = 64",
            name="ck_org_improv_adm_policy_activity_fp",
        ),
        sa.CheckConstraint(
            "length(record_fingerprint) = 64",
            name="ck_org_improv_adm_policy_record_fp",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "decision_activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_org_improv_adm_policy_activity_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "supersedes_policy_id"],
            [
                "organization_improvement_admission_dependency_policies.tenant_key",
                "organization_improvement_admission_dependency_policies.id",
            ],
            name="fk_org_improv_adm_policy_supersedes_tenant",
        ),
    )
    op.create_index(
        "ix_org_improv_adm_policy_scope_seq",
        "organization_improvement_admission_dependency_policies",
        [
            "tenant_key",
            "target_type",
            "execution_mode",
            "candidate_risk_class",
            "policy_version",
        ],
    )
    op.create_index(
        "ix_org_improv_adm_policy_activity",
        "organization_improvement_admission_dependency_policies",
        ["tenant_key", "decision_activity_id"],
    )


def downgrade() -> None:
    connection = op.get_bind()
    if connection.execute(
        sa.text(
            "SELECT COUNT(*) FROM organization_improvement_admission_dependency_policies"
        )
    ).scalar_one():
        raise RuntimeError("Cannot discard governed GRSI admission dependency policy")
    op.drop_index(
        "ix_org_improv_adm_policy_activity",
        table_name="organization_improvement_admission_dependency_policies",
    )
    op.drop_index(
        "ix_org_improv_adm_policy_scope_seq",
        table_name="organization_improvement_admission_dependency_policies",
    )
    op.drop_table("organization_improvement_admission_dependency_policies")
