from __future__ import annotations

import difflib
import hashlib
import json
from datetime import timedelta
from typing import Any, Optional
from urllib.parse import urlparse
from uuid import UUID

from pydantic import BaseModel, Field as PydanticField
from sqlmodel import Session, select

from app.core.config import settings
from app.models.domain import (
    HumanReview,
    Jurisdiction,
    JurisdictionSourceCertification,
    OfficialSource,
    RegulatoryAuthority,
    RegulatoryClassificationProposal,
    RegulatoryChange,
    ReviewStatus,
    SourceMonitor,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from app.schemas import (
    JurisdictionCreate,
    RegulatoryAuthorityCreate,
    RegulatoryClassificationProposalGenerateRequest,
    RegulatoryClassificationProposalReviewRequest,
    RegulatoryChangePublishRequest,
    RegulatoryChangeReviewRequest,
    RegulatorySourceOnboardingRequest,
    RegulatorySourceAuthorityReassignmentRequest,
    SourceMonitorCreate,
    SourceSnapshotCaptureRequest,
    VerifiedRuleRetireRequest,
)
from app.services.audit_log import record_audit
from app.services.llm_client import LLMProviderFactory, is_llm_enabled
from app.services.official_sources import normalize_country, normalize_domain


def normalize_jurisdiction_code(value: str) -> str:
    return value.strip().upper().replace(" ", "-").replace("_", "-")


def jurisdiction_code_for_country(value: str) -> str:
    country = normalize_country(value)
    known_codes = {
        "germany": "DE",
        "austria": "AT",
        "canada": "CA",
        "united kingdom": "GB",
        "australia": "AU",
    }
    return known_codes.get(country, normalize_jurisdiction_code(country))


def _apply_jurisdiction(session: Session, payload: JurisdictionCreate) -> Jurisdiction:
    code = normalize_jurisdiction_code(payload.code)
    jurisdiction = session.exec(select(Jurisdiction).where(Jurisdiction.code == code)).first()
    if jurisdiction is None:
        jurisdiction = Jurisdiction(code=code, name=payload.name.strip())
    jurisdiction.name = payload.name.strip()
    jurisdiction.jurisdiction_type = payload.jurisdiction_type
    jurisdiction.parent_code = normalize_jurisdiction_code(payload.parent_code) if payload.parent_code else None
    jurisdiction.region = payload.region.strip() if payload.region else None
    jurisdiction.metadata_json = json.dumps(payload.metadata, default=str, sort_keys=True) if payload.metadata else None
    jurisdiction.active = True
    jurisdiction.updated_at = now_utc()
    session.add(jurisdiction)
    return jurisdiction


def create_or_update_jurisdiction(session: Session, payload: JurisdictionCreate) -> Jurisdiction:
    jurisdiction = _apply_jurisdiction(session, payload)
    record_audit(
        session,
        action="jurisdiction_upserted",
        entity_type="jurisdiction",
        entity_id=jurisdiction.id,
        after_state=jurisdiction,
        source="regulatory_intelligence_v7",
    )
    session.commit()
    session.refresh(jurisdiction)
    return jurisdiction


def _validate_https_url(value: str, *, label: str) -> tuple[str, str]:
    normalized = value.strip()
    parsed = urlparse(normalized)
    if parsed.scheme.lower() != "https":
        raise ValueError(f"{label} must use HTTPS")
    if parsed.username or parsed.password:
        raise ValueError(f"{label} must not contain credentials")
    hostname = (parsed.hostname or "").lower().rstrip(".")
    if not hostname:
        raise ValueError(f"{label} must include a hostname")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError(f"{label} contains an invalid port") from exc
    if port not in (None, 443):
        raise ValueError(f"{label} must use the standard HTTPS port")
    return normalized, hostname


def _normalize_allowed_domains(values: list[str], *, source_hostname: str) -> list[str]:
    normalized: set[str] = set()
    for value in values or [source_hostname]:
        domain = value.strip().lower().rstrip(".")
        if not domain or any(marker in domain for marker in ("://", "/", "\\", "@", "*", ":")):
            raise ValueError("Allowed domains must be hostnames without schemes, paths, ports, or wildcards")
        try:
            domain = domain.encode("idna").decode("ascii")
        except UnicodeError as exc:
            raise ValueError(f"Invalid allowed domain: {value}") from exc
        normalized.add(domain)
    if not any(
        source_hostname == domain or source_hostname.endswith(f".{domain}")
        for domain in normalized
    ):
        raise ValueError("The official source domain must be included in allowed_domains")
    return sorted(normalized)


def onboard_regulatory_source(
    session: Session,
    payload: RegulatorySourceOnboardingRequest,
    *,
    actor: str,
    commit: bool = True,
) -> tuple[Jurisdiction, RegulatoryAuthority, OfficialSource, SourceMonitor]:
    source_url, source_hostname = _validate_https_url(payload.source_url, label="Official source URL")
    authority_website_url = None
    if payload.authority_website_url:
        authority_website_url, _ = _validate_https_url(
            payload.authority_website_url,
            label="Authority website URL",
        )
    allowed_domains = _normalize_allowed_domains(payload.allowed_domains, source_hostname=source_hostname)
    source_domain = normalize_domain(payload.source_domain)
    authority_domains = sorted({
        normalize_domain(domain)
        for domain in payload.authority_domains
        if domain.strip()
    })
    if source_domain not in authority_domains:
        raise ValueError("The source domain must be included in authority_domains")

    jurisdiction_payload = JurisdictionCreate(
        code=payload.jurisdiction_code,
        name=payload.jurisdiction_name,
        jurisdiction_type=payload.jurisdiction_type,
        parent_code=payload.parent_code,
        region=payload.region,
    )
    jurisdiction = _apply_jurisdiction(session, jurisdiction_payload)
    session.flush()

    authority = next((
        item for item in session.exec(
            select(RegulatoryAuthority).where(RegulatoryAuthority.jurisdiction_id == jurisdiction.id)
        ).all()
        if item.name.casefold() == payload.authority_name.strip().casefold()
    ), None)
    authority_created = authority is None
    if authority is None:
        authority = RegulatoryAuthority(
            jurisdiction_id=jurisdiction.id,
            name=payload.authority_name.strip(),
        )
    authority.name = payload.authority_name.strip()
    authority.authority_type = payload.authority_type.strip()
    authority.website_url = authority_website_url
    authority.domains_json = json.dumps(authority_domains, sort_keys=True)
    authority.active = True
    authority.updated_at = now_utc()
    session.add(authority)
    session.flush()

    source = session.exec(select(OfficialSource).where(OfficialSource.url == source_url)).first()
    source_created = source is None
    if source is None:
        source = OfficialSource(country=normalize_country(payload.jurisdiction_name), name=payload.source_name, url=source_url)
    if source.regulatory_authority_id not in (None, authority.id):
        raise ValueError("The official source is already assigned to another regulatory authority")
    if source.jurisdiction_id not in (None, jurisdiction.id):
        raise ValueError("The official source is already assigned to another jurisdiction")
    source.jurisdiction_id = jurisdiction.id
    source.regulatory_authority_id = authority.id
    source.country = normalize_country(payload.jurisdiction_name)
    source.domain = source_domain
    source.name = payload.source_name.strip()
    source.url = source_url
    source.source_type = payload.source_type
    source.authority = authority.name
    source.active = True
    source.updated_at = now_utc()
    session.add(source)
    session.flush()

    monitor = session.exec(
        select(SourceMonitor).where(SourceMonitor.official_source_id == source.id)
    ).first()
    monitor_created = monitor is None
    if monitor is None:
        monitor = SourceMonitor(official_source_id=source.id)
    monitor.schedule_minutes = payload.schedule_minutes
    monitor.fetch_method = payload.fetch_method
    monitor.allowed_domains_json = json.dumps(allowed_domains, sort_keys=True)
    monitor.max_redirects = payload.max_redirects
    monitor.parser_profile = payload.parser_profile
    monitor.parser_config_json = json.dumps(payload.parser_config, default=str, sort_keys=True) if payload.parser_config else None
    monitor.status = "active"
    monitor.next_check_at = now_utc()
    monitor.updated_at = now_utc()
    session.add(monitor)
    session.flush()

    record_audit(
        session,
        action="regulatory_source_onboarded",
        entity_type="official_source",
        entity_id=source.id,
        after_state={
            "jurisdiction_id": jurisdiction.id,
            "authority_id": authority.id,
            "official_source_id": source.id,
            "monitor_id": monitor.id,
            "allowed_domains": allowed_domains,
            "parser_profile": monitor.parser_profile,
            "authority_created": authority_created,
            "source_created": source_created,
            "monitor_created": monitor_created,
        },
        actor=actor,
        source="regulatory_intelligence_v7_2",
    )
    if commit:
        session.commit()
        for row in (jurisdiction, authority, source, monitor):
            session.refresh(row)
    return jurisdiction, authority, source, monitor


def ensure_jurisdiction_for_source(session: Session, source: OfficialSource) -> Jurisdiction:
    country = normalize_country(source.country)
    code = jurisdiction_code_for_country(country)
    jurisdiction = session.exec(select(Jurisdiction).where(Jurisdiction.code == code)).first()
    if jurisdiction:
        if source.jurisdiction_id != jurisdiction.id:
            source.jurisdiction_id = jurisdiction.id
            session.add(source)
        return jurisdiction
    jurisdiction = Jurisdiction(code=code, name=country.title(), jurisdiction_type="country")
    session.add(jurisdiction)
    session.flush()
    source.jurisdiction_id = jurisdiction.id
    session.add(source)
    return jurisdiction


def create_regulatory_authority(session: Session, payload: RegulatoryAuthorityCreate) -> RegulatoryAuthority:
    if session.get(Jurisdiction, payload.jurisdiction_id) is None:
        raise ValueError("Jurisdiction not found")
    sources: list[OfficialSource] = []
    for source_id in payload.official_source_ids:
        source = session.get(OfficialSource, source_id)
        if source is None:
            raise ValueError(f"Official source not found: {source_id}")
        sources.append(source)
    authority = RegulatoryAuthority(
        jurisdiction_id=payload.jurisdiction_id,
        name=payload.name.strip(),
        authority_type=payload.authority_type.strip(),
        website_url=payload.website_url,
        domains_json=json.dumps(sorted(set(payload.domains)), sort_keys=True),
    )
    session.add(authority)
    session.flush()
    for source in sources:
        source.jurisdiction_id = payload.jurisdiction_id
        source.regulatory_authority_id = authority.id
        session.add(source)
    record_audit(
        session,
        action="regulatory_authority_created",
        entity_type="regulatory_authority",
        entity_id=authority.id,
        after_state=authority,
        source="regulatory_intelligence_v7",
    )
    session.commit()
    session.refresh(authority)
    return authority


def reassign_official_source_authority(
    session: Session,
    source_id: UUID,
    payload: RegulatorySourceAuthorityReassignmentRequest,
    *,
    actor: str,
) -> tuple[OfficialSource, RegulatoryAuthority, bool]:
    """Reassign one official source to the already-approved primary authority.

    This is a controlled remediation operation. It changes only the source's
    authority relationship; monitor, retrieval, snapshot, and source identity
    remain unchanged.
    """
    reason = payload.reason.strip()
    if len(reason) < 10:
        raise ValueError("Reassignment reason must contain at least 10 non-whitespace characters")

    source = session.get(OfficialSource, source_id)
    if source is None or not source.active:
        raise ValueError("Active official source not found")
    if source.jurisdiction_id is None:
        raise ValueError("Official source is not attached to a jurisdiction")

    target = session.get(RegulatoryAuthority, payload.target_regulatory_authority_id)
    if target is None or not target.active:
        raise ValueError("Active target regulatory authority not found")
    if target.jurisdiction_id != source.jurisdiction_id:
        raise ValueError("Target regulatory authority does not belong to the official source jurisdiction")

    approved_primary = session.exec(
        select(JurisdictionSourceCertification)
        .where(JurisdictionSourceCertification.jurisdiction_id == source.jurisdiction_id)
        .where(JurisdictionSourceCertification.certification_scope == "primary_immigration")
        .where(JurisdictionSourceCertification.status == "approved")
        .order_by(JurisdictionSourceCertification.certification_version.desc())
    ).first()
    if approved_primary is None:
        raise ValueError("Source authority reassignment requires an approved primary immigration certification")
    if approved_primary.regulatory_authority_id != target.id:
        raise ValueError("Target authority is not the independently approved primary immigration authority")

    if source.regulatory_authority_id == target.id:
        return source, target, False

    blocking_certification = session.exec(
        select(JurisdictionSourceCertification).where(
            JurisdictionSourceCertification.official_source_id == source.id,
            JurisdictionSourceCertification.status.in_(["pending_review", "approved"]),
        )
    ).first()
    if blocking_certification is not None:
        raise ValueError(
            "Official source with a pending or approved source certification cannot be reassigned"
        )

    before = {
        "official_source_id": source.id,
        "jurisdiction_id": source.jurisdiction_id,
        "regulatory_authority_id": source.regulatory_authority_id,
    }
    source.regulatory_authority_id = target.id
    session.add(source)
    session.flush()

    record_audit(
        session,
        action="regulatory_source_authority_reassigned",
        entity_type="official_source",
        entity_id=source.id,
        before_state=before,
        after_state={
            "official_source_id": source.id,
            "jurisdiction_id": source.jurisdiction_id,
            "regulatory_authority_id": target.id,
        },
        reason=reason,
        actor=(actor or "api-operator"),
        source="regulatory_intelligence_v13_10_2_2",
    )
    session.commit()
    session.refresh(source)
    return source, target, True


def create_or_update_source_monitor(session: Session, payload: SourceMonitorCreate) -> SourceMonitor:
    source = session.get(OfficialSource, payload.official_source_id)
    if source is None:
        raise ValueError("Official source not found")
    monitor = session.exec(
        select(SourceMonitor).where(SourceMonitor.official_source_id == payload.official_source_id)
    ).first()
    if monitor is None:
        monitor = SourceMonitor(official_source_id=payload.official_source_id)
    monitor.schedule_minutes = payload.schedule_minutes
    monitor.fetch_method = payload.fetch_method
    source_domain = (urlparse(source.url).hostname or "").lower()
    allowed_domains = sorted({
        domain.strip().lower().rstrip(".")
        for domain in (payload.allowed_domains or [source_domain])
        if domain.strip()
    })
    if source_domain and not any(
        source_domain == domain or source_domain.endswith(f".{domain}")
        for domain in allowed_domains
    ):
        raise ValueError("The official source domain must be included in allowed_domains")
    monitor.allowed_domains_json = json.dumps(allowed_domains, sort_keys=True)
    monitor.max_redirects = payload.max_redirects
    monitor.parser_profile = payload.parser_profile
    monitor.parser_config_json = json.dumps(payload.parser_config, default=str, sort_keys=True) if payload.parser_config else None
    monitor.status = "active"
    monitor.next_check_at = now_utc()
    monitor.updated_at = now_utc()
    session.add(monitor)
    session.commit()
    session.refresh(monitor)
    return monitor


def _normalized_content(content: str) -> str:
    return "\n".join(line.rstrip() for line in content.replace("\r\n", "\n").split("\n")).strip()


CLASSIFICATION_TYPES = (
    "new_program",
    "rule_change",
    "program_removed",
    "processing_time_change",
    "salary_threshold_change",
    "investment_threshold_change",
    "age_limit_change",
    "occupation_list_change",
    "quota_change",
    "policy_change",
)
MATERIALITY_LEVELS = ("informational", "material", "critical")
CLASSIFICATION_PROMPT_VERSION = "regulatory-classifier-v1"
CLASSIFICATION_KEYWORDS = (
    ("processing_time_change", ("processing time", "processing days", "processing weeks")),
    ("salary_threshold_change", ("salary threshold", "minimum salary", "salary requirement")),
    ("investment_threshold_change", ("investment threshold", "minimum investment", "investor requirement")),
    ("age_limit_change", ("age limit", "maximum age", "under the age")),
    ("occupation_list_change", ("occupation list", "shortage occupation", "eligible occupations")),
    ("quota_change", ("quota", "annual cap", "application cap")),
    ("program_removed", ("program closed", "program removed", "no longer available")),
    ("new_program", ("new visa", "new permit", "new program", "introduced")),
)


class _ModelClassificationCandidate(BaseModel):
    change_type: str
    materiality: str
    summary: str = PydanticField(min_length=5, max_length=2000)
    rationale: str = PydanticField(min_length=5, max_length=5000)
    confidence: float = PydanticField(ge=0.0, le=1.0)
    evidence_line_numbers: list[int] = PydanticField(default_factory=list, max_length=25)


def _classify_change(old: str, new: str, requested: Optional[str]) -> str:
    if requested:
        return requested
    combined = f"{old}\n{new}".lower()
    for change_type, keywords in CLASSIFICATION_KEYWORDS:
        if any(keyword in combined for keyword in keywords):
            return change_type
    return "rule_change"


def _diff_payload(old: str, new: str) -> dict[str, Any]:
    lines = list(difflib.unified_diff(
        old.splitlines(),
        new.splitlines(),
        fromfile="previous",
        tofile="current",
        lineterm="",
        n=3,
    ))
    return {"unified_diff": lines[:500], "truncated": len(lines) > 500}


def _evidence_from_diff(
    diff_lines: list[str],
    line_numbers: Optional[list[int]] = None,
    keywords: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    requested = set(line_numbers or [])
    evidence: list[dict[str, Any]] = []
    for number, line in enumerate(diff_lines, start=1):
        if line.startswith(("+++", "---", "@@")):
            continue
        changed = line.startswith(("+", "-"))
        keyword_match = any(keyword in line.lower() for keyword in keywords)
        if (requested and number not in requested) or (not requested and keywords and not keyword_match):
            continue
        if not requested and not keywords and not changed:
            continue
        evidence.append({
            "line_number": number,
            "direction": "added" if line.startswith("+") else "removed" if line.startswith("-") else "context",
            "text": line[:1000],
        })
        if len(evidence) >= 25:
            break
    if evidence or requested:
        return evidence
    return _evidence_from_diff(diff_lines, keywords=())[:8]


def _deterministic_candidate(
    change: RegulatoryChange,
    previous: Optional[SourceSnapshot],
    current: SourceSnapshot,
) -> dict[str, Any]:
    old = previous.content_text if previous and previous.content_text else ""
    new = current.content_text or ""
    diff_lines = _diff_payload(old, new)["unified_diff"]
    change_type = _classify_change(old, new, change.change_type if change.change_type in CLASSIFICATION_TYPES else None)
    keywords = next((values for name, values in CLASSIFICATION_KEYWORDS if name == change_type), ())
    evidence = _evidence_from_diff(diff_lines, keywords=keywords)
    if change.change_type in CLASSIFICATION_TYPES:
        confidence = 0.82
        rationale = "The deterministic classifier retained the typed change detected by the controlled source pipeline."
    elif keywords and evidence:
        confidence = 0.7
        rationale = f"Deterministic keyword evidence matched the {change_type.replace('_', ' ')} category."
    else:
        confidence = 0.4
        rationale = "No specialised keyword rule matched; the deterministic safe fallback is a general rule change."
    return {
        "change_type": change_type,
        "materiality": change.materiality if change.materiality in MATERIALITY_LEVELS else "material",
        "summary": change.summary,
        "rationale": rationale,
        "confidence": confidence,
        "evidence": evidence,
        "method": "deterministic",
        "provider": None,
        "model": None,
        "model_metadata": None,
        "fallback_reason": None,
    }


def _strip_json_fences(value: str) -> str:
    content = value.strip()
    if content.startswith("```"):
        lines = content.splitlines()[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        content = "\n".join(lines).strip()
    return content


def _classification_candidate(
    change: RegulatoryChange,
    previous: Optional[SourceSnapshot],
    current: SourceSnapshot,
    *,
    use_model: bool,
) -> dict[str, Any]:
    fallback = _deterministic_candidate(change, previous, current)
    if not use_model:
        return fallback
    if not settings.regulatory_model_classification_enabled:
        fallback["fallback_reason"] = "Model-assisted regulatory classification is disabled by configuration."
        return fallback
    if not is_llm_enabled():
        fallback["fallback_reason"] = "No supported model provider is configured."
        return fallback

    old = previous.content_text if previous and previous.content_text else ""
    new = current.content_text or ""
    diff_lines = _diff_payload(old, new)["unified_diff"]
    numbered_diff: list[str] = []
    prompt_characters = 0
    for number, line in enumerate(diff_lines, start=1):
        bounded_line = f"{number}: {line[:1000]}"
        if prompt_characters + len(bounded_line) > 50_000:
            break
        numbered_diff.append(bounded_line)
        prompt_characters += len(bounded_line)
    prompt = {
        "domain": change.domain,
        "current_classification": change.change_type,
        "current_materiality": change.materiality,
        "allowed_change_types": list(CLASSIFICATION_TYPES),
        "allowed_materiality": list(MATERIALITY_LEVELS),
        "numbered_unified_diff": numbered_diff,
        "instructions": (
            "Return one JSON object only. Classify only what the supplied official-source diff supports. "
            "Evidence line numbers must refer to the numbered diff. This is an advisory proposal requiring human review."
        ),
        "required_fields": [
            "change_type",
            "materiality",
            "summary",
            "rationale",
            "confidence",
            "evidence_line_numbers",
        ],
    }
    try:
        provider = LLMProviderFactory.get_provider()
        response = provider.complete(
            system_prompt=(
                "You are a controlled regulatory-change classifier. Never invent a rule, date, threshold, "
                "programme, or authority. Use only supplied diff evidence and express uncertainty in confidence."
            ),
            messages=[{"role": "user", "content": json.dumps(prompt, sort_keys=True)}],
            response_format={"type": "json_object"},
        )
        candidate = _ModelClassificationCandidate.model_validate_json(_strip_json_fences(response.content))
        if candidate.change_type not in CLASSIFICATION_TYPES:
            raise ValueError("Model returned an unsupported change type")
        if candidate.materiality not in MATERIALITY_LEVELS:
            raise ValueError("Model returned an unsupported materiality")
        evidence = _evidence_from_diff(diff_lines, candidate.evidence_line_numbers)
        if not evidence:
            raise ValueError("Model proposal did not cite valid diff evidence")
        return {
            "change_type": candidate.change_type,
            "materiality": candidate.materiality,
            "summary": candidate.summary,
            "rationale": candidate.rationale,
            "confidence": min(candidate.confidence, 0.95),
            "evidence": evidence,
            "method": "model_assisted",
            "provider": response.provider,
            "model": response.model,
            "model_metadata": {
                "finish_reason": response.finish_reason,
                "prompt_tokens": response.prompt_tokens,
                "completion_tokens": response.completion_tokens,
                "total_tokens": response.total_tokens,
                "estimated_cost_usd": response.estimated_cost_usd,
            },
            "fallback_reason": None,
        }
    except Exception as exc:
        fallback["fallback_reason"] = (
            "Model proposal failed validation or execution; deterministic fallback used "
            f"({type(exc).__name__})."
        )
        return fallback


def _create_classification_proposal(
    session: Session,
    change: RegulatoryChange,
    *,
    use_model: bool,
    actor: str,
    supersede_pending: bool = True,
) -> RegulatoryClassificationProposal:
    previous = session.get(SourceSnapshot, change.previous_snapshot_id) if change.previous_snapshot_id else None
    current = session.get(SourceSnapshot, change.current_snapshot_id)
    if current is None:
        raise ValueError("Current source snapshot not found")
    candidate = _classification_candidate(change, previous, current, use_model=use_model)
    if supersede_pending:
        pending = session.exec(
            select(RegulatoryClassificationProposal)
            .where(RegulatoryClassificationProposal.regulatory_change_id == change.id)
            .where(RegulatoryClassificationProposal.status == "pending_review")
        ).all()
        for existing in pending:
            existing.status = "superseded"
            existing.updated_at = now_utc()
            session.add(existing)
    proposal = RegulatoryClassificationProposal(
        regulatory_change_id=change.id,
        previous_snapshot_id=change.previous_snapshot_id,
        current_snapshot_id=change.current_snapshot_id,
        proposed_change_type=candidate["change_type"],
        proposed_materiality=candidate["materiality"],
        proposed_summary=candidate["summary"],
        rationale=candidate["rationale"],
        evidence_json=json.dumps(candidate["evidence"], default=str, sort_keys=True),
        confidence=candidate["confidence"],
        method=candidate["method"],
        provider=candidate["provider"],
        model=candidate["model"],
        prompt_version=CLASSIFICATION_PROMPT_VERSION,
        model_metadata_json=(
            json.dumps(candidate["model_metadata"], default=str, sort_keys=True)
            if candidate["model_metadata"] else None
        ),
        fallback_reason=candidate["fallback_reason"],
        status="pending_review",
        created_by=actor,
    )
    session.add(proposal)
    session.flush()
    record_audit(
        session,
        action="regulatory_classification_proposed",
        entity_type="regulatory_classification_proposal",
        entity_id=proposal.id,
        after_state=proposal,
        actor=actor,
        source="regulatory_intelligence_v10_4",
    )
    return proposal


def generate_classification_proposal(
    session: Session,
    change_id: UUID,
    payload: RegulatoryClassificationProposalGenerateRequest,
) -> RegulatoryClassificationProposal:
    change = session.get(RegulatoryChange, change_id)
    if change is None:
        raise ValueError("Regulatory change not found")
    if change.status != "pending_review":
        raise ValueError("Classification proposals can only be generated for pending regulatory changes")
    proposal = _create_classification_proposal(
        session,
        change,
        use_model=payload.use_model,
        actor=payload.actor,
    )
    session.commit()
    session.refresh(proposal)
    return proposal


def review_classification_proposal(
    session: Session,
    proposal_id: UUID,
    payload: RegulatoryClassificationProposalReviewRequest,
) -> RegulatoryClassificationProposal:
    proposal = session.get(RegulatoryClassificationProposal, proposal_id)
    if proposal is None:
        raise ValueError("Regulatory classification proposal not found")
    if proposal.status != "pending_review":
        raise ValueError(f"Classification proposal cannot be reviewed from status '{proposal.status}'")
    change = session.get(RegulatoryChange, proposal.regulatory_change_id)
    if change is None:
        raise ValueError("Regulatory change not found")
    if change.status != "pending_review":
        raise ValueError("The regulatory change is no longer pending review")
    before = {"proposal_status": proposal.status, "change_type": change.change_type, "materiality": change.materiality}
    proposal.status = payload.decision
    proposal.reviewed_by = payload.reviewer
    proposal.reviewed_at = now_utc()
    proposal.review_notes = payload.notes
    proposal.updated_at = now_utc()
    if payload.decision == "accepted":
        change.change_type = proposal.proposed_change_type
        change.materiality = proposal.proposed_materiality
        change.summary = proposal.proposed_summary
        session.add(change)
        other_pending = session.exec(
            select(RegulatoryClassificationProposal)
            .where(RegulatoryClassificationProposal.regulatory_change_id == change.id)
            .where(RegulatoryClassificationProposal.status == "pending_review")
            .where(RegulatoryClassificationProposal.id != proposal.id)
        ).all()
        for other in other_pending:
            other.status = "superseded"
            other.updated_at = now_utc()
            session.add(other)
    session.add(proposal)
    record_audit(
        session,
        action="regulatory_classification_reviewed",
        entity_type="regulatory_classification_proposal",
        entity_id=proposal.id,
        before_state=before,
        after_state={
            "proposal": proposal,
            "change_type": change.change_type,
            "materiality": change.materiality,
        },
        reason=payload.notes,
        actor=payload.reviewer,
        source="regulatory_intelligence_v10_4",
    )
    session.commit()
    session.refresh(proposal)
    return proposal


def _snapshot_metadata(snapshot: Optional[SourceSnapshot]) -> dict[str, Any]:
    if snapshot is None or not snapshot.metadata_json:
        return {}
    try:
        value = json.loads(snapshot.metadata_json)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _program_lifecycle_events(
    previous_metadata: dict[str, Any],
    current_metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    previous_catalog = previous_metadata.get("program_catalog")
    current_catalog = current_metadata.get("program_catalog")
    if not isinstance(previous_catalog, list) or not isinstance(current_catalog, list):
        return []
    previous = {
        str(item.get("program_id")): item
        for item in previous_catalog
        if isinstance(item, dict) and item.get("program_id")
    }
    current = {
        str(item.get("program_id")): item
        for item in current_catalog
        if isinstance(item, dict) and item.get("program_id")
    }
    events: list[dict[str, Any]] = []
    for program_id in sorted(current.keys() - previous.keys()):
        program = current[program_id]
        if program.get("active", True):
            events.append({
                "change_type": "new_program",
                "program_id": program_id,
                "program_name": program.get("name") or program_id,
                "title": f"New mobility program detected: {program.get('name') or program_id}",
                "summary": "A new program appeared in the authority's structured official catalogue.",
                "before": None,
                "after": program,
            })
    for program_id in sorted(previous.keys() & current.keys()):
        before = previous[program_id]
        after = current[program_id]
        if before == after:
            continue
        retired = bool(before.get("active", True)) and not bool(after.get("active", True))
        changed_fields = sorted({
            key for key in set(before) | set(after)
            if before.get(key) != after.get(key)
        })
        events.append({
            "change_type": "program_removed" if retired else "rule_change",
            "program_id": program_id,
            "program_name": after.get("name") or before.get("name") or program_id,
            "title": (
                f"Mobility program retired: {after.get('name') or before.get('name') or program_id}"
                if retired else
                f"Mobility program changed: {after.get('name') or before.get('name') or program_id}"
            ),
            "summary": (
                f"The authority catalogue changed the program status from {before.get('status', 'unknown')} "
                f"to {after.get('status', 'unknown')}."
                if retired else
                f"The authority catalogue changed these program fields: {', '.join(changed_fields)}."
            ),
            "before": before,
            "after": after,
        })
    if current_metadata.get("missing_means_retired"):
        for program_id in sorted(previous.keys() - current.keys()):
            program = previous[program_id]
            events.append({
                "change_type": "program_removed",
                "program_id": program_id,
                "program_name": program.get("name") or program_id,
                "title": f"Mobility program removed from catalogue: {program.get('name') or program_id}",
                "summary": "A previously listed program no longer appears in the complete authority catalogue.",
                "before": program,
                "after": None,
            })
    return events


def capture_source_snapshot(
    session: Session,
    source_id: UUID,
    payload: SourceSnapshotCaptureRequest,
) -> tuple[SourceSnapshot, Optional[RegulatoryChange], bool]:
    source = session.get(OfficialSource, source_id)
    if source is None:
        raise ValueError("Official source not found")

    content = _normalized_content(payload.content_text)
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    previous = session.exec(
        select(SourceSnapshot)
        .where(SourceSnapshot.official_source_id == source_id)
        .where(SourceSnapshot.content_hash.is_not(None))
        .order_by(SourceSnapshot.captured_at.desc())
    ).first()
    unchanged = previous is not None and previous.content_hash == digest
    snapshot = SourceSnapshot(
        official_source_id=source.id,
        previous_snapshot_id=previous.id if previous else None,
        url=source.url,
        content_hash=digest,
        content_text=content,
        http_status=payload.http_status,
        retrieval_method=payload.retrieval_method,
        parser_version=payload.parser_version,
        status="unchanged" if unchanged else ("baseline" if previous is None else "changed"),
        metadata_json=json.dumps(payload.metadata, default=str, sort_keys=True) if payload.metadata else None,
    )
    session.add(snapshot)
    session.flush()

    monitor = session.exec(select(SourceMonitor).where(SourceMonitor.official_source_id == source.id)).first()
    if monitor:
        monitor.last_checked_at = now_utc()
        monitor.next_check_at = monitor.last_checked_at + timedelta(minutes=monitor.schedule_minutes)
        monitor.last_http_status = payload.http_status
        monitor.last_error = None
        monitor.updated_at = now_utc()
        session.add(monitor)

    change: Optional[RegulatoryChange] = None
    if previous is not None and not unchanged:
        jurisdiction = ensure_jurisdiction_for_source(session, source)
        lifecycle_events = _program_lifecycle_events(_snapshot_metadata(previous), payload.metadata)
        if lifecycle_events:
            change_specs = lifecycle_events
        else:
            change_type = _classify_change(previous.content_text or "", content, payload.change_type)
            change_specs = [{
                "change_type": change_type,
                "title": payload.title or f"{source.name}: {change_type.replace('_', ' ')}",
                "summary": payload.summary or "Official-source content changed and requires human validation.",
            }]
        base_diff = _diff_payload(previous.content_text or "", content)
        for spec in change_specs:
            diff_payload = dict(base_diff)
            if spec.get("program_id"):
                diff_payload["program_change"] = spec
            detected_change = RegulatoryChange(
                jurisdiction_id=jurisdiction.id,
                official_source_id=source.id,
                previous_snapshot_id=previous.id,
                current_snapshot_id=snapshot.id,
                domain=source.domain,
                change_type=str(spec["change_type"]),
                title=str(spec["title"]),
                summary=str(spec["summary"]),
                diff_json=json.dumps(diff_payload, default=str, sort_keys=True),
                materiality=payload.materiality,
                status="pending_review",
                effective_at=payload.effective_at,
            )
            session.add(detected_change)
            session.flush()
            if change is None:
                change = detected_change
            session.add(HumanReview(
                regulatory_change_id=detected_change.id,
                review_type="regulatory_change",
                status=ReviewStatus.pending,
                priority="high" if payload.materiality == "critical" else "medium",
                reason=f"Validate {detected_change.change_type} detected at {source.url}",
            ))
            _create_classification_proposal(
                session,
                detected_change,
                use_model=False,
                actor=payload.actor,
                supersede_pending=False,
            )
            record_audit(
                session,
                action="regulatory_change_detected",
                entity_type="regulatory_change",
                entity_id=detected_change.id,
                after_state=detected_change,
                actor=payload.actor,
                source="regulatory_intelligence_v7_3",
            )

    record_audit(
        session,
        action="source_snapshot_captured",
        entity_type="source_snapshot",
        entity_id=snapshot.id,
        after_state={"source_id": source.id, "content_hash": digest, "status": snapshot.status},
        actor=payload.actor,
        source="regulatory_intelligence_v7",
    )
    session.commit()
    session.refresh(snapshot)
    if change:
        session.refresh(change)
    return snapshot, change, unchanged


def review_regulatory_change(
    session: Session,
    change_id: UUID,
    payload: RegulatoryChangeReviewRequest,
) -> RegulatoryChange:
    change = session.get(RegulatoryChange, change_id)
    if change is None:
        raise ValueError("Regulatory change not found")
    if change.status not in {"pending_review", "approved", "rejected"}:
        raise ValueError(f"Regulatory change cannot be reviewed from status '{change.status}'")
    if payload.decision == "approved":
        proposals = session.exec(
            select(RegulatoryClassificationProposal)
            .where(RegulatoryClassificationProposal.regulatory_change_id == change.id)
        ).all()
        if proposals and any(proposal.status == "pending_review" for proposal in proposals):
            raise ValueError("Resolve the pending classification proposal before approving this change")
        if proposals and not any(proposal.status == "accepted" for proposal in proposals):
            raise ValueError("An accepted classification proposal is required before approving this change")
    before = {"status": change.status, "reviewed_by": change.reviewed_by}
    change.status = payload.decision
    change.reviewed_at = now_utc()
    change.reviewed_by = payload.reviewer
    change.review_notes = payload.notes
    session.add(change)
    reviews = session.exec(
        select(HumanReview).where(HumanReview.regulatory_change_id == change.id)
    ).all()
    for review in reviews:
        review.status = ReviewStatus.resolved if payload.decision == "approved" else ReviewStatus.rejected
        review.reviewer_notes = payload.notes
        review.updated_at = now_utc()
        session.add(review)
    record_audit(
        session,
        action="regulatory_change_reviewed",
        entity_type="regulatory_change",
        entity_id=change.id,
        before_state=before,
        after_state=change,
        reason=payload.notes,
        actor=payload.reviewer,
        source="regulatory_intelligence_v7",
    )
    session.commit()
    session.refresh(change)
    return change


def publish_regulatory_change(
    session: Session,
    change_id: UUID,
    payload: RegulatoryChangePublishRequest,
) -> VerifiedRule:
    change = session.get(RegulatoryChange, change_id)
    if change is None:
        raise ValueError("Regulatory change not found")
    existing = session.exec(
        select(VerifiedRule).where(VerifiedRule.regulatory_change_id == change.id)
    ).first()
    if existing:
        from app.services.regulatory_knowledge_graph import project_verified_rule

        project_verified_rule(session, existing, actor=existing.approved_by or payload.reviewer)
        session.commit()
        session.refresh(existing)
        return existing
    if change.status != "approved":
        raise ValueError("Only an approved regulatory change can be published")
    jurisdiction = session.get(Jurisdiction, change.jurisdiction_id)
    if jurisdiction is None:
        raise ValueError("Jurisdiction not found")
    published_at = now_utc()
    superseded_rule: Optional[VerifiedRule] = None
    if payload.supersedes_rule_id:
        superseded_rule = session.get(VerifiedRule, payload.supersedes_rule_id)
        if superseded_rule is None:
            raise ValueError("Superseded verified rule not found")
        if not superseded_rule.active:
            raise ValueError("Superseded verified rule is already inactive")
        if superseded_rule.jurisdiction_id != change.jurisdiction_id or superseded_rule.domain != change.domain:
            raise ValueError("A verified rule can only supersede a rule in the same jurisdiction and domain")
        before_rule = {"active": superseded_rule.active, "effective_to": superseded_rule.effective_to}
        superseded_rule.active = False
        superseded_rule.effective_to = payload.effective_from or change.effective_at or published_at
        superseded_rule.retired_at = published_at
        superseded_rule.retired_by = payload.reviewer
        superseded_rule.retirement_reason = f"Superseded by regulatory change {change.id}"
        superseded_rule.updated_at = published_at
        session.add(superseded_rule)
        session.flush()
        from app.services.regulatory_knowledge_graph import deactivate_rule_projection

        deactivate_rule_projection(session, superseded_rule, actor=payload.reviewer)
        record_audit(
            session,
            action="verified_rule_superseded",
            entity_type="verified_rule",
            entity_id=superseded_rule.id,
            before_state=before_rule,
            after_state=superseded_rule,
            reason=superseded_rule.retirement_reason,
            actor=payload.reviewer,
            source="regulatory_intelligence_v7",
        )
    rule = VerifiedRule(
        country=normalize_country(jurisdiction.name),
        domain=change.domain,
        rule_key=payload.rule_key,
        statement=payload.statement,
        official_source_id=change.official_source_id,
        jurisdiction_id=change.jurisdiction_id,
        regulatory_change_id=change.id,
        source_snapshot_id=change.current_snapshot_id,
        supersedes_rule_id=superseded_rule.id if superseded_rule else None,
        confidence=payload.confidence,
        active=True,
        effective_from=payload.effective_from or change.effective_at,
        effective_to=payload.effective_to,
        approved_by=payload.reviewer,
        published_at=published_at,
    )
    change.status = "published"
    change.published_at = published_at
    session.add(rule)
    session.add(change)
    session.flush()
    from app.services.regulatory_knowledge_graph import project_verified_rule

    project_verified_rule(session, rule, actor=payload.reviewer)
    record_audit(
        session,
        action="verified_rule_published",
        entity_type="verified_rule",
        entity_id=rule.id,
        after_state=rule,
        reason=change.review_notes,
        actor=payload.reviewer,
        source="regulatory_intelligence_v7",
    )
    session.commit()
    session.refresh(rule)
    return rule


def retire_verified_rule(
    session: Session,
    rule_id: UUID,
    payload: VerifiedRuleRetireRequest,
) -> VerifiedRule:
    rule = session.get(VerifiedRule, rule_id)
    if rule is None:
        raise ValueError("Verified rule not found")
    if not rule.active:
        raise ValueError("Verified rule is already inactive")
    before = {"active": rule.active, "effective_to": rule.effective_to}
    retired_at = now_utc()
    rule.active = False
    rule.effective_to = payload.effective_to or retired_at
    rule.retired_at = retired_at
    rule.retired_by = payload.reviewer
    rule.retirement_reason = payload.reason
    rule.updated_at = retired_at
    session.add(rule)
    session.flush()
    from app.services.regulatory_knowledge_graph import deactivate_rule_projection

    deactivate_rule_projection(session, rule, actor=payload.reviewer)
    record_audit(
        session,
        action="verified_rule_retired",
        entity_type="verified_rule",
        entity_id=rule.id,
        before_state=before,
        after_state=rule,
        reason=payload.reason,
        actor=payload.reviewer,
        source="regulatory_intelligence_v7",
    )
    session.commit()
    session.refresh(rule)
    return rule
