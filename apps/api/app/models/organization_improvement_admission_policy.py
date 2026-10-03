from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Index, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.domain import now_utc


class OrganizationImprovementAdmissionDependencyPolicy(SQLModel, table=True):
    """Append-only Board-authored GRSI.E prerequisite policy for one exact scope."""

    __tablename__ = "organization_improvement_admission_dependency_policies"
    __table_args__ = (
        UniqueConstraint(
            "tenant_key",
            "id",
            name="uq_org_improv_adm_policy_tenant_id",
        ),
        UniqueConstraint(
            "tenant_key",
            "idempotency_key",
            name="uq_org_improv_adm_policy_idempotency",
        ),
        UniqueConstraint(
            "tenant_key",
            "target_type",
            "execution_mode",
            "candidate_risk_class",
            "policy_version",
            name="uq_org_improv_adm_policy_scope_version",
        ),
        UniqueConstraint(
            "tenant_key",
            "supersedes_policy_id",
            name="uq_org_improv_adm_policy_supersedes",
        ),
        CheckConstraint(
            "target_type = 'code_configuration'",
            name="ck_org_improv_adm_policy_target",
        ),
        CheckConstraint(
            "execution_mode IN ('shadow','canary')",
            name="ck_org_improv_adm_policy_mode",
        ),
        CheckConstraint(
            "candidate_risk_class IN ('low','medium','high','critical')",
            name="ck_org_improv_adm_policy_risk",
        ),
        CheckConstraint(
            "policy_version >= 1",
            name="ck_org_improv_adm_policy_version",
        ),
        CheckConstraint(
            "supersedes_policy_id IS NULL OR supersedes_policy_id <> id",
            name="ck_org_improv_adm_policy_not_self",
        ),
        CheckConstraint(
            "length(decision_activity_fingerprint) = 64",
            name="ck_org_improv_adm_policy_activity_fp",
        ),
        CheckConstraint(
            "length(record_fingerprint) = 64",
            name="ck_org_improv_adm_policy_record_fp",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "decision_activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_org_improv_adm_policy_activity_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "supersedes_policy_id"],
            [
                "organization_improvement_admission_dependency_policies.tenant_key",
                "organization_improvement_admission_dependency_policies.id",
            ],
            name="fk_org_improv_adm_policy_supersedes_tenant",
        ),
        Index(
            "ix_org_improv_adm_policy_scope_seq",
            "tenant_key",
            "target_type",
            "execution_mode",
            "candidate_risk_class",
            "policy_version",
        ),
        Index(
            "ix_org_improv_adm_policy_activity",
            "tenant_key",
            "decision_activity_id",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_key: str
    target_type: str
    execution_mode: str
    candidate_risk_class: str
    policy_version: int
    phase_requirements_json: str
    policy_reason: str
    supersedes_policy_id: UUID | None = None
    decision_activity_id: UUID
    decision_activity_fingerprint: str = Field(max_length=64)
    idempotency_key: str
    record_fingerprint: str = Field(max_length=64)
    created_by: str
    created_at: datetime = Field(default_factory=now_utc)
