from __future__ import annotations

import json
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
    MobilityPathway,
    MobilityPathwayVersion,
    MobilityPathwayVersionEvidence,
    OfficialSource,
    RegulatoryChange,
    OrganizationActorType,
    OrganizationContribution,
    OrganizationContributionImpactKind,
    OrganizationContributionRecordKind,
    OrganizationContributionVerificationMethod,
    OrganizationalWorkItem,
    SourceSnapshot,
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
    idempotent_existing,
    require_human,
    require_mutation_role,
    require_role,
    stage_mutations,
    tenant_record,
)
from app.services.organization_semantic_activity import stage_contribution_record_activity


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



def _regulatory_change_publication_version(
    change: RegulatoryChange,
    rule: VerifiedRule,
) -> str:
    """Return the immutable logical identity for one reviewed regulatory publication."""

    return canonical_fingerprint(
        {
            "regulatory_change_id": change.id,
            "change_status": change.status,
            "jurisdiction_id": change.jurisdiction_id,
            "official_source_id": change.official_source_id,
            "previous_snapshot_id": change.previous_snapshot_id,
            "current_snapshot_id": change.current_snapshot_id,
            "domain": change.domain,
            "change_type": change.change_type,
            "materiality": change.materiality,
            "effective_at": _db_stable_datetime(change.effective_at) if change.effective_at is not None else None,
            "reviewed_by": change.reviewed_by,
            "reviewed_at": _db_stable_datetime(change.reviewed_at),
            "published_at": _db_stable_datetime(change.published_at),
            "verified_rule_id": rule.id,
            "verified_rule_active": rule.active,
            "verified_rule_approved_by": rule.approved_by,
            "verified_rule_statement": rule.statement,
            "verified_rule_confidence": rule.confidence,
            "verified_rule_effective_from": _db_stable_datetime(rule.effective_from) if rule.effective_from is not None else None,
            "verified_rule_effective_to": _db_stable_datetime(rule.effective_to) if rule.effective_to is not None else None,
            "verified_rule_supersedes_rule_id": rule.supersedes_rule_id,
        }
    )


