from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from sqlmodel import Session, select

from app.models.domain import AuditLog, RegulatoryChange, SourceSnapshot
from app.services.audit_log import record_audit
from app.services.regulatory_autonomy import ROUTING_VERSION


VERIFICATION_VERSION = "regulatory-machine-verification-v1"
VERIFICATION_METHOD = "snapshot-catalog-differential-v1"
ROUTING_ACTION = "regulatory_autonomy_routed"
VERIFICATION_ACTION = "regulatory_machine_verification_completed"
SUPPORTED_CHANGE_TYPES = {"new_program", "program_removed"}


@dataclass(frozen=True)
class CatalogDifferential:
    valid: bool
    added_program_ids: tuple[str, ...]
    removed_program_ids: tuple[str, ...]
    deactivated_program_ids: tuple[str, ...]
    reasons: tuple[str, ...]

    def payload(self) -> dict[str, Any]:
        value = asdict(self)
        for key in ("added_program_ids", "removed_program_ids", "deactivated_program_ids", "reasons"):
            value[key] = list(value[key])
        return value


@dataclass(frozen=True)
class RegulatoryMachineVerification:
    regulatory_change_id: str
    verification_version: str
    verification_method: str
    verdict: str
    independently_verified: bool
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


def _catalog_index(catalog: Any) -> tuple[dict[str, dict[str, Any]], list[str]]:
    if not isinstance(catalog, list) or not catalog:
        return {}, ["structured_program_catalog_missing"]

    index: dict[str, dict[str, Any]] = {}
    reasons: list[str] = []
    for item in catalog:
        if not isinstance(item, dict):
            reasons.append("program_catalog_record_invalid")
            continue
        program_id = str(item.get("program_id") or "").strip()
        name = str(item.get("name") or "").strip()
        if not program_id or not name:
            reasons.append("program_catalog_identity_missing")
            continue
        if program_id in index:
            reasons.append("program_catalog_duplicate_identity")
            continue
        index[program_id] = item
    return index, sorted(set(reasons))


def evaluate_catalog_differential(
    *,
    change_type: str,
    previous_catalog: Any,
    current_catalog: Any,
    missing_means_retired: bool,
) -> CatalogDifferential:
    """Independently verify structured program change semantics from snapshot data.

    The function deliberately does not consume RegulatoryClassificationProposal.
    It derives the result from the immutable previous/current program catalogs.
    """

    if change_type not in SUPPORTED_CHANGE_TYPES:
        return CatalogDifferential(
            valid=False,
            added_program_ids=(),
            removed_program_ids=(),
            deactivated_program_ids=(),
            reasons=("unsupported_machine_verification_change_type",),
        )

    previous, previous_reasons = _catalog_index(previous_catalog)
    current, current_reasons = _catalog_index(current_catalog)
    reasons = previous_reasons + current_reasons
    if reasons:
        return CatalogDifferential(
            valid=False,
            added_program_ids=(),
            removed_program_ids=(),
            deactivated_program_ids=(),
            reasons=tuple(sorted(set(reasons))),
        )

    previous_ids = set(previous)
    current_ids = set(current)
    added = sorted(
        program_id
        for program_id in current_ids - previous_ids
        if bool(current[program_id].get("active", False))
    )
    missing = sorted(previous_ids - current_ids)
    deactivated = sorted(
        program_id
        for program_id in previous_ids & current_ids
        if bool(previous[program_id].get("active", False))
        and not bool(current[program_id].get("active", False))
    )

    if change_type == "new_program":
        if not added:
            reasons.append("no_independent_new_program_delta")
    elif change_type == "program_removed":
        if not deactivated and not (missing_means_retired and missing):
            reasons.append("no_independent_program_retirement_delta")
        if missing and not missing_means_retired:
            reasons.append("program_absence_not_semantically_retired")

    return CatalogDifferential(
        valid=not reasons,
        added_program_ids=tuple(added),
        removed_program_ids=tuple(missing if missing_means_retired else ()),
        deactivated_program_ids=tuple(deactivated),
        reasons=tuple(sorted(set(reasons))),
    )


def _latest_machine_route(session: Session, change: RegulatoryChange) -> AuditLog | None:
    return session.exec(
        select(AuditLog)
        .where(AuditLog.action == ROUTING_ACTION)
        .where(AuditLog.entity_type == "regulatory_change")
        .where(AuditLog.entity_id == str(change.id))
        .order_by(AuditLog.created_at.desc())
    ).first()


