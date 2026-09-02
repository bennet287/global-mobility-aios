from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Index, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.domain import now_utc


_AUTONOMY_LEVEL_CHECK = "autonomy_level IN ('A0','A1','A2','A3','A4','A5')"
_BOARD_CEILING_CHECK = "board_ceiling IN ('A0','A1','A2','A3','A4','A5')"
_RISK_CEILING_CHECK = "risk_ceiling IN ('R0','R1','R2','R3','R4','R5')"
_AUTONOMY_WITHIN_BOARD_CEILING_CHECK = """
CASE autonomy_level
    WHEN 'A0' THEN 0 WHEN 'A1' THEN 1 WHEN 'A2' THEN 2
    WHEN 'A3' THEN 3 WHEN 'A4' THEN 4 WHEN 'A5' THEN 5
END
<=
CASE board_ceiling
    WHEN 'A0' THEN 0 WHEN 'A1' THEN 1 WHEN 'A2' THEN 2
    WHEN 'A3' THEN 3 WHEN 'A4' THEN 4 WHEN 'A5' THEN 5
END
"""


class CapabilityAutonomyProfile(SQLModel, table=True):
    """Immutable Board-established autonomy truth for one capability/context scope."""

    __tablename__ = "capability_autonomy_profiles"
    __table_args__ = (
        UniqueConstraint("tenant_key", "id", name="uq_cap_autonomy_profile_tenant_id"),
        UniqueConstraint(
            "tenant_key",
            "idempotency_key",
            name="uq_cap_autonomy_profile_idempotency",
        ),
        UniqueConstraint(
            "tenant_key",
            "position_key",
            "capability_key",
            "context_scope",
            "profile_sequence",
            name="uq_cap_autonomy_profile_scope_sequence",
        ),
        UniqueConstraint(
            "tenant_key",
            "supersedes_profile_id",
            name="uq_cap_autonomy_profile_supersedes",
        ),
        CheckConstraint("profile_sequence >= 1", name="ck_cap_autonomy_profile_sequence_positive"),
        CheckConstraint(_AUTONOMY_LEVEL_CHECK, name="ck_cap_autonomy_profile_level"),
        CheckConstraint(_BOARD_CEILING_CHECK, name="ck_cap_autonomy_profile_board_ceiling"),
        CheckConstraint(_RISK_CEILING_CHECK, name="ck_cap_autonomy_profile_risk_ceiling"),
        CheckConstraint(
            _AUTONOMY_WITHIN_BOARD_CEILING_CHECK,
            name="ck_cap_autonomy_profile_within_board_ceiling",
        ),
        CheckConstraint(
            "supersedes_profile_id IS NULL OR supersedes_profile_id <> id",
            name="ck_cap_autonomy_profile_not_self_superseding",
        ),
        CheckConstraint(
            "length(record_fingerprint) = 64",
            name="ck_cap_autonomy_profile_fingerprint",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "decision_activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_cap_autonomy_profile_decision_activity_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "supersedes_profile_id"],
            ["capability_autonomy_profiles.tenant_key", "capability_autonomy_profiles.id"],
            name="fk_cap_autonomy_profile_supersedes_tenant",
        ),
        Index(
            "ix_cap_autonomy_profile_scope_sequence",
            "tenant_key",
            "position_key",
            "capability_key",
            "context_scope",
            "profile_sequence",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    tenant_key: str = Field(index=True)
    position_key: str = Field(index=True)
    capability_key: str = Field(index=True)
    context_scope: str = Field(index=True)
    profile_sequence: int = Field(index=True)
    autonomy_level: str = Field(index=True)
    board_ceiling: str = Field(index=True)
    authority_requirement: str = Field(index=True)
    risk_ceiling: str = Field(index=True)
    evidence_policy_version: str = Field(index=True)
    supersedes_profile_id: UUID | None = Field(default=None, index=True)
    governance_source: str = Field(default="human_board", index=True)
    decision_activity_id: UUID = Field(index=True)
    idempotency_key: str = Field(index=True)
    record_fingerprint: str = Field(max_length=64, index=True)
    effective_from: datetime = Field(default_factory=now_utc, index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    created_by: str = Field(index=True)


class CapabilityAutonomyEvidence(SQLModel, table=True):
    """Immutable deterministic lineage from an autonomy profile to canonical Activity."""

    __tablename__ = "capability_autonomy_evidence"
    __table_args__ = (
        UniqueConstraint("tenant_key", "id", name="uq_cap_autonomy_evidence_tenant_id"),
        UniqueConstraint(
            "tenant_key",
            "profile_id",
            "evidence_sequence",
            name="uq_cap_autonomy_evidence_profile_sequence",
        ),
        UniqueConstraint(
            "tenant_key",
            "profile_id",
            "source_activity_id",
            name="uq_cap_autonomy_evidence_profile_activity",
        ),
        CheckConstraint("evidence_sequence >= 1", name="ck_cap_autonomy_evidence_sequence_positive"),
        CheckConstraint(
            "length(source_activity_fingerprint) = 64",
            name="ck_cap_autonomy_evidence_source_fingerprint",
        ),
        CheckConstraint(
            "length(record_fingerprint) = 64",
            name="ck_cap_autonomy_evidence_record_fingerprint",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "profile_id"],
            ["capability_autonomy_profiles.tenant_key", "capability_autonomy_profiles.id"],
            name="fk_cap_autonomy_evidence_profile_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "source_activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_cap_autonomy_evidence_activity_tenant",
        ),
        Index(
            "ix_cap_autonomy_evidence_profile_sequence",
            "tenant_key",
            "profile_id",
            "evidence_sequence",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    tenant_key: str = Field(index=True)
    profile_id: UUID = Field(index=True)
    evidence_sequence: int = Field(index=True)
    source_activity_id: UUID = Field(index=True)
    source_activity_fingerprint: str = Field(max_length=64, index=True)
    record_fingerprint: str = Field(max_length=64, index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
