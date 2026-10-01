from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Index, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.domain import now_utc


class OrganizationImprovementEvaluationCampaign(SQLModel, table=True):
    """Versioned current-vs-candidate comparison contract.

    A campaign is evaluation lineage only. It does not approve, promote, activate,
    deploy or expand the authority of an improvement candidate.
    """

    __tablename__ = "organization_improvement_evaluation_campaigns"
    __table_args__ = (
        UniqueConstraint("tenant_key", "id", name="uq_org_improvement_eval_campaign_tenant_id"),
        UniqueConstraint("tenant_key", "campaign_key", name="uq_org_improvement_eval_campaign_tenant_key"),
        UniqueConstraint(
            "tenant_key",
            "candidate_id",
            "campaign_version",
            name="uq_org_improvement_eval_campaign_candidate_version",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "candidate_id"],
            ["organization_improvement_candidates.tenant_key", "organization_improvement_candidates.id"],
            name="fk_org_improvement_eval_campaign_candidate_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "proposal_id"],
            ["organization_improvement_proposals.tenant_key", "organization_improvement_proposals.id"],
            name="fk_org_improvement_eval_campaign_proposal_tenant",
        ),
        CheckConstraint("campaign_version >= 1", name="ck_org_improvement_eval_campaign_version"),
        CheckConstraint(
            "required_structurally_separate_evaluators >= 1",
            name="ck_org_improvement_eval_campaign_required_evaluators",
        ),
        CheckConstraint(
            "status IN ('open','closed')",
            name="ck_org_improvement_eval_campaign_status",
        ),
        CheckConstraint(
            "comparison_conclusion IN ('not_assessed','constraints_met','constraints_not_met')",
            name="ck_org_improvement_eval_campaign_conclusion",
        ),
        CheckConstraint("length(baseline_fingerprint) = 64", name="ck_org_improvement_eval_campaign_baseline_fp"),
        CheckConstraint("length(candidate_fingerprint) = 64", name="ck_org_improvement_eval_campaign_candidate_fp"),
        CheckConstraint("length(evaluation_set_fingerprint) = 64", name="ck_org_improvement_eval_campaign_set_fp"),
        CheckConstraint("length(record_fingerprint) = 64", name="ck_org_improvement_eval_campaign_record_fp"),
        Index("ix_org_improvement_eval_campaign_tenant_candidate", "tenant_key", "candidate_id", "created_at"),
        Index("ix_org_improvement_eval_campaign_tenant_status", "tenant_key", "status", "created_at"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_key: str = Field(index=True)
    campaign_key: str = Field(index=True)
    campaign_version: int = Field(default=1)
    candidate_id: UUID = Field(index=True)
    proposal_id: UUID = Field(index=True)
    target_type: str = Field(index=True)
    target_reference: str
    baseline_version: str
    baseline_fingerprint: str = Field(max_length=64, index=True)
    candidate_version: str
    candidate_fingerprint: str = Field(max_length=64, index=True)
    candidate_author_identities_json: str
    candidate_author_evidence_reference_ids_json: str
    evaluation_set_key: str
    evaluation_set_version: str
    evaluation_set_fingerprint: str = Field(max_length=64, index=True)
    evaluation_set_reference_ids_json: str
    regression_constraints_json: str
    required_structurally_separate_evaluators: int = Field(default=1)
    status: str = Field(default="open", index=True)
    comparison_conclusion: str = Field(default="not_assessed", index=True)
    record_fingerprint: str = Field(max_length=64, index=True)
    created_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    closed_by: str | None = Field(default=None, index=True)
    closed_at: datetime | None = Field(default=None, index=True)


class OrganizationImprovementEvaluationReport(SQLModel, table=True):
    """Immutable evaluator report under one improvement evaluation campaign."""

    __tablename__ = "organization_improvement_evaluation_reports"
    __table_args__ = (
        UniqueConstraint("tenant_key", "id", name="uq_org_improvement_eval_report_tenant_id"),
        UniqueConstraint("tenant_key", "report_key", name="uq_org_improvement_eval_report_tenant_key"),
        ForeignKeyConstraint(
            ["tenant_key", "campaign_id"],
            ["organization_improvement_evaluation_campaigns.tenant_key", "organization_improvement_evaluation_campaigns.id"],
            name="fk_org_improvement_eval_report_campaign_tenant",
        ),
        CheckConstraint(
            "evaluator_actor_type IN ('human','agent','worker','system','external_human')",
            name="ck_org_improvement_eval_report_actor_type",
        ),
        CheckConstraint("length(record_fingerprint) = 64", name="ck_org_improvement_eval_report_record_fp"),
        Index("ix_org_improvement_eval_report_tenant_campaign", "tenant_key", "campaign_id", "recorded_at"),
        Index("ix_org_improvement_eval_report_tenant_evaluator", "tenant_key", "evaluator_identity", "recorded_at"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_key: str = Field(index=True)
    report_key: str = Field(index=True)
    campaign_id: UUID = Field(index=True)
    evaluator_actor_type: str = Field(index=True)
    evaluator_identity: str = Field(index=True)
    evaluator_independence_group: str
    independence_evidence_reference_ids_json: str
    baseline_measurements_json: str
    candidate_measurements_json: str
    constraint_results_json: str
    evaluation_evidence_reference_ids_json: str
    reproducibility_reference_ids_json: str
    constraints_satisfied: bool = Field(index=True)
    record_fingerprint: str = Field(max_length=64, index=True)
    recorded_by: str = Field(index=True)
    recorded_at: datetime = Field(default_factory=now_utc, index=True)
