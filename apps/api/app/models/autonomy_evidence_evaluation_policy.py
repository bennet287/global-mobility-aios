from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Index, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.domain import now_utc


class CapabilityAutonomyEvidenceEvaluationPolicy(SQLModel, table=True):
    """Append-only Board policy for qualified, time-bounded I.4 evidence evaluation."""

    __tablename__ = "capability_autonomy_evidence_evaluation_policies"
    __table_args__ = (
        UniqueConstraint(
            "tenant_key",
            "id",
            name="uq_cap_auto_eval_policy_tenant_id",
        ),
        UniqueConstraint(
            "tenant_key",
            "idempotency_key",
            name="uq_cap_auto_eval_policy_idempotency",
        ),
        UniqueConstraint(
            "tenant_key",
            "profile_id",
            "policy_sequence",
            name="uq_cap_auto_eval_policy_profile_sequence",
        ),
        UniqueConstraint(
            "tenant_key",
            "supersedes_policy_id",
            name="uq_cap_auto_eval_policy_supersedes",
        ),
        CheckConstraint(
            "profile_sequence >= 1",
            name="ck_cap_auto_eval_profile_sequence_positive",
        ),
        CheckConstraint(
            "policy_sequence >= 1",
            name="ck_cap_auto_eval_policy_sequence_positive",
        ),
        CheckConstraint(
            "max_observation_age_seconds >= 1",
            name="ck_cap_auto_eval_observation_age_positive",
        ),
        CheckConstraint(
            "max_source_age_seconds >= 1",
            name="ck_cap_auto_eval_source_age_positive",
        ),
        CheckConstraint(
            "max_candidate_observations >= 1 AND max_candidate_observations <= 5000",
            name="ck_cap_auto_eval_candidate_bound",
        ),
        CheckConstraint(
            "supersedes_policy_id IS NULL OR supersedes_policy_id <> id",
            name="ck_cap_auto_eval_not_self_superseding",
        ),
        CheckConstraint(
            "length(profile_record_fingerprint) = 64",
            name="ck_cap_auto_eval_profile_fingerprint",
        ),
        CheckConstraint(
            "length(decision_activity_fingerprint) = 64",
            name="ck_cap_auto_eval_activity_fingerprint",
        ),
        CheckConstraint(
            "length(record_fingerprint) = 64",
            name="ck_cap_auto_eval_record_fingerprint",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "profile_id"],
            ["capability_autonomy_profiles.tenant_key", "capability_autonomy_profiles.id"],
            name="fk_cap_auto_eval_profile_tenant",
        ),
        ForeignKeyConstraint(
            ["position_id"],
            ["organization_positions.id"],
            name="fk_cap_auto_eval_position",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "decision_activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_cap_auto_eval_activity_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "supersedes_policy_id"],
            [
                "capability_autonomy_evidence_evaluation_policies.tenant_key",
                "capability_autonomy_evidence_evaluation_policies.id",
            ],
            name="fk_cap_auto_eval_supersedes_tenant",
        ),
        Index(
            "ix_cap_auto_eval_policy_profile_seq",
            "tenant_key",
            "profile_id",
            "policy_sequence",
        ),
        Index(
            "ix_cap_auto_eval_policy_profile_created",
            "tenant_key",
            "profile_id",
            "created_at",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_key: str
    profile_id: UUID
    profile_sequence: int
    profile_record_fingerprint: str = Field(max_length=64)
    position_id: UUID
    position_key: str
    capability_key: str
    context_scope: str
    policy_sequence: int
    qualification_contract: str
    max_observation_age_seconds: int
    max_source_age_seconds: int
    max_candidate_observations: int
    policy_reason: str
    supersedes_policy_id: UUID | None = Field(default=None)
    decision_activity_id: UUID
    decision_activity_fingerprint: str = Field(max_length=64)
    idempotency_key: str
    record_fingerprint: str = Field(max_length=64)
    effective_from: datetime = Field(default_factory=now_utc)
    created_at: datetime = Field(default_factory=now_utc)
    created_by: str
