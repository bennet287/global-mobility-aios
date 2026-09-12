from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from sqlmodel import Session, select

from app.models.domain import AuditLog, HumanReview, RegulatoryChange, ReviewStatus, VerifiedRule
from app.services.audit_log import record_audit
from app.services.regulatory_authority_bridge import (
    BRIDGE_ACTION,
    BRIDGE_VERSION,
    assess_regulatory_authority_bridge,
)
from app.services.regulatory_promotion_authorization import (
    AUTHORIZATION_ACTION,
    AUTHORIZATION_VERSION,
)


EXECUTION_ADAPTER_VERSION = "regulatory-publication-execution-adapter-v1"
EXECUTION_ADAPTER_ACTION = "regulatory_machine_publication_execution_preflight"
MACHINE_PUBLICATION_ENABLED = False

# RI.A7.4 adds durable Board-delegated review disposition and an atomic
# multi-rule publication-set contract. Production execution remains gated by the
# independent MACHINE_PUBLICATION_ENABLED kill switch.
REVIEW_DISPOSITION_CONTRACT_READY = True
MULTI_RULE_PUBLICATION_CONTRACT_READY = True

CANONICAL_CONTRACT_BLOCKERS = frozenset(
    {
        "machine_review_disposition_contract_missing",
        "atomic_multi_rule_publication_contract_missing",
    }
)


@dataclass(frozen=True)
class RegulatoryPublicationExecutionPreflight:
    regulatory_change_id: str
    adapter_version: str
    bridge_audit_id: str | None
    authorization_audit_id: str | None
    board_delegation_valid: bool
    evidence_ready: bool
    source_snapshot_id: str | None
    source_snapshot_content_hash: str | None
    intended_rule_count: int
    existing_verified_rule_count: int
    pending_human_review_count: int
    review_disposition_contract_ready: bool
    multi_rule_publication_contract_ready: bool
    machine_publication_enabled: bool
    execution_authority: bool
    execution_state: str
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