def validate_regulatory_change_publication_outcome(
    session: Session,
    context: OrganizationCommandContext,
    *,
    change_id: UUID,
    rule_id: UUID,
    outcome_type: str = "regulatory_change_publication_completed",
    verification_basis: str,
) -> AuthoritativeOutcomeDescriptor:
    """Validate the bounded D3B reviewed regulatory-change publication source.

    This is a sealed integration validator. The generic authenticated Contribution
    command remains ExecutiveDecision-only and cannot select this source directly.
    """

    require_human(context)
    require_role(context, "admin", "reviewer")
    if context.tenant_key != LEGACY_DEFAULT_TENANT:
        raise ContributionSourceRejected(
            "legacy regulatory-change publication records are only mapped to the default tenant"
        )

    change = session.get(RegulatoryChange, change_id)
    if change is None:
        raise ContributionSourceRejected("regulatory change was not found")
    if change.status != "published":
        raise ContributionSourceRejected(
            "regulatory change is not in the published authoritative state"
        )
    if not change.reviewed_by or change.reviewed_at is None:
        raise ContributionSourceRejected(
            "regulatory change lacks prior human review attribution"
        )
    if change.published_at is None:
        raise ContributionSourceRejected(
            "regulatory change lacks publication timestamp attribution"
        )

    snapshot = session.get(SourceSnapshot, change.current_snapshot_id)
    if snapshot is None:
        raise ContributionSourceRejected("regulatory change current source snapshot was not found")
    if snapshot.official_source_id != change.official_source_id:
        raise ContributionSourceRejected(
            "regulatory change source snapshot does not match its official source"
        )
    snapshot_hash = str(snapshot.content_hash or "").strip().lower()
    if len(snapshot_hash) != 64 or any(ch not in "0123456789abcdef" for ch in snapshot_hash):
        raise ContributionSourceRejected(
            "regulatory change publication requires an immutable SHA-256 source snapshot"
        )

    rule = session.get(VerifiedRule, rule_id)
    if rule is None:
        raise ContributionSourceRejected("published verified rule was not found")
    if rule.regulatory_change_id != change.id:
        raise ContributionSourceRejected(
            "verified rule provenance does not reference the regulatory change"
        )
    if rule.initial_rule_assertion_id is not None:
        raise ContributionSourceRejected(
            "regulatory-change publication adapter cannot emit an initial-rule publication"
        )
    if rule.jurisdiction_id != change.jurisdiction_id:
        raise ContributionSourceRejected("verified rule jurisdiction provenance is inconsistent")
    if rule.official_source_id != change.official_source_id:
        raise ContributionSourceRejected("verified rule official-source provenance is inconsistent")
    if rule.source_snapshot_id != change.current_snapshot_id:
        raise ContributionSourceRejected("verified rule snapshot provenance is inconsistent")
    if rule.domain != change.domain:
        raise ContributionSourceRejected("verified rule regulatory domain is inconsistent")
    if not rule.active or not rule.approved_by or rule.published_at is None:
        raise ContributionSourceRejected(
            "verified rule is not an active human-published regulatory-change rule"
        )
    if rule.approved_by.strip().casefold() != context.actor_id.strip().casefold():
        raise ContributionSourceRejected(
            "verified rule publisher does not match the authenticated emitter actor"
        )
    if _db_stable_datetime(rule.published_at) != _db_stable_datetime(change.published_at):
        raise ContributionSourceRejected(
            "verified rule publication timestamp does not match the regulatory change publication"
        )
    if rule.supersedes_rule_id is not None:
        superseded_rule = session.get(VerifiedRule, rule.supersedes_rule_id)
        if superseded_rule is None:
            raise ContributionSourceRejected("superseded verified rule was not found")
        if superseded_rule.active:
            raise ContributionSourceRejected("superseded verified rule remains active")
        if (
            superseded_rule.jurisdiction_id != change.jurisdiction_id
            or superseded_rule.domain != change.domain
        ):
            raise ContributionSourceRejected(
                "superseded verified rule provenance is outside the regulatory-change scope"
            )
        if not superseded_rule.retired_by or (
            superseded_rule.retired_by.strip().casefold()
            != context.actor_id.strip().casefold()
        ):
            raise ContributionSourceRejected(
                "superseded verified rule retirement is not attributed to the authenticated publisher"
            )
    if not verification_basis.strip():
        raise ContributionSourceRejected("verification basis is required")

    source_version = _regulatory_change_publication_version(change, rule)
    provenance = {
        "jurisdiction_id": str(change.jurisdiction_id),
        "official_source_id": str(change.official_source_id),
        "previous_snapshot_id": str(change.previous_snapshot_id) if change.previous_snapshot_id else None,
        "current_snapshot_id": str(change.current_snapshot_id),
        "source_snapshot_hash": snapshot_hash,
        "domain": change.domain,
        "change_type": change.change_type,
        "materiality": change.materiality,
        "reviewed_by": change.reviewed_by,
        "reviewed_at": _db_stable_datetime(change.reviewed_at),
        "verified_rule_id": str(rule.id),
        "supersedes_rule_id": str(rule.supersedes_rule_id) if rule.supersedes_rule_id else None,
    }
    return AuthoritativeOutcomeDescriptor(
        source_type="regulatory_change",
        source_id=str(change.id),
        source_version=source_version,
        source_state="published",
        tenant_key=context.tenant_key,
        outcome_type=outcome_type,
        verification_method=OrganizationContributionVerificationMethod.human_attestation,
        verification_basis=verification_basis,
        provenance=provenance,
        verified_by=rule.approved_by,
        verified_at=_db_stable_datetime(change.published_at),
        _validation_token=_DESCRIPTOR_TOKEN,
    )


