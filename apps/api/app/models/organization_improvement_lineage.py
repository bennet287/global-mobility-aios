from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Index, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.domain import now_utc


class OrganizationImprovementProposal(SQLModel, table=True):
    """Authority-neutral proposal to investigate a bounded capability improvement.

    This record identifies improvement intent and baseline lineage only. It does not
    grant authority, autonomy, credentials, tools, budget, deployment, external
    action, evaluation success, or active-version status.
    """

    __tablename__ = "organization_improvement_proposals"
    __table_args__ = (
        UniqueConstraint("tenant_key", "id", name="uq_org_improvement_proposal_tenant_id"),
        UniqueConstraint(
            "tenant_key",
            "proposal_key",
            name="uq_org_improvement_proposal_tenant_key",
        ),
        UniqueConstraint(
            "tenant_key",
            "supersedes_proposal_id",
            name="uq_org_improvement_proposal_supersedes",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "work_item_id"],
            ["organizational_work_items.tenant_key", "organizational_work_items.id"],
            name="fk_org_improvement_proposal_work_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "supersedes_proposal_id"],
            ["organization_improvement_proposals.tenant_key", "organization_improvement_proposals.id"],
            name="fk_org_improvement_proposal_supersedes_tenant",
        ),
        CheckConstraint(
            "status IN ('open','withdrawn')",
            name="ck_org_improvement_proposal_status",
        ),
        CheckConstraint(
            "length(baseline_fingerprint) = 64",
            name="ck_org_improvement_proposal_baseline_fingerprint",
        ),
        CheckConstraint(
            "length(record_fingerprint) = 64",
            name="ck_org_improvement_proposal_record_fingerprint",
        ),
        CheckConstraint(
            "supersedes_proposal_id IS NULL OR supersedes_proposal_id <> id",
            name="ck_org_improvement_proposal_not_self_superseding",
        ),
        Index(
            "ix_org_improvement_proposal_tenant_target",
            "tenant_key",
            "target_type",
            "target_reference",
        ),
        Index(
            "ix_org_improvement_proposal_tenant_work",
            "tenant_key",
            "work_item_id",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_key: str = Field(index=True)
    proposal_key: str = Field(index=True)
    work_item_id: UUID = Field(index=True)
    target_type: str = Field(index=True)
    target_reference: str
    baseline_version: str
    baseline_fingerprint: str = Field(max_length=64, index=True)
    problem_statement: str
    hypothesis: str
    expected_improvement: str
    acceptance_constraints_json: str
    evidence_reference_ids_json: str
    supersedes_proposal_id: UUID | None = Field(default=None, index=True)
    status: str = Field(default="open", index=True)
    record_fingerprint: str = Field(max_length=64, index=True)
    created_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    withdrawn_by: str | None = Field(default=None, index=True)
    withdrawn_reason: str | None = None
    withdrawn_at: datetime | None = Field(default=None, index=True)


class OrganizationImprovementCandidate(SQLModel, table=True):
    """Immutable candidate-artifact lineage under one improvement proposal.

    Candidate preparation is not approval, evaluation success, activation, autonomy,
    deployment, permission/tool authority, spending authority, or production truth.
    """

    __tablename__ = "organization_improvement_candidates"
    __table_args__ = (
        UniqueConstraint("tenant_key", "id", name="uq_org_improvement_candidate_tenant_id"),
        UniqueConstraint(
            "tenant_key",
            "candidate_key",
            name="uq_org_improvement_candidate_tenant_key",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "proposal_id"],
            ["organization_improvement_proposals.tenant_key", "organization_improvement_proposals.id"],
            name="fk_org_improvement_candidate_proposal_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "parent_candidate_id"],
            ["organization_improvement_candidates.tenant_key", "organization_improvement_candidates.id"],
            name="fk_org_improvement_candidate_parent_tenant",
        ),
        CheckConstraint(
            "status IN ('prepared','withdrawn')",
            name="ck_org_improvement_candidate_status",
        ),
        CheckConstraint(
            "length(baseline_fingerprint) = 64",
            name="ck_org_improvement_candidate_baseline_fingerprint",
        ),
        CheckConstraint(
            "length(candidate_fingerprint) = 64",
            name="ck_org_improvement_candidate_artifact_fingerprint",
        ),
        CheckConstraint(
            "length(record_fingerprint) = 64",
            name="ck_org_improvement_candidate_record_fingerprint",
        ),
        CheckConstraint(
            "parent_candidate_id IS NULL OR parent_candidate_id <> id",
            name="ck_org_improvement_candidate_not_self_parent",
        ),
        Index(
            "ix_org_improvement_candidate_tenant_proposal",
            "tenant_key",
            "proposal_id",
            "created_at",
        ),
        Index(
            "ix_org_improvement_candidate_tenant_target",
            "tenant_key",
            "target_type",
            "target_reference",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_key: str = Field(index=True)
    candidate_key: str = Field(index=True)
    proposal_id: UUID = Field(index=True)
    parent_candidate_id: UUID | None = Field(default=None, index=True)
    target_type: str = Field(index=True)
    target_reference: str
    baseline_version: str
    baseline_fingerprint: str = Field(max_length=64, index=True)
    candidate_version: str
    candidate_fingerprint: str = Field(max_length=64, index=True)
    artifact_reference: str
    implementation_provenance_json: str
    candidate_hypothesis: str
    expected_improvement: str
    acceptance_constraints_json: str
    status: str = Field(default="prepared", index=True)
    record_fingerprint: str = Field(max_length=64, index=True)
    created_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    withdrawn_by: str | None = Field(default=None, index=True)
    withdrawn_reason: str | None = None
    withdrawn_at: datetime | None = Field(default=None, index=True)
