from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.domain import now_utc


class EligibilityAssessmentRevision(SQLModel, table=True):
    """Canonical governed identity/version record for one EligibilityAssessment effect.

    Legacy ``EligibilityAssessment`` rows remain readable and writable through the
    pre-V1.3 path. A row in this companion table is what makes an assessment part of
    the governed canonical eligibility aggregate introduced by V1.3-G.3.
    """

    __tablename__ = "eligibility_assessment_revisions"
    __table_args__ = (
        UniqueConstraint(
            "tenant_key",
            "aggregate_key",
            "version",
            name="uq_eligibility_revision_aggregate_version",
        ),
        UniqueConstraint(
            "assessment_id",
            name="uq_eligibility_revision_assessment",
        ),
        UniqueConstraint(
            "tenant_key",
            "governance_activity_id",
            name="uq_eligibility_revision_governance_activity",
        ),
        UniqueConstraint(
            "tenant_key",
            "effect_fingerprint",
            name="uq_eligibility_revision_effect_fingerprint",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_eligibility_revision_version_positive",
        ),
        CheckConstraint(
            "lifecycle_status IN ('active','superseded')",
            name="ck_eligibility_revision_lifecycle_status",
        ),
        CheckConstraint(
            "length(original_action_fingerprint) = 64",
            name="ck_eligibility_revision_action_fingerprint",
        ),
        CheckConstraint(
            "length(intent_fingerprint) = 64",
            name="ck_eligibility_revision_intent_fingerprint",
        ),
        CheckConstraint(
            "length(readiness_fingerprint) = 64",
            name="ck_eligibility_revision_readiness_fingerprint",
        ),
        CheckConstraint(
            "length(verification_fingerprint) = 64",
            name="ck_eligibility_revision_verification_fingerprint",
        ),
        CheckConstraint(
            "length(verification_floor_fingerprint) = 64",
            name="ck_eligibility_revision_floor_fingerprint",
        ),
        CheckConstraint(
            "length(effect_fingerprint) = 64",
            name="ck_eligibility_revision_effect_fingerprint",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "governance_activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_eligibility_revision_governance_activity_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "verification_activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_eligibility_revision_verification_activity_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "verification_floor_activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_eligibility_revision_floor_activity_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "semantic_activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_eligibility_revision_semantic_activity_tenant",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    assessment_id: UUID = Field(index=True, foreign_key="eligibility_assessments.id")
    tenant_key: str = Field(index=True)
    aggregate_key: str = Field(index=True)
    version: int = Field(index=True)
    lifecycle_status: str = Field(default="active", index=True)
    supersedes_revision_id: Optional[UUID] = Field(
        default=None,
        index=True,
        foreign_key="eligibility_assessment_revisions.id",
    )
    lead_id: UUID = Field(index=True, foreign_key="leads.id")
    profile_id: UUID = Field(index=True, foreign_key="profiles.id")
    profile_version: int = Field(index=True)
    pathway_version_id: UUID = Field(index=True, foreign_key="mobility_pathway_versions.id")
    governance_activity_id: UUID = Field(index=True)
    verification_activity_id: UUID = Field(index=True)
    verification_floor_activity_id: UUID = Field(index=True)
    semantic_activity_id: Optional[UUID] = Field(default=None, index=True)
    original_action_fingerprint: str = Field(index=True, max_length=64)
    intent_fingerprint: str = Field(index=True, max_length=64)
    readiness_fingerprint: str = Field(index=True, max_length=64)
    verification_fingerprint: str = Field(index=True, max_length=64)
    verification_floor_fingerprint: str = Field(index=True, max_length=64)
    effect_fingerprint: str = Field(index=True, max_length=64)
    post_review_required: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
