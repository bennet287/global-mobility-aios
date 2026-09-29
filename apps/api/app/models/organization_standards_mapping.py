from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Index, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.domain import now_utc

class OrganizationStandardsMapping(SQLModel, table=True):
    """Human-authored traceability from one canonical AIOS control/policy to an external requirement.

    Presence is not a claim of certification, compliance, applicability, or control effectiveness.
    """
    __tablename__ = "organization_standards_mappings"
    __table_args__ = (
        UniqueConstraint("tenant_key","id",name="uq_org_std_mapping_tenant_id"),
        UniqueConstraint("tenant_key","mapping_key",name="uq_org_std_mapping_tenant_key"),
        UniqueConstraint("tenant_key","supersedes_mapping_id",name="uq_org_std_mapping_supersedes"),
        ForeignKeyConstraint(["tenant_key","supersedes_mapping_id"],["organization_standards_mappings.tenant_key","organization_standards_mappings.id"],name="fk_org_std_mapping_supersedes_tenant"),
        CheckConstraint("target_type IN ('organization_control','capability_autonomy_promotion_policy','capability_autonomy_evidence_evaluation_policy')",name="ck_org_std_mapping_target_type"),
        CheckConstraint("mapping_state IN ('current','withdrawn')",name="ck_org_std_mapping_state"),
        CheckConstraint("length(record_fingerprint) = 64",name="ck_org_std_mapping_fingerprint"),
        CheckConstraint("supersedes_mapping_id IS NULL OR supersedes_mapping_id <> id",name="ck_org_std_mapping_not_self"),
        Index("ix_org_std_mapping_tenant_framework","tenant_key","framework_key","framework_version"),
        Index("ix_org_std_mapping_tenant_target","tenant_key","target_type","target_id"),
    )
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_key: str
    mapping_key: str
    target_type: str
    target_id: UUID
    target_version: str
    framework_key: str
    framework_version: str
    requirement_id: str
    source_reference: str
    justification: str
    evidence_reference_ids_json: str
    mapping_state: str = "current"
    supersedes_mapping_id: UUID | None = None
    record_fingerprint: str = Field(max_length=64)
    created_by: str
    created_at: datetime = Field(default_factory=now_utc)
