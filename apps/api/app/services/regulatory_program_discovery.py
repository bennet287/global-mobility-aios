from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from sqlmodel import Session, select

from app.models.domain import (
    AuditLog,
    Jurisdiction,
    MobilityPathway,
    MobilityPathwayVersion,
    RegulatoryChange,
    SourceSnapshot,
)
from app.services.audit_log import record_audit
from app.services.regulatory_integrity_watchdog import WATCHDOG_ACTION, WATCHDOG_VERSION
from app.services.regulatory_machine_verification import VERIFICATION_ACTION, VERIFICATION_VERSION


DISCOVERY_VERSION = "regulatory-program-discovery-v1"
DISCOVERY_ACTION = "regulatory_pathway_candidates_discovered"
SUPPORTED_CHANGE_TYPE = "new_program"
MAX_CANDIDATES_PER_CHANGE = 25


@dataclass(frozen=True)
class PathwayCandidate:
    candidate_key: str
    program_id: str
    name: str
    summary: str
    effective_date: str | None
    status: str
    active: bool
    possible_existing_pathway_ids: tuple[str, ...]
    candidate_only: bool
    publication_allowed: bool
    pathway_create_allowed: bool
    canonical_write_allowed: bool

    def payload(self) -> dict[str, Any]:
        value = asdict(self)
        value["possible_existing_pathway_ids"] = list(self.possible_existing_pathway_ids)
        return value


@dataclass(frozen=True)
class ProgramDiscoveryPacket:
    regulatory_change_id: str
    discovery_version: str
    source_snapshot_id: str | None
    source_snapshot_content_hash: str | None
    verification_audit_id: str | None
    watchdog_audit_id: str | None
    candidates: tuple[PathwayCandidate, ...]
    fanout_limited: bool
    candidate_only: bool
    publication_allowed: bool
    pathway_create_allowed: bool
    canonical_write_allowed: bool
    reasons: tuple[str, ...]

    def payload(self) -> dict[str, Any]:
        return {
            "regulatory_change_id": self.regulatory_change_id,
            "discovery_version": self.discovery_version,
            "source_snapshot_id": self.source_snapshot_id,
            "source_snapshot_content_hash": self.source_snapshot_content_hash,
            "verification_audit_id": self.verification_audit_id,
            "watchdog_audit_id": self.watchdog_audit_id,
            "candidates": [item.payload() for item in self.candidates],
            "fanout_limited": self.fanout_limited,
            "candidate_only": self.candidate_only,
            "publication_allowed": self.publication_allowed,
            "pathway_create_allowed": self.pathway_create_allowed,
            "canonical_write_allowed": self.canonical_write_allowed,
            "reasons": list(self.reasons),
        }