def _json_payload(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _pathway_publication_evidence_state(
    session: Session,
    version: MobilityPathwayVersion,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    evidence_rows = list(
        session.exec(
            select(MobilityPathwayVersionEvidence).where(
                MobilityPathwayVersionEvidence.pathway_version_id == version.id
            )
        ).all()
    )
    evidence_rows.sort(
        key=lambda row: (
            row.evidence_role,
            str(row.official_source_id),
            str(row.source_snapshot_id),
            str(row.id),
        )
    )
    evidence_state: list[dict[str, Any]] = []
    for row in evidence_rows:
        source = session.get(OfficialSource, row.official_source_id)
        snapshot = session.get(SourceSnapshot, row.source_snapshot_id)
        evidence_state.append(
            {
                "evidence_role": row.evidence_role,
                "official_source_id": row.official_source_id,
                "source_snapshot_id": row.source_snapshot_id,
                "required_for_publication": row.required_for_publication,
                "metadata": _json_payload(row.metadata_json, {}),
                "source_active": source.active if source is not None else None,
                "source_country": source.country if source is not None else None,
                "source_domain": source.domain if source is not None else None,
                "source_snapshot_content_hash": snapshot.content_hash if snapshot is not None else None,
            }
        )

    rule_state: list[dict[str, Any]] = []
    raw_rule_ids = _json_payload(version.verified_rule_ids_json, [])
    try:
        rule_ids = [UUID(str(value)) for value in raw_rule_ids]
    except (TypeError, ValueError) as exc:
        raise ContributionSourceRejected(
            "published pathway version has invalid verified-rule provenance"
        ) from exc
    for rule_id in sorted(rule_ids, key=str):
        rule = session.get(VerifiedRule, rule_id)
        if rule is None:
            raise ContributionSourceRejected(
                f"published pathway verified rule {rule_id} was not found"
            )
        rule_state.append(
            {
                "id": rule.id,
                "country": rule.country,
                "domain": rule.domain,
                "rule_key": rule.rule_key,
                "statement": rule.statement,
                "official_source_id": rule.official_source_id,
                "source_snapshot_id": rule.source_snapshot_id,
                "confidence": rule.confidence,
                "active": rule.active,
                "approved_by": rule.approved_by,
                "published_at": (
                    _db_stable_datetime(rule.published_at)
                    if rule.published_at is not None
                    else None
                ),
            }
        )
    return evidence_state, rule_state


def _pathway_publication_version(
    session: Session,
    pathway: MobilityPathway,
    version: MobilityPathwayVersion,
) -> str:
    evidence_state, rule_state = _pathway_publication_evidence_state(
        session,
        version,
    )
    return canonical_fingerprint(
        {
            "pathway_id": pathway.id,
            "pathway_key": pathway.pathway_key,
            "pathway_name": pathway.name,
            "country": pathway.country,
            "domain": pathway.domain,
            "jurisdiction_id": pathway.jurisdiction_id,
            "catalogue_status": pathway.catalogue_status,
            "pathway_version_id": version.id,
            "version_number": version.version_number,
            "lifecycle_status": version.lifecycle_status,
            "supersedes_version_id": version.supersedes_version_id,
            "official_source_id": version.official_source_id,
            "source_snapshot_id": version.source_snapshot_id,
            "verified_rule_ids": _json_payload(version.verified_rule_ids_json, []),
            "eligibility_criteria": _json_payload(version.eligibility_criteria_json, {}),
            "required_documents": _json_payload(version.required_documents_json, []),
            "costs": _json_payload(version.costs_json, {}),
            "processing_time": _json_payload(version.processing_time_json, {}),
            "benefits": _json_payload(version.benefits_json, []),
            "risks": _json_payload(version.risks_json, []),
            "metadata": _json_payload(version.metadata_json, {}),
            "effective_from": (
                _db_stable_datetime(version.effective_from)
                if version.effective_from is not None
                else None
            ),
            "effective_to": (
                _db_stable_datetime(version.effective_to)
                if version.effective_to is not None
                else None
            ),
            "human_review_required": version.human_review_required,
            "approved_by": version.approved_by,
            "review_notes": version.review_notes or "",
            "published_at": _db_stable_datetime(version.published_at),
            "evidence": evidence_state,
            "verified_rules": rule_state,
        }
    )


def validate_pathway_version_publication_outcome(
    session: Session,
    context: OrganizationCommandContext,
    *,
    pathway_version_id: UUID,
    outcome_type: str = "pathway_version_published",
    verification_basis: str,
) -> AuthoritativeOutcomeDescriptor:
    """Validate one bounded D3C human-published pathway-version outcome.

    This sealed integration validator reuses the catalogue's exact publication-evidence
    blocker contract after the publication state has been staged. The generic
    authenticated Contribution API remains ExecutiveDecision-only.
    """

    require_human(context)
    require_role(context, "admin", "operator", "reviewer")
    if context.tenant_key != LEGACY_DEFAULT_TENANT:
        raise ContributionSourceRejected(
            "legacy pathway-version publication records are only mapped to the default tenant"
        )

    version = session.get(MobilityPathwayVersion, pathway_version_id)
    if version is None:
        raise ContributionSourceRejected("published pathway version was not found")
    pathway = session.get(MobilityPathway, version.pathway_id)
    if pathway is None:
        raise ContributionSourceRejected("published pathway was not found")
    if version.lifecycle_status != "published":
        raise ContributionSourceRejected(
            "pathway version is not in the published authoritative state"
        )
    if pathway.catalogue_status != "active":
        raise ContributionSourceRejected(
            "published pathway is not active in the governed catalogue"
        )
    if not version.approved_by or version.published_at is None:
        raise ContributionSourceRejected(
            "published pathway version lacks human publication attribution"
        )
    if version.approved_by.strip().casefold() != context.actor_id.strip().casefold():
        raise ContributionSourceRejected(
            "pathway-version publisher does not match the authenticated emitter actor"
        )
    if version.created_by.strip().casefold() == version.approved_by.strip().casefold():
        raise ContributionSourceRejected(
            "pathway-version proposer and publisher must remain distinct"
        )
    if not verification_basis.strip():
        raise ContributionSourceRejected("verification basis is required")

    # Reuse the exact catalogue evidence/certification/rule gate. This helper excludes
    # lifecycle checks, so it remains valid immediately after the draft -> published
    # transition has been staged inside the same transaction.
    from app.services.pathway_catalogue import _publication_evidence_blockers

    blockers = _publication_evidence_blockers(session, pathway, version)
    if blockers:
        raise ContributionSourceRejected(
            "published pathway evidence no longer satisfies the publication gate: "
            + blockers[0]
        )

    evidence_state, rule_state = _pathway_publication_evidence_state(
        session,
        version,
    )
    evidence_roles = {str(item["evidence_role"]) for item in evidence_state}

    other_published = list(
        session.exec(
            select(MobilityPathwayVersion).where(
                MobilityPathwayVersion.pathway_id == pathway.id,
                MobilityPathwayVersion.lifecycle_status == "published",
                MobilityPathwayVersion.id != version.id,
            )
        ).all()
    )
    if other_published:
        raise ContributionSourceRejected(
            "pathway publication left more than one current published version"
        )

    source_version = _pathway_publication_version(session, pathway, version)
    provenance = {
        "pathway_id": str(pathway.id),
        "pathway_key": pathway.pathway_key,
        "pathway_name": pathway.name,
        "country": pathway.country,
        "domain": pathway.domain,
        "jurisdiction_id": str(pathway.jurisdiction_id) if pathway.jurisdiction_id else None,
        "version_number": version.version_number,
        "supersedes_version_id": (
            str(version.supersedes_version_id) if version.supersedes_version_id else None
        ),
        "evidence_roles": sorted(evidence_roles),
        "evidence": evidence_state,
        "verified_rules": rule_state,
    }
    return AuthoritativeOutcomeDescriptor(
        source_type="mobility_pathway_version",
        source_id=str(version.id),
        source_version=source_version,
        source_state="published",
        tenant_key=context.tenant_key,
        outcome_type=outcome_type,
        verification_method=OrganizationContributionVerificationMethod.human_attestation,
        verification_basis=verification_basis,
        provenance=provenance,
        verified_by=version.approved_by,
        verified_at=_db_stable_datetime(version.published_at),
        _validation_token=_DESCRIPTOR_TOKEN,
    )


def _require_descriptor(
    context: OrganizationCommandContext,
    descriptor: AuthoritativeOutcomeDescriptor,
) -> None:
    if descriptor.source_type in {
        "jurisdiction_source_certification",
        "initial_rule_assertion",
        "regulatory_change",
    }:
        require_human(context)
        require_role(context, "admin", "reviewer")
    elif descriptor.source_type == "mobility_pathway_version":
        require_human(context)
        require_role(context, "admin", "operator", "reviewer")
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
    if not _commit:
        stage_mutations(session, mutations=[mutation], context=context)
        stage_contribution_record_activity(session, context, row)
        return row
    try:
        stage_mutations(session, mutations=[mutation], context=context)
        stage_contribution_record_activity(session, context, row)
        session.commit()
        session.refresh(row)
    except Exception:
        session.rollback()
        raise
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
    if not _commit:
        stage_mutations(session, mutations=[mutation], context=context)
        stage_contribution_record_activity(session, context, row)
        return row
    try:
        stage_mutations(session, mutations=[mutation], context=context)
        stage_contribution_record_activity(session, context, row)
        session.commit()
        session.refresh(row)
    except Exception:
        session.rollback()
        raise
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
