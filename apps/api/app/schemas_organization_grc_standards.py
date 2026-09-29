from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class GRCStandardsMappingCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mapping_key: str = Field(min_length=1, max_length=255)
    target_type: str = Field(pattern="^(organization_control|capability_autonomy_promotion_policy|capability_autonomy_evidence_evaluation_policy)$")
    target_id: UUID
    framework_key: str = Field(min_length=1, max_length=255)
    framework_version: str = Field(min_length=1, max_length=255)
    requirement_id: str = Field(min_length=1, max_length=255)
    source_reference: str = Field(min_length=1, max_length=2000)
    justification: str = Field(min_length=1, max_length=4000)
    evidence_reference_ids: list[UUID] = Field(min_length=1, max_length=100)
    mapping_state: str = Field(default="current", pattern="^(current|withdrawn)$")
    supersedes_mapping_id: UUID | None = None

class GRCStandardsMappingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    mapping_key: str
    target_type: str
    target_id: UUID
    target_version: str
    framework_key: str
    framework_version: str
    requirement_id: str
    source_reference: str
    justification: str
    evidence_reference_ids: tuple[UUID, ...]
    mapping_state: str
    supersedes_mapping_id: UUID | None
    record_fingerprint: str
    created_by: str
    created_at: datetime
    traceability_conclusion: str = "declared_mapping_only"
    limitations: tuple[str, ...] = (
        "Mapping presence does not establish certification, compliance, applicability or control effectiveness.",
        "Mapping absence does not establish noncompliance.",
        "External framework text and applicability are not independently certified by this record.",
    )
