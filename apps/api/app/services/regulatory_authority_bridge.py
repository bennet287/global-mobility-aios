from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from sqlmodel import Session, select

from app.core.organization_constitution import AutonomyLevel, RiskTier
from app.models.domain import AuditLog, RegulatoryChange
from app.services.audit_log import record_audit
from app.services.organization_autonomy_profile import (
    AutonomyProfileIntegrityError,
    capability_autonomy_profile_snapshot,
)
from app.services.regulatory_promotion_authorization import (
    AUTHORIZATION_ACTION,
    AUTHORIZATION_VERSION,
)


BRIDGE_VERSION = "regulatory-authority-bridge-v1"
BRIDGE_ACTION = "regulatory_machine_authority_bridge_assessed"
POSITION_KEY = "reviewer"
CAPABILITY_KEY = "verified_rule.publication"
CONTEXT_SCOPE = "regulatory:new_program:deterministic"
REQUIRED_AUTHORITY = "deterministic_verified_rule_publication"
MINIMUM_AUTONOMY = AutonomyLevel.A4
REQUIRED_RISK = RiskTier.R4
EXECUTION_BRIDGE_ENABLED = False


@dataclass(frozen=True)
class RegulatoryAuthorityBridgeAssessment:
    regulatory_change_id: str
    bridge_version: str
    authorization_audit_id: str | None
    autonomy_profile_id: str | None
    autonomy_profile_sequence: int | None
    position_key: str
    capability_key: str
    context_scope: str
    autonomy_level: str | None
    board_ceiling: str | None
    authority_requirement: str | None
    risk_ceiling: str | None
    governance_source: str | None
    evidence_ready: bool
    board_delegation_valid: bool
    execution_bridge_enabled: bool
    execution_authority: bool
    bridge_state: str
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


def _latest_authorization(
    session: Session,
    change: RegulatoryChange,
) -> tuple[AuditLog | None, dict[str, Any]]:
    audit = session.exec(
        select(AuditLog)
        .where(AuditLog.action == AUTHORIZATION_ACTION)
        .where(AuditLog.entity_type == "regulatory_change")
        .where(AuditLog.entity_id == str(change.id))
        .order_by(AuditLog.created_at.desc())
    ).first()
    payload = _load_json(audit.after_state_json if audit else None, {})
    valid = bool(
        audit
        and payload.get("authorization_version") == AUTHORIZATION_VERSION
        and payload.get("verified_rule_writes_allowed") is False
        and payload.get("pathway_writes_allowed") is False
        and payload.get("publication_writes_allowed") is False
        and payload.get("canonical_write_allowed") is False
        and payload.get("execution_authority") is False
    )
    return audit, payload if valid else {}


def _autonomy_rank(value: str) -> int:
    return int(AutonomyLevel(value).value[1])


