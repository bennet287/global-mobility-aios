"""Universal mobility profile versions and assessment provenance.

Revision ID: 0011_universal_mobility_profile
Revises: 0010_authority_parser_profiles
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "0011_universal_mobility_profile"
down_revision = "0010_authority_parser_profiles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("profiles") as batch:
        batch.add_column(sa.Column("profile_version", sa.Integer(), nullable=False, server_default="1"))
        batch.add_column(sa.Column("lifecycle_status", sa.String(), nullable=False, server_default="active"))
        batch.add_column(sa.Column("supersedes_profile_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("education_json", sa.String(), nullable=True))
        batch.add_column(sa.Column("employment_json", sa.String(), nullable=True))
        batch.add_column(sa.Column("family_json", sa.String(), nullable=True))
        batch.add_column(sa.Column("finances_json", sa.String(), nullable=True))
        batch.add_column(sa.Column("goals_json", sa.String(), nullable=True))
        batch.add_column(sa.Column("constraints_json", sa.String(), nullable=True))
        batch.add_column(sa.Column("consent_json", sa.String(), nullable=True))
        batch.add_column(sa.Column("evidence_json", sa.String(), nullable=True))
        batch.add_column(sa.Column("completeness_score", sa.Float(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("readiness_stage", sa.String(), nullable=False, server_default="foundation"))
        batch.add_column(sa.Column("consent_status", sa.String(), nullable=False, server_default="not_recorded"))
        batch.add_column(sa.Column("activated_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("updated_by", sa.String(), nullable=True))
        batch.create_foreign_key(
            "fk_profiles_supersedes_profile_id",
            "profiles",
            ["supersedes_profile_id"],
            ["id"],
        )
        for column in ("profile_version", "lifecycle_status", "supersedes_profile_id", "readiness_stage", "consent_status"):
            batch.create_index(f"ix_profiles_{column}", [column], unique=False)

    with op.batch_alter_table("eligibility_assessments") as batch:
        batch.add_column(sa.Column("profile_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("profile_version", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_eligibility_assessments_profile_id",
            "profiles",
            ["profile_id"],
            ["id"],
        )
        batch.create_index("ix_eligibility_assessments_profile_id", ["profile_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("eligibility_assessments") as batch:
        batch.drop_index("ix_eligibility_assessments_profile_id")
        batch.drop_constraint("fk_eligibility_assessments_profile_id", type_="foreignkey")
        batch.drop_column("profile_version")
        batch.drop_column("profile_id")

    with op.batch_alter_table("profiles") as batch:
        for column in ("consent_status", "readiness_stage", "supersedes_profile_id", "lifecycle_status", "profile_version"):
            batch.drop_index(f"ix_profiles_{column}")
        batch.drop_constraint("fk_profiles_supersedes_profile_id", type_="foreignkey")
        for column in (
            "updated_by",
            "activated_at",
            "consent_status",
            "readiness_stage",
            "completeness_score",
            "evidence_json",
            "consent_json",
            "constraints_json",
            "goals_json",
            "finances_json",
            "family_json",
            "employment_json",
            "education_json",
            "supersedes_profile_id",
            "lifecycle_status",
            "profile_version",
        ):
            batch.drop_column(column)
