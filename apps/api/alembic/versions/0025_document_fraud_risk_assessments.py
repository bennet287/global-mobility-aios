"""Human-reviewed document fraud-risk indicators.

Revision ID: 0025_document_fraud_risk_assessments
Revises: 0024_document_requirement_assessments
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "0025_document_fraud_risk_assessments"
down_revision = "0024_document_requirement_assessments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_fraud_risk_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assessment_key", sa.String(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=True),
        sa.Column("profile_version", sa.Integer(), nullable=True),
        sa.Column("application_id", sa.Uuid(), nullable=True),
        sa.Column("result_status", sa.String(), nullable=False, server_default="no_indicators"),
        sa.Column("review_status", sa.String(), nullable=False, server_default="not_required"),
        sa.Column("risk_band", sa.String(), nullable=False, server_default="none"),
        sa.Column("indicator_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("high_indicator_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("warning_indicator_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("indicators_json", sa.String(), nullable=False),
        sa.Column("source_snapshot_json", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("automated_fraud_determination", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("adverse_action_taken", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("generated_by", sa.String(), nullable=False, server_default="system"),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"]),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "id",
        "lead_id",
        "profile_id",
        "profile_version",
        "application_id",
        "result_status",
        "review_status",
        "risk_band",
        "reviewed_by",
        "reviewed_at",
        "created_at",
    ):
        op.create_index(
            f"ix_document_fraud_risk_assessments_{column}",
            "document_fraud_risk_assessments",
            [column],
        )
    op.create_index(
        "ix_document_fraud_risk_assessments_assessment_key",
        "document_fraud_risk_assessments",
        ["assessment_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("document_fraud_risk_assessments")
