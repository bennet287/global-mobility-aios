from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Index, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.domain import now_utc


_AUTONOMY_LEVEL_CHECK = "{field} IN ('A0','A1','A2','A3','A4','A5')"
_ONE_STEP_PROMOTION_CHECK = (
    "CASE target_autonomy_level "
    "WHEN 'A0' THEN 0 WHEN 'A1' THEN 1 WHEN 'A2' THEN 2 "
    "WHEN 'A3' THEN 3 WHEN 'A4' THEN 4 WHEN 'A5' THEN 5 END = "
    "CASE from_autonomy_level "
    "WHEN 'A0' THEN 0 WHEN 'A1' THEN 1 WHEN 'A2' THEN 2 "
    "WHEN 'A3' THEN 3 WHEN 'A4' THEN 4 WHEN 'A5' THEN 5 END + 1"
)
_RATE_FIELDS = (
    "min_evidence_grounding_rate",
    "min_human_acceptance_rate",
    "max_human_modification_rate",
    "max_human_rejection_rate",
    "max_verifier_contradiction_rate",
    "min_policy_compliance_rate",
    "min_freshness_compliance_rate",
    "min_sla_met_rate",
)


class CapabilityAutonomyPromotionPolicy(SQLModel, table=True):
    """Append-only Board-authored criteria for one exact autonomy promotion step."""

    __tablename__ = "capability_autonomy_promotion_policies"
    __table_args__ = (
        UniqueConstraint(
            "tenant_key",
            "id",
            name="uq_cap_auto_prom_policy_tenant_id",
        ),
        UniqueConstraint(
            "tenant_key",
            "idempotency_key",
            name="uq_cap_auto_prom_policy_idempotency",
        ),
        UniqueConstraint(
            "tenant_key",
            "position_key",
            "capability_key",
            "context_scope",
            "from_autonomy_level",
            "target_autonomy_level",
            "evidence_policy_version",
            "policy_sequence",
            name="uq_cap_auto_prom_policy_scope_sequence",
        ),
        UniqueConstraint(
            "tenant_key",
            "supersedes_policy_id",
            name="uq_cap_auto_prom_policy_supersedes",
        ),
        CheckConstraint(
            "policy_sequence >= 1",
            name="ck_cap_auto_prom_policy_sequence_positive",
        ),
        CheckConstraint(
            _AUTONOMY_LEVEL_CHECK.format(field="from_autonomy_level"),
            name="ck_cap_auto_prom_policy_from_level",
        ),
        CheckConstraint(
            _AUTONOMY_LEVEL_CHECK.format(field="target_autonomy_level"),
            name="ck_cap_auto_prom_policy_target_level",
        ),
        CheckConstraint(
            _ONE_STEP_PROMOTION_CHECK,
            name="ck_cap_auto_prom_policy_one_step",
        ),
        CheckConstraint(
            "min_qualifying_execution_volume >= 1",
            name="ck_cap_auto_prom_policy_min_volume",
        ),
        CheckConstraint(
            "min_human_reviewed_count >= 1",
            name="ck_cap_auto_prom_policy_min_reviewed",
        ),
        CheckConstraint(
            "max_critical_error_count >= 0",
            name="ck_cap_auto_prom_policy_max_critical",
        ),
        CheckConstraint(
            "min_recovery_applicable_count >= 0",
            name="ck_cap_auto_prom_policy_min_recovery",
        ),
        CheckConstraint(
            "max_incident_count >= 0",
            name="ck_cap_auto_prom_policy_max_incident",
        ),
        *(
            CheckConstraint(
                f"{field} >= 0 AND {field} <= 1",
                name=f"ck_cap_auto_prom_{field.replace('_', '')[:34]}",
            )
            for field in _RATE_FIELDS
        ),
        CheckConstraint(
            "min_recovery_success_rate IS NULL OR "
            "(min_recovery_success_rate >= 0 AND min_recovery_success_rate <= 1)",
            name="ck_cap_auto_prom_recovery_rate",
        ),
        CheckConstraint(
            "min_recovery_success_rate IS NULL OR min_recovery_applicable_count >= 1",
            name="ck_cap_auto_prom_recovery_sample",
        ),
        CheckConstraint(
            "supersedes_policy_id IS NULL OR supersedes_policy_id <> id",
            name="ck_cap_auto_prom_policy_not_self_superseding",
        ),
        CheckConstraint(
            "length(decision_activity_fingerprint) = 64",
            name="ck_cap_auto_prom_policy_activity_fingerprint",
        ),
        CheckConstraint(
            "length(record_fingerprint) = 64",
            name="ck_cap_auto_prom_policy_record_fingerprint",
        ),
        ForeignKeyConstraint(
            ["position_id"],
            ["organization_positions.id"],
            name="fk_cap_auto_prom_policy_position",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "decision_activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_cap_auto_prom_policy_activity_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "supersedes_policy_id"],
            ["capability_autonomy_promotion_policies.tenant_key", "capability_autonomy_promotion_policies.id"],
            name="fk_cap_auto_prom_policy_supersedes_tenant",
        ),
        Index(
            "ix_cap_auto_prom_policy_scope_seq",
            "tenant_key",
            "position_key",
            "capability_key",
            "context_scope",
            "from_autonomy_level",
            "target_autonomy_level",
            "evidence_policy_version",
            "policy_sequence",
        ),
        Index("ix_cap_auto_prom_policy_tenant", "tenant_key"),
        Index("ix_cap_auto_prom_policy_position_key", "position_key"),
        Index("ix_cap_auto_prom_policy_capability", "capability_key"),
        Index("ix_cap_auto_prom_policy_context", "context_scope"),
        Index("ix_cap_auto_prom_policy_from", "from_autonomy_level"),
        Index("ix_cap_auto_prom_policy_target", "target_autonomy_level"),
        Index("ix_cap_auto_prom_policy_evidence_ver", "evidence_policy_version"),
        Index("ix_cap_auto_prom_policy_position", "position_id"),
        Index("ix_cap_auto_prom_policy_activity", "decision_activity_id"),
        Index("ix_cap_auto_prom_policy_record_fp", "record_fingerprint"),
        Index("ix_cap_auto_prom_policy_created", "created_at"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_key: str
    position_id: UUID
    position_key: str
    capability_key: str
    context_scope: str
    policy_sequence: int
    from_autonomy_level: str
    target_autonomy_level: str
    evidence_policy_version: str
    min_qualifying_execution_volume: int
    min_human_reviewed_count: int
    min_evidence_grounding_rate: float
    min_human_acceptance_rate: float
    max_human_modification_rate: float
    max_human_rejection_rate: float
    max_verifier_contradiction_rate: float
    min_policy_compliance_rate: float
    min_freshness_compliance_rate: float
    max_critical_error_count: int
    min_recovery_applicable_count: int = Field(default=0)
    min_recovery_success_rate: float | None = Field(default=None)
    min_sla_met_rate: float
    max_incident_count: int
    policy_reason: str
    supersedes_policy_id: UUID | None = Field(default=None)
    decision_activity_id: UUID
    decision_activity_fingerprint: str = Field(max_length=64)
    idempotency_key: str
    record_fingerprint: str = Field(max_length=64)
    effective_from: datetime = Field(default_factory=now_utc)
    created_at: datetime = Field(default_factory=now_utc)
    created_by: str
