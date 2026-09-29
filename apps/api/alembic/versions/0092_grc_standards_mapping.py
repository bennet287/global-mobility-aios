"""Add explicit evidence-bound external standards mappings.

Revision ID: 0092_grc_standards_mapping
Revises: 0091_grc_risk_control_reference
"""
from alembic import op
import sqlalchemy as sa

revision = "0092_grc_standards_mapping"
down_revision = "0091_grc_risk_control_reference"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "organization_standards_mappings",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("tenant_key", sa.String(), nullable=False),
        sa.Column("mapping_key", sa.String(), nullable=False),
        sa.Column("target_type", sa.String(), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("target_version", sa.String(), nullable=False),
        sa.Column("framework_key", sa.String(), nullable=False),
        sa.Column("framework_version", sa.String(), nullable=False),
        sa.Column("requirement_id", sa.String(), nullable=False),
        sa.Column("source_reference", sa.String(), nullable=False),
        sa.Column("justification", sa.String(), nullable=False),
        sa.Column("evidence_reference_ids_json", sa.String(), nullable=False),
        sa.Column("mapping_state", sa.String(), nullable=False),
        sa.Column("supersedes_mapping_id", sa.Uuid(), nullable=True),
        sa.Column("record_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("tenant_key", "id", name="uq_org_std_mapping_tenant_id"),
        sa.UniqueConstraint("tenant_key", "mapping_key", name="uq_org_std_mapping_tenant_key"),
        sa.UniqueConstraint("tenant_key", "supersedes_mapping_id", name="uq_org_std_mapping_supersedes"),
        sa.ForeignKeyConstraint(["tenant_key","supersedes_mapping_id"],["organization_standards_mappings.tenant_key","organization_standards_mappings.id"],name="fk_org_std_mapping_supersedes_tenant"),
        sa.CheckConstraint("target_type IN ('organization_control','capability_autonomy_promotion_policy','capability_autonomy_evidence_evaluation_policy')",name="ck_org_std_mapping_target_type"),
        sa.CheckConstraint("mapping_state IN ('current','withdrawn')",name="ck_org_std_mapping_state"),
        sa.CheckConstraint("length(record_fingerprint) = 64",name="ck_org_std_mapping_fingerprint"),
        sa.CheckConstraint("supersedes_mapping_id IS NULL OR supersedes_mapping_id <> id",name="ck_org_std_mapping_not_self"),
    )
    op.create_index("ix_org_std_mapping_tenant_framework","organization_standards_mappings",["tenant_key","framework_key","framework_version"])
    op.create_index("ix_org_std_mapping_tenant_target","organization_standards_mappings",["tenant_key","target_type","target_id"])

def downgrade() -> None:
    connection = op.get_bind()
    if connection.execute(sa.text("SELECT COUNT(*) FROM organization_standards_mappings")).scalar_one():
        raise RuntimeError("Cannot discard governed standards mappings")
    op.drop_index("ix_org_std_mapping_tenant_target", table_name="organization_standards_mappings")
    op.drop_index("ix_org_std_mapping_tenant_framework", table_name="organization_standards_mappings")
    op.drop_table("organization_standards_mappings")
