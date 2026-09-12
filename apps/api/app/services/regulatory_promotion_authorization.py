from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from sqlmodel import Session, select

from app.models.domain import AuditLog, RegulatoryChange
from app.services.audit_log import record_audit
from app.services.regulatory_freshness_guard import FRESHNESS_ACTION, FRESHNESS_VERSION
from app.services.regulatory_promotion_policy import PROMOTION_ACTION, PROMOTION_POLICY_VERSION
from app.services.regulatory_rule_compiler import COMPILER_ACTION, COMPILER_VERSION


AUTHORIZATION_VERSION = "regulatory-promotion-authorization-v1"
AUTHORIZATION_ACTION = "regulatory_machine_promotion_authorization_assessed"
AUTHORITY_MODEL = "human-board-governed-publication-v1"
EXECUTION_AUTHORITY = False


@dataclass(frozen=True)
class IntendedRuleMutation:
    candidate_key: str
    program_id: str
    rule_key: str
    field: str
    operator: str
    value_type: str
    value: Any
    currency: str | None
    unit: str | None
    effective_from: str | None
    effective_to: str | None
    source_text: str
    intended_operation: str
    execution_allowed: bool

    def payload(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PromotionAuthorizationEnvelope:
    regulatory_change_id: str
    authorization_version: str
    authority_model: str
    promotion_audit_id: str | None
    freshness_audit_id: str | None
    compiler_audit_id: str | None
    source_snapshot_id: str | None
    source_snapshot_content_hash: str | None
    authorization_state: str
    evidence_ready: bool
    execution_authority: bool
    human_publication_contract_required: bool
    intended_rule_mutations: tuple[IntendedRuleMutation, ...]
    verified_rule_writes_allowed: bool
    pathway_writes_allowed: bool
    publication_writes_allowed: bool
    canonical_write_allowed: bool
    reasons: tuple[str, ...]

    def payload(self) -> dict[str, Any]:
        return {
            "regulatory_change_id": self.regulatory_change_id,
            "authorization_version": self.authorization_version,
            "authority_model": self.authority_model,
            "promotion_audit_id": self.promotion_audit_id,
            "freshness_audit_id": self.freshness_audit_id,
            "compiler_audit_id": self.compiler_audit_id,
            "source_snapshot_id": self.source_snapshot_id,
            "source_snapshot_content_hash": self.source_snapshot_content_hash,
            "authorization_state": self.authorization_state,
            "evidence_ready": self.evidence_ready,
            "execution_authority": self.execution_authority,
            "human_publication_contract_required": self.human_publication_contract_required,
            "intended_rule_mutations": [item.payload() for item in self.intended_rule_mutations],
            "verified_rule_writes_allowed": self.verified_rule_writes_allowed,
            "pathway_writes_allowed": self.pathway_writes_allowed,
            "publication_writes_allowed": self.publication_writes_allowed,
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


def _current_promotion(
    session: Session,
    change: RegulatoryChange,
) -> tuple[AuditLog | None, dict[str, Any]]:
    audit, payload = _latest_audit(session, change=change, action=PROMOTION_ACTION)
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


def _current_freshness(
    session: Session,
    change: RegulatoryChange,
) -> tuple[AuditLog | None, dict[str, Any]]:
    audit, payload = _latest_audit(session, change=change, action=FRESHNESS_ACTION)
    valid = bool(
        audit
        and payload.get("freshness_version") == FRESHNESS_VERSION
        and payload.get("canonical_write_allowed") is False
    )
    return audit, payload if valid else {}


def _current_compiler(
    session: Session,
    change: RegulatoryChange,
) -> tuple[AuditLog | None, dict[str, Any]]:
    audit, payload = _latest_audit(session, change=change, action=COMPILER_ACTION)
    valid = bool(
        audit
        and payload.get("compiler_version") == COMPILER_VERSION
        and payload.get("candidate_only") is True
        and payload.get("verified_rule_write_allowed") is False
        and payload.get("pathway_write_allowed") is False
        and payload.get("publication_allowed") is False
        and payload.get("canonical_write_allowed") is False
    )
    return audit, payload if valid else {}


def _eligible_program_ids(promotion_payload: dict[str, Any]) -> set[str]:
    candidates = promotion_payload.get("candidates", []) if isinstance(promotion_payload, dict) else []
    if not isinstance(candidates, list):
        return set()
    return {
        str(candidate.get("program_id") or "").strip()
        for candidate in candidates
        if isinstance(candidate, dict)
        and candidate.get("shadow_promotion_eligible") is True
        and candidate.get("outcome") == "shadow_eligible"
        and str(candidate.get("program_id") or "").strip()
    }


def _intended_mutations(
    compiler_payload: dict[str, Any],
    *,
    eligible_program_ids: set[str],
) -> tuple[IntendedRuleMutation, ...]:
    candidates = compiler_payload.get("candidates", []) if isinstance(compiler_payload, dict) else []
    if not isinstance(candidates, list):
        return ()
    mutations: list[IntendedRuleMutation] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        program_id = str(candidate.get("program_id") or "").strip()
        if program_id not in eligible_program_ids:
            continue
        if candidate.get("compile_status") != "typed_candidate":
            continue
        typed_rules = candidate.get("typed_rules", [])
        if not isinstance(typed_rules, list):
            continue
        for rule in typed_rules:
            if not isinstance(rule, dict) or rule.get("deterministic") is not True:
                continue
            rule_key = str(rule.get("rule_key") or "").strip()
            source_text = str(rule.get("source_text") or "").strip()
            if not rule_key or not source_text:
                continue
            mutations.append(
                IntendedRuleMutation(
                    candidate_key=str(candidate.get("candidate_key") or "").strip(),
                    program_id=program_id,
                    rule_key=rule_key,
                    field=str(rule.get("field") or "").strip(),
                    operator=str(rule.get("operator") or "").strip(),
                    value_type=str(rule.get("value_type") or "").strip(),
                    value=rule.get("value"),
                    currency=(str(rule.get("currency") or "").strip() or None),
                    unit=(str(rule.get("unit") or "").strip() or None),
                    effective_from=(str(rule.get("effective_from") or "").strip() or None),
                    effective_to=(str(rule.get("effective_to") or "").strip() or None),
                    source_text=source_text,
                    intended_operation="create_verified_rule_candidate",
                    execution_allowed=False,
                )
            )
    return tuple(sorted(mutations, key=lambda item: (item.program_id, item.rule_key)))


def assess_machine_promotion_authorization(
    session: Session,
    change: RegulatoryChange,
) -> PromotionAuthorizationEnvelope:
    """Bind verified evidence into an execution-disabled machine-promotion envelope.

    Current canonical rule publication is governed by authenticated human review and
    Human Board authority. This envelope therefore records readiness and exact intended
    mutations only; it never fabricates a human approver or grants execution authority.
    """

    reasons: list[str] = []
    if change.status != "pending_review":
        reasons.append("change_not_pending_review")

    promotion_audit, promotion_payload = _current_promotion(session, change)
    if not promotion_payload:
        reasons.append("current_shadow_promotion_packet_missing")

    freshness_audit, freshness_payload = _current_freshness(session, change)
    if not freshness_payload:
        reasons.append("current_freshness_packet_missing")

    compiler_audit, compiler_payload = _current_compiler(session, change)
    if not compiler_payload:
        reasons.append("current_compiler_packet_missing")

    if promotion_payload and compiler_payload:
        if promotion_payload.get("compiler_audit_id") != str(compiler_audit.id):
            reasons.append("promotion_compiler_lineage_mismatch")
        if promotion_payload.get("source_snapshot_id") != compiler_payload.get("source_snapshot_id"):
            reasons.append("promotion_compiler_snapshot_mismatch")
        if promotion_payload.get("source_snapshot_content_hash") != compiler_payload.get("source_snapshot_content_hash"):
            reasons.append("promotion_compiler_snapshot_hash_mismatch")
        promotion_reasons = promotion_payload.get("reasons", [])
        if isinstance(promotion_reasons, list) and promotion_reasons:
            reasons.append("shadow_promotion_packet_has_exceptions")

    if freshness_payload and promotion_payload:
        if freshness_payload.get("promotion_audit_id") != str(promotion_audit.id):
            reasons.append("freshness_promotion_lineage_mismatch")
        if freshness_payload.get("source_snapshot_id") != promotion_payload.get("source_snapshot_id"):
            reasons.append("freshness_promotion_snapshot_mismatch")
        if freshness_payload.get("source_snapshot_content_hash") != promotion_payload.get("source_snapshot_content_hash"):
            reasons.append("freshness_promotion_snapshot_hash_mismatch")
        if freshness_payload.get("quarantine_required") is not False:
            reasons.append("freshness_quarantine_required")
        if freshness_payload.get("shadow_eligibility_revoked") is True:
            reasons.append("shadow_eligibility_revoked")
        if freshness_payload.get("freshness_status") not in {"fresh", "fresh_equivalent"}:
            reasons.append("freshness_not_clear")

    eligible_ids = _eligible_program_ids(promotion_payload)
    if not eligible_ids:
        reasons.append("no_shadow_eligible_candidates")

    mutations = _intended_mutations(compiler_payload, eligible_program_ids=eligible_ids)
    if not mutations:
        reasons.append("no_deterministic_rule_mutations_ready")

    unique_reasons = tuple(sorted(set(reasons)))
    evidence_ready = not unique_reasons
    return PromotionAuthorizationEnvelope(
        regulatory_change_id=str(change.id),
        authorization_version=AUTHORIZATION_VERSION,
        authority_model=AUTHORITY_MODEL,
        promotion_audit_id=str(promotion_audit.id) if promotion_audit else None,
        freshness_audit_id=str(freshness_audit.id) if freshness_audit else None,
        compiler_audit_id=str(compiler_audit.id) if compiler_audit else None,
        source_snapshot_id=promotion_payload.get("source_snapshot_id") if promotion_payload else None,
        source_snapshot_content_hash=(
            promotion_payload.get("source_snapshot_content_hash") if promotion_payload else None
        ),
        authorization_state=(
            "evidence_ready_authority_missing" if evidence_ready else "quarantined"
        ),
        evidence_ready=evidence_ready,
        execution_authority=EXECUTION_AUTHORITY,
        human_publication_contract_required=True,
        intended_rule_mutations=mutations,
        verified_rule_writes_allowed=False,
        pathway_writes_allowed=False,
        publication_writes_allowed=False,
        canonical_write_allowed=False,
        reasons=unique_reasons,
    )


def generate_machine_promotion_authorization_envelopes(
    session: Session,
    *,
    limit: int = 100,
    actor: str = "regulatory-promotion-authorization-agent",
) -> dict[str, Any]:
    """Generate RI.A7.1 authorization envelopes without executing canonical writes."""

    changes = session.exec(
        select(RegulatoryChange)
        .where(RegulatoryChange.status == "pending_review")
        .where(RegulatoryChange.change_type == "new_program")
        .order_by(RegulatoryChange.detected_at)
        .limit(min(max(limit, 1), 500))
    ).all()

    envelopes: list[PromotionAuthorizationEnvelope] = []
    audit_writes = 0
    for change in changes:
        _, promotion_payload = _current_promotion(session, change)
        _, freshness_payload = _current_freshness(session, change)
        if not promotion_payload or not freshness_payload:
            continue

        envelope = assess_machine_promotion_authorization(session, change)
        envelopes.append(envelope)
        payload = envelope.payload()
        previous = session.exec(
            select(AuditLog)
            .where(AuditLog.action == AUTHORIZATION_ACTION)
            .where(AuditLog.entity_type == "regulatory_change")
            .where(AuditLog.entity_id == str(change.id))
            .order_by(AuditLog.created_at.desc())
        ).first()
        previous_payload = _load_json(previous.after_state_json if previous else None, {})
        if previous_payload == payload:
            continue

        record_audit(
            session,
            action=AUTHORIZATION_ACTION,
            entity_type="regulatory_change",
            entity_id=change.id,
            after_state=payload,
            reason=(
                "Machine-promotion evidence envelope generated; current publication authority remains human-governed and execution is disabled."
            ),
            actor=actor,
            source=AUTHORIZATION_VERSION,
        )
        audit_writes += 1

    session.commit()
    return {
        "authorization_version": AUTHORIZATION_VERSION,
        "authority_model": AUTHORITY_MODEL,
        "execution_authority": False,
        "scanned": len(changes),
        "envelopes": len(envelopes),
        "evidence_ready": sum(1 for item in envelopes if item.evidence_ready),
        "quarantined": sum(1 for item in envelopes if not item.evidence_ready),
        "verified_rule_writes": 0,
        "pathway_writes": 0,
        "publication_writes": 0,
        "canonical_writes": 0,
        "audit_writes": audit_writes,
        "packets": [item.payload() for item in envelopes],
    }
