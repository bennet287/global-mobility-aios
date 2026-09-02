"""Regulatory intelligence foundation.

Revision ID: 0007_regulatory_intelligence
Revises: 0006_eligibility_opportunities
Create Date: 2026-07-13
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_regulatory_intelligence"
down_revision = "0006_eligibility_opportunities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jurisdictions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("jurisdiction_type", sa.String(), nullable=False),
        sa.Column("parent_code", sa.String(), nullable=True),
        sa.Column("region", sa.String(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("metadata_json", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    for column in ("id", "code", "name", "jurisdiction_type", "parent_code", "region", "active"):
        op.create_index(f"ix_jurisdictions_{column}", "jurisdictions", [column])

    op.create_table(
        "regulatory_authorities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("jurisdiction_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("authority_type", sa.String(), nullable=False),
        sa.Column("website_url", sa.String(), nullable=True),
        sa.Column("domains_json", sa.String(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["jurisdiction_id"], ["jurisdictions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("id", "jurisdiction_id", "name", "authority_type", "active"):
        op.create_index(f"ix_regulatory_authorities_{column}", "regulatory_authorities", [column])

    with op.batch_alter_table("official_sources") as batch:
        batch.add_column(sa.Column("jurisdiction_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("regulatory_authority_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key("fk_official_sources_jurisdiction", "jurisdictions", ["jurisdiction_id"], ["id"])
        batch.create_foreign_key("fk_official_sources_authority", "regulatory_authorities", ["regulatory_authority_id"], ["id"])
        batch.create_index("ix_official_sources_jurisdiction_id", ["jurisdiction_id"])
        batch.create_index("ix_official_sources_regulatory_authority_id", ["regulatory_authority_id"])

    op.create_table(
        "source_monitors",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("official_source_id", sa.Uuid(), nullable=False),
        sa.Column("schedule_minutes", sa.Integer(), nullable=False),
        sa.Column("fetch_method", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(), nullable=True),
        sa.Column("next_check_at", sa.DateTime(), nullable=True),
        sa.Column("last_http_status", sa.Integer(), nullable=True),
        sa.Column("last_error", sa.String(), nullable=True),
        sa.Column("etag", sa.String(), nullable=True),
        sa.Column("last_modified", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["official_source_id"], ["official_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("official_source_id"),
    )
    for column in ("id", "official_source_id", "status", "last_checked_at", "next_check_at"):
        op.create_index(f"ix_source_monitors_{column}", "source_monitors", [column])

    with op.batch_alter_table("source_snapshots") as batch:
        batch.add_column(sa.Column("previous_snapshot_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("content_text", sa.String(), nullable=True))
        batch.add_column(sa.Column("http_status", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("retrieval_method", sa.String(), nullable=False, server_default="reference"))
        batch.add_column(sa.Column("parser_version", sa.String(), nullable=True))
        batch.create_foreign_key("fk_source_snapshots_previous", "source_snapshots", ["previous_snapshot_id"], ["id"])
        batch.create_index("ix_source_snapshots_previous_snapshot_id", ["previous_snapshot_id"])

    op.create_table(
        "regulatory_changes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("jurisdiction_id", sa.Uuid(), nullable=False),
        sa.Column("official_source_id", sa.Uuid(), nullable=False),
        sa.Column("previous_snapshot_id", sa.Uuid(), nullable=True),
        sa.Column("current_snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("change_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("diff_json", sa.String(), nullable=True),
        sa.Column("materiality", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("effective_at", sa.DateTime(), nullable=True),
        sa.Column("detected_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("review_notes", sa.String(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["jurisdiction_id"], ["jurisdictions.id"]),
        sa.ForeignKeyConstraint(["official_source_id"], ["official_sources.id"]),
        sa.ForeignKeyConstraint(["previous_snapshot_id"], ["source_snapshots.id"]),
        sa.ForeignKeyConstraint(["current_snapshot_id"], ["source_snapshots.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("id", "jurisdiction_id", "official_source_id", "previous_snapshot_id", "current_snapshot_id", "domain", "change_type", "materiality", "status", "detected_at"):
        op.create_index(f"ix_regulatory_changes_{column}", "regulatory_changes", [column])

    with op.batch_alter_table("verified_rules") as batch:
        batch.add_column(sa.Column("jurisdiction_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("regulatory_change_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("source_snapshot_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("effective_from", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("effective_to", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("approved_by", sa.String(), nullable=True))
        batch.add_column(sa.Column("published_at", sa.DateTime(), nullable=True))
        batch.create_foreign_key("fk_verified_rules_jurisdiction", "jurisdictions", ["jurisdiction_id"], ["id"])
        batch.create_foreign_key("fk_verified_rules_change", "regulatory_changes", ["regulatory_change_id"], ["id"])
        batch.create_foreign_key("fk_verified_rules_snapshot", "source_snapshots", ["source_snapshot_id"], ["id"])
        batch.create_index("ix_verified_rules_jurisdiction_id", ["jurisdiction_id"])
        batch.create_index("ix_verified_rules_regulatory_change_id", ["regulatory_change_id"])
        batch.create_index("ix_verified_rules_source_snapshot_id", ["source_snapshot_id"])

    with op.batch_alter_table("human_reviews") as batch:
        batch.add_column(sa.Column("regulatory_change_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key("fk_human_reviews_regulatory_change", "regulatory_changes", ["regulatory_change_id"], ["id"])
        batch.create_index("ix_human_reviews_regulatory_change_id", ["regulatory_change_id"])


def downgrade() -> None:
    with op.batch_alter_table("human_reviews") as batch:
        batch.drop_index("ix_human_reviews_regulatory_change_id")
        batch.drop_constraint("fk_human_reviews_regulatory_change", type_="foreignkey")
        batch.drop_column("regulatory_change_id")
    with op.batch_alter_table("verified_rules") as batch:
        for index in ("ix_verified_rules_source_snapshot_id", "ix_verified_rules_regulatory_change_id", "ix_verified_rules_jurisdiction_id"):
            batch.drop_index(index)
        for constraint in ("fk_verified_rules_snapshot", "fk_verified_rules_change", "fk_verified_rules_jurisdiction"):
            batch.drop_constraint(constraint, type_="foreignkey")
        for column in ("published_at", "approved_by", "effective_to", "effective_from", "source_snapshot_id", "regulatory_change_id", "jurisdiction_id"):
            batch.drop_column(column)
    op.drop_table("regulatory_changes")
    with op.batch_alter_table("source_snapshots") as batch:
        batch.drop_index("ix_source_snapshots_previous_snapshot_id")
        batch.drop_constraint("fk_source_snapshots_previous", type_="foreignkey")
        for column in ("parser_version", "retrieval_method", "http_status", "content_text", "previous_snapshot_id"):
            batch.drop_column(column)
    op.drop_table("source_monitors")
    with op.batch_alter_table("official_sources") as batch:
        batch.drop_index("ix_official_sources_regulatory_authority_id")
        batch.drop_index("ix_official_sources_jurisdiction_id")
        batch.drop_constraint("fk_official_sources_authority", type_="foreignkey")
        batch.drop_constraint("fk_official_sources_jurisdiction", type_="foreignkey")
        batch.drop_column("regulatory_authority_id")
        batch.drop_column("jurisdiction_id")
    op.drop_table("regulatory_authorities")
    op.drop_table("jurisdictions")
