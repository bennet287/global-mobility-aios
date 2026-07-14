from __future__ import annotations

import difflib
import hashlib
import json
from datetime import timedelta
from typing import Any, Optional
from urllib.parse import urlparse
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    HumanReview,
    Jurisdiction,
    OfficialSource,
    RegulatoryAuthority,
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
    RegulatoryChangePublishRequest,
    RegulatoryChangeReviewRequest,
    RegulatorySourceOnboardingRequest,
    SourceMonitorCreate,
    SourceSnapshotCaptureRequest,
    VerifiedRuleRetireRequest,
)
from app.services.audit_log import record_audit
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


def _classify_change(old: str, new: str, requested: Optional[str]) -> str:
    if requested:
        return requested
    combined = f"{old}\n{new}".lower()
    classifiers = (
        ("processing_time_change", ("processing time", "processing days", "processing weeks")),
        ("salary_threshold_change", ("salary threshold", "minimum salary", "salary requirement")),
        ("investment_threshold_change", ("investment threshold", "minimum investment", "investor requirement")),
        ("age_limit_change", ("age limit", "maximum age", "under the age")),
        ("occupation_list_change", ("occupation list", "shortage occupation", "eligible occupations")),
        ("quota_change", ("quota", "annual cap", "application cap")),
        ("program_removed", ("program closed", "program removed", "no longer available")),
        ("new_program", ("new visa", "new permit", "new program", "introduced")),
    )
    for change_type, keywords in classifiers:
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
