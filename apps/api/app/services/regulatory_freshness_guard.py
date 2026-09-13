from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from sqlmodel import Session, select

from app.models.domain import AuditLog, OfficialSource, RegulatoryChange, SourceSnapshot
from app.services.audit_log import record_audit
from app.services.regulatory_promotion_policy import PROMOTION_ACTION, PROMOTION_POLICY_VERSION


FRESHNESS_VERSION = "regulatory-freshness-guard-v1"
FRESHNESS_ACTION = "regulatory_freshness_quarantine_assessed"
FATAL_FRESHNESS_REASONS = {
    "change_not_pending_review",
    "current_shadow_promotion_packet_missing",
    "official_source_missing",
    "official_source_inactive",
    "current_snapshot_missing",
    "current_snapshot_content_hash_missing",
    "promotion_snapshot_id_missing",
    "promotion_snapshot_hash_missing",
    "promotion_snapshot_id_mismatch",
    "promotion_snapshot_hash_mismatch",
    "latest_source_snapshot_missing",
    "latest_source_snapshot_hash_missing",
    "newer_snapshot_content_drift",
}


@dataclass(frozen=True)
class RegulatoryFreshnessAssessment:
    regulatory_change_id: str
    freshness_version: str
    promotion_audit_id: str | None
    source_snapshot_id: str | None
    source_snapshot_content_hash: str | None
    latest_snapshot_id: str | None
    latest_snapshot_content_hash: str | None
    source_active: bool | None
    freshness_status: str
    quarantine_required: bool
    shadow_eligibility_revoked: bool
    rollback_reference_snapshot_id: str | None
    rollback_reference_snapshot_content_hash: str | None
    canonical_write_allowed: bool
    reasons: tuple[str, ...]

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


def _current_shadow_promotion(
    session: Session,
    change: RegulatoryChange,
) -> tuple[AuditLog | None, dict[str, Any]]:
    audit = session.exec(
        select(AuditLog)
        .where(AuditLog.action == PROMOTION_ACTION)
        .where(AuditLog.entity_type == "regulatory_change")
        .where(AuditLog.entity_id == str(change.id))
        .order_by(AuditLog.created_at.desc())
    ).first()
    payload = _load_json(audit.after_state_json if audit else None, {})
    valid = bool(
        audit
        and payload.get("promotion_policy_version") == PROMOTION_POLICY_VERSION
        and payload.get("shadow_mode") is True
        and payload.get("publication_writes_allowed") is False
        and payload.get("pathway_writes_allowed") is False
        and payload.get("verified_rule_writes_allowed") is False
        and payload.get("canonical_write_allowed") is False
    )
    return audit, payload if valid else {}


def _contains_shadow_eligible_candidate(payload: dict[str, Any]) -> bool:
    candidates = payload.get("candidates", []) if isinstance(payload, dict) else []
    if not isinstance(candidates, list):
        return False
    return any(
        isinstance(candidate, dict)
        and candidate.get("shadow_promotion_eligible") is True
        and candidate.get("outcome") == "shadow_eligible"
        for candidate in candidates
    )