def _latest_audit(
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


def _current_authorization(
    session: Session,
    change: RegulatoryChange,
) -> tuple[AuditLog | None, dict[str, Any]]:
    audit, payload = _latest_audit(session, change=change, action=AUTHORIZATION_ACTION)
    valid = bool(
        audit
        and payload.get("authorization_version") == AUTHORIZATION_VERSION
        and payload.get("evidence_ready") is True
        and payload.get("authorization_state") == "evidence_ready_authority_missing"
        and payload.get("execution_authority") is False
        and payload.get("verified_rule_writes_allowed") is False
        and payload.get("publication_writes_allowed") is False
        and payload.get("canonical_write_allowed") is False
    )
    return audit, payload if valid else {}


def _current_bridge(
    session: Session,
    change: RegulatoryChange,
) -> tuple[AuditLog | None, dict[str, Any]]:
    audit, payload = _latest_audit(session, change=change, action=BRIDGE_ACTION)
    valid = bool(
        audit
        and payload.get("bridge_version") == BRIDGE_VERSION
        and payload.get("evidence_ready") is True
        and payload.get("board_delegation_valid") is True
        and payload.get("bridge_state") == "delegation_ready_execution_adapter_missing"
        and payload.get("execution_bridge_enabled") is False
        and payload.get("execution_authority") is False
        and payload.get("canonical_write_allowed") is False
    )
    return audit, payload if valid else {}


def _execution_state(reasons: tuple[str, ...]) -> str:
    """Classify preflight reasons without allowing the kill switch to mask drift."""

    reason_set = set(reasons)
    if not reason_set:
        return "execution_authorized"

    non_switch_reasons = reason_set - {"machine_publication_disabled"}
    if not non_switch_reasons:
        return "ready_but_disabled"
    if non_switch_reasons.issubset(CANONICAL_CONTRACT_BLOCKERS):
        return "blocked_canonical_contract_gap"
    return "quarantined"


def assess_regulatory_publication_execution(
    session: Session,
    change: RegulatoryChange,
    *,
    machine_publication_enabled: bool | None = None,
) -> RegulatoryPublicationExecutionPreflight:
    """Fail-closed preflight for deterministic Board-delegated publication.

    RI.A7.4 closes the two canonical representation gaps identified by RI.A7.3:
    Board-delegated machine disposition is persisted separately from human review,
    and one publication set can own multiple VerifiedRules atomically. Live execution
    remains disabled by default; the explicit override exists only so the governed
    transaction service can prove the same preflight when its own kill switch is enabled.
    """

    enabled = MACHINE_PUBLICATION_ENABLED if machine_publication_enabled is None else bool(machine_publication_enabled)
    reasons: list[str] = []
    if change.status != "pending_review":
        reasons.append("change_not_pending_review")
    if change.change_type != "new_program":
        reasons.append("change_type_not_supported")

    authorization_audit, authorization = _current_authorization(session, change)
    if not authorization:
        reasons.append("current_authorization_envelope_missing_or_not_ready")

    bridge_audit, bridge = _current_bridge(session, change)
    if not bridge:
        reasons.append("current_authority_bridge_missing_or_not_delegation_ready")

    live_bridge = assess_regulatory_authority_bridge(session, change)
    if not live_bridge.evidence_ready:
        reasons.append("live_evidence_not_ready")
    if not live_bridge.board_delegation_valid:
        reasons.append("live_board_delegation_invalid")
    if live_bridge.bridge_state != "delegation_ready_execution_adapter_missing":
        reasons.append("live_bridge_state_not_delegation_ready")

    if authorization and bridge:
        if bridge.get("authorization_audit_id") != str(authorization_audit.id):
            reasons.append("bridge_authorization_lineage_mismatch")
        if bridge.get("autonomy_profile_id") != live_bridge.autonomy_profile_id:
            reasons.append("bridge_autonomy_profile_stale")
        if bridge.get("autonomy_profile_sequence") != live_bridge.autonomy_profile_sequence:
            reasons.append("bridge_autonomy_profile_sequence_stale")

    intended = authorization.get("intended_rule_mutations", []) if authorization else []
    if not isinstance(intended, list):
        intended = []
        reasons.append("intended_rule_mutations_invalid")
    intended_rule_count = len(intended)
    if intended_rule_count < 1:
        reasons.append("no_intended_rule_mutations")
    if intended_rule_count > 100:
        reasons.append("intended_rule_mutation_bound_exceeded")

    source_snapshot_id = authorization.get("source_snapshot_id") if authorization else None
    source_snapshot_hash = authorization.get("source_snapshot_content_hash") if authorization else None
    if not source_snapshot_id or not source_snapshot_hash:
        reasons.append("authorization_snapshot_provenance_missing")

    pending_reviews = session.exec(
        select(HumanReview)
        .where(HumanReview.regulatory_change_id == change.id)
        .where(HumanReview.status == ReviewStatus.pending)
    ).all()
    if pending_reviews and not REVIEW_DISPOSITION_CONTRACT_READY:
        reasons.append("machine_review_disposition_contract_missing")

    existing_rules = session.exec(
        select(VerifiedRule).where(VerifiedRule.regulatory_change_id == change.id)
    ).all()
    if existing_rules:
        reasons.append("verified_rules_already_exist_for_change")

    if intended_rule_count > 1 and not MULTI_RULE_PUBLICATION_CONTRACT_READY:
        reasons.append("atomic_multi_rule_publication_contract_missing")

    if not enabled:
        reasons.append("machine_publication_disabled")

    unique_reasons = tuple(sorted(set(reasons)))
    execution_state = _execution_state(unique_reasons)
    execution_authority = execution_state == "execution_authorized"

    return RegulatoryPublicationExecutionPreflight(
        regulatory_change_id=str(change.id),
        adapter_version=EXECUTION_ADAPTER_VERSION,
        bridge_audit_id=str(bridge_audit.id) if bridge_audit else None,
        authorization_audit_id=str(authorization_audit.id) if authorization_audit else None,
        board_delegation_valid=live_bridge.board_delegation_valid,
        evidence_ready=live_bridge.evidence_ready,
        source_snapshot_id=source_snapshot_id,
        source_snapshot_content_hash=source_snapshot_hash,
        intended_rule_count=intended_rule_count,
        existing_verified_rule_count=len(existing_rules),
        pending_human_review_count=len(pending_reviews),
        review_disposition_contract_ready=REVIEW_DISPOSITION_CONTRACT_READY,
        multi_rule_publication_contract_ready=MULTI_RULE_PUBLICATION_CONTRACT_READY,
        machine_publication_enabled=enabled,
        execution_authority=execution_authority,
        execution_state=execution_state,
        canonical_write_allowed=execution_authority,
        reasons=unique_reasons,
    )


def scan_regulatory_publication_execution_preflight(
    session: Session,
    *,
    limit: int = 100,
    actor: str = "regulatory-publication-execution-adapter",
) -> dict[str, Any]:
    """Persist execution preflights; production publication remains disabled."""

    changes = session.exec(
        select(RegulatoryChange)
        .where(RegulatoryChange.status == "pending_review")
        .where(RegulatoryChange.change_type == "new_program")
        .order_by(RegulatoryChange.detected_at)
        .limit(min(max(limit, 1), 500))
    ).all()

    assessments: list[RegulatoryPublicationExecutionPreflight] = []
    audit_writes = 0
    for change in changes:
        _, bridge = _current_bridge(session, change)
        if not bridge:
            continue
        assessment = assess_regulatory_publication_execution(session, change)
        assessments.append(assessment)
        payload = assessment.payload()
        previous = session.exec(
            select(AuditLog)
            .where(AuditLog.action == EXECUTION_ADAPTER_ACTION)
            .where(AuditLog.entity_type == "regulatory_change")
            .where(AuditLog.entity_id == str(change.id))
            .order_by(AuditLog.created_at.desc())
        ).first()
        if _load_json(previous.after_state_json if previous else None, {}) == payload:
            continue
        record_audit(
            session,
            action=EXECUTION_ADAPTER_ACTION,
            entity_type="regulatory_change",
            entity_id=change.id,
            after_state=payload,
            reason=(
                "Publication execution preflight evaluated live Board delegation, evidence lineage, and canonical contract readiness; production execution remains gated."
            ),
            actor=actor,
            source=EXECUTION_ADAPTER_VERSION,
        )
        audit_writes += 1

    session.commit()
    return {
        "adapter_version": EXECUTION_ADAPTER_VERSION,
        "machine_publication_enabled": MACHINE_PUBLICATION_ENABLED,
        "review_disposition_contract_ready": REVIEW_DISPOSITION_CONTRACT_READY,
        "multi_rule_publication_contract_ready": MULTI_RULE_PUBLICATION_CONTRACT_READY,
        "scanned": len(changes),
        "assessed": len(assessments),
        "execution_authorized": sum(1 for item in assessments if item.execution_authority),
        "blocked_contract_gap": sum(1 for item in assessments if item.execution_state == "blocked_canonical_contract_gap"),
        "ready_but_disabled": sum(1 for item in assessments if item.execution_state == "ready_but_disabled"),
        "verified_rule_writes": 0,
        "publication_writes": 0,
        "canonical_writes": 0,
        "audit_writes": audit_writes,
        "assessments": [item.payload() for item in assessments],
    }