def assess_regulatory_authority_bridge(
    session: Session,
    change: RegulatoryChange,
) -> RegulatoryAuthorityBridgeAssessment:
    """Assess whether Human Board autonomy truth could authorize the RI.A7.1 envelope.

    This is deliberately not an execution adapter. Even a valid Board delegation only
    proves that the organizational authority prerequisite exists. The existing
    regulatory publication transaction remains human-authenticated, so canonical writes
    stay disabled until a separate, explicitly governed machine publication route is
    implemented and proven.
    """

    reasons: list[str] = []
    authorization_audit, authorization = _latest_authorization(session, change)
    evidence_ready = bool(
        authorization
        and authorization.get("evidence_ready") is True
        and authorization.get("authorization_state") == "evidence_ready_authority_missing"
    )
    if not authorization:
        reasons.append("current_authorization_envelope_missing")
    elif not evidence_ready:
        reasons.append("authorization_evidence_not_ready")

    profile = None
    current_revision = None
    try:
        profile = capability_autonomy_profile_snapshot(
            session,
            tenant_key="default",
            position_key=POSITION_KEY,
            capability_key=CAPABILITY_KEY,
            context_scope=CONTEXT_SCOPE,
        )
    except AutonomyProfileIntegrityError:
        reasons.append("autonomy_profile_integrity_failed")

    if profile is None:
        reasons.append("board_autonomy_profile_missing")
    else:
        current_revision = profile.revisions[-1]
        try:
            if _autonomy_rank(current_revision.autonomy_level) < _autonomy_rank(MINIMUM_AUTONOMY.value):
                reasons.append("autonomy_level_below_machine_publication_threshold")
            if _autonomy_rank(current_revision.board_ceiling) < _autonomy_rank(current_revision.autonomy_level):
                reasons.append("autonomy_level_exceeds_board_ceiling")
        except ValueError:
            reasons.append("autonomy_tier_invalid")
        if current_revision.authority_requirement != REQUIRED_AUTHORITY:
            reasons.append("authority_requirement_mismatch")
        if current_revision.risk_ceiling != REQUIRED_RISK.value:
            reasons.append("risk_ceiling_must_be_r4")
        if current_revision.governance_source != "human_board":
            reasons.append("governance_source_not_human_board")

    delegation_reasons = {
        "autonomy_profile_integrity_failed",
        "board_autonomy_profile_missing",
        "autonomy_level_below_machine_publication_threshold",
        "autonomy_level_exceeds_board_ceiling",
        "autonomy_tier_invalid",
        "authority_requirement_mismatch",
        "risk_ceiling_must_be_r4",
        "governance_source_not_human_board",
    }
    unique_reasons = tuple(sorted(set(reasons)))
    board_delegation_valid = not any(reason in delegation_reasons for reason in unique_reasons)
    execution_authority = bool(
        evidence_ready and board_delegation_valid and EXECUTION_BRIDGE_ENABLED
    )
    if execution_authority:
        bridge_state = "execution_authorized"
    elif evidence_ready and board_delegation_valid:
        bridge_state = "delegation_ready_execution_adapter_missing"
    elif evidence_ready:
        bridge_state = "board_delegation_required"
    else:
        bridge_state = "quarantined"

    return RegulatoryAuthorityBridgeAssessment(
        regulatory_change_id=str(change.id),
        bridge_version=BRIDGE_VERSION,
        authorization_audit_id=str(authorization_audit.id) if authorization_audit else None,
        autonomy_profile_id=str(profile.current_profile_id) if profile else None,
        autonomy_profile_sequence=(current_revision.profile_sequence if current_revision else None),
        position_key=POSITION_KEY,
        capability_key=CAPABILITY_KEY,
        context_scope=CONTEXT_SCOPE,
        autonomy_level=(current_revision.autonomy_level if current_revision else None),
        board_ceiling=(current_revision.board_ceiling if current_revision else None),
        authority_requirement=(current_revision.authority_requirement if current_revision else None),
        risk_ceiling=(current_revision.risk_ceiling if current_revision else None),
        governance_source=(current_revision.governance_source if current_revision else None),
        evidence_ready=evidence_ready,
        board_delegation_valid=board_delegation_valid,
        execution_bridge_enabled=EXECUTION_BRIDGE_ENABLED,
        execution_authority=execution_authority,
        bridge_state=bridge_state,
        canonical_write_allowed=False,
        reasons=unique_reasons,
    )


def scan_regulatory_authority_bridge(
    session: Session,
    *,
    limit: int = 100,
    actor: str = "regulatory-authority-bridge-agent",
) -> dict[str, Any]:
    """Persist RI.A7.2 bridge assessments only; never publish regulatory truth."""

    changes = session.exec(
        select(RegulatoryChange)
        .where(RegulatoryChange.status == "pending_review")
        .where(RegulatoryChange.change_type == "new_program")
        .order_by(RegulatoryChange.detected_at)
        .limit(min(max(limit, 1), 500))
    ).all()

    assessments: list[RegulatoryAuthorityBridgeAssessment] = []
    audit_writes = 0
    for change in changes:
        _, authorization = _latest_authorization(session, change)
        if not authorization:
            continue
        assessment = assess_regulatory_authority_bridge(session, change)
        assessments.append(assessment)
        payload = assessment.payload()
        previous = session.exec(
            select(AuditLog)
            .where(AuditLog.action == BRIDGE_ACTION)
            .where(AuditLog.entity_type == "regulatory_change")
            .where(AuditLog.entity_id == str(change.id))
            .order_by(AuditLog.created_at.desc())
        ).first()
        if _load_json(previous.after_state_json if previous else None, {}) == payload:
            continue
        record_audit(
            session,
            action=BRIDGE_ACTION,
            entity_type="regulatory_change",
            entity_id=change.id,
            after_state=payload,
            reason=(
                "Assessed Human Board capability delegation for deterministic regulatory publication; execution adapter remains disabled."
            ),
            actor=actor,
            source=BRIDGE_VERSION,
        )
        audit_writes += 1

    session.commit()
    return {
        "bridge_version": BRIDGE_VERSION,
        "execution_bridge_enabled": EXECUTION_BRIDGE_ENABLED,
        "scanned": len(changes),
        "assessed": len(assessments),
        "delegation_ready": sum(1 for item in assessments if item.board_delegation_valid and item.evidence_ready),
        "board_delegation_required": sum(1 for item in assessments if item.evidence_ready and not item.board_delegation_valid),
        "execution_authorized": sum(1 for item in assessments if item.execution_authority),
        "verified_rule_writes": 0,
        "publication_writes": 0,
        "canonical_writes": 0,
        "audit_writes": audit_writes,
        "assessments": [item.payload() for item in assessments],
    }
