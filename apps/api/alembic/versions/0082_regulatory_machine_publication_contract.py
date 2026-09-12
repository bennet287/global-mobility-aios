"""Add Board-delegated machine publication contract state.

Revision ID: 0082_regulatory_machine_publication_contract
Revises: 0081_capability_autonomy_evidence_evaluation_policy
Create Date: 2026-09-13
"""

from alembic import op
import sqlalchemy as sa


revision = "0082_regulatory_machine_publication_contract"
down_revision = "0081_capability_autonomy_evidence_evaluation_policy"
branch_labels = None
depends_on = None


def _uuid() -> sa.Uuid:
    return sa.Uuid()


def upgrade() -> None:
    op.create_table(
        "regulatory_publication_sets",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("regulatory_change_id", _uuid(), nullable=False),
        sa.Column("source_snapshot_id", _uuid(), nullable=False),
        sa.Column("source_snapshot_hash", sa.String(length=64), nullable=False),
        sa.Column("publication_mode", sa.String(), nullable=False),
        sa.Column("actor_type", sa.String(), nullable=False),
        sa.Column("actor_key", sa.String(), nullable=False),
        sa.Column("authorization_audit_id", _uuid(), nullable=False),
        sa.Column("authority_bridge_audit_id", _uuid(), nullable=False),
        sa.Column("autonomy_profile_id", _uuid(), nullable=False),
        sa.Column("autonomy_profile_sequence", sa.Integer(), nullable=False),
        sa.Column("intended_rule_count", sa.Integer(), nullable=False),
        sa.Column("intended_mutations_sha256", sa.String(length=64), nullable=False),
        sa.Column("published_rules_json", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "length(source_snapshot_hash) = 64",
            name="ck_reg_pub_set_snapshot_hash",
        ),
        sa.CheckConstraint(
            "length(intended_mutations_sha256) = 64",
            name="ck_reg_pub_set_mutations_hash",
        ),
        sa.CheckConstraint(
            "autonomy_profile_sequence >= 1",
            name="ck_reg_pub_set_profile_sequence_positive",
        ),
        sa.CheckConstraint(
            "intended_rule_count >= 1 AND intended_rule_count <= 100",
            name="ck_reg_pub_set_rule_count_bound",
        ),
        sa.ForeignKeyConstraint(
            ["regulatory_change_id"],
            ["regulatory_changes.id"],
            name="fk_reg_pub_set_change",
        ),
        sa.ForeignKeyConstraint(
            ["source_snapshot_id"],
            ["source_snapshots.id"],
            name="fk_reg_pub_set_snapshot",
        ),
        sa.ForeignKeyConstraint(
            ["authorization_audit_id"],
            ["audit_logs.id"],
            name="fk_reg_pub_set_authorization_audit",
        ),
        sa.ForeignKeyConstraint(
            ["authority_bridge_audit_id"],
            ["audit_logs.id"],
            name="fk_reg_pub_set_bridge_audit",
        ),
        sa.ForeignKeyConstraint(
            ["autonomy_profile_id"],
            ["capability_autonomy_profiles.id"],
            name="fk_reg_pub_set_autonomy_profile",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "regulatory_change_id",
            name="uq_reg_pub_set_change",
        ),
    )
    for name, columns in (
        ("ix_reg_pub_set_source_snapshot_id", ["source_snapshot_id"]),
        ("ix_reg_pub_set_publication_mode", ["publication_mode"]),
        ("ix_reg_pub_set_actor_type", ["actor_type"]),
        ("ix_reg_pub_set_actor_key", ["actor_key"]),
        ("ix_reg_pub_set_authorization_audit_id", ["authorization_audit_id"]),
        ("ix_reg_pub_set_authority_bridge_audit_id", ["authority_bridge_audit_id"]),
        ("ix_reg_pub_set_autonomy_profile_id", ["autonomy_profile_id"]),
        ("ix_reg_pub_set_intended_mutations_sha256", ["intended_mutations_sha256"]),
        ("ix_reg_pub_set_status", ["status"]),
        ("ix_reg_pub_set_published_at", ["published_at"]),
    ):
        op.create_index(name, "regulatory_publication_sets", columns)

    op.create_table(
        "regulatory_review_dispositions",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("human_review_id", _uuid(), nullable=False),
        sa.Column("regulatory_change_id", _uuid(), nullable=False),
        sa.Column("publication_set_id", _uuid(), nullable=False),
        sa.Column("disposition", sa.String(), nullable=False),
        sa.Column("actor_type", sa.String(), nullable=False),
        sa.Column("actor_key", sa.String(), nullable=False),
        sa.Column("authority_bridge_audit_id", _uuid(), nullable=False),
        sa.Column("disposition_reason", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["human_review_id"],
            ["human_reviews.id"],
            name="fk_reg_review_disposition_review",
        ),
        sa.ForeignKeyConstraint(
            ["regulatory_change_id"],
            ["regulatory_changes.id"],
            name="fk_reg_review_disposition_change",
        ),
        sa.ForeignKeyConstraint(
            ["publication_set_id"],
            ["regulatory_publication_sets.id"],
            name="fk_reg_review_disposition_publication_set",
        ),
        sa.ForeignKeyConstraint(
            ["authority_bridge_audit_id"],
            ["audit_logs.id"],
            name="fk_reg_review_disposition_bridge_audit",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "human_review_id",
            name="uq_reg_review_disposition_review",
        ),
    )
    for name, columns in (
        ("ix_reg_review_disposition_change", ["regulatory_change_id"]),
        ("ix_reg_review_disposition_publication_set", ["publication_set_id"]),
        ("ix_reg_review_disposition_disposition", ["disposition"]),
        ("ix_reg_review_disposition_actor_type", ["actor_type"]),
        ("ix_reg_review_disposition_actor_key", ["actor_key"]),
        ("ix_reg_review_disposition_bridge_audit", ["authority_bridge_audit_id"]),
        ("ix_reg_review_disposition_created_at", ["created_at"]),
    ):
        op.create_index(name, "regulatory_review_dispositions", columns)


def downgrade() -> None:
    op.drop_table("regulatory_review_dispositions")
    op.drop_table("regulatory_publication_sets")
