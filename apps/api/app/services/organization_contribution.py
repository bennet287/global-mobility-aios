from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Mapping, Sequence
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    ExecutiveDecision,
    OrganizationActorType,
    OrganizationContribution,
    OrganizationContributionImpactKind,
    OrganizationContributionRecordKind,
    OrganizationContributionVerificationMethod,
    OrganizationalWorkItem,
)
from app.services.organization_command import (
    AuditMutation,
    AuthorityDenied,
    ContributionSourceRejected,
    OrganizationCommandContext,
    canonical_fingerprint,
    canonical_json,
    canonical_payload_json,
    commit_mutations,
    idempotent_existing,
    require_human,
    require_mutation_role,
    tenant_record,
)


_DESCRIPTOR_TOKEN = object()
_TELEMETRY_SOURCES = frozenset(
    {
        "agent_run",
        "workflow_run",
        "organization_execution_attempt",
        "organizational_action_output",
        "tool_call",
        "llm_request",
        "audit_log",
        "automation_retry",
        "message",
        "ui_interaction",
    }
)


@dataclass(frozen=True)
class AuthoritativeOutcomeDescriptor:
    source_type: str
    source_id: str
    source_version: str
    source_state: str
    tenant_key: str
    outcome_type: str
    verification_method: OrganizationContributionVerificationMethod
    verification_basis: str
    provenance: Mapping[str, Any]
    verified_by: str
    verified_at: datetime
    _validation_token: object = field(repr=False, compare=False)


def validate_authoritative_outcome(
    session: Session,
    context: OrganizationCommandContext,
    *,
    source_type: str,
    source_id: UUID | str,
    source_version: str,
    outcome_type: str,
    verification_basis: str,
) -> AuthoritativeOutcomeDescriptor:
    """Validate the deliberately narrow 13.16.1B source allowlist.

    Only an approved/rejected ExecutiveDecision is enabled in this slice. Other
    plausible domain sources need a separate reviewed adapter before use.
    """

    require_mutation_role(context)
    normalized = source_type.strip().lower()
    if normalized in _TELEMETRY_SOURCES:
        raise ContributionSourceRejected(f"{normalized} is execution telemetry, not an outcome authority")
    if normalized != "executive_decision":
        raise ContributionSourceRejected(f"no authoritative contribution adapter is enabled for {normalized!r}")
    try:
        decision_id = UUID(str(source_id))
    except ValueError as exc:
        raise ContributionSourceRejected("executive decision source ID must be a UUID") from exc
    decision = tenant_record(
        session,
        ExecutiveDecision,
        decision_id,
        context.tenant_key,
        label="executive decision source",
    )
    if decision.status not in {"approved", "rejected"}:
        raise ContributionSourceRejected("executive decision is not in an authoritative terminal state")
    expected_version = decision.record_fingerprint or decision.updated_at.isoformat()
    if source_version != expected_version:
        raise ContributionSourceRejected("executive decision source version is stale or unrecognized")
    if not decision.decided_by or not decision.decided_at:
        raise ContributionSourceRejected("executive decision lacks governed decision attribution")
    if not verification_basis.strip():
        raise ContributionSourceRejected("verification basis is required")
    return AuthoritativeOutcomeDescriptor(
        source_type=normalized,
        source_id=str(decision.id),
        source_version=expected_version,
        source_state=decision.status,
        tenant_key=context.tenant_key,
        outcome_type=outcome_type,
        verification_method=OrganizationContributionVerificationMethod.human_attestation,
        verification_basis=verification_basis,
        provenance={"decision_key": decision.decision_key, "decision_type": decision.decision_type},
        verified_by=decision.decided_by,
        verified_at=decision.decided_at,
        _validation_token=_DESCRIPTOR_TOKEN,
    )


def _require_descriptor(
    context: OrganizationCommandContext,
    descriptor: AuthoritativeOutcomeDescriptor,
) -> None:
    require_mutation_role(context)
    if context.actor_type in {
        OrganizationActorType.agent,
        OrganizationActorType.worker,
        OrganizationActorType.external_human,
    }:
        raise AuthorityDenied("agent, worker, and external-human identities cannot write the contribution ledger")
    if descriptor._validation_token is not _DESCRIPTOR_TOKEN:
        raise ContributionSourceRejected("authoritative descriptor was not produced by the source validator")
    if descriptor.tenant_key != context.tenant_key:
        raise ContributionSourceRejected("authoritative descriptor tenant does not match command tenant")


