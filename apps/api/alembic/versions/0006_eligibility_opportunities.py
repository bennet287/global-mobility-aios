"""Eligibility assessments and opportunity catalogue.

Revision ID: 0006_eligibility_opportunities
Revises: 0005_coach_training_intake
Create Date: 2026-07-13
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_eligibility_opportunities"
down_revision = "0005_coach_training_intake"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "eligibility_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=False),
        sa.Column("agent_run_id", sa.Uuid(), nullable=True),
        sa.Column("target_country", sa.String(), nullable=True),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=True),
        sa.Column("assessment_json", sa.String(), nullable=True),
        sa.Column("risks_json", sa.String(), nullable=True),
        sa.Column("required_documents_json", sa.String(), nullable=True),
        sa.Column("pathways_json", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["agent_run_id"], ["agent_runs.id"]),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_eligibility_assessments_id", "eligibility_assessments", ["id"])
    op.create_index("ix_eligibility_assessments_lead_id", "eligibility_assessments", ["lead_id"])
    op.create_index("ix_eligibility_assessments_agent_run_id", "eligibility_assessments", ["agent_run_id"])
    op.create_index("ix_eligibility_assessments_target_country", "eligibility_assessments", ["target_country"])
    op.create_index("ix_eligibility_assessments_domain", "eligibility_assessments", ["domain"])
    op.create_index("ix_eligibility_assessments_status", "eligibility_assessments", ["status"])

    op.create_table(
        "opportunities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("organization", sa.String(), nullable=True),
        sa.Column("country", sa.String(), nullable=False),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("profession_tags_json", sa.String(), nullable=True),
        sa.Column("field_tags_json", sa.String(), nullable=True),
        sa.Column("required_years_experience", sa.Float(), nullable=True),
        sa.Column("language_requirement", sa.String(), nullable=True),
        sa.Column("salary_eur", sa.Float(), nullable=True),
        sa.Column("budget_eur", sa.Float(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_opportunities_id", "opportunities", ["id"])
    op.create_index("ix_opportunities_country", "opportunities", ["country"])
    op.create_index("ix_opportunities_domain", "opportunities", ["domain"])
    op.create_index("ix_opportunities_active", "opportunities", ["active"])

    if not sa.inspect(op.get_bind()).has_table("audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("actor", sa.String(), nullable=False),
            sa.Column("action", sa.String(), nullable=False),
            sa.Column("entity_type", sa.String(), nullable=False),
            sa.Column("entity_id", sa.String(), nullable=True),
            sa.Column("before_state_json", sa.String(), nullable=True),
            sa.Column("after_state_json", sa.String(), nullable=True),
            sa.Column("reason", sa.String(), nullable=True),
            sa.Column("source", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_audit_logs_id", "audit_logs", ["id"])
        op.create_index("ix_audit_logs_actor", "audit_logs", ["actor"])
        op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
        op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
        op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])
        op.create_index("ix_audit_logs_source", "audit_logs", ["source"])
        op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    if sa.inspect(op.get_bind()).has_table("audit_logs"):
        op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
        op.drop_index("ix_audit_logs_source", table_name="audit_logs")
        op.drop_index("ix_audit_logs_entity_id", table_name="audit_logs")
        op.drop_index("ix_audit_logs_entity_type", table_name="audit_logs")
        op.drop_index("ix_audit_logs_action", table_name="audit_logs")
        op.drop_index("ix_audit_logs_actor", table_name="audit_logs")
        op.drop_index("ix_audit_logs_id", table_name="audit_logs")
        op.drop_table("audit_logs")

    op.drop_index("ix_opportunities_active", table_name="opportunities")
    op.drop_index("ix_opportunities_domain", table_name="opportunities")
    op.drop_index("ix_opportunities_country", table_name="opportunities")
    op.drop_index("ix_opportunities_id", table_name="opportunities")
    op.drop_table("opportunities")

    op.drop_index("ix_eligibility_assessments_status", table_name="eligibility_assessments")
    op.drop_index("ix_eligibility_assessments_domain", table_name="eligibility_assessments")
    op.drop_index("ix_eligibility_assessments_target_country", table_name="eligibility_assessments")
    op.drop_index("ix_eligibility_assessments_agent_run_id", table_name="eligibility_assessments")
    op.drop_index("ix_eligibility_assessments_lead_id", table_name="eligibility_assessments")
    op.drop_index("ix_eligibility_assessments_id", table_name="eligibility_assessments")
    op.drop_table("eligibility_assessments")
