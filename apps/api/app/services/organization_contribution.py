from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Mapping, Sequence
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    ExecutiveDecision,
    InitialRuleAssertion,
    JurisdictionSourceCertification,
    OrganizationActorType,
    OrganizationContribution,
    OrganizationContributionImpactKind,
    OrganizationContributionRecordKind,
    OrganizationContributionVerificationMethod,
    OrganizationalWorkItem,
    VerifiedRule,
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
    require_role,
    stage_mutations,
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


LEGACY_DEFAULT_TENANT = "default"


def _db_stable_datetime(value: datetime) -> datetime:
    """Normalize timestamps to the representation preserved by current DB backends.

    The D2 emitter stages the Contribution before the source transaction commits.
    SQLite persists timezone-aware UTC datetimes as naive values, so a later replay
    must fingerprint the same logical instant using the same canonical representation.
    PostgreSQL UTC values normalize to the same representation here as well.
    """

    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def _source_certification_review_version(
    certification: JurisdictionSourceCertification,
    review_evidence: Mapping[str, Any],
) -> str:
    """Return the stable reviewed-state identity used by the D2 certification adapter."""

    return canonical_fingerprint(
        {
            "certification_id": certification.id,
            "certification_version": certification.certification_version,
            "certification_scope": certification.certification_scope,
            "official_source_id": certification.official_source_id,
            "status": certification.status,
            "reviewed_by": certification.reviewed_by,
            "review_notes": certification.review_notes or "",
            "review_evidence": dict(review_evidence),
        }
    )


def validate_source_certification_outcome(
    session: Session,
    context: OrganizationCommandContext,
    *,
    certification_id: UUID,
    review_evidence: Mapping[str, Any],
    outcome_type: str = "source_certification_review_completed",
    verification_basis: str,
) -> AuthoritativeOutcomeDescriptor:
    """Validate one terminal source-certification review for the bounded D2 adapter.

    This validator is intentionally separate from ``validate_authoritative_outcome`` so
    the authenticated generic Contribution API keeps its original ExecutiveDecision-only
    source contract. Only the reviewed source-certification integration path calls this
    adapter validator.
    """

    require_human(context)
    require_role(context, "admin", "reviewer")
    if context.tenant_key != LEGACY_DEFAULT_TENANT:
        raise ContributionSourceRejected(
            "legacy source-certification records are only mapped to the default tenant"
        )
    certification = session.get(JurisdictionSourceCertification, certification_id)
    if certification is None:
        raise ContributionSourceRejected("source certification was not found")
    if certification.status not in {"approved", "rejected"}:
        raise ContributionSourceRejected(
            "source certification is not in an authoritative reviewed terminal state"
        )
    if not certification.reviewed_by or certification.reviewed_at is None:
        raise ContributionSourceRejected("source certification lacks review attribution")
    if certification.reviewed_by.strip().casefold() != context.actor_id.strip().casefold():
        raise ContributionSourceRejected(
            "source certification reviewer does not match the authenticated emitter actor"
        )
    if certification.proposed_by.strip().casefold() == certification.reviewed_by.strip().casefold():
        raise ContributionSourceRejected(
            "source certification proposer and reviewer must remain distinct"
        )
    if str(review_evidence.get("decision", "")).strip().lower() != certification.status:
        raise ContributionSourceRejected(
            "source certification review evidence does not match the reviewed state"
        )

    structured_required = bool(review_evidence.get("structured_review_pack_required"))
    if structured_required:
        if review_evidence.get("independent_human_attestation") is not True:
            raise ContributionSourceRejected(
                "structured source certification requires independent-human attestation"
            )
        evidence_hash = str(review_evidence.get("evidence_pack_sha256", "")).strip().lower()
        if len(evidence_hash) != 64 or any(ch not in "0123456789abcdef" for ch in evidence_hash):
            raise ContributionSourceRejected(
                "structured source certification requires the deterministic evidence-pack SHA-256"
            )
        if not str(review_evidence.get("source_snapshot_id", "")).strip():
            raise ContributionSourceRejected(
                "structured source certification requires the reviewed source snapshot"
            )

    if not verification_basis.strip():
        raise ContributionSourceRejected("verification basis is required")

    source_version = _source_certification_review_version(certification, review_evidence)
    provenance = {
        "certification_version": certification.certification_version,
        "certification_scope": certification.certification_scope,
        "jurisdiction_id": str(certification.jurisdiction_id),
        "regulatory_authority_id": str(certification.regulatory_authority_id),
        "official_source_id": str(certification.official_source_id),
        "review_evidence": dict(review_evidence),
    }
    return AuthoritativeOutcomeDescriptor(
        source_type="jurisdiction_source_certification",
        source_id=str(certification.id),
        source_version=source_version,
        source_state=certification.status,
        tenant_key=context.tenant_key,
        outcome_type=outcome_type,
        verification_method=OrganizationContributionVerificationMethod.human_attestation,
        verification_basis=verification_basis,
        provenance=provenance,
        verified_by=certification.reviewed_by,
        verified_at=_db_stable_datetime(certification.reviewed_at),
        _validation_token=_DESCRIPTOR_TOKEN,
    )


