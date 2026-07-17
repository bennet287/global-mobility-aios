"""Immutable multi-year and multi-country mobility scenarios.

Revision ID: 0029_multi_year_mobility_scenarios
Revises: 0028_country_ranking_assessments
Create Date: 2026-07-14
"""
from alembic import op
import sqlalchemy as sa

revision = "0029_multi_year_mobility_scenarios"
down_revision = "0028_country_ranking_assessments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mobility_scenarios",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scenario_key", sa.String(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=True),
        sa.Column("profile_version", sa.Integer(), nullable=True),
        sa.Column("baseline_timeline_id", sa.Uuid(), nullable=True),
        sa.Column("scenario_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("supersedes_scenario_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="human_confirmed"),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("input_sha256", sa.String(), nullable=False),
        sa.Column("countries_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("pathway_version_ids_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("verified_rule_ids_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("regulatory_impact_ids_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("explicit_user_acceptance", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("user_attestation", sa.String(), nullable=False),
        sa.Column("review_notes", sa.String(), nullable=False),
        sa.Column("human_confirmation_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("original_scenario_preserved", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("global_coverage_claim_ready", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("warning", sa.String(), nullable=False),
        sa.Column("reviewed_by", sa.String(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"]),
        sa.ForeignKeyConstraint(["baseline_timeline_id"], ["mobility_timelines.id"]),
        sa.ForeignKeyConstraint(["supersedes_scenario_id"], ["mobility_scenarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "id", "lead_id", "profile_id", "profile_version", "baseline_timeline_id",
        "scenario_version", "supersedes_scenario_id", "status", "start_date",
        "input_sha256", "global_coverage_claim_ready", "reviewed_by", "reviewed_at", "created_at",
    ):
        op.create_index(f"ix_mobility_scenarios_{column}", "mobility_scenarios", [column])
    op.create_index(
        "ix_mobility_scenarios_scenario_key",
        "mobility_scenarios",
        ["scenario_key"],
        unique=True,
    )

    op.create_table(
        "mobility_scenario_stages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scenario_id", sa.Uuid(), nullable=False),
        sa.Column("stage_order", sa.Integer(), nullable=False),
        sa.Column("stage_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("country", sa.String(), nullable=False),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("pathway_id", sa.Uuid(), nullable=False),
        sa.Column("pathway_version_id", sa.Uuid(), nullable=False),
        sa.Column("planned_start", sa.DateTime(), nullable=False),
        sa.Column("planned_end", sa.DateTime(), nullable=False),
        sa.Column("duration_months", sa.Integer(), nullable=False),
        sa.Column("gap_months_before", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dependencies_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("verified_rule_ids_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("source_snapshot_ids_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("timing_basis_json", sa.String(), nullable=False, server_default="{}"),
        sa.Column("uncertainty_json", sa.String(), nullable=False, server_default="{}"),
        sa.Column("human_confirmation_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["scenario_id"], ["mobility_scenarios.id"]),
        sa.ForeignKeyConstraint(["pathway_id"], ["mobility_pathways.id"]),
        sa.ForeignKeyConstraint(["pathway_version_id"], ["mobility_pathway_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "id", "scenario_id", "stage_order", "stage_type", "country", "domain",
        "pathway_id", "pathway_version_id", "planned_start", "planned_end", "created_at",
    ):
        op.create_index(f"ix_mobility_scenario_stages_{column}", "mobility_scenario_stages", [column])


def downgrade() -> None:
    op.drop_table("mobility_scenario_stages")
    op.drop_table("mobility_scenarios")