def create_contribution(
    session: Session,
    context: OrganizationCommandContext,
    *,
    contribution_key: str,
    descriptor: AuthoritativeOutcomeDescriptor,
    contribution_type: str,
    title: str,
    outcome_summary: str,
    department: str,
    accountable_position_key: str,
    authority_level: str,
    impact_kind: OrganizationContributionImpactKind | str,
    effective_at: datetime,
    work_item_id: UUID | None = None,
    decision_id: UUID | None = None,
    objective_key: str | None = None,
    phase_key: str | None = None,
    lead_id: UUID | None = None,
    profile_id: UUID | None = None,
    application_id: UUID | None = None,
    corporate_account_id: UUID | None = None,
    corporate_mobility_case_id: UUID | None = None,
    measured_value: Decimal | None = None,
    baseline_value: Decimal | None = None,
    target_value: Decimal | None = None,
    measurement_unit: str | None = None,
    impact: Mapping[str, Any] | None = None,
    evidence_summary: Sequence[Any] | None = None,
    human_action_required: bool = False,
) -> OrganizationContribution:
    _require_descriptor(context, descriptor)
    impact_kind = OrganizationContributionImpactKind(impact_kind)
    if work_item_id is not None:
        tenant_record(session, OrganizationalWorkItem, work_item_id, context.tenant_key, label="work item")
    if decision_id is not None:
        tenant_record(session, ExecutiveDecision, decision_id, context.tenant_key, label="decision")
    command = {
        "contribution_key": contribution_key,
        "descriptor": descriptor,
        "contribution_type": contribution_type,
        "title": title,
        "outcome_summary": outcome_summary,
        "department": department,
        "accountable_position_key": accountable_position_key,
        "authority_level": authority_level,
        "impact_kind": impact_kind,
        "effective_at": effective_at,
        "work_item_id": work_item_id,
        "decision_id": decision_id,
        "objective_key": objective_key,
        "phase_key": phase_key,
        "lead_id": lead_id,
        "profile_id": profile_id,
        "application_id": application_id,
        "corporate_account_id": corporate_account_id,
        "corporate_mobility_case_id": corporate_mobility_case_id,
        "measured_value": measured_value,
        "baseline_value": baseline_value,
        "target_value": target_value,
        "measurement_unit": measurement_unit,
        "impact": impact or {},
        "evidence_summary": list(evidence_summary or ()),
        "human_action_required": human_action_required,
        "actor_type": context.actor_type,
        "actor_id": context.actor_id,
        "tenant_key": context.tenant_key,
    }
    fingerprint = canonical_fingerprint(command)
    existing = session.exec(
        select(OrganizationContribution).where(
            OrganizationContribution.tenant_key == context.tenant_key,
            OrganizationContribution.contribution_key == contribution_key,
        )
    ).first()
    replay = idempotent_existing(
        existing,
        fingerprint,
        fingerprint_field="record_fingerprint",
        label="contribution",
    )
    if replay is not None:
        return replay
    row = OrganizationContribution(
        contribution_key=contribution_key,
        record_fingerprint=fingerprint,
        tenant_key=context.tenant_key,
        contribution_type=contribution_type,
        title=title,
        outcome_summary=outcome_summary,
        actor_type=context.actor_type,
        actor_id=context.actor_id,
        department=department,
        accountable_position_key=accountable_position_key,
        authority_level=authority_level,
        objective_key=objective_key,
        phase_key=phase_key,
        work_item_id=work_item_id,
        decision_id=decision_id,
        lead_id=lead_id,
        profile_id=profile_id,
        application_id=application_id,
        corporate_account_id=corporate_account_id,
        corporate_mobility_case_id=corporate_mobility_case_id,
        source_object_type=descriptor.source_type,
        source_object_id=descriptor.source_id,
        source_object_version=descriptor.source_version,
        source_state=descriptor.source_state,
        verification_method=descriptor.verification_method,
        record_kind=OrganizationContributionRecordKind.outcome,
        verified_by=descriptor.verified_by,
        verified_at=descriptor.verified_at,
        human_review_state="completed",
        impact_kind=impact_kind,
        measured_value=measured_value,
        baseline_value=baseline_value,
        target_value=target_value,
        measurement_unit=measurement_unit,
        impact_json=canonical_payload_json(impact),
        evidence_summary_json=canonical_json(list(evidence_summary or ())),
        human_action_required=human_action_required,
        effective_at=effective_at,
        created_by=context.actor_id,
    )
    session.add(row)
    commit_mutations(
        session,
        mutations=[AuditMutation("organization.contribution.create", "organization_contribution", row.id, after_state=row)],
        context=context,
        refresh=(row,),
    )
    return row