def assess_regulatory_freshness(
    session: Session,
    change: RegulatoryChange,
) -> RegulatoryFreshnessAssessment:
    reasons: list[str] = []
    if change.status != "pending_review":
        reasons.append("change_not_pending_review")

    promotion_audit, promotion_payload = _current_shadow_promotion(session, change)
    if not promotion_payload:
        reasons.append("current_shadow_promotion_packet_missing")

    source = session.get(OfficialSource, change.official_source_id)
    if source is None:
        reasons.append("official_source_missing")
        source_active: bool | None = None
    else:
        source_active = bool(source.active)
        if not source_active:
            reasons.append("official_source_inactive")

    current = session.get(SourceSnapshot, change.current_snapshot_id)
    if current is None:
        reasons.append("current_snapshot_missing")
    elif not current.content_hash:
        reasons.append("current_snapshot_content_hash_missing")

    promotion_snapshot_id = str(promotion_payload.get("source_snapshot_id") or "") if promotion_payload else ""
    promotion_snapshot_hash = str(promotion_payload.get("source_snapshot_content_hash") or "") if promotion_payload else ""
    if promotion_payload:
        if not promotion_snapshot_id:
            reasons.append("promotion_snapshot_id_missing")
        elif current is not None and promotion_snapshot_id != str(current.id):
            reasons.append("promotion_snapshot_id_mismatch")
        if not promotion_snapshot_hash:
            reasons.append("promotion_snapshot_hash_missing")
        elif current is not None and promotion_snapshot_hash != str(current.content_hash or ""):
            reasons.append("promotion_snapshot_hash_mismatch")

    latest = session.exec(
        select(SourceSnapshot)
        .where(SourceSnapshot.official_source_id == change.official_source_id)
        .order_by(SourceSnapshot.captured_at.desc())
    ).first()
    if latest is None:
        reasons.append("latest_source_snapshot_missing")
    elif not latest.content_hash:
        reasons.append("latest_source_snapshot_hash_missing")

    freshness_status = "fresh"
    if current is not None and latest is not None and latest.id != current.id:
        if latest.content_hash and current.content_hash and latest.content_hash == current.content_hash:
            freshness_status = "fresh_equivalent"
        else:
            reasons.append("newer_snapshot_content_drift")

    unique_reasons = tuple(sorted(set(reasons)))
    quarantine_required = any(reason in FATAL_FRESHNESS_REASONS for reason in unique_reasons)
    if quarantine_required:
        freshness_status = "quarantined"

    shadow_eligibility_revoked = quarantine_required and _contains_shadow_eligible_candidate(promotion_payload)
    return RegulatoryFreshnessAssessment(
        regulatory_change_id=str(change.id),
        freshness_version=FRESHNESS_VERSION,
        promotion_audit_id=str(promotion_audit.id) if promotion_audit else None,
        source_snapshot_id=str(current.id) if current else None,
        source_snapshot_content_hash=current.content_hash if current else None,
        latest_snapshot_id=str(latest.id) if latest else None,
        latest_snapshot_content_hash=latest.content_hash if latest else None,
        source_active=source_active,
        freshness_status=freshness_status,
        quarantine_required=quarantine_required,
        shadow_eligibility_revoked=shadow_eligibility_revoked,
        rollback_reference_snapshot_id=promotion_snapshot_id or None,
        rollback_reference_snapshot_content_hash=promotion_snapshot_hash or None,
        canonical_write_allowed=False,
        reasons=unique_reasons,
    )


def scan_regulatory_freshness(
    session: Session,
    *,
    limit: int = 100,
    actor: str = "regulatory-freshness-agent",
) -> dict[str, Any]:
    """Assess RI.A8 freshness and quarantine state without mutating canonical truth."""

    changes = session.exec(
        select(RegulatoryChange)
        .where(RegulatoryChange.status == "pending_review")
        .where(RegulatoryChange.change_type == "new_program")
        .order_by(RegulatoryChange.detected_at)
        .limit(min(max(limit, 1), 500))
    ).all()

    assessments: list[RegulatoryFreshnessAssessment] = []
    audit_writes = 0
    for change in changes:
        _, promotion_payload = _current_shadow_promotion(session, change)
        if not promotion_payload:
            continue
        assessment = assess_regulatory_freshness(session, change)
        assessments.append(assessment)
        payload = assessment.payload()

        previous = session.exec(
            select(AuditLog)
            .where(AuditLog.action == FRESHNESS_ACTION)
            .where(AuditLog.entity_type == "regulatory_change")
            .where(AuditLog.entity_id == str(change.id))
            .order_by(AuditLog.created_at.desc())
        ).first()
        previous_payload = _load_json(previous.after_state_json if previous else None, {})
        if previous_payload == payload:
            continue

        record_audit(
            session,
            action=FRESHNESS_ACTION,
            entity_type="regulatory_change",
            entity_id=change.id,
            after_state=payload,
            reason=(
                "Freshness guard assessed source drift and quarantine/rollback readiness; canonical rollback remains disabled."
            ),
            actor=actor,
            source=FRESHNESS_VERSION,
        )
        audit_writes += 1

    session.commit()
    return {
        "freshness_version": FRESHNESS_VERSION,
        "scanned": len(changes),
        "assessed": len(assessments),
        "fresh": sum(1 for item in assessments if item.freshness_status == "fresh"),
        "fresh_equivalent": sum(1 for item in assessments if item.freshness_status == "fresh_equivalent"),
        "quarantined": sum(1 for item in assessments if item.quarantine_required),
        "shadow_eligibility_revocations": sum(1 for item in assessments if item.shadow_eligibility_revoked),
        "rollback_writes": 0,
        "publication_writes": 0,
        "pathway_writes": 0,
        "verified_rule_writes": 0,
        "canonical_writes": 0,
        "audit_writes": audit_writes,
        "assessments": [item.payload() for item in assessments],
    }
