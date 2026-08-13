from __future__ import annotations

from enum import Enum
from typing import Any, Mapping
from uuid import UUID

from sqlmodel import Session, SQLModel, select

from app.models.domain import (
    AgencySubmission,
    AgentRun,
    ApplicationRecord,
    AuditLog,
    AutomationEvent,
    CorporateComplianceEvent,
    CorporateMobilityCase,
    EligibilityAssessment,
    ExternalValidationFinding,
    ExternalValidationRun,
    Lead,
    MobilityPathwayVersion,
    MobilityTimelineMilestone,
    OfficialSource,
    OrganizationActivity,
    OrganizationBlocker,
    OrganizationContribution,
    OrganizationHumanAction,
    OrganizationHumanActionRequest,
    OrganizationRecordReference,
    OrganizationReferenceRole,
    OrganizationReferenceTargetType,
    OrganizationalWorkItem,
    PathwayComparisonAssessment,
    Profile,
    RegulatoryChange,
    SourceSnapshot,
    VerifiedRule,
    ExecutiveDecision,
)
from app.services.organization_command import (
    AuditMutation,
    InvalidReference,
    OrganizationCommandContext,
    TenantMismatch,
    canonical_fingerprint,
    canonical_payload_json,
    commit_mutations,
    idempotent_existing,
    require_mutation_role,
    tenant_record,
)


TARGET_MODELS: dict[OrganizationReferenceTargetType, type[SQLModel]] = {
    OrganizationReferenceTargetType.lead: Lead,
    OrganizationReferenceTargetType.profile: Profile,
    OrganizationReferenceTargetType.application: ApplicationRecord,
    OrganizationReferenceTargetType.corporate_mobility_case: CorporateMobilityCase,
    OrganizationReferenceTargetType.pathway_comparison_assessment: PathwayComparisonAssessment,
    OrganizationReferenceTargetType.eligibility_assessment: EligibilityAssessment,
    OrganizationReferenceTargetType.source_snapshot: SourceSnapshot,
    OrganizationReferenceTargetType.official_source: OfficialSource,
    OrganizationReferenceTargetType.external_validation_run: ExternalValidationRun,
    OrganizationReferenceTargetType.external_validation_finding: ExternalValidationFinding,
    OrganizationReferenceTargetType.agent_run: AgentRun,
    OrganizationReferenceTargetType.automation_event: AutomationEvent,
    OrganizationReferenceTargetType.audit_log: AuditLog,
    OrganizationReferenceTargetType.regulatory_change: RegulatoryChange,
    OrganizationReferenceTargetType.verified_rule: VerifiedRule,
    OrganizationReferenceTargetType.mobility_pathway_version: MobilityPathwayVersion,
    OrganizationReferenceTargetType.agency_submission: AgencySubmission,
    OrganizationReferenceTargetType.corporate_compliance_event: CorporateComplianceEvent,
    OrganizationReferenceTargetType.mobility_timeline_milestone: MobilityTimelineMilestone,
}

_OWNER_MODELS = {
    "activity_id": OrganizationActivity,
    "contribution_id": OrganizationContribution,
    "work_item_id": OrganizationalWorkItem,
    "decision_id": ExecutiveDecision,
    "blocker_id": OrganizationBlocker,
    "human_action_request_id": OrganizationHumanActionRequest,
    "human_action_id": OrganizationHumanAction,
}

_TELEMETRY_TARGETS = {
    OrganizationReferenceTargetType.agent_run,
    OrganizationReferenceTargetType.automation_event,
    OrganizationReferenceTargetType.audit_log,
}

_AUTHORITATIVE_STATES = frozenset(
    {"active", "approved", "accepted", "completed", "passed", "published", "resolved", "verified"}
)


def _enum_value(value: Any) -> Any:
    return value.value if isinstance(value, Enum) else value


def _record_state(record: SQLModel) -> str | None:
    for name in (
        "status",
        "lifecycle_status",
        "review_status",
        "verification_status",
        "validation_status",
        "publication_status",
        "certification_status",
    ):
        value = getattr(record, name, None)
        if value is not None:
            return str(_enum_value(value))
    active = getattr(record, "active", None)
    if active is not None:
        return "active" if active else "inactive"
    return None


def _validate_owner(
    session: Session,
    context: OrganizationCommandContext,
    owners: Mapping[str, UUID | None],
) -> None:
    selected = [(name, record_id) for name, record_id in owners.items() if record_id is not None]
    if len(selected) != 1:
        raise InvalidReference("organization reference requires exactly one owner")
    name, record_id = selected[0]
    tenant_record(session, _OWNER_MODELS[name], record_id, context.tenant_key, label="reference owner")  # type: ignore[arg-type]


