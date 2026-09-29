from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class GRCEvidenceExportEntry(BaseModel):
    record_type: str
    record_id: UUID
    relation: str
    related_record_type: str | None = None
    related_record_id: UUID | None = None
    status: str | None = None
    record_fingerprint: str | None = None
    source_object_version: str | None = None
    supersedes_record_id: UUID | None = None
    target_type: str | None = None
    target_id: str | None = None
    target_version: str | None = None
    occurred_at: datetime | None = None


class GRCEvidenceExportRead(BaseModel):
    schema_version: str = "grc-risk-evidence-v1"
    tenant_key: str
    risk_id: UUID
    work_item_id: UUID
    evidence_validity: str = "not_assessed"
    coverage: str = "explicitly_linked_records_only"
    source_records: tuple[GRCEvidenceExportEntry, ...]
    limitations: tuple[str, ...] = (
        "A recorded link is not proof of evidence validity, policy applicability, approval, or risk mitigation.",
        "Activity source identities and reference targets are recorded claims, not independently verified causation or target contents.",
        "Record fingerprints identify creation commands; they do not hash mutable current row state.",
        "Legacy global audit-log contents and unlinked records are excluded; this is not a completeness or certified snapshot claim.",
    )
