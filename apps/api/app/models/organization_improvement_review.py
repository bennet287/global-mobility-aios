from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Index, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.domain import now_utc


class OrganizationImprovementReviewPackage(SQLModel, table=True):
    """Immutable candidate-bound cross-team review requirement package.

    The package records which reviews are required and which canonical records are
    bound as evidence. It never owns the underlying review outcome, approval,
    promotion, deployment, authority, autonomy, tool, credential or budget truth.
    """

    __tablename__ = "organization_improvement_review_packages"
    __table_args__ = (
        UniqueConstraint("tenant_key", "id", name="uq_org_improvement_review_package_tenant_id"),
        UniqueConstraint("tenant_key", "package_key", name="uq_org_improvement_review_package_tenant_key"),
        UniqueConstraint(
            "tenant_key",
            "candidate_id",
            "package_version",
            name="uq_org_improvement_review_package_candidate_version",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "candidate_id"],
            ["organization_improvement_candidates.tenant_key", "organization_improvement_candidates.id"],
            name="fk_org_improvement_review_package_candidate_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "proposal_id"],
            ["organization_improvement_proposals.tenant_key", "organization_improvement_proposals.id"],
            name="fk_org_improvement_review_package_proposal_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "evaluation_campaign_id"],
            [
                "organization_improvement_evaluation_campaigns.tenant_key",
                "organization_improvement_evaluation_campaigns.id",
            ],
            name="fk_org_improvement_review_package_campaign_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "supersedes_package_id"],
            ["organization_improvement_review_packages.tenant_key", "organization_improvement_review_packages.id"],
            name="fk_org_improvement_review_package_supersedes_tenant",
        ),
        CheckConstraint("package_version >= 1", name="ck_org_improvement_review_package_version"),
        CheckConstraint(
            "risk_class IN ('low','medium','high','critical')",
            name="ck_org_improvement_review_package_risk_class",
        ),
        CheckConstraint(
            "length(candidate_fingerprint) = 64",
            name="ck_org_improvement_review_package_candidate_fp",
        ),
        CheckConstraint(
            "length(review_policy_fingerprint) = 64",
            name="ck_org_improvement_review_package_policy_fp",
        ),
        CheckConstraint(
            "length(record_fingerprint) = 64",
            name="ck_org_improvement_review_package_record_fp",
        ),
        CheckConstraint(
            "supersedes_package_id IS NULL OR supersedes_package_id <> id",
            name="ck_org_improvement_review_package_not_self",
        ),
        Index(
            "ix_org_improvement_review_package_tenant_candidate",
            "tenant_key",
            "candidate_id",
            "created_at",
        ),
        Index(
            "ix_org_improvement_review_package_tenant_risk",
            "tenant_key",
            "risk_class",
            "created_at",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_key: str
    package_key: str
    package_version: int
    candidate_id: UUID
    proposal_id: UUID
    evaluation_campaign_id: UUID
    candidate_fingerprint: str = Field(max_length=64)
    risk_class: str
    risk_basis_reference_ids_json: str
    review_policy_key: str
    review_policy_version: int
    review_policy_fingerprint: str = Field(max_length=64)
    required_review_kinds_json: str
    review_bindings_json: str
    supersedes_package_id: UUID | None = None
    record_fingerprint: str = Field(max_length=64)
    created_by: str
    created_at: datetime = Field(default_factory=now_utc)