def _validate_target(
    session: Session,
    context: OrganizationCommandContext,
    target_type: OrganizationReferenceTargetType,
    target_id: str,
    target_state: str | None,
    reference_role: OrganizationReferenceRole,
) -> SQLModel:
    model = TARGET_MODELS[target_type]
    try:
        typed_id = UUID(target_id)
    except ValueError as exc:
        raise InvalidReference("reference target ID must be a UUID") from exc
    if hasattr(model, "tenant_key"):
        target = session.exec(
            select(model).where(model.id == typed_id, model.tenant_key == context.tenant_key)  # type: ignore[attr-defined]
        ).first()
        if target is None:
            raise InvalidReference("reference target does not exist")
    elif context.tenant_key != "default":
        # Current legacy target tables predate tenant columns; authenticated local
        # records are therefore scoped to the documented `default` tenant only.
        raise TenantMismatch("legacy reference target is not available to this tenant")
    else:
        target = session.get(model, typed_id)
        if target is None:
            raise InvalidReference("reference target does not exist")
    actual_state = _record_state(target)
    if target_state is not None and actual_state is not None and target_state != actual_state:
        raise InvalidReference("reference target state does not match the authoritative record")
    if reference_role is OrganizationReferenceRole.authoritative_outcome:
        if target_type in _TELEMETRY_TARGETS:
            raise InvalidReference("execution telemetry cannot be an authoritative-outcome reference")
        if actual_state not in _AUTHORITATIVE_STATES:
            raise InvalidReference("reference target is not in a suitable authoritative state")
    return target


def create_record_reference(
    session: Session,
    context: OrganizationCommandContext,
    *,
    reference_key: str,
    reference_role: OrganizationReferenceRole | str,
    target_type: OrganizationReferenceTargetType | str,
    target_id: UUID | str,
    activity_id: UUID | None = None,
    contribution_id: UUID | None = None,
    work_item_id: UUID | None = None,
    decision_id: UUID | None = None,
    blocker_id: UUID | None = None,
    human_action_request_id: UUID | None = None,
    human_action_id: UUID | None = None,
    target_version: str | None = None,
    target_state: str | None = None,
    content_hash: str | None = None,
    label: str | None = None,
    source_url: str | None = None,
    metadata: Mapping[str, Any] | None = None,
    supersedes_reference_id: UUID | None = None,
) -> OrganizationRecordReference:
    require_mutation_role(context)
    try:
        reference_role = OrganizationReferenceRole(reference_role)
        target_type = OrganizationReferenceTargetType(target_type)
    except ValueError as exc:
        raise InvalidReference("reference role or target type is not allowlisted") from exc
    owners = {
        "activity_id": activity_id,
        "contribution_id": contribution_id,
        "work_item_id": work_item_id,
        "decision_id": decision_id,
        "blocker_id": blocker_id,
        "human_action_request_id": human_action_request_id,
        "human_action_id": human_action_id,
    }
    _validate_owner(session, context, owners)
    normalized_target_id = str(target_id)
    _validate_target(session, context, target_type, normalized_target_id, target_state, reference_role)
    if supersedes_reference_id is not None:
        tenant_record(
            session,
            OrganizationRecordReference,
            supersedes_reference_id,
            context.tenant_key,
            label="superseded reference",
        )
    command = {
        "reference_key": reference_key,
        "reference_role": reference_role,
        "target_type": target_type,
        "target_id": normalized_target_id,
        "owners": owners,
        "target_version": target_version,
        "target_state": target_state,
        "content_hash": content_hash,
        "label": label,
        "source_url": source_url,
        "metadata": metadata or {},
        "supersedes_reference_id": supersedes_reference_id,
        "tenant_key": context.tenant_key,
    }
    fingerprint = canonical_fingerprint(command)
    existing = session.exec(
        select(OrganizationRecordReference).where(
            OrganizationRecordReference.tenant_key == context.tenant_key,
            OrganizationRecordReference.reference_key == reference_key,
        )
    ).first()
    replay = idempotent_existing(existing, fingerprint, fingerprint_field="record_fingerprint", label="record reference")
    if replay is not None:
        return replay
    row = OrganizationRecordReference(
        reference_key=reference_key,
        record_fingerprint=fingerprint,
        tenant_key=context.tenant_key,
        activity_id=activity_id,
        contribution_id=contribution_id,
        work_item_id=work_item_id,
        decision_id=decision_id,
        blocker_id=blocker_id,
        human_action_request_id=human_action_request_id,
        human_action_id=human_action_id,
        reference_role=reference_role,
        target_type=target_type,
        target_id=normalized_target_id,
        target_version=target_version,
        target_state=target_state,
        content_hash=content_hash,
        label=label,
        source_url=source_url,
        metadata_json=canonical_payload_json(metadata),
        supersedes_reference_id=supersedes_reference_id,
        created_by=context.actor_id,
    )
    session.add(row)
    commit_mutations(
        session,
        mutations=[AuditMutation("organization.reference.create", "organization_record_reference", row.id, after_state=row)],
        context=context,
        refresh=(row,),
    )
    return row
