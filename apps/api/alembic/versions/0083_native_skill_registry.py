"""Add native organizational skill registry.

Revision ID: 0083_native_skill_registry
Revises: 0082_regulatory_machine_publication_contract
Create Date: 2026-09-14
"""

from alembic import op
import sqlalchemy as sa


revision = "0083_native_skill_registry"
down_revision = "0082_regulatory_machine_publication_contract"
branch_labels = None
depends_on = None


def _uuid() -> sa.Uuid:
    return sa.Uuid()


def upgrade() -> None:
    op.create_table(
        "organization_skills",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("skill_key", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("capability_family", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("origin", sa.String(), nullable=False),
        sa.Column("source_ref", sa.String(), nullable=True),
        sa.Column("source_license", sa.String(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content_sha256", sa.String(), nullable=False),
        sa.Column("compatible_departments_json", sa.String(), nullable=False),
        sa.Column("compatible_position_keys_json", sa.String(), nullable=False),
        sa.Column("tool_requirements_json", sa.String(), nullable=False),
        sa.Column("permission_requirements_json", sa.String(), nullable=False),
        sa.Column("input_schema_json", sa.String(), nullable=False),
        sa.Column("output_schema_json", sa.String(), nullable=False),
        sa.Column("evidence_expectations_json", sa.String(), nullable=False),
        sa.Column("validation_status", sa.String(), nullable=False),
        sa.Column("validation_summary_json", sa.String(), nullable=False),
        sa.Column("performance_summary_json", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("supersedes_skill_id", _uuid(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("origin IN ('native','imported','learned')", name="ck_org_skill_origin"),
        sa.CheckConstraint("status IN ('active','deprecated','superseded','quarantined')", name="ck_org_skill_status"),
        sa.CheckConstraint("validation_status IN ('unvalidated','passed','failed')", name="ck_org_skill_validation_status"),
        sa.CheckConstraint("version >= 1", name="ck_org_skill_version_positive"),
        sa.CheckConstraint("length(content_sha256) = 64", name="ck_org_skill_content_sha256"),
        sa.ForeignKeyConstraint(["supersedes_skill_id"], ["organization_skills.id"], name="fk_org_skill_supersedes"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("skill_key", "version", name="uq_org_skill_key_version"),
    )
    for column in (
        "id",
        "skill_key",
        "capability_family",
        "origin",
        "source_ref",
        "version",
        "content_sha256",
        "validation_status",
        "status",
        "supersedes_skill_id",
        "created_by",
        "created_at",
    ):
        op.create_index(f"ix_organization_skills_{column}", "organization_skills", [column])
    op.create_index(
        "ux_organization_skills_active_skill_key",
        "organization_skills",
        ["skill_key"],
        unique=True,
        sqlite_where=sa.text("status = 'active'"),
        postgresql_where=sa.text("status = 'active'"),
    )

    op.create_table(
        "organization_position_skills",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("organization_position_id", _uuid(), nullable=False),
        sa.Column("organization_skill_id", _uuid(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("assignment_reason", sa.String(), nullable=False),
        sa.Column("assigned_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('eligible','disabled')", name="ck_org_position_skill_status"),
        sa.ForeignKeyConstraint(["organization_position_id"], ["organization_positions.id"], name="fk_org_position_skill_position"),
        sa.ForeignKeyConstraint(["organization_skill_id"], ["organization_skills.id"], name="fk_org_position_skill_skill"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_position_id", "organization_skill_id", name="uq_org_position_skill_binding"),
    )
    for column in (
        "id",
        "organization_position_id",
        "organization_skill_id",
        "status",
        "assigned_by",
        "created_at",
    ):
        op.create_index(
            f"ix_organization_position_skills_{column}",
            "organization_position_skills",
            [column],
        )


def downgrade() -> None:
    op.drop_table("organization_position_skills")
    op.drop_index("ux_organization_skills_active_skill_key", table_name="organization_skills")
    op.drop_table("organization_skills")
