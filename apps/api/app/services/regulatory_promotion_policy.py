from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from sqlmodel import Session, select

from app.models.domain import AuditLog, RegulatoryChange
from app.services.audit_log import record_audit
from app.services.regulatory_program_discovery import DISCOVERY_ACTION, DISCOVERY_VERSION
from app.services.regulatory_rule_compiler import COMPILER_ACTION, COMPILER_VERSION


PROMOTION_POLICY_VERSION = "regulatory-promotion-policy-v1"
PROMOTION_ACTION = "regulatory_shadow_promotion_assessed"
SHADOW_MODE = True


@dataclass(frozen=True)
class ShadowCandidateAssessment:
    candidate_key: str
    program_id: str
    outcome: str
    shadow_promotion_eligible: bool
    reasons: tuple[str, ...]
    typed_rule_keys: tuple[str, ...]
    publication_allowed: bool
    pathway_write_allowed: bool
    verified_rule_write_allowed: bool
    canonical_write_allowed: bool

    def payload(self) -> dict[str, Any]:
        value = asdict(self)
        value["reasons"] = list(self.reasons)
        value["typed_rule_keys"] = list(self.typed_rule_keys)
        return value


@dataclass(frozen=True)
class PromotionPolicyPacket:
    regulatory_change_id: str
    promotion_policy_version: str
    shadow_mode: bool
    compiler_audit_id: str | None
    discovery_audit_id: str | None
    source_snapshot_id: str | None
    source_snapshot_content_hash: str | None
    candidates: tuple[ShadowCandidateAssessment, ...]
    publication_writes_allowed: bool
    pathway_writes_allowed: bool
    verified_rule_writes_allowed: bool
    canonical_write_allowed: bool
    reasons: tuple[str, ...]

    def payload(self) -> dict[str, Any]:
        return {
            "regulatory_change_id": self.regulatory_change_id,
            "promotion_policy_version": self.promotion_policy_version,
            "shadow_mode": self.shadow_mode,
            "compiler_audit_id": self.compiler_audit_id,
            "discovery_audit_id": self.discovery_audit_id,
            "source_snapshot_id": self.source_snapshot_id,
            "source_snapshot_content_hash": self.source_snapshot_content_hash,
            "candidates": [item.payload() for item in self.candidates],
            "publication_writes_allowed": self.publication_writes_allowed,
            "pathway_writes_allowed": self.pathway_writes_allowed,
            "verified_rule_writes_allowed": self.verified_rule_writes_allowed,
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


def _current_compiler_packet(
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


def _current_discovery_packet(
    session: Session,
    change: RegulatoryChange,
) -> tuple[AuditLog | None, dict[str, Any]]:
    audit, payload = _latest_audit(session, change=change, action=DISCOVERY_ACTION)
    valid = bool(
        audit
        and payload.get("discovery_version") == DISCOVERY_VERSION
        and payload.get("discovery_eligible") is True
        and payload.get("candidate_only") is True
        and payload.get("publication_allowed") is False
        and payload.get("pathway_create_allowed") is False
        and payload.get("canonical_write_allowed") is False
    )
    return audit, payload if valid else {}


def _discovery_candidate_by_program(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    values = payload.get("candidates", []) if isinstance(payload, dict) else []
    if not isinstance(values, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for value in values:
        if not isinstance(value, dict):
            continue
        program_id = str(value.get("program_id") or "").strip()
        if program_id:
            result[program_id] = value
    return result


def evaluate_shadow_candidate(
    candidate: dict[str, Any],
    *,
    discovery_candidate: dict[str, Any] | None,
) -> ShadowCandidateAssessment:
    reasons: list[str] = []
    program_id = str(candidate.get("program_id") or "").strip()
    candidate_key = str(candidate.get("candidate_key") or "").strip()
    compile_status = str(candidate.get("compile_status") or "").strip()
    status = str(candidate.get("status") or "").strip().lower()
    typed_rules = candidate.get("typed_rules", [])
    candidate_reasons = candidate.get("reasons", [])

    if not candidate_key:
        reasons.append("candidate_key_missing")
    if not program_id:
        reasons.append("program_id_missing")
    if status not in {"active", "open", "available", "current"}:
        reasons.append("candidate_not_explicitly_active")
    if compile_status != "typed_candidate":
        reasons.append("candidate_not_fully_typed")
    if not isinstance(typed_rules, list) or not typed_rules:
        reasons.append("typed_rules_missing")
    else:
        seen: set[str] = set()
        for rule in typed_rules:
            if not isinstance(rule, dict):
                reasons.append("typed_rule_payload_invalid")
                continue
            rule_key = str(rule.get("rule_key") or "").strip()
            if not rule_key:
                reasons.append("typed_rule_key_missing")
            elif rule_key in seen:
                reasons.append("typed_rule_duplicate_key")
            else:
                seen.add(rule_key)
            if rule.get("deterministic") is not True:
                reasons.append("typed_rule_not_deterministic")
            if rule.get("publication_allowed") is not False:
                reasons.append("compiler_publication_boundary_invalid")
            if rule.get("canonical_write_allowed") is not False:
                reasons.append("compiler_canonical_boundary_invalid")
            if not str(rule.get("source_text") or "").strip():
                reasons.append("typed_rule_source_text_missing")

    if isinstance(candidate_reasons, list) and candidate_reasons:
        reasons.append("compiler_candidate_has_exceptions")

    if discovery_candidate is None:
        reasons.append("discovery_candidate_lineage_missing")
    else:
        possible_existing = discovery_candidate.get("possible_existing_pathway_ids", [])
        if isinstance(possible_existing, list) and possible_existing:
            reasons.append("possible_existing_pathway_requires_lineage_resolution")
        if discovery_candidate.get("candidate_only") is not True:
            reasons.append("discovery_candidate_boundary_invalid")
        if discovery_candidate.get("publication_allowed") is not False:
            reasons.append("discovery_publication_boundary_invalid")
        if discovery_candidate.get("pathway_create_allowed") is not False:
            reasons.append("discovery_pathway_boundary_invalid")
        if discovery_candidate.get("canonical_write_allowed") is not False:
            reasons.append("discovery_canonical_boundary_invalid")

    unique_reasons = tuple(sorted(set(reasons)))
    eligible = not unique_reasons
    rule_keys = tuple(
        sorted(
            str(rule.get("rule_key"))
            for rule in typed_rules
            if isinstance(rule, dict) and str(rule.get("rule_key") or "").strip()
        )
    ) if isinstance(typed_rules, list) else ()

    return ShadowCandidateAssessment(
        candidate_key=candidate_key,
        program_id=program_id,
        outcome="shadow_eligible" if eligible else "quarantined",
        shadow_promotion_eligible=eligible,
        reasons=unique_reasons,
        typed_rule_keys=rule_keys,
        publication_allowed=False,
        pathway_write_allowed=False,
        verified_rule_write_allowed=False,
        canonical_write_allowed=False,
    )


def assess_regulatory_shadow_promotion(
    session: Session,
    change: RegulatoryChange,
) -> PromotionPolicyPacket:
    reasons: list[str] = []
    if change.status != "pending_review":
        reasons.append("change_not_pending_review")

    compiler_audit, compiler_payload = _current_compiler_packet(session, change)
    if not compiler_payload:
        reasons.append("current_compiler_packet_missing")

    discovery_audit, discovery_payload = _current_discovery_packet(session, change)
    if not discovery_payload:
        reasons.append("current_discovery_packet_missing")

    if compiler_payload and discovery_payload:
        if compiler_payload.get("discovery_audit_id") != str(discovery_audit.id):
            reasons.append("compiler_discovery_lineage_mismatch")
        if compiler_payload.get("source_snapshot_id") != discovery_payload.get("source_snapshot_id"):
            reasons.append("compiler_discovery_snapshot_mismatch")
        if compiler_payload.get("source_snapshot_content_hash") != discovery_payload.get("source_snapshot_content_hash"):
            reasons.append("compiler_discovery_snapshot_hash_mismatch")

    discovery_by_program = _discovery_candidate_by_program(discovery_payload)
    candidate_values = compiler_payload.get("candidates", []) if compiler_payload else []
    assessments: list[ShadowCandidateAssessment] = []
    if not isinstance(candidate_values, list):
        reasons.append("compiler_candidates_invalid")
    else:
        for candidate in candidate_values:
            if not isinstance(candidate, dict):
                reasons.append("compiler_candidate_invalid")
                continue
            program_id = str(candidate.get("program_id") or "").strip()
            assessments.append(
                evaluate_shadow_candidate(
                    candidate,
                    discovery_candidate=discovery_by_program.get(program_id),
                )
            )

    if not assessments:
        reasons.append("no_compiled_candidates_to_assess")

    return PromotionPolicyPacket(
        regulatory_change_id=str(change.id),
        promotion_policy_version=PROMOTION_POLICY_VERSION,
        shadow_mode=SHADOW_MODE,
        compiler_audit_id=str(compiler_audit.id) if compiler_audit else None,
        discovery_audit_id=str(discovery_audit.id) if discovery_audit else None,
        source_snapshot_id=compiler_payload.get("source_snapshot_id") if compiler_payload else None,
        source_snapshot_content_hash=compiler_payload.get("source_snapshot_content_hash") if compiler_payload else None,
        candidates=tuple(assessments),
        publication_writes_allowed=False,
        pathway_writes_allowed=False,
        verified_rule_writes_allowed=False,
        canonical_write_allowed=False,
        reasons=tuple(sorted(set(reasons))),
    )


def run_shadow_promotion_policy(
    session: Session,
    *,
    limit: int = 100,
    actor: str = "regulatory-promotion-policy-agent",
) -> dict[str, Any]:
    """Assess RI.A7 promotion eligibility in shadow mode without canonical writes."""

    changes = session.exec(
        select(RegulatoryChange)
        .where(RegulatoryChange.status == "pending_review")
        .where(RegulatoryChange.change_type == "new_program")
        .order_by(RegulatoryChange.detected_at)
        .limit(min(max(limit, 1), 500))
    ).all()

    packets: list[PromotionPolicyPacket] = []
    audit_writes = 0
    for change in changes:
        _, compiler_payload = _current_compiler_packet(session, change)
        if not compiler_payload:
            continue
        packet = assess_regulatory_shadow_promotion(session, change)
        packets.append(packet)
        payload = packet.payload()

        previous = session.exec(
            select(AuditLog)
            .where(AuditLog.action == PROMOTION_ACTION)
            .where(AuditLog.entity_type == "regulatory_change")
            .where(AuditLog.entity_id == str(change.id))
            .order_by(AuditLog.created_at.desc())
        ).first()
        previous_payload = _load_json(previous.after_state_json if previous else None, {})
        if previous_payload == payload:
            continue

        record_audit(
            session,
            action=PROMOTION_ACTION,
            entity_type="regulatory_change",
            entity_id=change.id,
            after_state=payload,
            reason=(
                "Shadow promotion policy evaluated deterministic candidates; canonical publication remains disabled."
            ),
            actor=actor,
            source=PROMOTION_POLICY_VERSION,
        )
        audit_writes += 1

    session.commit()
    return {
        "promotion_policy_version": PROMOTION_POLICY_VERSION,
        "shadow_mode": True,
        "scanned": len(changes),
        "evaluated_packets": len(packets),
        "shadow_eligible_candidates": sum(
            1 for packet in packets for candidate in packet.candidates if candidate.shadow_promotion_eligible
        ),
        "quarantined_candidates": sum(
            1 for packet in packets for candidate in packet.candidates if not candidate.shadow_promotion_eligible
        ),
        "publication_writes": 0,
        "pathway_writes": 0,
        "verified_rule_writes": 0,
        "canonical_writes": 0,
        "audit_writes": audit_writes,
        "packets": [packet.payload() for packet in packets],
    }
