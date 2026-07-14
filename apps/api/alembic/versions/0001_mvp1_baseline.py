"""MVP-1 baseline schema.

Revision ID: 0001_mvp1_baseline
Revises:
Create Date: 2026-07-06

The baseline is deliberately static. Importing current SQLModel metadata here
would cause a fresh database to create tables owned by later migrations.
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_mvp1_baseline"
down_revision = None
branch_labels = None
depends_on = None


def _index(table: str, column: str) -> None:
    op.create_index(f"ix_{table}_{column}", table, [column])


def upgrade() -> None:
    op.create_table(
        "leads",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("intent", sa.String(length=12), nullable=False),
        sa.Column("target_country", sa.String(), nullable=True),
        sa.Column("status", sa.String(length=15), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("leads", "id")
    _index("leads", "email")

    op.create_table(
        "verification_audits",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("claim", sa.String(), nullable=False),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("country", sa.String(), nullable=True),
        sa.Column("verdict", sa.String(length=12), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("official_sources_found", sa.Integer(), nullable=False),
        sa.Column("requires_human_review", sa.Boolean(), nullable=False),
        sa.Column("explanation", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("verification_audits", "id")

    op.create_table(
        "applications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=True),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("target_country", sa.String(), nullable=True),
        sa.Column("target_institution_or_employer", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("applications", "id")
    _index("applications", "lead_id")

    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=True),
        sa.Column("document_type", sa.String(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("storage_key", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("extracted_metadata_json", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("documents", "id")
    _index("documents", "lead_id")

    op.create_table(
        "profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=False),
        sa.Column("profile_type", sa.String(), nullable=False),
        sa.Column("highest_qualification", sa.String(), nullable=True),
        sa.Column("field_of_study", sa.String(), nullable=True),
        sa.Column("current_country", sa.String(), nullable=True),
        sa.Column("target_country", sa.String(), nullable=True),
        sa.Column("desired_role", sa.String(), nullable=True),
        sa.Column("years_experience", sa.Float(), nullable=True),
        sa.Column("budget_eur", sa.Float(), nullable=True),
        sa.Column("language_scores_json", sa.String(), nullable=True),
        sa.Column("skills_json", sa.String(), nullable=True),
        sa.Column("missing_fields_json", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("profiles", "id")
    _index("profiles", "lead_id")

    op.create_table(
        "visa_checks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=True),
        sa.Column("target_country", sa.String(), nullable=True),
        sa.Column("visa_type", sa.String(), nullable=True),
        sa.Column("eligibility_status", sa.String(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("missing_requirements_json", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("visa_checks", "id")
    _index("visa_checks", "lead_id")

    op.create_table(
        "workflow_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workflow_name", sa.String(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=18), nullable=False),
        sa.Column("detected_intent", sa.String(length=12), nullable=False),
        sa.Column("route", sa.String(), nullable=True),
        sa.Column("input_json", sa.String(), nullable=True),
        sa.Column("output_json", sa.String(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("workflow_runs", "id")
    _index("workflow_runs", "lead_id")

    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workflow_run_id", sa.Uuid(), nullable=True),
        sa.Column("lead_id", sa.Uuid(), nullable=True),
        sa.Column("agent_name", sa.String(), nullable=False),
        sa.Column("task", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("input_json", sa.String(), nullable=True),
        sa.Column("output_json", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["workflow_runs.id"]),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("agent_runs", "id")
    _index("agent_runs", "workflow_run_id")
    _index("agent_runs", "lead_id")

    op.create_table(
        "follow_ups",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=False),
        sa.Column("workflow_run_id", sa.Uuid(), nullable=True),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=9), nullable=False),
        sa.Column("due_at", sa.DateTime(), nullable=True),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["workflow_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("follow_ups", "id")
    _index("follow_ups", "lead_id")
    _index("follow_ups", "workflow_run_id")

    op.create_table(
        "truth_claims",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=True),
        sa.Column("workflow_run_id", sa.Uuid(), nullable=True),
        sa.Column("claim", sa.String(), nullable=False),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("country", sa.String(), nullable=True),
        sa.Column("verdict", sa.String(length=12), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("requires_human_review", sa.Boolean(), nullable=False),
        sa.Column("explanation", sa.String(), nullable=False),
        sa.Column("red_flags_json", sa.String(), nullable=True),
        sa.Column("recommended_next_step", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["workflow_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("truth_claims", "id")
    _index("truth_claims", "lead_id")
    _index("truth_claims", "workflow_run_id")

    op.create_table(
        "human_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=True),
        sa.Column("truth_claim_id", sa.Uuid(), nullable=True),
        sa.Column("workflow_run_id", sa.Uuid(), nullable=True),
        sa.Column("review_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=8), nullable=False),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("reviewer_notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["truth_claim_id"], ["truth_claims.id"]),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["workflow_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("human_reviews", "id")
    _index("human_reviews", "lead_id")
    _index("human_reviews", "truth_claim_id")
    _index("human_reviews", "workflow_run_id")

    op.create_table(
        "source_references",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("truth_claim_id", sa.Uuid(), nullable=True),
        sa.Column("source_url", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("country", sa.String(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["truth_claim_id"], ["truth_claims.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("source_references", "id")
    _index("source_references", "truth_claim_id")


def downgrade() -> None:
    for table in (
        "source_references",
        "human_reviews",
        "truth_claims",
        "follow_ups",
        "agent_runs",
        "workflow_runs",
        "visa_checks",
        "profiles",
        "documents",
        "applications",
        "verification_audits",
        "leads",
    ):
        op.drop_table(table)