def _load_json(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _latest_audit_payload(
    session: Session,
    *,
    change: RegulatoryChange,
    action: str,
) -> tuple[AuditLog | None, dict[str, Any]]:
    audit = session.exec(
        select(AuditLog)
        .where(AuditLog.action == action)
        .where(AuditLog.entity_type == "regulatory_change")
        .where(AuditLog.entity_id == str(change.id))
        .order_by(AuditLog.created_at.desc())
    ).first()
    return audit, _load_json(audit.after_state_json if audit else None, {})


def _integrity_clear(
    session: Session,
    change: RegulatoryChange,
) -> tuple[bool, AuditLog | None, dict[str, Any]]:
    audit, payload = _latest_audit_payload(session, change=change, action=WATCHDOG_ACTION)
    clear = bool(
        audit
        and payload.get("watchdog_version") == WATCHDOG_VERSION
        and payload.get("eligible_for_future_promotion") is True
        and payload.get("canonical_write_allowed") is False
    )
    return clear, audit, payload


def _verified_new_program_ids(
    session: Session,
    change: RegulatoryChange,
) -> tuple[AuditLog | None, dict[str, Any], list[str]]:
    audit, payload = _latest_audit_payload(session, change=change, action=VERIFICATION_ACTION)
    if not (
        audit
        and payload.get("verification_version") == VERIFICATION_VERSION
        and payload.get("independently_verified") is True
        and payload.get("canonical_write_allowed") is False
    ):
        return audit, payload, []
    differential = payload.get("evidence", {}).get("catalog_differential", {})
    if not isinstance(differential, dict):
        return audit, payload, []
    values = differential.get("added_program_ids", [])
    return audit, payload, sorted({str(value).strip() for value in values if str(value).strip()})


def _normalize(value: str | None) -> str:
    return " ".join((value or "").strip().lower().split())


def _possible_existing_pathways(
    session: Session,
    *,
    change: RegulatoryChange,
    program_id: str,
    program_name: str,
) -> tuple[str, ...]:
    rows = session.exec(
        select(MobilityPathwayVersion, MobilityPathway)
        .join(MobilityPathway, MobilityPathway.id == MobilityPathwayVersion.pathway_id)
        .where(MobilityPathwayVersion.lifecycle_status.in_(["draft", "published", "superseded"]))
    ).all()
    matches: set[str] = set()
    normalized_name = _normalize(program_name)
    for version, pathway in rows:
        if pathway.jurisdiction_id != change.jurisdiction_id:
            continue
        metadata = _load_json(version.metadata_json, {})
        source_program_id = str(metadata.get("source_program_id") or "").strip() if isinstance(metadata, dict) else ""
        name_match = bool(normalized_name and _normalize(pathway.name) == normalized_name)
        source_program_match = bool(source_program_id and source_program_id == program_id)
        source_match = bool(version.official_source_id and version.official_source_id == change.official_source_id)
        if source_program_match or (name_match and source_match):
            matches.add(str(pathway.id))
    return tuple(sorted(matches))


def discover_pathway_candidates(
    session: Session,
    change: RegulatoryChange,
    *,
    max_candidates: int = MAX_CANDIDATES_PER_CHANGE,
) -> ProgramDiscoveryPacket:
    reasons: list[str] = []
    if change.status != "pending_review":
        reasons.append("change_not_pending_review")
    if change.change_type != SUPPORTED_CHANGE_TYPE:
        reasons.append("change_not_new_program")

    integrity_clear, watchdog_audit, _ = _integrity_clear(session, change)
    if not integrity_clear:
        reasons.append("regulatory_integrity_clearance_missing")

    verification_audit, verification_payload, added_program_ids = _verified_new_program_ids(session, change)
    if not added_program_ids:
        reasons.append("independently_verified_new_program_delta_missing")

    snapshot = session.get(SourceSnapshot, change.current_snapshot_id)
    if snapshot is None:
        reasons.append("current_snapshot_missing")
        metadata: dict[str, Any] = {}
    else:
        metadata = _load_json(snapshot.metadata_json, {})
        if snapshot.official_source_id != change.official_source_id:
            reasons.append("current_snapshot_source_mismatch")
        if metadata.get("parser_profile") != "structured_program_catalog_v1":
            reasons.append("current_snapshot_parser_profile_invalid")
        verification_evidence = verification_payload.get("evidence", {}) if verification_payload else {}
        verified_snapshot_id = str(verification_evidence.get("current_snapshot_id") or "")
        verified_snapshot_hash = str(verification_evidence.get("current_snapshot_content_hash") or "")
        if verified_snapshot_id and verified_snapshot_id != str(snapshot.id):
            reasons.append("verification_snapshot_id_mismatch")
        if verified_snapshot_hash and verified_snapshot_hash != str(snapshot.content_hash or ""):
            reasons.append("verification_snapshot_hash_mismatch")

    catalog = metadata.get("program_catalog") if isinstance(metadata, dict) else None
    catalog_index: dict[str, dict[str, Any]] = {}
    if not isinstance(catalog, list):
        reasons.append("structured_program_catalog_missing")
    else:
        for row in catalog:
            if not isinstance(row, dict):
                continue
            program_id = str(row.get("program_id") or "").strip()
            if program_id:
                catalog_index[program_id] = row

    unresolved_ids = [program_id for program_id in added_program_ids if program_id not in catalog_index]
    if unresolved_ids:
        reasons.append("verified_program_missing_from_current_catalog")

    bounded_limit = max(1, min(max_candidates, MAX_CANDIDATES_PER_CHANGE))
    candidate_ids = [program_id for program_id in added_program_ids if program_id in catalog_index]
    fanout_limited = len(candidate_ids) > bounded_limit
    if fanout_limited:
        reasons.append("candidate_fanout_limit_reached")
    selected_ids = candidate_ids[:bounded_limit]

    jurisdiction = session.get(Jurisdiction, change.jurisdiction_id)
    candidates: list[PathwayCandidate] = []
    for program_id in selected_ids:
        row = catalog_index[program_id]
        name = str(row.get("name") or "").strip()
        if not name:
            reasons.append("candidate_program_name_missing")
            continue
        candidate_key = ":".join(
            [
                str(change.jurisdiction_id),
                str(change.official_source_id),
                program_id,
            ]
        )
        candidates.append(
            PathwayCandidate(
                candidate_key=candidate_key,
                program_id=program_id,
                name=name,
                summary=str(row.get("summary") or "").strip(),
                effective_date=(str(row.get("effective_date") or "").strip() or None),
                status=str(row.get("status") or "unknown").strip().lower(),
                active=bool(row.get("active", False)),
                possible_existing_pathway_ids=_possible_existing_pathways(
                    session,
                    change=change,
                    program_id=program_id,
                    program_name=name,
                ),
                candidate_only=True,
                publication_allowed=False,
                pathway_create_allowed=False,
                canonical_write_allowed=False,
            )
        )

    if not candidates:
        reasons.append("no_pathway_candidates_discovered")

    return ProgramDiscoveryPacket(
        regulatory_change_id=str(change.id),
        discovery_version=DISCOVERY_VERSION,
        source_snapshot_id=str(snapshot.id) if snapshot else None,
        source_snapshot_content_hash=snapshot.content_hash if snapshot else None,
        verification_audit_id=str(verification_audit.id) if verification_audit else None,
        watchdog_audit_id=str(watchdog_audit.id) if watchdog_audit else None,
        candidates=tuple(candidates),
        fanout_limited=fanout_limited,
        candidate_only=True,
        publication_allowed=False,
        pathway_create_allowed=False,
        canonical_write_allowed=False,
        reasons=tuple(sorted(set(reasons))),
    )


def discover_new_program_candidates(
    session: Session,
    *,
    limit: int = 100,
    actor: str = "regulatory-discovery-agent",
) -> dict[str, Any]:
    """Discover RI.A5 pathway candidates without creating or publishing pathways."""

    changes = session.exec(
        select(RegulatoryChange)
        .where(RegulatoryChange.status == "pending_review")
        .where(RegulatoryChange.change_type == SUPPORTED_CHANGE_TYPE)
        .order_by(RegulatoryChange.detected_at)
        .limit(min(max(limit, 1), 500))
    ).all()

    packets: list[ProgramDiscoveryPacket] = []
    audit_writes = 0
    for change in changes:
        packet = discover_pathway_candidates(session, change)
        if not packet.candidates:
            continue
        if "regulatory_integrity_clearance_missing" in packet.reasons:
            continue
        payload = packet.payload()
        packets.append(packet)

        previous = session.exec(
            select(AuditLog)
            .where(AuditLog.action == DISCOVERY_ACTION)
            .where(AuditLog.entity_type == "regulatory_change")
            .where(AuditLog.entity_id == str(change.id))
            .order_by(AuditLog.created_at.desc())
        ).first()
        previous_payload = _load_json(previous.after_state_json if previous else None, {})
        if previous_payload == payload:
            continue

        record_audit(
            session,
            action=DISCOVERY_ACTION,
            entity_type="regulatory_change",
            entity_id=change.id,
            after_state=payload,
            reason="Verified new-program evidence produced pathway candidates only; publication remains forbidden.",
            actor=actor,
            source=DISCOVERY_VERSION,
        )
        audit_writes += 1

    session.commit()
    return {
        "discovery_version": DISCOVERY_VERSION,
        "scanned": len(changes),
        "candidate_packets": len(packets),
        "candidate_count": sum(len(packet.candidates) for packet in packets),
        "fanout_limited": sum(1 for packet in packets if packet.fanout_limited),
        "pathway_writes": 0,
        "publication_writes": 0,
        "canonical_writes": 0,
        "audit_writes": audit_writes,
        "packets": [packet.payload() for packet in packets],
    }