def append_contribution_correction(
    session: Session,
    context: OrganizationCommandContext,
    *,
    contribution_key: str,
    original_contribution_id: UUID,
    descriptor: AuthoritativeOutcomeDescriptor,
    record_kind: OrganizationContributionRecordKind | str,
    title: str,
    outcome_summary: str,
    effective_at: datetime,
    retraction_reason: str | None = None,
) -> OrganizationContribution:
    require_human(context, admin=True)
    _require_descriptor(context, descriptor)
    original = tenant_record(
        session,
        OrganizationContribution,
        original_contribution_id,
        context.tenant_key,
        label="original contribution",
    )
    kind = OrganizationContributionRecordKind(record_kind)
    if kind not in {OrganizationContributionRecordKind.supersession, OrganizationContributionRecordKind.retraction}:
        raise ContributionSourceRejected("a correction must be a supersession or retraction")
    if kind is OrganizationContributionRecordKind.retraction and not (retraction_reason or "").strip():
        raise ContributionSourceRejected("retraction reason is required")
    command = {
        "contribution_key": contribution_key,
        "original_contribution_id": original.id,
        "descriptor": descriptor,
        "record_kind": kind,
        "title": title,
        "outcome_summary": outcome_summary,
        "effective_at": effective_at,
        "retraction_reason": retraction_reason,
        "actor": context.actor_id,
    }
    fingerprint = canonical_fingerprint(command)
    existing = session.exec(
        select(OrganizationContribution).where(
            OrganizationContribution.tenant_key == context.tenant_key,
            OrganizationContribution.contribution_key == contribution_key,
        )
    ).first()
    replay = idempotent_existing(existing, fingerprint, fingerprint_field="record_fingerprint", label="contribution")
    if replay is not None:
        return replay
    row = OrganizationContribution(
        contribution_key=contribution_key,
        record_fingerprint=fingerprint,
        tenant_key=context.tenant_key,
        contribution_type=original.contribution_type,
        title=title,
        outcome_summary=outcome_summary,
        actor_type=context.actor_type,
        actor_id=context.actor_id,
        department=original.department,
        accountable_position_key=original.accountable_position_key,
        authority_level=original.authority_level,
        objective_key=original.objective_key,
        phase_key=original.phase_key,
        work_item_id=original.work_item_id,
        decision_id=original.decision_id,
        lead_id=original.lead_id,
        profile_id=original.profile_id,
        application_id=original.application_id,
        corporate_account_id=original.corporate_account_id,
        corporate_mobility_case_id=original.corporate_mobility_case_id,
        source_object_type=descriptor.source_type,
        source_object_id=descriptor.source_id,
        source_object_version=descriptor.source_version,
        source_state=descriptor.source_state,
        verification_method=descriptor.verification_method,
        record_kind=kind,
        verified_by=descriptor.verified_by,
        verified_at=descriptor.verified_at,
        human_review_state="completed",
        impact_kind=original.impact_kind,
        impact_json=original.impact_json,
        evidence_summary_json=original.evidence_summary_json,
        human_action_required=original.human_action_required,
        effective_at=effective_at,
        supersedes_contribution_id=original.id,
        retraction_reason=retraction_reason,
        created_by=context.actor_id,
    )
    session.add(row)
    commit_mutations(
        session,
        mutations=[AuditMutation("organization.contribution.correct", "organization_contribution", row.id, after_state=row)],
        context=context,
        refresh=(row,),
    )
    return row
