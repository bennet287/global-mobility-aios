from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from sqlmodel import Session, select

from app.models.domain import AuditLog, MobilityPathway, MobilityPathwayVersion, RegulatoryChange
from app.models.eligibility_revision import EligibilityAssessmentRevision
from app.services.audit_log import record_audit
from app.services.regulatory_integrity_watchdog import WATCHDOG_ACTION, WATCHDOG_VERSION


PROPAGATION_VERSION = "regulatory-reassessment-propagation-v1"
PROPAGATION_ACTION = "regulatory_reassessment_impact_identified"
MAX_PATHWAY_FANOUT_PER_CHANGE = 50


@dataclass(frozen=True)
class ReassessmentImpact:
    regulatory_change_id: str
    propagation_version: str
    pathway_version_ids: tuple[str, ...]
    eligibility_revision_ids: tuple[str, ...]
    fanout_limited: bool
    reassessment_write_allowed: bool
    canonical_write_allowed: bool
    reasons: tuple[str, ...]

    def payload(self) -> dict[str, Any]:
        value = asdict(self)
        value["pathway_version_ids"] = list(self.pathway_version_ids)
        value["eligibility_revision_ids"] = list(self.eligibility_revision_ids)
        value["reasons"] = list(self.reasons)
        return value


def _load_json(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _integrity_clear(session: Session, change: RegulatoryChange) -> tuple[bool, str | None]:
    audit = session.exec(
        select(AuditLog)
        .where(AuditLog.action == WATCHDOG_ACTION)
        .where(AuditLog.entity_type == "regulatory_change")
        .where(AuditLog.entity_id == str(change.id))
        .order_by(AuditLog.created_at.desc())
    ).first()
    payload = _load_json(audit.after_state_json if audit else None, {})
    clear = bool(
        audit
        and payload.get("watchdog_version") == WATCHDOG_VERSION
        and payload.get("eligible_for_future_promotion") is True
        and payload.get("canonical_write_allowed") is False
    )
    return clear, str(audit.id) if audit else None


def _domain_matches(pathway_domain: str, change_domain: str) -> bool:
    pathway = (pathway_domain or "").strip().lower()
    change = (change_domain or "").strip().lower()
    if pathway == change:
        return True
    if change == "visa" and pathway in {"study", "work", "family", "settlement", "digital_nomad", "visa"}:
        return True
    return False


def identify_reassessment_impact(
    session: Session,
    change: RegulatoryChange,
    *,
    max_pathways: int = MAX_PATHWAY_FANOUT_PER_CHANGE,
) -> ReassessmentImpact:
    integrity_clear, _ = _integrity_clear(session, change)
    reasons: list[str] = []
    if change.status != "pending_review":
        reasons.append("change_not_pending_review")
    if not integrity_clear:
        reasons.append("regulatory_integrity_clearance_missing")

    matches: list[MobilityPathwayVersion] = []
    if integrity_clear:
        rows = session.exec(
            select(MobilityPathwayVersion, MobilityPathway)
            .join(MobilityPathway, MobilityPathway.id == MobilityPathwayVersion.pathway_id)
            .where(MobilityPathwayVersion.lifecycle_status == "published")
            .order_by(MobilityPathwayVersion.published_at, MobilityPathwayVersion.id)
        ).all()
        for version, pathway in rows:
            jurisdiction_match = bool(
                pathway.jurisdiction_id
                and pathway.jurisdiction_id == change.jurisdiction_id
            )
            source_match = bool(
                version.official_source_id
                and version.official_source_id == change.official_source_id
            )
            if not jurisdiction_match and not source_match:
                continue
            if not _domain_matches(pathway.domain, change.domain):
                continue
            matches.append(version)

    fanout_limited = len(matches) > max_pathways
    selected = matches[: max(1, min(max_pathways, MAX_PATHWAY_FANOUT_PER_CHANGE))]
    if fanout_limited:
        reasons.append("pathway_fanout_limit_reached")

    pathway_ids = tuple(str(row.id) for row in selected)
    eligibility_ids: list[str] = []
    if pathway_ids:
        selected_ids = {row.id for row in selected}
        revisions = session.exec(
            select(EligibilityAssessmentRevision)
            .where(EligibilityAssessmentRevision.lifecycle_status == "active")
            .order_by(EligibilityAssessmentRevision.created_at)
        ).all()
        eligibility_ids = [
            str(row.id)
            for row in revisions
            if row.pathway_version_id in selected_ids
        ]

    return ReassessmentImpact(
        regulatory_change_id=str(change.id),
        propagation_version=PROPAGATION_VERSION,
        pathway_version_ids=pathway_ids,
        eligibility_revision_ids=tuple(eligibility_ids),
        fanout_limited=fanout_limited,
        reassessment_write_allowed=False,
        canonical_write_allowed=False,
        reasons=tuple(sorted(set(reasons))),
    )


def propagate_regulatory_reassessment_impacts(
    session: Session,
    *,
    limit: int = 100,
    actor: str = "regulatory-impact-agent",
) -> dict[str, Any]:
    """Identify bounded downstream reassessment candidates without mutating assessments."""

    changes = session.exec(
        select(RegulatoryChange)
        .where(RegulatoryChange.status == "pending_review")
        .order_by(RegulatoryChange.detected_at)
        .limit(min(max(limit, 1), 500))
    ).all()

    impacts: list[ReassessmentImpact] = []
    audit_writes = 0
    for change in changes:
        clear, watchdog_audit_id = _integrity_clear(session, change)
        if not clear:
            continue
        impact = identify_reassessment_impact(session, change)
        impacts.append(impact)
        payload = impact.payload()
        payload["watchdog_audit_id"] = watchdog_audit_id

        previous = session.exec(
            select(AuditLog)
            .where(AuditLog.action == PROPAGATION_ACTION)
            .where(AuditLog.entity_type == "regulatory_change")
            .where(AuditLog.entity_id == str(change.id))
            .order_by(AuditLog.created_at.desc())
        ).first()
        previous_payload = _load_json(previous.after_state_json if previous else None, {})
        if previous_payload == payload:
            continue

        record_audit(
            session,
            action=PROPAGATION_ACTION,
            entity_type="regulatory_change",
            entity_id=change.id,
            after_state=payload,
            reason=(
                "Bounded downstream reassessment candidates identified; assessments remain unchanged."
            ),
            actor=actor,
            source=PROPAGATION_VERSION,
        )
        audit_writes += 1

    session.commit()
    return {
        "propagation_version": PROPAGATION_VERSION,
        "scanned": len(changes),
        "integrity_clear_inputs": len(impacts),
        "pathway_candidates": sum(len(item.pathway_version_ids) for item in impacts),
        "eligibility_revision_candidates": sum(len(item.eligibility_revision_ids) for item in impacts),
        "fanout_limited": sum(1 for item in impacts if item.fanout_limited),
        "reassessment_writes": 0,
        "canonical_writes": 0,
        "audit_writes": audit_writes,
        "impacts": [item.payload() for item in impacts],
    }