def _initial_rule_publication_version(
    assertion: InitialRuleAssertion,
    rule: VerifiedRule,
) -> str:
    """Return the immutable logical identity for one initial-rule publication."""

    return canonical_fingerprint(
        {
            "assertion_id": assertion.id,
            "assertion_sha256": assertion.assertion_sha256,
            "assertion_status": assertion.status,
            "published_rule_id": assertion.published_rule_id,
            "jurisdiction_id": assertion.jurisdiction_id,
            "official_source_id": assertion.official_source_id,
            "source_snapshot_id": assertion.source_snapshot_id,
            "domain": assertion.domain,
            "rule_key": assertion.rule_key,
            "verified_rule_id": rule.id,
            "verified_rule_active": rule.active,
            "verified_rule_approved_by": rule.approved_by,
            "verified_rule_statement": rule.statement,
            "verified_rule_confidence": rule.confidence,
            "verified_rule_effective_from": rule.effective_from,
            "verified_rule_effective_to": rule.effective_to,
        }
    )


def validate_initial_rule_publication_outcome(
    session: Session,
    context: OrganizationCommandContext,
    *,
    assertion_id: UUID,
    rule_id: UUID,
    outcome_type: str = "verified_rule_publication_completed",
    verification_basis: str,
) -> AuthoritativeOutcomeDescriptor:
    """Validate the bounded D3A initial-rule/VerifiedRule publication source.

    This remains a sealed integration validator. The generic authenticated
    Contribution command is still ExecutiveDecision-only and cannot select this
    source type directly.
    """

    require_human(context)
    require_role(context, "admin", "reviewer")
    if context.tenant_key != LEGACY_DEFAULT_TENANT:
        raise ContributionSourceRejected(
            "legacy initial-rule publication records are only mapped to the default tenant"
        )

    assertion = session.get(InitialRuleAssertion, assertion_id)
    if assertion is None:
        raise ContributionSourceRejected("initial rule assertion was not found")
    if assertion.status != "published":
        raise ContributionSourceRejected(
            "initial rule assertion is not in the published authoritative state"
        )
    if assertion.published_rule_id is None or assertion.published_rule_id != rule_id:
        raise ContributionSourceRejected(
            "initial rule assertion does not reference the supplied published rule"
        )
    if not assertion.reviewed_by or assertion.reviewed_at is None:
        raise ContributionSourceRejected(
            "initial rule assertion lacks independent review attribution"
        )
    if not assertion.published_by or assertion.published_at is None:
        raise ContributionSourceRejected(
            "initial rule assertion lacks publication attribution"
        )
    if assertion.published_by.strip().casefold() != context.actor_id.strip().casefold():
        raise ContributionSourceRejected(
            "initial rule publisher does not match the authenticated emitter actor"
        )
    if assertion.proposed_by.strip().casefold() == assertion.reviewed_by.strip().casefold():
        raise ContributionSourceRejected(
            "initial rule proposer and reviewer must remain distinct"
        )
    if assertion.proposed_by.strip().casefold() == assertion.published_by.strip().casefold():
        raise ContributionSourceRejected(
            "initial rule proposer and publisher must remain distinct"
        )

    rule = session.get(VerifiedRule, rule_id)
    if rule is None:
        raise ContributionSourceRejected("published verified rule was not found")
    if rule.initial_rule_assertion_id != assertion.id:
        raise ContributionSourceRejected(
            "verified rule provenance does not reference the initial rule assertion"
        )
    if rule.regulatory_change_id is not None:
        raise ContributionSourceRejected(
            "initial-rule publication adapter cannot emit a regulatory-change rule"
        )
    if rule.jurisdiction_id != assertion.jurisdiction_id:
        raise ContributionSourceRejected("verified rule jurisdiction provenance is inconsistent")
    if rule.official_source_id != assertion.official_source_id:
        raise ContributionSourceRejected("verified rule official-source provenance is inconsistent")
    if rule.source_snapshot_id != assertion.source_snapshot_id:
        raise ContributionSourceRejected("verified rule snapshot provenance is inconsistent")
    if rule.rule_key != assertion.rule_key or rule.domain != assertion.domain:
        raise ContributionSourceRejected("verified rule semantic provenance is inconsistent")
    if rule.statement != assertion.statement or rule.confidence != assertion.confidence:
        raise ContributionSourceRejected("verified rule published content is inconsistent")
    if (
        rule.effective_from != assertion.effective_from
        or rule.effective_to != assertion.effective_to
    ):
        raise ContributionSourceRejected("verified rule effective-period provenance is inconsistent")
    if not rule.active or not rule.approved_by or rule.published_at is None:
        raise ContributionSourceRejected(
            "verified rule is not an active human-published rule"
        )
    if rule.approved_by.strip().casefold() != assertion.published_by.strip().casefold():
        raise ContributionSourceRejected(
            "verified rule publisher attribution does not match the assertion publication"
        )
    if _db_stable_datetime(rule.published_at) != _db_stable_datetime(assertion.published_at):
        raise ContributionSourceRejected(
            "verified rule publication timestamp does not match the assertion publication"
        )
    if not verification_basis.strip():
        raise ContributionSourceRejected("verification basis is required")

    source_version = _initial_rule_publication_version(assertion, rule)
    provenance = {
        "assertion_sha256": assertion.assertion_sha256,
        "jurisdiction_id": str(assertion.jurisdiction_id),
        "official_source_id": str(assertion.official_source_id),
        "source_snapshot_id": str(assertion.source_snapshot_id),
        "domain": assertion.domain,
        "rule_key": assertion.rule_key,
        "verified_rule_id": str(rule.id),
        "reviewed_by": assertion.reviewed_by,
        "published_by": assertion.published_by,
    }
    return AuthoritativeOutcomeDescriptor(
        source_type="initial_rule_assertion",
        source_id=str(assertion.id),
        source_version=source_version,
        source_state="published",
        tenant_key=context.tenant_key,
        outcome_type=outcome_type,
        verification_method=OrganizationContributionVerificationMethod.human_attestation,
        verification_basis=verification_basis,
        provenance=provenance,
        verified_by=assertion.published_by,
        verified_at=_db_stable_datetime(assertion.published_at),
        _validation_token=_DESCRIPTOR_TOKEN,
    )


