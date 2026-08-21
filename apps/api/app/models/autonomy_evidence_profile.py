from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Index, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.domain import now_utc


_HUMAN_REVIEW_OUTCOME_CHECK = (
    "human_review_outcome IN ('accepted','modified','rejected','not_reviewed')"
)
_RECOVERY_OUTCOME_CHECK = (
    "recovery_outcome IN ('succeeded','failed','not_applicable')"
)


class CapabilityAutonomyEvidenceObservation(SQLModel, table=True):
    """Immutable qualifying shadow evidence for one exact I.1 autonomy profile."""

    __tablename__ = "capability_autonomy_evidence_observations"
    __table_args__ = (
        UniqueConstraint(
            "tenant_key",
            "id",
            name="uq_cap_autonomy_observation_tenant_id",
        ),
        UniqueConstraint(
            "tenant_key",
            "idempotency_key",
            name="uq_cap_autonomy_observation_idempotency",
        ),
        UniqueConstraint(
            "tenant_key",
            "profile_id",
            "source_activity_id",
            name="uq_cap_autonomy_observation_profile_activity",
        ),
        CheckConstraint(
            "profile_sequence >= 1",
            name="ck_cap_autonomy_observation_profile_sequence_positive",
        ),
        CheckConstraint(
            _HUMAN_REVIEW_OUTCOME_CHECK,
            name="ck_cap_autonomy_observation_human_outcome",
        ),
        CheckConstraint(
            _RECOVERY_OUTCOME_CHECK,
            name="ck_cap_autonomy_observation_recovery_outcome",
        ),
        CheckConstraint(
            "incident_count >= 0",
            name="ck_cap_autonomy_observation_incident_nonnegative",
        ),
        CheckConstraint(
            "length(source_activity_fingerprint) = 64",
            name="ck_cap_autonomy_observation_source_fingerprint",
        ),
        CheckConstraint(
            "length(record_fingerprint) = 64",
            name="ck_cap_autonomy_observation_record_fingerprint",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "profile_id"],
            ["capability_autonomy_profiles.tenant_key", "capability_autonomy_profiles.id"],
            name="fk_cap_autonomy_observation_profile_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "source_activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_cap_autonomy_observation_activity_tenant",
        ),
        ForeignKeyConstraint(
            ["position_id"],
            ["organization_positions.id"],
            name="fk_cap_autonomy_observation_position",
        ),
        Index(
            "ix_cap_autonomy_observation_profile_created",
            "tenant_key",
            "profile_id",
            "created_at",
        ),
        Index("ix_cap_auto_obs_evidence_policy", "evidence_policy_version"),
        Index("ix_cap_auto_obs_source_fingerprint", "source_activity_fingerprint"),
        Index("ix_cap_auto_obs_human_review", "human_review_outcome"),
        Index("ix_cap_auto_obs_verifier_contradiction", "verifier_contradiction"),
        Index("ix_cap_auto_obs_freshness_compliant", "freshness_compliant"),
        Index("ix_cap_auto_obs_created_actor_type", "created_by_actor_type"),
        Index("ix_cap_auto_obs_created_actor_key", "created_by_actor_key"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    tenant_key: str = Field(index=True)
    profile_id: UUID = Field(index=True)
    position_id: UUID = Field(index=True)
    position_key: str = Field(index=True)
    capability_key: str = Field(index=True)
    context_scope: str = Field(index=True)
    profile_sequence: int = Field(index=True)
    evidence_policy_version: str
    source_activity_id: UUID = Field(index=True)
    source_activity_fingerprint: str = Field(max_length=64)
    human_review_outcome: str
    evidence_grounded: bool = Field(index=True)
    verifier_contradiction: bool
    policy_compliant: bool = Field(index=True)
    freshness_compliant: bool
    critical_error: bool = Field(index=True)
    recovery_outcome: str = Field(index=True)
    sla_met: bool = Field(index=True)
    incident_count: int = Field(default=0)
    idempotency_key: str = Field(index=True)
    record_fingerprint: str = Field(max_length=64, index=True)
    created_by_actor_type: str
    created_by_actor_key: str
    created_at: datetime = Field(default_factory=now_utc, index=True)
