"""Coach reviews, training cases, and public intake sessions v7.3

Revision ID: 0005_coach_training_intake
Revises: 0004_agent_run_status
Create Date: 2026-07-13
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_coach_training_intake"
down_revision = "0004_agent_run_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "coach_reviews",
        sa.Column("id", sa.CHAR(32), nullable=False),
        sa.Column("lead_id", sa.CHAR(32), nullable=True),
        sa.Column("agent_run_id", sa.CHAR(32), nullable=True),
        sa.Column("coach_agent_name", sa.String(), nullable=False),
        sa.Column("target_agent_name", sa.String(), nullable=False),
        sa.Column("conclusion_valid", sa.Boolean(), nullable=False),
        sa.Column("missing_facts_json", sa.Text(), nullable=True),
        sa.Column("source_issues_json", sa.Text(), nullable=True),
        sa.Column("corrected_summary", sa.Text(), nullable=True),
        sa.Column("confidence", sa.String(), nullable=False),
        sa.Column("operator_feedback", sa.Text(), nullable=True),
        sa.Column("operator_override_json", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["agent_run_id"], ["agent_runs.id"]),
    )
    op.create_index("ix_coach_reviews_lead_id", "coach_reviews", ["lead_id"])
    op.create_index("ix_coach_reviews_agent_run_id", "coach_reviews", ["agent_run_id"])
    op.create_index("ix_coach_reviews_target_agent_name", "coach_reviews", ["target_agent_name"])
    op.create_index("ix_coach_reviews_status", "coach_reviews", ["status"])

    op.create_table(
        "training_cases",
        sa.Column("id", sa.CHAR(32), nullable=False),
        sa.Column("lead_id", sa.CHAR(32), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("country", sa.String(), nullable=False),
        sa.Column("profession", sa.String(), nullable=False),
        sa.Column("scenario_json", sa.Text(), nullable=True),
        sa.Column("expected_outcome_json", sa.Text(), nullable=True),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("times_run", sa.Integer(), nullable=False),
        sa.Column("avg_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
    )
    op.create_index("ix_training_cases_lead_id", "training_cases", ["lead_id"])
    op.create_index("ix_training_cases_country", "training_cases", ["country"])
    op.create_index("ix_training_cases_profession", "training_cases", ["profession"])

    op.create_table(
        "intake_sessions",
        sa.Column("id", sa.CHAR(32), nullable=False),
        sa.Column("lead_id", sa.CHAR(32), nullable=True),
        sa.Column("session_token", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("answers_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_token"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
    )
    op.create_index("ix_intake_sessions_session_token", "intake_sessions", ["session_token"])
    op.create_index("ix_intake_sessions_lead_id", "intake_sessions", ["lead_id"])


def downgrade() -> None:
    op.drop_index("ix_intake_sessions_lead_id", table_name="intake_sessions")
    op.drop_index("ix_intake_sessions_session_token", table_name="intake_sessions")
    op.drop_table("intake_sessions")

    op.drop_index("ix_training_cases_profession", table_name="training_cases")
    op.drop_index("ix_training_cases_country", table_name="training_cases")
    op.drop_index("ix_training_cases_lead_id", table_name="training_cases")
    op.drop_table("training_cases")

    op.drop_index("ix_coach_reviews_status", table_name="coach_reviews")
    op.drop_index("ix_coach_reviews_target_agent_name", table_name="coach_reviews")
    op.drop_index("ix_coach_reviews_agent_run_id", table_name="coach_reviews")
    op.drop_index("ix_coach_reviews_lead_id", table_name="coach_reviews")
    op.drop_table("coach_reviews")