def verify_regulatory_change_independently(
    session: Session,
    change: RegulatoryChange,
) -> RegulatoryMachineVerification:
    route_audit = _latest_machine_route(session, change)
    route_payload = _load_json(route_audit.after_state_json if route_audit else None, {})
    route_is_current_candidate = bool(
        route_audit
        and route_payload.get("routing_version") == ROUTING_VERSION
        and route_payload.get("machine_verification_candidate") is True
        and route_payload.get("canonical_write_allowed") is False
    )

    reasons: list[str] = []
    if change.status != "pending_review":
        reasons.append("change_not_pending_review")
    if not route_is_current_candidate:
        reasons.append("current_machine_verification_route_missing")

    current = session.get(SourceSnapshot, change.current_snapshot_id)
    previous = session.get(SourceSnapshot, change.previous_snapshot_id) if change.previous_snapshot_id else None

    if current is None:
        reasons.append("current_snapshot_missing")
    if previous is None:
        reasons.append("previous_snapshot_missing")

    if current is not None:
        if current.official_source_id != change.official_source_id:
            reasons.append("current_snapshot_source_mismatch")
        if not current.content_hash:
            reasons.append("current_snapshot_hash_missing")
    if previous is not None:
        if previous.official_source_id != change.official_source_id:
            reasons.append("previous_snapshot_source_mismatch")
        if not previous.content_hash:
            reasons.append("previous_snapshot_hash_missing")
    if current is not None and previous is not None:
        if current.previous_snapshot_id != previous.id:
            reasons.append("snapshot_chain_mismatch")
        if current.content_hash == previous.content_hash:
            reasons.append("snapshot_hash_unchanged")

    current_meta = _load_json(current.metadata_json if current else None, {})
    previous_meta = _load_json(previous.metadata_json if previous else None, {})
    if current_meta.get("parser_profile") != "structured_program_catalog_v1":
        reasons.append("current_snapshot_parser_profile_invalid")
    if previous_meta.get("parser_profile") != "structured_program_catalog_v1":
        reasons.append("previous_snapshot_parser_profile_invalid")

    differential = evaluate_catalog_differential(
        change_type=change.change_type,
        previous_catalog=previous_meta.get("program_catalog"),
        current_catalog=current_meta.get("program_catalog"),
        missing_means_retired=bool(current_meta.get("missing_means_retired", False)),
    )
    reasons.extend(differential.reasons)

    independent = not reasons
    verdict = "verified" if independent else "unresolved"
    return RegulatoryMachineVerification(
        regulatory_change_id=str(change.id),
        verification_version=VERIFICATION_VERSION,
        verification_method=VERIFICATION_METHOD,
        verdict=verdict,
        independently_verified=independent,
        canonical_write_allowed=False,
        reasons=tuple(sorted(set(reasons))),
        evidence={
            "routing_audit_id": str(route_audit.id) if route_audit else None,
            "routing_version": route_payload.get("routing_version") if route_payload else None,
            "classifier_output_used_as_verification_evidence": False,
            "previous_snapshot_id": str(previous.id) if previous else None,
            "previous_snapshot_content_hash": previous.content_hash if previous else None,
            "current_snapshot_id": str(current.id) if current else None,
            "current_snapshot_content_hash": current.content_hash if current else None,
            "snapshot_chain_verified": bool(
                current is not None and previous is not None and current.previous_snapshot_id == previous.id
            ),
            "catalog_differential": differential.payload(),
        },
    )


def verify_routed_regulatory_changes(
    session: Session,
    *,
    limit: int = 100,
    actor: str = "regulatory-verification-agent",
) -> dict[str, Any]:
    """Verify RI.A1 candidates without approving changes or publishing canonical truth."""

    changes = session.exec(
        select(RegulatoryChange)
        .where(RegulatoryChange.status == "pending_review")
        .order_by(RegulatoryChange.detected_at)
        .limit(min(max(limit, 1), 500))
    ).all()

    results: list[RegulatoryMachineVerification] = []
    audit_writes = 0
    for change in changes:
        route_audit = _latest_machine_route(session, change)
        route_payload = _load_json(route_audit.after_state_json if route_audit else None, {})
        if not (
            route_payload.get("routing_version") == ROUTING_VERSION
            and route_payload.get("machine_verification_candidate") is True
        ):
            continue

        result = verify_regulatory_change_independently(session, change)
        results.append(result)
        payload = result.payload()
        previous_verification = session.exec(
            select(AuditLog)
            .where(AuditLog.action == VERIFICATION_ACTION)
            .where(AuditLog.entity_type == "regulatory_change")
            .where(AuditLog.entity_id == str(change.id))
            .order_by(AuditLog.created_at.desc())
        ).first()
        previous_payload = _load_json(
            previous_verification.after_state_json if previous_verification else None,
            {},
        )
        if previous_payload == payload:
            continue

        record_audit(
            session,
            action=VERIFICATION_ACTION,
            entity_type="regulatory_change",
            entity_id=change.id,
            after_state=payload,
            reason=(
                "Independent snapshot-catalog verification passed; canonical publication remains forbidden."
                if result.independently_verified
                else "Independent verification could not establish the routed change; keep it outside machine promotion."
            ),
            actor=actor,
            source=VERIFICATION_VERSION,
        )
        audit_writes += 1

    session.commit()
    return {
        "verification_version": VERIFICATION_VERSION,
        "verification_method": VERIFICATION_METHOD,
        "scanned": len(changes),
        "routed_candidates": len(results),
        "independently_verified": sum(1 for item in results if item.independently_verified),
        "unresolved": sum(1 for item in results if not item.independently_verified),
        "canonical_writes": 0,
        "audit_writes": audit_writes,
        "results": [item.payload() for item in results],
    }
