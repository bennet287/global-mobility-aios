from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlmodel import Session, select

from app.models.domain import AuditLog, RegulatoryChange, SourceSnapshot
from app.services.audit_log import record_audit
from app.services.regulatory_program_discovery import DISCOVERY_ACTION, DISCOVERY_VERSION


COMPILER_VERSION = "regulatory-rule-compiler-v1"
COMPILER_ACTION = "regulatory_candidate_rules_compiled"
SUPPORTED_OPERATORS = {
    "eq",
    "neq",
    "gt",
    "gte",
    "lt",
    "lte",
    "in",
    "not_in",
    "present",
    "absent",
}
SUPPORTED_VALUE_TYPES = {
    "string",
    "integer",
    "decimal",
    "boolean",
    "date",
    "currency_amount",
    "string_list",
}


@dataclass(frozen=True)
class CompiledRuleCandidate:
    rule_key: str
    field: str
    operator: str
    value_type: str
    value: Any
    unit: str | None
    currency: str | None
    effective_from: str | None
    effective_to: str | None
    source_text: str
    deterministic: bool
    publication_allowed: bool
    canonical_write_allowed: bool

    def payload(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CompiledPathwayCandidate:
    candidate_key: str
    program_id: str
    name: str
    status: str
    summary: str
    effective_date: str | None
    compile_status: str
    typed_rules: tuple[CompiledRuleCandidate, ...]
    reasons: tuple[str, ...]
    pathway_create_allowed: bool
    publication_allowed: bool
    canonical_write_allowed: bool

    def payload(self) -> dict[str, Any]:
        return {
            "candidate_key": self.candidate_key,
            "program_id": self.program_id,
            "name": self.name,
            "status": self.status,
            "summary": self.summary,
            "effective_date": self.effective_date,
            "compile_status": self.compile_status,
            "typed_rules": [item.payload() for item in self.typed_rules],
            "reasons": list(self.reasons),
            "pathway_create_allowed": self.pathway_create_allowed,
            "publication_allowed": self.publication_allowed,
            "canonical_write_allowed": self.canonical_write_allowed,
        }


@dataclass(frozen=True)
class RegulatoryCompilePacket:
    regulatory_change_id: str
    compiler_version: str
    discovery_audit_id: str | None
    source_snapshot_id: str | None
    source_snapshot_content_hash: str | None
    candidates: tuple[CompiledPathwayCandidate, ...]
    candidate_only: bool
    verified_rule_write_allowed: bool
    pathway_write_allowed: bool
    publication_allowed: bool
    canonical_write_allowed: bool
    reasons: tuple[str, ...]

    def payload(self) -> dict[str, Any]:
        return {
            "regulatory_change_id": self.regulatory_change_id,
            "compiler_version": self.compiler_version,
            "discovery_audit_id": self.discovery_audit_id,
            "source_snapshot_id": self.source_snapshot_id,
            "source_snapshot_content_hash": self.source_snapshot_content_hash,
            "candidates": [item.payload() for item in self.candidates],
            "candidate_only": self.candidate_only,
            "verified_rule_write_allowed": self.verified_rule_write_allowed,
            "pathway_write_allowed": self.pathway_write_allowed,
            "publication_allowed": self.publication_allowed,
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


def _latest_discovery(
    session: Session,
    change: RegulatoryChange,
) -> tuple[AuditLog | None, dict[str, Any]]:
    audit = session.exec(
        select(AuditLog)
        .where(AuditLog.action == DISCOVERY_ACTION)
        .where(AuditLog.entity_type == "regulatory_change")
        .where(AuditLog.entity_id == str(change.id))
        .order_by(AuditLog.created_at.desc())
    ).first()
    payload = _load_json(audit.after_state_json if audit else None, {})
    valid = bool(
        audit
        and payload.get("discovery_version") == DISCOVERY_VERSION
        and payload.get("candidate_only") is True
        and payload.get("publication_allowed") is False
        and payload.get("pathway_create_allowed") is False
        and payload.get("canonical_write_allowed") is False
    )
    return audit, payload if valid else {}


def _iso_date(value: Any) -> tuple[str | None, str | None]:
    if value in (None, ""):
        return None, None
    if not isinstance(value, str):
        return None, "date_value_not_string"
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return None, "date_value_invalid"
    return parsed.isoformat(), None


def _normalize_rule_value(
    *,
    operator: str,
    value_type: str,
    value: Any,
) -> tuple[Any, str | None, str | None, list[str]]:
    reasons: list[str] = []
    currency: str | None = None
    unit: str | None = None

    if operator in {"present", "absent"}:
        if value not in (None, ""):
            reasons.append("presence_operator_must_not_define_value")
        return None, currency, unit, reasons

    if value_type == "string":
        if not isinstance(value, str) or not value.strip():
            reasons.append("string_value_invalid")
            return value, currency, unit, reasons
        return value.strip(), currency, unit, reasons

    if value_type == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            reasons.append("integer_value_invalid")
        return value, currency, unit, reasons

    if value_type == "decimal":
        try:
            normalized = format(Decimal(str(value)), "f")
        except (InvalidOperation, ValueError, TypeError):
            reasons.append("decimal_value_invalid")
            return value, currency, unit, reasons
        return normalized, currency, unit, reasons

    if value_type == "boolean":
        if not isinstance(value, bool):
            reasons.append("boolean_value_invalid")
        return value, currency, unit, reasons

    if value_type == "date":
        normalized, error = _iso_date(value)
        if error:
            reasons.append(error)
            return value, currency, unit, reasons
        return normalized, currency, unit, reasons

    if value_type == "currency_amount":
        if not isinstance(value, dict):
            reasons.append("currency_amount_value_invalid")
            return value, currency, unit, reasons
        amount = value.get("amount")
        code = str(value.get("currency") or "").strip().upper()
        try:
            normalized_amount = format(Decimal(str(amount)), "f")
        except (InvalidOperation, ValueError, TypeError):
            reasons.append("currency_amount_invalid")
            normalized_amount = str(amount)
        if len(code) != 3 or not code.isalpha():
            reasons.append("currency_code_invalid")
        currency = code or None
        return {"amount": normalized_amount, "currency": code}, currency, unit, reasons

    if value_type == "string_list":
        if not isinstance(value, list) or not value:
            reasons.append("string_list_value_invalid")
            return value, currency, unit, reasons
        normalized = [str(item).strip() for item in value if str(item).strip()]
        if len(normalized) != len(value):
            reasons.append("string_list_value_invalid")
        return normalized, currency, unit, reasons

    reasons.append("value_type_unsupported")
    return value, currency, unit, reasons


def compile_typed_rule(raw: Any) -> tuple[CompiledRuleCandidate | None, tuple[str, ...]]:
    if not isinstance(raw, dict):
        return None, ("typed_rule_record_invalid",)

    rule_key = str(raw.get("rule_key") or raw.get("rule_id") or "").strip()
    field = str(raw.get("field") or "").strip()
    operator = str(raw.get("operator") or "").strip().lower()
    value_type = str(raw.get("value_type") or "").strip().lower()
    source_text = str(raw.get("source_text") or "").strip()
    reasons: list[str] = []

    if not rule_key:
        reasons.append("typed_rule_key_missing")
    if not field:
        reasons.append("typed_rule_field_missing")
    if operator not in SUPPORTED_OPERATORS:
        reasons.append("typed_rule_operator_unsupported")
    if value_type not in SUPPORTED_VALUE_TYPES:
        reasons.append("typed_rule_value_type_unsupported")
    if not source_text:
        reasons.append("typed_rule_source_text_missing")

    value = raw.get("value")
    normalized_value: Any = value
    currency: str | None = None
    unit = str(raw.get("unit") or "").strip() or None
    if operator in SUPPORTED_OPERATORS and value_type in SUPPORTED_VALUE_TYPES:
        normalized_value, currency, _, value_reasons = _normalize_rule_value(
            operator=operator,
            value_type=value_type,
            value=value,
        )
        reasons.extend(value_reasons)

    effective_from, effective_from_error = _iso_date(raw.get("effective_from"))
    effective_to, effective_to_error = _iso_date(raw.get("effective_to"))
    if effective_from_error:
        reasons.append("typed_rule_effective_from_invalid")
    if effective_to_error:
        reasons.append("typed_rule_effective_to_invalid")
    if effective_from and effective_to and effective_to < effective_from:
        reasons.append("typed_rule_effective_window_reversed")

    if reasons:
        return None, tuple(sorted(set(reasons)))

    return (
        CompiledRuleCandidate(
            rule_key=rule_key,
            field=field,
            operator=operator,
            value_type=value_type,
            value=normalized_value,
            unit=unit,
            currency=currency,
            effective_from=effective_from,
            effective_to=effective_to,
            source_text=source_text,
            deterministic=True,
            publication_allowed=False,
            canonical_write_allowed=False,
        ),
        (),
    )


def compile_regulatory_candidates(
    session: Session,
    change: RegulatoryChange,
) -> RegulatoryCompilePacket:
    reasons: list[str] = []
    if change.status != "pending_review":
        reasons.append("change_not_pending_review")

    discovery_audit, discovery_payload = _latest_discovery(session, change)
    if not discovery_payload:
        reasons.append("current_pathway_discovery_packet_missing")

    snapshot = session.get(SourceSnapshot, change.current_snapshot_id)
    if snapshot is None:
        reasons.append("current_snapshot_missing")
        metadata: dict[str, Any] = {}
    else:
        metadata = _load_json(snapshot.metadata_json, {})
        if snapshot.official_source_id != change.official_source_id:
            reasons.append("current_snapshot_source_mismatch")
        discovered_snapshot_id = str(discovery_payload.get("source_snapshot_id") or "")
        discovered_snapshot_hash = str(discovery_payload.get("source_snapshot_content_hash") or "")
        if discovered_snapshot_id and discovered_snapshot_id != str(snapshot.id):
            reasons.append("discovery_snapshot_id_mismatch")
        if discovered_snapshot_hash and discovered_snapshot_hash != str(snapshot.content_hash or ""):
            reasons.append("discovery_snapshot_hash_mismatch")

    catalog = metadata.get("program_catalog") if isinstance(metadata, dict) else None
    catalog_index: dict[str, dict[str, Any]] = {}
    if not isinstance(catalog, list):
        reasons.append("structured_program_catalog_missing")
    else:
        for row in catalog:
            if isinstance(row, dict):
                program_id = str(row.get("program_id") or "").strip()
                if program_id:
                    catalog_index[program_id] = row

    compiled_candidates: list[CompiledPathwayCandidate] = []
    discovered_candidates = discovery_payload.get("candidates", []) if discovery_payload else []
    if not isinstance(discovered_candidates, list):
        reasons.append("discovery_candidates_invalid")
        discovered_candidates = []

    for candidate in discovered_candidates:
        if not isinstance(candidate, dict):
            reasons.append("discovery_candidate_invalid")
            continue
        program_id = str(candidate.get("program_id") or "").strip()
        row = catalog_index.get(program_id)
        candidate_reasons: list[str] = []
        if row is None:
            candidate_reasons.append("candidate_program_missing_from_current_catalog")
            row = {}

        raw_rules = row.get("typed_rules")
        compiled_rules: list[CompiledRuleCandidate] = []
        if raw_rules in (None, []):
            candidate_reasons.append("typed_rule_evidence_missing")
        elif not isinstance(raw_rules, list):
            candidate_reasons.append("typed_rule_collection_invalid")
        else:
            seen_rule_keys: set[str] = set()
            for raw_rule in raw_rules:
                compiled, rule_reasons = compile_typed_rule(raw_rule)
                if compiled is None:
                    candidate_reasons.extend(rule_reasons)
                    continue
                if compiled.rule_key in seen_rule_keys:
                    candidate_reasons.append("typed_rule_duplicate_key")
                    continue
                seen_rule_keys.add(compiled.rule_key)
                compiled_rules.append(compiled)

        if raw_rules not in (None, []) and candidate_reasons:
            compile_status = "quarantined"
        elif compiled_rules:
            compile_status = "typed_candidate"
        else:
            compile_status = "pathway_only"

        compiled_candidates.append(
            CompiledPathwayCandidate(
                candidate_key=str(candidate.get("candidate_key") or "").strip(),
                program_id=program_id,
                name=str(candidate.get("name") or row.get("name") or "").strip(),
                status=str(candidate.get("status") or row.get("status") or "unknown").strip().lower(),
                summary=str(candidate.get("summary") or row.get("summary") or "").strip(),
                effective_date=(str(candidate.get("effective_date") or row.get("effective_date") or "").strip() or None),
                compile_status=compile_status,
                typed_rules=tuple(compiled_rules),
                reasons=tuple(sorted(set(candidate_reasons))),
                pathway_create_allowed=False,
                publication_allowed=False,
                canonical_write_allowed=False,
            )
        )

    if not compiled_candidates:
        reasons.append("no_discovered_candidates_to_compile")

    return RegulatoryCompilePacket(
        regulatory_change_id=str(change.id),
        compiler_version=COMPILER_VERSION,
        discovery_audit_id=str(discovery_audit.id) if discovery_audit else None,
        source_snapshot_id=str(snapshot.id) if snapshot else None,
        source_snapshot_content_hash=snapshot.content_hash if snapshot else None,
        candidates=tuple(compiled_candidates),
        candidate_only=True,
        verified_rule_write_allowed=False,
        pathway_write_allowed=False,
        publication_allowed=False,
        canonical_write_allowed=False,
        reasons=tuple(sorted(set(reasons))),
    )


def compile_discovered_regulatory_candidates(
    session: Session,
    *,
    limit: int = 100,
    actor: str = "regulatory-compiler-agent",
) -> dict[str, Any]:
    """Compile typed candidate structures without writing canonical regulatory truth."""

    changes = session.exec(
        select(RegulatoryChange)
        .where(RegulatoryChange.status == "pending_review")
        .where(RegulatoryChange.change_type == "new_program")
        .order_by(RegulatoryChange.detected_at)
        .limit(min(max(limit, 1), 500))
    ).all()

    packets: list[RegulatoryCompilePacket] = []
    audit_writes = 0
    for change in changes:
        discovery_audit, discovery_payload = _latest_discovery(session, change)
        if not discovery_payload:
            continue
        packet = compile_regulatory_candidates(session, change)
        packets.append(packet)
        payload = packet.payload()

        previous = session.exec(
            select(AuditLog)
            .where(AuditLog.action == COMPILER_ACTION)
            .where(AuditLog.entity_type == "regulatory_change")
            .where(AuditLog.entity_id == str(change.id))
            .order_by(AuditLog.created_at.desc())
        ).first()
        previous_payload = _load_json(previous.after_state_json if previous else None, {})
        if previous_payload == payload:
            continue

        record_audit(
            session,
            action=COMPILER_ACTION,
            entity_type="regulatory_change",
            entity_id=change.id,
            after_state=payload,
            reason=(
                "Candidate pathway/rule structure compiled from explicit typed evidence only; canonical publication remains forbidden."
            ),
            actor=actor,
            source=COMPILER_VERSION,
        )
        audit_writes += 1

    session.commit()
    return {
        "compiler_version": COMPILER_VERSION,
        "scanned": len(changes),
        "compile_packets": len(packets),
        "typed_candidates": sum(
            1
            for packet in packets
            for candidate in packet.candidates
            if candidate.compile_status == "typed_candidate"
        ),
        "pathway_only_candidates": sum(
            1
            for packet in packets
            for candidate in packet.candidates
            if candidate.compile_status == "pathway_only"
        ),
        "quarantined_candidates": sum(
            1
            for packet in packets
            for candidate in packet.candidates
            if candidate.compile_status == "quarantined"
        ),
        "verified_rule_writes": 0,
        "pathway_writes": 0,
        "publication_writes": 0,
        "canonical_writes": 0,
        "audit_writes": audit_writes,
        "packets": [packet.payload() for packet in packets],
    }
