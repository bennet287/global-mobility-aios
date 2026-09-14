from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from sqlmodel import Session, select

from app.models.domain import (
    AuditLog,
    JurisdictionSourceCertification,
    OfficialSource,
    RegulatoryAuthority,
    RegulatoryChange,
    RegulatoryClassificationProposal,
    SourceSnapshot,
)
from app.services.audit_log import record_audit


ROUTING_VERSION = "regulatory-autonomy-routing-v1"
MACHINE_ROUTABLE_CHANGE_TYPES = {"new_program", "program_removed"}
MACHINE_ROUTABLE_MATERIALITY = {"low", "medium", "high"}


@dataclass(frozen=True)
class RegulatoryAutonomyAssessment:
    regulatory_change_id: str
    routing_version: str
    route: str
    machine_verification_candidate: bool
    canonical_write_allowed: bool
    reasons: tuple[str, ...]
    evidence: dict[str, Any]

    def payload(self) -> dict[str, Any]:
        value = asdict(self)
        value["reasons"] = list(self.reasons)
        return value


def _load_json(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def evaluate_regulatory_autonomy_gates(
    *,
    change_status: str,
    change_type: str,
    materiality: str,
    source_active: bool,
    source_authority_consistent: bool,
    certification_approved: bool,
    certification_covers_domain: bool,
    snapshot_provenance_valid: bool,
    structured_program_evidence: bool,
    deterministic_evidence_present: bool,
) -> tuple[bool, list[str]]:
    """Deterministically decide whether a change may enter machine verification.

    This gate deliberately does *not* authorize publication or any canonical rule
    write. It only routes sufficiently constrained evidence into the next machine
    verification stage. Ambiguous or high-risk cases remain on the exception path.
    """

    reasons: list[str] = []
    if change_status != "pending_review":
        reasons.append("change_not_pending_review")
    if change_type not in MACHINE_ROUTABLE_CHANGE_TYPES:
        reasons.append("change_type_requires_interpretation")
    if materiality not in MACHINE_ROUTABLE_MATERIALITY:
        reasons.append("critical_or_unknown_materiality")
    if not source_active:
        reasons.append("official_source_inactive")
    if not source_authority_consistent:
        reasons.append("source_authority_provenance_incomplete")
    if not certification_approved:
        reasons.append("approved_source_certification_missing")
    if certification_approved and not certification_covers_domain:
        reasons.append("source_certification_domain_mismatch")
    if not snapshot_provenance_valid:
        reasons.append("source_snapshot_provenance_invalid")
    if not structured_program_evidence:
        reasons.append("structured_program_evidence_missing")
    if not deterministic_evidence_present:
        reasons.append("deterministic_classification_evidence_missing")
    return not reasons, reasons


def _approved_certification(
    session: Session,
    *,
    change: RegulatoryChange,
    source: OfficialSource,
) -> JurisdictionSourceCertification | None:
    if source.regulatory_authority_id is None:
        return None
    rows = session.exec(
        select(JurisdictionSourceCertification)
        .where(JurisdictionSourceCertification.jurisdiction_id == change.jurisdiction_id)
        .where(JurisdictionSourceCertification.regulatory_authority_id == source.regulatory_authority_id)
        .where(JurisdictionSourceCertification.official_source_id == source.id)
        .where(JurisdictionSourceCertification.status == "approved")
        .order_by(JurisdictionSourceCertification.certification_version.desc())
    ).all()
    return rows[0] if rows else None


def _certification_covers_domain(
    certification: JurisdictionSourceCertification | None,
    domain: str,
) -> bool:
    if certification is None:
        return False
    values = _load_json(certification.coverage_domains_json, [])
    if not isinstance(values, list):
        return False
    normalized = {str(value).strip().lower() for value in values}
    return "*" in normalized or "all" in normalized or domain.strip().lower() in normalized


def assess_regulatory_change_autonomy(
    session: Session,
    change: RegulatoryChange,
) -> RegulatoryAutonomyAssessment:
    source = session.get(OfficialSource, change.official_source_id)
    snapshot = session.get(SourceSnapshot, change.current_snapshot_id)
    authority = (
        session.get(RegulatoryAuthority, source.regulatory_authority_id)
        if source is not None and source.regulatory_authority_id is not None
        else None
    )
    certification = (
        _approved_certification(session, change=change, source=source)
        if source is not None
        else None
    )
    proposal = session.exec(
        select(RegulatoryClassificationProposal)
        .where(RegulatoryClassificationProposal.regulatory_change_id == change.id)
        .where(RegulatoryClassificationProposal.method == "deterministic")
        .order_by(RegulatoryClassificationProposal.created_at.desc())
    ).first()

    metadata = _load_json(snapshot.metadata_json if snapshot else None, {})
    program_catalog = metadata.get("program_catalog") if isinstance(metadata, dict) else None
    deterministic_evidence = _load_json(proposal.evidence_json if proposal else None, [])

    source_authority_consistent = bool(
        source
        and authority
        and source.jurisdiction_id == change.jurisdiction_id
        and authority.jurisdiction_id == change.jurisdiction_id
        and source.regulatory_authority_id == authority.id
    )
    snapshot_provenance_valid = bool(
        source
        and snapshot
        and snapshot.official_source_id == source.id
        and snapshot.content_hash
        and snapshot.status == "changed"
    )
    structured_program_evidence = isinstance(program_catalog, list) and bool(program_catalog)
    deterministic_evidence_present = isinstance(deterministic_evidence, list) and bool(deterministic_evidence)

    eligible, reasons = evaluate_regulatory_autonomy_gates(
        change_status=change.status,
        change_type=change.change_type,
        materiality=change.materiality,
        source_active=bool(source and source.active),
        source_authority_consistent=source_authority_consistent,
        certification_approved=certification is not None,
        certification_covers_domain=_certification_covers_domain(certification, change.domain),
        snapshot_provenance_valid=snapshot_provenance_valid,
        structured_program_evidence=structured_program_evidence,
        deterministic_evidence_present=deterministic_evidence_present,
    )

    return RegulatoryAutonomyAssessment(
        regulatory_change_id=str(change.id),
        routing_version=ROUTING_VERSION,
        route="machine_verification_candidate" if eligible else "human_exception",
        machine_verification_candidate=eligible,
        canonical_write_allowed=False,
        reasons=tuple(reasons),
        evidence={
            "official_source_id": str(source.id) if source else None,
            "regulatory_authority_id": str(authority.id) if authority else None,
            "source_snapshot_id": str(snapshot.id) if snapshot else None,
            "source_certification_id": str(certification.id) if certification else None,
            "deterministic_classification_proposal_id": str(proposal.id) if proposal else None,
            "structured_program_evidence": structured_program_evidence,
            "snapshot_content_hash": snapshot.content_hash if snapshot else None,
        },
    )


def route_pending_regulatory_changes(
    session: Session,
    *,
    limit: int = 100,
    actor: str = "regulatory-intelligence-agent",
) -> dict[str, Any]:
    """Route pending changes without changing their canonical review/publication state."""

    changes = session.exec(
        select(RegulatoryChange)
        .where(RegulatoryChange.status == "pending_review")
        .order_by(RegulatoryChange.detected_at)
        .limit(min(max(limit, 1), 500))
    ).all()
    assessments: list[RegulatoryAutonomyAssessment] = []
    audit_writes = 0
    for change in changes:
        assessment = assess_regulatory_change_autonomy(session, change)
        assessments.append(assessment)
        payload = assessment.payload()
        previous = session.exec(
            select(AuditLog)
            .where(AuditLog.action == "regulatory_autonomy_routed")
            .where(AuditLog.entity_type == "regulatory_change")
            .where(AuditLog.entity_id == str(change.id))
            .order_by(AuditLog.created_at.desc())
        ).first()
        previous_payload = _load_json(previous.after_state_json if previous else None, {})
        if previous_payload == payload:
            continue
        record_audit(
            session,
            action="regulatory_autonomy_routed",
            entity_type="regulatory_change",
            entity_id=change.id,
            after_state=payload,
            reason=(
                "Evidence satisfies machine-verification routing gates; canonical publication remains forbidden."
                if assessment.machine_verification_candidate
                else "Change remains on the human-exception path until machine-verification routing gates are satisfied."
            ),
            actor=actor,
            source=ROUTING_VERSION,
        )
        audit_writes += 1
    session.commit()
    return {
        "routing_version": ROUTING_VERSION,
        "scanned": len(assessments),
        "machine_verification_candidates": sum(
            1 for item in assessments if item.machine_verification_candidate
        ),
        "human_exceptions": sum(
            1 for item in assessments if not item.machine_verification_candidate
        ),
        "canonical_writes": 0,
        "audit_writes": audit_writes,
        "assessments": [item.payload() for item in assessments],
    }
