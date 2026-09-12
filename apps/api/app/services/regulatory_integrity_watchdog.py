from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session, select

from app.models.domain import AuditLog, RegulatoryChange, SourceSnapshot
from app.services.audit_log import record_audit
from app.services.regulatory_machine_verification import VERIFICATION_ACTION, VERIFICATION_VERSION


WATCHDOG_VERSION = "regulatory-integrity-watchdog-v1"
WATCHDOG_ACTION = "regulatory_integrity_watchdog_completed"


@dataclass(frozen=True)
class RegulatoryIntegrityAssessment:
    regulatory_change_id: str
    watchdog_version: str
    temporal_integrity: bool
    contradiction_free: bool
    eligible_for_future_promotion: bool
    canonical_write_allowed: bool
    reasons: tuple[str, ...]
    conflicting_change_ids: tuple[str, ...]
    evidence: dict[str, Any]

    def payload(self) -> dict[str, Any]:
        value = asdict(self)
        value["reasons"] = list(self.reasons)
        value["conflicting_change_ids"] = list(self.conflicting_change_ids)
        return value


def _load_json(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def evaluate_temporal_integrity(
    *,
    previous_captured_at: datetime | None,
    current_captured_at: datetime | None,
    detected_at: datetime | None,
) -> tuple[bool, list[str]]:
    """Check only chronology that is safe to assert without legal interpretation."""

    reasons: list[str] = []
    previous = _normalize_datetime(previous_captured_at)
    current = _normalize_datetime(current_captured_at)
    detected = _normalize_datetime(detected_at)

    if previous is None:
        reasons.append("previous_snapshot_capture_time_missing")
    if current is None:
        reasons.append("current_snapshot_capture_time_missing")
    if detected is None:
        reasons.append("change_detection_time_missing")
    if previous is not None and current is not None and current < previous:
        reasons.append("snapshot_capture_time_reversed")
    if current is not None and detected is not None and detected < current:
        reasons.append("change_detected_before_current_snapshot_capture")
    return not reasons, reasons


def _verified_packet(session: Session, change: RegulatoryChange) -> tuple[AuditLog | None, dict[str, Any]]:
    audit = session.exec(
        select(AuditLog)
        .where(AuditLog.action == VERIFICATION_ACTION)
        .where(AuditLog.entity_type == "regulatory_change")
        .where(AuditLog.entity_id == str(change.id))
        .order_by(AuditLog.created_at.desc())
    ).first()
    payload = _load_json(audit.after_state_json if audit else None, {})
    if not (
        audit
        and payload.get("verification_version") == VERIFICATION_VERSION
        and payload.get("independently_verified") is True
        and payload.get("canonical_write_allowed") is False
    ):
        return audit, {}
    return audit, payload


def _program_state_facts(payload: dict[str, Any]) -> tuple[set[str], set[str]]:
    differential = payload.get("evidence", {}).get("catalog_differential", {})
    if not isinstance(differential, dict):
        return set(), set()
    present = {
        str(value)
        for value in differential.get("added_program_ids", [])
        if str(value).strip()
    }
    retired = {
        str(value)
        for key in ("removed_program_ids", "deactivated_program_ids")
        for value in differential.get(key, [])
        if str(value).strip()
    }
    return present, retired


def _contradictions_for_change(
    *,
    change: RegulatoryChange,
    payload: dict[str, Any],
    peers: list[tuple[RegulatoryChange, dict[str, Any]]],
) -> tuple[bool, list[str]]:
    present, retired = _program_state_facts(payload)
    conflicts: list[str] = []
    for peer, peer_payload in peers:
        if peer.id == change.id:
            continue
        if peer.jurisdiction_id != change.jurisdiction_id or peer.domain != change.domain:
            continue
        peer_present, peer_retired = _program_state_facts(peer_payload)
        if present & peer_retired or retired & peer_present:
            conflicts.append(str(peer.id))
    return not conflicts, sorted(set(conflicts))


def assess_regulatory_integrity(
    session: Session,
    change: RegulatoryChange,
    *,
    peers: list[tuple[RegulatoryChange, dict[str, Any]]] | None = None,
) -> RegulatoryIntegrityAssessment:
    verification_audit, verification_payload = _verified_packet(session, change)
    reasons: list[str] = []
    if not verification_payload:
        reasons.append("independent_machine_verification_missing")

    previous = session.get(SourceSnapshot, change.previous_snapshot_id) if change.previous_snapshot_id else None
    current = session.get(SourceSnapshot, change.current_snapshot_id)
    temporal_ok, temporal_reasons = evaluate_temporal_integrity(
        previous_captured_at=previous.captured_at if previous else None,
        current_captured_at=current.captured_at if current else None,
        detected_at=change.detected_at,
    )
    reasons.extend(temporal_reasons)

    contradiction_ok, conflicting_ids = _contradictions_for_change(
        change=change,
        payload=verification_payload,
        peers=peers or [],
    ) if verification_payload else (False, [])
    if verification_payload and not contradiction_ok:
        reasons.append("contradictory_independently_verified_program_state")

    eligible = bool(verification_payload) and temporal_ok and contradiction_ok
    return RegulatoryIntegrityAssessment(
        regulatory_change_id=str(change.id),
        watchdog_version=WATCHDOG_VERSION,
        temporal_integrity=temporal_ok,
        contradiction_free=contradiction_ok,
        eligible_for_future_promotion=eligible,
        canonical_write_allowed=False,
        reasons=tuple(sorted(set(reasons))),
        conflicting_change_ids=tuple(conflicting_ids),
        evidence={
            "verification_audit_id": str(verification_audit.id) if verification_audit else None,
            "verification_version": verification_payload.get("verification_version") if verification_payload else None,
            "previous_snapshot_id": str(previous.id) if previous else None,
            "previous_snapshot_captured_at": previous.captured_at.isoformat() if previous else None,
            "current_snapshot_id": str(current.id) if current else None,
            "current_snapshot_captured_at": current.captured_at.isoformat() if current else None,
            "change_detected_at": change.detected_at.isoformat() if change.detected_at else None,
            "program_state_facts": {
                "present": sorted(_program_state_facts(verification_payload)[0]) if verification_payload else [],
                "retired": sorted(_program_state_facts(verification_payload)[1]) if verification_payload else [],
            },
        },
    )


def scan_regulatory_integrity(
    session: Session,
    *,
    limit: int = 100,
    actor: str = "regulatory-integrity-agent",
) -> dict[str, Any]:
    """Run RI.A3 without approving, publishing, superseding, or mutating canonical truth."""

    changes = session.exec(
        select(RegulatoryChange)
        .where(RegulatoryChange.status == "pending_review")
        .order_by(RegulatoryChange.detected_at)
        .limit(min(max(limit, 1), 500))
    ).all()

    verified_peers: list[tuple[RegulatoryChange, dict[str, Any]]] = []
    for change in changes:
        _, payload = _verified_packet(session, change)
        if payload:
            verified_peers.append((change, payload))

    assessments: list[RegulatoryIntegrityAssessment] = []
    audit_writes = 0
    for change, _ in verified_peers:
        assessment = assess_regulatory_integrity(session, change, peers=verified_peers)
        assessments.append(assessment)
        payload = assessment.payload()
        previous_audit = session.exec(
            select(AuditLog)
            .where(AuditLog.action == WATCHDOG_ACTION)
            .where(AuditLog.entity_type == "regulatory_change")
            .where(AuditLog.entity_id == str(change.id))
            .order_by(AuditLog.created_at.desc())
        ).first()
        previous_payload = _load_json(previous_audit.after_state_json if previous_audit else None, {})
        if previous_payload == payload:
            continue

        record_audit(
            session,
            action=WATCHDOG_ACTION,
            entity_type="regulatory_change",
            entity_id=change.id,
            after_state=payload,
            reason=(
                "Temporal and contradiction watchdog passed; no canonical write authority is granted."
                if assessment.eligible_for_future_promotion
                else "Integrity watchdog found a temporal or contradiction exception; keep change outside promotion."
            ),
            actor=actor,
            source=WATCHDOG_VERSION,
        )
        audit_writes += 1

    session.commit()
    return {
        "watchdog_version": WATCHDOG_VERSION,
        "scanned": len(changes),
        "independently_verified_inputs": len(verified_peers),
        "integrity_clear": sum(1 for item in assessments if item.eligible_for_future_promotion),
        "integrity_exceptions": sum(1 for item in assessments if not item.eligible_for_future_promotion),
        "canonical_writes": 0,
        "audit_writes": audit_writes,
        "assessments": [item.payload() for item in assessments],
    }
