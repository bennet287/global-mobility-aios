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
        sa.Column("source_snapshot_hash", sa.String(), nullable=False),
        sa.Column("publication_mode", sa.String(), nullable=False),
        sa.Column("actor_type", sa.String(), nullable=False),
        sa.Column("actor_key", sa.String(), nullable=False),
        sa.Column("authorization_audit_id", _uuid(), nullable=False),
        sa.Column("authority_bridge_audit_id", _uuid(), nullable=False),
        sa.Column("autonomy_profile_id", sa.String(), nullable=False),
        sa.Column("autonomy_profile_sequence", sa.Integer(), nullable=False),
        sa.Column("intended_rule_count", sa.Integer(), nullable=False),
        sa.Column("intended_mutations_sha256", sa.String(), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "regulatory_change_id",
            name="uq_reg_pub_set_change",
        ),
    )
    for column in (
        "id",
        "regulatory_change_id",
        "source_snapshot_id",
        "source_snapshot_hash",
        "publication_mode",
        "actor_type",
        "actor_key",
        "authorization_audit_id",
        "authority_bridge_audit_id",
        "autonomy_profile_id",
        "intended_mutations_sha256",
        "status",
        "published_at",
    ):
        op.create_index(
            f"ix_regulatory_publication_sets_{column}",
            "regulatory_publication_sets",
            [column],
        )

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
    for column in (
        "id",
        "human_review_id",
        "regulatory_change_id",
        "publication_set_id",
        "disposition",
        "actor_type",
        "actor_key",
        "authority_bridge_audit_id",
        "created_at",
    ):
        op.create_index(
            f"ix_regulatory_review_dispositions_{column}",
            "regulatory_review_dispositions",
            [column],
        )


def downgrade() -> None:
    op.drop_table("regulatory_review_dispositions")
    op.drop_table("regulatory_publication_sets")
