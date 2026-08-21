"""Add Board-authored autonomy promotion eligibility criteria.

Revision ID: 0080_capability_autonomy_promotion_policy_foundation
Revises: 0079_capability_autonomy_evidence_profile_foundation
Create Date: 2026-08-22
"""

from alembic import op
import sqlalchemy as sa


revision = "0080_capability_autonomy_promotion_policy_foundation"
down_revision = "0079_capability_autonomy_evidence_profile_foundation"
branch_labels = None
depends_on = None


def _uuid() -> sa.Uuid:
    return sa.Uuid()


def upgrade() -> None:
    op.create_table(
        "capability_autonomy_promotion_policies",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("tenant_key", sa.String(), nullable=False),
        sa.Column("profile_id", _uuid(), nullable=False),
        sa.Column("profile_sequence", sa.Integer(), nullable=False),
        sa.Column("profile_record_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("position_id", _uuid(), nullable=False),
        sa.Column("position_key", sa.String(), nullable=False),
        sa.Column("capability_key", sa.String(), nullable=False),
        sa.Column("context_scope", sa.String(), nullable=False),
        sa.Column("policy_sequence", sa.Integer(), nullable=False),
        sa.Column("from_autonomy_level", sa.String(), nullable=False),
        sa.Column("target_autonomy_level", sa.String(), nullable=False),
        sa.Column("evidence_policy_version", sa.String(), nullable=False),
        sa.Column("min_qualifying_execution_volume", sa.Integer(), nullable=False),
        sa.Column("min_human_reviewed_count", sa.Integer(), nullable=False),
        sa.Column("min_evidence_grounding_rate", sa.Float(), nullable=False),
        sa.Column("min_human_acceptance_rate", sa.Float(), nullable=False),
        sa.Column("max_human_modification_rate", sa.Float(), nullable=False),
        sa.Column("max_human_rejection_rate", sa.Float(), nullable=False),
        sa.Column("max_verifier_contradiction_rate", sa.Float(), nullable=False),
        sa.Column("min_policy_compliance_rate", sa.Float(), nullable=False),
        sa.Column("min_freshness_compliance_rate", sa.Float(), nullable=False),
        sa.Column("max_critical_error_count", sa.Integer(), nullable=False),
        sa.Column("min_recovery_applicable_count", sa.Integer(), nullable=False),
        sa.Column("min_recovery_success_rate", sa.Float(), nullable=True),
        sa.Column("min_sla_met_rate", sa.Float(), nullable=False),
        sa.Column("max_incident_count", sa.Integer(), nullable=False),
        sa.Column("policy_reason", sa.String(), nullable=False),
        sa.Column("supersedes_policy_id", _uuid(), nullable=True),
        sa.Column("decision_activity_id", _uuid(), nullable=False),
        sa.Column("decision_activity_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key", sa.String(), nullable=False),
        sa.Column("record_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.CheckConstraint(
            "profile_sequence >= 1",
            name="ck_cap_auto_prom_profile_sequence_positive",
        ),
        sa.CheckConstraint(
            "policy_sequence >= 1",
            name="ck_cap_auto_prom_policy_sequence_positive",
        ),
        sa.CheckConstraint(
            "from_autonomy_level IN ('A0','A1','A2','A3','A4','A5')",
            name="ck_cap_auto_prom_policy_from_level",
        ),
        sa.CheckConstraint(
            "target_autonomy_level IN ('A0','A1','A2','A3','A4','A5')",
            name="ck_cap_auto_prom_policy_target_level",
        ),
        sa.CheckConstraint(
            "CASE target_autonomy_level "
            "WHEN 'A0' THEN 0 WHEN 'A1' THEN 1 WHEN 'A2' THEN 2 "
            "WHEN 'A3' THEN 3 WHEN 'A4' THEN 4 WHEN 'A5' THEN 5 END = "
            "CASE from_autonomy_level "
            "WHEN 'A0' THEN 0 WHEN 'A1' THEN 1 WHEN 'A2' THEN 2 "
            "WHEN 'A3' THEN 3 WHEN 'A4' THEN 4 WHEN 'A5' THEN 5 END + 1",
            name="ck_cap_auto_prom_policy_one_step",
        ),
        sa.CheckConstraint(
            "min_qualifying_execution_volume >= 1",
            name="ck_cap_auto_prom_policy_min_volume",
        ),
        sa.CheckConstraint(
            "min_human_reviewed_count >= 1",
            name="ck_cap_auto_prom_policy_min_reviewed",
        ),
        sa.CheckConstraint(
            "max_critical_error_count >= 0",
            name="ck_cap_auto_prom_policy_max_critical",
        ),
        sa.CheckConstraint(
            "min_recovery_applicable_count >= 0",
            name="ck_cap_auto_prom_policy_min_recovery",
        ),
        sa.CheckConstraint(
            "max_incident_count >= 0",
            name="ck_cap_auto_prom_policy_max_incident",
        ),
        sa.CheckConstraint(
            "min_evidence_grounding_rate >= 0 AND min_evidence_grounding_rate <= 1",
            name="ck_cap_auto_prom_minevidencegroundingrate",
        ),
        sa.CheckConstraint(
            "min_human_acceptance_rate >= 0 AND min_human_acceptance_rate <= 1",
            name="ck_cap_auto_prom_minhumanacceptancerate",
        ),
        sa.CheckConstraint(
            "max_human_modification_rate >= 0 AND max_human_modification_rate <= 1",
            name="ck_cap_auto_prom_maxhumanmodificationrate",
        ),
        sa.CheckConstraint(
            "max_human_rejection_rate >= 0 AND max_human_rejection_rate <= 1",
            name="ck_cap_auto_prom_maxhumanrejectionrate",
        ),
        sa.CheckConstraint(
            "max_verifier_contradiction_rate >= 0 AND max_verifier_contradiction_rate <= 1",
            name="ck_cap_auto_prom_maxverifiercontradictionrate",
        ),
        sa.CheckConstraint(
            "min_policy_compliance_rate >= 0 AND min_policy_compliance_rate <= 1",
            name="ck_cap_auto_prom_minpolicycompliancerate",
        ),
        sa.CheckConstraint(
            "min_freshness_compliance_rate >= 0 AND min_freshness_compliance_rate <= 1",
            name="ck_cap_auto_prom_minfreshnesscompliancerate",
        ),
        sa.CheckConstraint(
            "min_sla_met_rate >= 0 AND min_sla_met_rate <= 1",
            name="ck_cap_auto_prom_minslametrate",
        ),
        sa.CheckConstraint(
            "min_recovery_success_rate IS NULL OR "
            "(min_recovery_success_rate >= 0 AND min_recovery_success_rate <= 1)",
            name="ck_cap_auto_prom_recovery_rate",
        ),
        sa.CheckConstraint(
            "min_recovery_success_rate IS NULL OR min_recovery_applicable_count >= 1",
            name="ck_cap_auto_prom_recovery_sample",
        ),
        sa.CheckConstraint(
            "supersedes_policy_id IS NULL OR supersedes_policy_id <> id",
            name="ck_cap_auto_prom_policy_not_self_superseding",
        ),
        sa.CheckConstraint(
            "length(profile_record_fingerprint) = 64",
            name="ck_cap_auto_prom_profile_fingerprint",
        ),
        sa.CheckConstraint(
            "length(decision_activity_fingerprint) = 64",
            name="ck_cap_auto_prom_policy_activity_fingerprint",
        ),
        sa.CheckConstraint(
            "length(record_fingerprint) = 64",
            name="ck_cap_auto_prom_policy_record_fingerprint",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "profile_id"],
            ["capability_autonomy_profiles.tenant_key", "capability_autonomy_profiles.id"],
            name="fk_cap_auto_prom_policy_profile_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["position_id"],
            ["organization_positions.id"],
            name="fk_cap_auto_prom_policy_position",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "decision_activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_cap_auto_prom_policy_activity_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "supersedes_policy_id"],
            ["capability_autonomy_promotion_policies.tenant_key", "capability_autonomy_promotion_policies.id"],
            name="fk_cap_auto_prom_policy_supersedes_tenant",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_key", "id", name="uq_cap_auto_prom_policy_tenant_id"),
        sa.UniqueConstraint(
            "tenant_key",
            "idempotency_key",
            name="uq_cap_auto_prom_policy_idempotency",
        ),
        sa.UniqueConstraint(
            "tenant_key",
            "profile_id",
            "policy_sequence",
            name="uq_cap_auto_prom_policy_profile_sequence",
        ),
        sa.UniqueConstraint(
            "tenant_key",
            "supersedes_policy_id",
            name="uq_cap_auto_prom_policy_supersedes",
        ),
    )
    for name, columns in (
        ("ix_cap_auto_prom_policy_profile_seq", ["tenant_key", "profile_id", "policy_sequence"]),
        ("ix_cap_auto_prom_policy_tenant", ["tenant_key"]),
        ("ix_cap_auto_prom_policy_profile", ["profile_id"]),
        ("ix_cap_auto_prom_policy_position_key", ["position_key"]),
        ("ix_cap_auto_prom_policy_capability", ["capability_key"]),
        ("ix_cap_auto_prom_policy_context", ["context_scope"]),
        ("ix_cap_auto_prom_policy_from", ["from_autonomy_level"]),
        ("ix_cap_auto_prom_policy_target", ["target_autonomy_level"]),
        ("ix_cap_auto_prom_policy_evidence_ver", ["evidence_policy_version"]),
        ("ix_cap_auto_prom_policy_position", ["position_id"]),
        ("ix_cap_auto_prom_policy_activity", ["decision_activity_id"]),
        ("ix_cap_auto_prom_policy_record_fp", ["record_fingerprint"]),
        ("ix_cap_auto_prom_policy_created", ["created_at"]),
    ):
        op.create_index(name, "capability_autonomy_promotion_policies", columns)


def downgrade() -> None:
    op.drop_table("capability_autonomy_promotion_policies")