def _require_descriptor(
    context: OrganizationCommandContext,
    descriptor: AuthoritativeOutcomeDescriptor,
) -> None:
    if descriptor.source_type in {
        "jurisdiction_source_certification",
        "initial_rule_assertion",
    }:
        require_human(context)
        require_role(context, "admin", "reviewer")
    else:
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


def _write_contribution(
    session: Session,
    context: OrganizationCommandContext,
    *,
    _commit: bool,
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
    mutation = AuditMutation(
        "organization.contribution.create",
        "organization_contribution",
        row.id,
        after_state=row,
    )
    if _commit:
        commit_mutations(session, mutations=[mutation], context=context, refresh=(row,))
    else:
        stage_mutations(session, mutations=[mutation], context=context)
    return row


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
    """Create and commit a standalone authoritative Contribution command."""

    return _write_contribution(
        session,
        context,
        _commit=True,
        contribution_key=contribution_key,
        descriptor=descriptor,
        contribution_type=contribution_type,
        title=title,
        outcome_summary=outcome_summary,
        department=department,
        accountable_position_key=accountable_position_key,
        authority_level=authority_level,
        impact_kind=impact_kind,
        effective_at=effective_at,
        work_item_id=work_item_id,
        decision_id=decision_id,
        objective_key=objective_key,
        phase_key=phase_key,
        lead_id=lead_id,
        profile_id=profile_id,
        application_id=application_id,
        corporate_account_id=corporate_account_id,
        corporate_mobility_case_id=corporate_mobility_case_id,
        measured_value=measured_value,
        baseline_value=baseline_value,
        target_value=target_value,
        measurement_unit=measurement_unit,
        impact=impact,
        evidence_summary=evidence_summary,
        human_action_required=human_action_required,
    )


def stage_contribution(
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
    """Stage a Contribution and its audit inside a caller-owned transaction.

    This internal integration primitive never commits or rolls back. Real source
    adapters must call it only while their authoritative source transition owns the
    surrounding transaction. The public/API command remains ``create_contribution``.
    """

    return _write_contribution(
        session,
        context,
        _commit=False,
        contribution_key=contribution_key,
        descriptor=descriptor,
        contribution_type=contribution_type,
        title=title,
        outcome_summary=outcome_summary,
        department=department,
        accountable_position_key=accountable_position_key,
        authority_level=authority_level,
        impact_kind=impact_kind,
        effective_at=effective_at,
        work_item_id=work_item_id,
        decision_id=decision_id,
        objective_key=objective_key,
        phase_key=phase_key,
        lead_id=lead_id,
        profile_id=profile_id,
        application_id=application_id,
        corporate_account_id=corporate_account_id,
        corporate_mobility_case_id=corporate_mobility_case_id,
        measured_value=measured_value,
        baseline_value=baseline_value,
        target_value=target_value,
        measurement_unit=measurement_unit,
        impact=impact,
        evidence_summary=evidence_summary,
        human_action_required=human_action_required,
    )


def _write_contribution_correction(
    session: Session,
    context: OrganizationCommandContext,
    *,
    _commit: bool,
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
    mutation = AuditMutation(
        "organization.contribution.correct",
        "organization_contribution",
        row.id,
        after_state=row,
    )
    if _commit:
        commit_mutations(session, mutations=[mutation], context=context, refresh=(row,))
    else:
        stage_mutations(session, mutations=[mutation], context=context)
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
    """Append and commit a standalone Contribution correction/retraction."""

    return _write_contribution_correction(
        session,
        context,
        _commit=True,
        contribution_key=contribution_key,
        original_contribution_id=original_contribution_id,
        descriptor=descriptor,
        record_kind=record_kind,
        title=title,
        outcome_summary=outcome_summary,
        effective_at=effective_at,
        retraction_reason=retraction_reason,
    )


def stage_contribution_correction(
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
    """Stage a correction/retraction inside a caller-owned transaction."""

    return _write_contribution_correction(
        session,
        context,
        _commit=False,
        contribution_key=contribution_key,
        original_contribution_id=original_contribution_id,
        descriptor=descriptor,
        record_kind=record_kind,
        title=title,
        outcome_summary=outcome_summary,
        effective_at=effective_at,
        retraction_reason=retraction_reason,
    )
