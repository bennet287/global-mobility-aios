"""Add authority-neutral GRSI improvement proposal and candidate lineage.

Revision ID: 0094_grsi_improvement_lineage
Revises: 0093_monetary_allocation
"""
from alembic import op
import sqlalchemy as sa

revision = "0094_grsi_improvement_lineage"
down_revision = "0093_monetary_allocation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organization_improvement_proposals",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("tenant_key", sa.String(), nullable=False),
        sa.Column("proposal_key", sa.String(), nullable=False),
        sa.Column("work_item_id", sa.Uuid(), nullable=False),
        sa.Column("target_type", sa.String(), nullable=False),
        sa.Column("target_reference", sa.String(), nullable=False),
        sa.Column("baseline_version", sa.String(), nullable=False),
        sa.Column("baseline_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("problem_statement", sa.String(), nullable=False),
        sa.Column("hypothesis", sa.String(), nullable=False),
        sa.Column("expected_improvement", sa.String(), nullable=False),
        sa.Column("acceptance_constraints_json", sa.String(), nullable=False),
        sa.Column("evidence_reference_ids_json", sa.String(), nullable=False),
        sa.Column("supersedes_proposal_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("record_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("withdrawn_by", sa.String(), nullable=True),
        sa.Column("withdrawn_reason", sa.String(), nullable=True),
        sa.Column("withdrawn_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("tenant_key", "id", name="uq_org_improvement_proposal_tenant_id"),
        sa.UniqueConstraint("tenant_key", "proposal_key", name="uq_org_improvement_proposal_tenant_key"),
        sa.UniqueConstraint("tenant_key", "supersedes_proposal_id", name="uq_org_improvement_proposal_supersedes"),
        sa.ForeignKeyConstraint(
            ["tenant_key", "work_item_id"],
            ["organizational_work_items.tenant_key", "organizational_work_items.id"],
            name="fk_org_improvement_proposal_work_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "supersedes_proposal_id"],
            ["organization_improvement_proposals.tenant_key", "organization_improvement_proposals.id"],
            name="fk_org_improvement_proposal_supersedes_tenant",
        ),
        sa.CheckConstraint("status IN ('open','withdrawn')", name="ck_org_improvement_proposal_status"),
        sa.CheckConstraint("length(baseline_fingerprint) = 64", name="ck_org_improvement_proposal_baseline_fingerprint"),
        sa.CheckConstraint("length(record_fingerprint) = 64", name="ck_org_improvement_proposal_record_fingerprint"),
        sa.CheckConstraint("supersedes_proposal_id IS NULL OR supersedes_proposal_id <> id", name="ck_org_improvement_proposal_not_self_superseding"),
    )
    op.create_index(
        "ix_org_improvement_proposal_tenant_target",
        "organization_improvement_proposals",
        ["tenant_key", "target_type", "target_reference"],
    )
    op.create_index(
        "ix_org_improvement_proposal_tenant_work",
        "organization_improvement_proposals",
        ["tenant_key", "work_item_id"],
    )

    op.create_table(
        "organization_improvement_candidates",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("tenant_key", sa.String(), nullable=False),
        sa.Column("candidate_key", sa.String(), nullable=False),
        sa.Column("proposal_id", sa.Uuid(), nullable=False),
        sa.Column("parent_candidate_id", sa.Uuid(), nullable=True),
        sa.Column("target_type", sa.String(), nullable=False),
        sa.Column("target_reference", sa.String(), nullable=False),
        sa.Column("baseline_version", sa.String(), nullable=False),
        sa.Column("baseline_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("candidate_version", sa.String(), nullable=False),
        sa.Column("candidate_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("artifact_reference", sa.String(), nullable=False),
        sa.Column("implementation_provenance_json", sa.String(), nullable=False),
        sa.Column("candidate_hypothesis", sa.String(), nullable=False),
        sa.Column("expected_improvement", sa.String(), nullable=False),
        sa.Column("acceptance_constraints_json", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("record_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("withdrawn_by", sa.String(), nullable=True),
        sa.Column("withdrawn_reason", sa.String(), nullable=True),
        sa.Column("withdrawn_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("tenant_key", "id", name="uq_org_improvement_candidate_tenant_id"),
        sa.UniqueConstraint("tenant_key", "candidate_key", name="uq_org_improvement_candidate_tenant_key"),
        sa.ForeignKeyConstraint(
            ["tenant_key", "proposal_id"],
            ["organization_improvement_proposals.tenant_key", "organization_improvement_proposals.id"],
            name="fk_org_improvement_candidate_proposal_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "parent_candidate_id"],
            ["organization_improvement_candidates.tenant_key", "organization_improvement_candidates.id"],
            name="fk_org_improvement_candidate_parent_tenant",
        ),
        sa.CheckConstraint("status IN ('prepared','withdrawn')", name="ck_org_improvement_candidate_status"),
        sa.CheckConstraint("length(baseline_fingerprint) = 64", name="ck_org_improvement_candidate_baseline_fingerprint"),
        sa.CheckConstraint("length(candidate_fingerprint) = 64", name="ck_org_improvement_candidate_artifact_fingerprint"),
        sa.CheckConstraint("length(record_fingerprint) = 64", name="ck_org_improvement_candidate_record_fingerprint"),
        sa.CheckConstraint("parent_candidate_id IS NULL OR parent_candidate_id <> id", name="ck_org_improvement_candidate_not_self_parent"),
    )
    op.create_index(
        "ix_org_improvement_candidate_tenant_proposal",
        "organization_improvement_candidates",
        ["tenant_key", "proposal_id", "created_at"],
    )
    op.create_index(
        "ix_org_improvement_candidate_tenant_target",
        "organization_improvement_candidates",
        ["tenant_key", "target_type", "target_reference"],
    )


def downgrade() -> None:
    connection = op.get_bind()
    if connection.execute(sa.text("SELECT COUNT(*) FROM organization_improvement_candidates")).scalar_one():
        raise RuntimeError("Cannot discard governed improvement candidate lineage")
    if connection.execute(sa.text("SELECT COUNT(*) FROM organization_improvement_proposals")).scalar_one():
        raise RuntimeError("Cannot discard governed improvement proposal lineage")
    op.drop_index("ix_org_improvement_candidate_tenant_target", table_name="organization_improvement_candidates")
    op.drop_index("ix_org_improvement_candidate_tenant_proposal", table_name="organization_improvement_candidates")
    op.drop_table("organization_improvement_candidates")
    op.drop_index("ix_org_improvement_proposal_tenant_work", table_name="organization_improvement_proposals")
    op.drop_index("ix_org_improvement_proposal_tenant_target", table_name="organization_improvement_proposals")
    op.drop_table("organization_improvement_proposals")
