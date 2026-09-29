from __future__ import annotations
import json
from uuid import UUID
from sqlmodel import Session, select

from app.models.domain import OrganizationControl, OrganizationRecordReference
from app.models.autonomy_promotion_policy import CapabilityAutonomyPromotionPolicy
from app.models.autonomy_evidence_evaluation_policy import CapabilityAutonomyEvidenceEvaluationPolicy
from app.models.organization_standards_mapping import OrganizationStandardsMapping
from app.schemas_organization_grc_standards import GRCStandardsMappingRead
from app.services.organization_command import (
    AuditMutation, InvalidReference, NotFound, OrganizationCommandContext,
    canonical_fingerprint, canonical_payload_json, commit_mutations,
    idempotent_existing, require_human, tenant_record,
)

_TARGETS = {
    "organization_control": OrganizationControl,
    "capability_autonomy_promotion_policy": CapabilityAutonomyPromotionPolicy,
    "capability_autonomy_evidence_evaluation_policy": CapabilityAutonomyEvidenceEvaluationPolicy,
}

def _target_version(session: Session, context: OrganizationCommandContext, target_type: str, target_id: UUID) -> str:
    model = _TARGETS.get(target_type)
    if model is None:
        raise InvalidReference("standards mapping target is not allowlisted")
    if target_type == "organization_control":
        if context.tenant_key != "default":
            raise NotFound("organization control is not available to this tenant")
        target = session.get(OrganizationControl, target_id)
        if target is None or target.control_key != "global" or target.status != "active":
            raise InvalidReference("standards mapping requires the active global organization control")
        return canonical_fingerprint({
            "id": str(target.id), "control_key": target.control_key, "status": target.status,
            "reason": target.reason, "changed_by": target.changed_by,
            "updated_at": target.updated_at.isoformat(),
        })
    target = tenant_record(session, model, target_id, context.tenant_key, label="standards mapping target")
    successor = session.exec(select(model.id).where(model.tenant_key == context.tenant_key, model.supersedes_policy_id == target.id)).first()
    if successor is not None:
        raise InvalidReference("standards mapping target policy was superseded")
    return target.record_fingerprint

def create_standards_mapping(
    session: Session, context: OrganizationCommandContext, *, mapping_key: str, target_type: str,
    target_id: UUID, framework_key: str, framework_version: str, requirement_id: str,
    source_reference: str, justification: str, evidence_reference_ids: list[UUID],
    mapping_state: str = "current", supersedes_mapping_id: UUID | None = None,
) -> OrganizationStandardsMapping:
    require_human(context, admin=True)
    for label, value in {
        "mapping key": mapping_key, "framework key": framework_key, "framework version": framework_version,
        "requirement ID": requirement_id, "source reference": source_reference, "justification": justification,
    }.items():
        if not value.strip():
            raise InvalidReference(f"{label} is required")
    if mapping_state not in {"current","withdrawn"} or (mapping_state == "withdrawn" and supersedes_mapping_id is None):
        raise InvalidReference("standards mapping correction must have a valid state and predecessor")
    if not evidence_reference_ids or len(set(evidence_reference_ids)) != len(evidence_reference_ids):
        raise InvalidReference("standards mapping requires unique concrete evidence references")
    evidence = []
    for reference_id in evidence_reference_ids:
        row = tenant_record(session, OrganizationRecordReference, reference_id, context.tenant_key, label="standards mapping evidence")
        if row.reference_role.value != "evidence":
            raise InvalidReference("standards mapping evidence must use evidence references")
        evidence.append(row)
    target_version = _target_version(session, context, target_type, target_id)
    if supersedes_mapping_id is not None:
        predecessor = tenant_record(session, OrganizationStandardsMapping, supersedes_mapping_id, context.tenant_key, label="superseded standards mapping")
        if (predecessor.target_type, predecessor.target_id, predecessor.framework_key, predecessor.framework_version, predecessor.requirement_id) != (
            target_type, target_id, framework_key.strip(), framework_version.strip(), requirement_id.strip()
        ):
            raise InvalidReference("standards mapping correction must retain the same target and external requirement identity")
    command = {
        "mapping_key": mapping_key.strip(), "target_type": target_type, "target_id": str(target_id),
        "target_version": target_version, "framework_key": framework_key.strip(), "framework_version": framework_version.strip(),
        "requirement_id": requirement_id.strip(), "source_reference": source_reference.strip(), "justification": justification.strip(),
        "evidence_reference_ids": sorted(str(v) for v in evidence_reference_ids), "mapping_state": mapping_state,
        "supersedes_mapping_id": str(supersedes_mapping_id) if supersedes_mapping_id else None, "tenant_key": context.tenant_key,
    }
    fingerprint = canonical_fingerprint(command)
    existing = session.exec(select(OrganizationStandardsMapping).where(
        OrganizationStandardsMapping.tenant_key == context.tenant_key,
        OrganizationStandardsMapping.mapping_key == mapping_key.strip(),
    )).first()
    replay = idempotent_existing(existing, fingerprint, fingerprint_field="record_fingerprint", label="standards mapping")
    if replay is not None:
        return replay
    row = OrganizationStandardsMapping(
        tenant_key=context.tenant_key, mapping_key=mapping_key.strip(), target_type=target_type, target_id=target_id,
        target_version=target_version, framework_key=framework_key.strip(), framework_version=framework_version.strip(),
        requirement_id=requirement_id.strip(), source_reference=source_reference.strip(), justification=justification.strip(),
        evidence_reference_ids_json=canonical_payload_json(sorted(str(v) for v in evidence_reference_ids)),
        mapping_state=mapping_state, supersedes_mapping_id=supersedes_mapping_id, record_fingerprint=fingerprint,
        created_by=context.actor_id,
    )
    session.add(row)
    commit_mutations(session, mutations=[AuditMutation("organization.grc.standards_mapping.create","organization_standards_mapping",row.id,after_state=row)], context=context, refresh=(row,))
    return row

def project_standards_mappings(session: Session, context: OrganizationCommandContext) -> tuple[GRCStandardsMappingRead, ...]:
    require_human(context, admin=True)
    rows = session.exec(select(OrganizationStandardsMapping).where(OrganizationStandardsMapping.tenant_key == context.tenant_key)).all()
    superseded = {row.supersedes_mapping_id for row in rows if row.supersedes_mapping_id is not None}
    result = []
    for row in sorted(rows, key=lambda item: (item.framework_key,item.framework_version,item.requirement_id,item.created_at,str(item.id))):
        if row.id in superseded or row.mapping_state != "current":
            continue
        if _target_version(session, context, row.target_type, row.target_id) != row.target_version:
            continue
        result.append(GRCStandardsMappingRead(
            **row.model_dump(), evidence_reference_ids=tuple(UUID(v) for v in json.loads(row.evidence_reference_ids_json))
        ))
    return tuple(result)
