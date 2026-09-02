from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    Jurisdiction,
    OfficialSource,
    RegulatoryAuthority,
    RegulatoryChange,
    RegulatoryClassificationProposal,
    SourceMonitor,
    VerifiedRule,
    now_utc,
)
from app.services.jurisdiction_registry import jurisdiction_registry_coverage


TRACKED_CHANGE_TYPES = (
    "new_program",
    "program_removed",
    "rule_change",
    "processing_time_change",
    "salary_threshold_change",
    "investment_threshold_change",
    "age_limit_change",
    "occupation_list_change",
    "quota_change",
    "policy_change",
)

FRESHNESS_FILTERS = ("all", "fresh", "stale", "never_checked", "inactive", "unmonitored")
COVERAGE_FILTERS = ("all", "ready", "gap", "not_required", "unregistered")
CONFIDENCE_FILTERS = ("all", "high", "medium", "low", "unknown")
MATERIALITY_FILTERS = ("all", "informational", "material", "critical")
REVIEW_STATE_FILTERS = ("all", "pending_review", "approved", "rejected", "published")


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _load(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return fallback


def _monitor_freshness(monitor: SourceMonitor | None, now: datetime) -> str:
    if monitor is None:
        return "unmonitored"
    if monitor.status != "active":
        return "inactive"
    last_checked = _aware(monitor.last_checked_at)
    if last_checked is None:
        return "never_checked"
    freshness_window = timedelta(minutes=max(monitor.schedule_minutes * 2, 1440))
    return "fresh" if last_checked >= now - freshness_window else "stale"


def _confidence_band(value: float | None) -> str:
    if value is None:
        return "unknown"
    if value >= 0.9:
        return "high"
    if value >= 0.7:
        return "medium"
    return "low"


def _coverage_state(entry: dict[str, Any] | None) -> str:
    if entry is None:
        return "unregistered"
    if not entry.get("coverage_required", False):
        return "not_required"
    return "ready" if entry.get("coverage_ready", False) else "gap"


def _change_payload(
    change: RegulatoryChange,
    jurisdictions: dict[Any, Jurisdiction],
    sources: dict[Any, OfficialSource],
    authorities: dict[Any, RegulatoryAuthority],
    monitors: dict[Any, SourceMonitor],
    coverage_entries: dict[Any, dict[str, Any]],
    rule_by_change: dict[Any, VerifiedRule],
    proposal_by_change: dict[Any, RegulatoryClassificationProposal],
    now: datetime,
) -> dict[str, Any]:
    jurisdiction = jurisdictions.get(change.jurisdiction_id)
    source = sources.get(change.official_source_id)
    authority = authorities.get(source.regulatory_authority_id) if source and source.regulatory_authority_id else None
    monitor = monitors.get(change.official_source_id)
    coverage_entry = coverage_entries.get(change.jurisdiction_id)
    rule = rule_by_change.get(change.id)
    proposal = proposal_by_change.get(change.id)
    confidence: float | None = None
    confidence_source = "unknown"
    if rule is not None:
        confidence = rule.confidence
        confidence_source = "verified_rule"
    elif proposal is not None:
        confidence = proposal.confidence
        confidence_source = (
            "accepted_classification_proposal"
            if proposal.status == "accepted"
            else "classification_proposal"
        )
    diff = _load(change.diff_json, {})
    program = diff.get("program_change", {}) if isinstance(diff, dict) else {}
    return {
        "id": change.id,
        "jurisdiction_id": change.jurisdiction_id,
        "jurisdiction_code": jurisdiction.code if jurisdiction else None,
        "country": jurisdiction.name if jurisdiction else (source.country if source else "Unknown"),
        "jurisdiction_type": jurisdiction.jurisdiction_type if jurisdiction else None,
        "region": jurisdiction.region if jurisdiction else None,
        "change_type": change.change_type,
        "title": change.title,
        "summary": change.summary,
        "program_id": program.get("program_id"),
        "program_name": program.get("program_name"),
        "domain": change.domain,
        "materiality": change.materiality,
        "status": change.status,
        "source_id": source.id if source else None,
        "source_name": source.name if source else None,
        "source_url": source.url if source else None,
        "authority_id": authority.id if authority else None,
        "authority_name": authority.name if authority else (source.authority if source else None),
        "freshness": _monitor_freshness(monitor, now),
        "monitor_status": monitor.status if monitor else None,
        "last_checked_at": monitor.last_checked_at if monitor else None,
        "coverage": _coverage_state(coverage_entry),
        "coverage_gaps": coverage_entry.get("missing", []) if coverage_entry else ["registry_entry"],
        "confidence": confidence,
        "confidence_band": _confidence_band(confidence),
        "confidence_source": confidence_source,
        "effective_at": change.effective_at,
        "detected_at": change.detected_at,
        "reviewed_at": change.reviewed_at,
        "reviewed_by": change.reviewed_by,
        "published_at": change.published_at,
    }


def _activity_level(count: int) -> str:
    if count >= 10:
        return "very_high"
    if count >= 5:
        return "high"
    if count >= 2:
        return "medium"
    if count == 1:
        return "low"
    return "none"


def _validate_filter(value: str, allowed: tuple[str, ...], label: str) -> str:
    normalized = value.strip().lower()
    if normalized not in allowed:
        raise ValueError(f"Unsupported {label} filter '{value}'")
    return normalized


def global_intelligence_dashboard(
    session: Session,
    *,
    window_days: int = 90,
    freshness: str = "all",
    coverage: str = "all",
    authority_id: UUID | None = None,
    confidence: str = "all",
    materiality: str = "all",
    review_state: str = "all",
) -> dict[str, Any]:
    freshness = _validate_filter(freshness, FRESHNESS_FILTERS, "freshness")
    coverage = _validate_filter(coverage, COVERAGE_FILTERS, "coverage")
    confidence = _validate_filter(confidence, CONFIDENCE_FILTERS, "confidence")
    materiality = _validate_filter(materiality, MATERIALITY_FILTERS, "materiality")
    review_state = _validate_filter(review_state, REVIEW_STATE_FILTERS, "review state")

    now = now_utc()
    normalized_window = max(1, min(window_days, 730))
    since = now - timedelta(days=normalized_window)
    today = now.date()
    jurisdictions_list = list(session.exec(select(Jurisdiction).where(Jurisdiction.active == True)).all())  # noqa: E712
    sources_list = list(session.exec(select(OfficialSource).where(OfficialSource.active == True)).all())  # noqa: E712
    authorities_list = list(session.exec(select(RegulatoryAuthority).where(RegulatoryAuthority.active == True)).all())  # noqa: E712
    monitors_list = list(session.exec(select(SourceMonitor)).all())
    base_changes = list(session.exec(
        select(RegulatoryChange)
        .where(RegulatoryChange.detected_at >= since.replace(tzinfo=None))
        .order_by(RegulatoryChange.detected_at.desc())
    ).all())
    active_rules = list(session.exec(select(VerifiedRule).where(VerifiedRule.active == True)).all())  # noqa: E712
    all_rules = list(session.exec(select(VerifiedRule).order_by(VerifiedRule.updated_at.desc())).all())
    proposals = list(session.exec(
        select(RegulatoryClassificationProposal)
        .order_by(RegulatoryClassificationProposal.updated_at.desc())
    ).all())

    jurisdictions = {row.id: row for row in jurisdictions_list}
    sources = {row.id: row for row in sources_list}
    authorities = {row.id: row for row in authorities_list}
    monitors = {row.official_source_id: row for row in monitors_list}
    rule_by_change: dict[Any, VerifiedRule] = {}
    for rule in all_rules:
        if rule.regulatory_change_id and rule.regulatory_change_id not in rule_by_change:
            rule_by_change[rule.regulatory_change_id] = rule
    proposal_by_change: dict[Any, RegulatoryClassificationProposal] = {}
    for proposal in proposals:
        existing = proposal_by_change.get(proposal.regulatory_change_id)
        if existing is None or (proposal.status == "accepted" and existing.status != "accepted"):
            proposal_by_change[proposal.regulatory_change_id] = proposal

    registry = jurisdiction_registry_coverage(session)
    coverage_entries = {row["jurisdiction_id"]: row for row in registry.get("entries", [])}
    base_pairs = [
        (
            change,
            _change_payload(
                change,
                jurisdictions,
                sources,
                authorities,
                monitors,
                coverage_entries,
                rule_by_change,
                proposal_by_change,
                now,
            ),
        )
        for change in base_changes
    ]

    def matches(payload: dict[str, Any]) -> bool:
        return all((
            freshness == "all" or payload["freshness"] == freshness,
            coverage == "all" or payload["coverage"] == coverage,
            authority_id is None or payload["authority_id"] == authority_id,
            confidence == "all" or payload["confidence_band"] == confidence,
            materiality == "all" or payload["materiality"] == materiality,
            review_state == "all" or payload["status"] == review_state,
        ))

    filtered_pairs = [(change, payload) for change, payload in base_pairs if matches(payload)]
    changes = [change for change, _payload in filtered_pairs]
    payloads = [payload for _change, payload in filtered_pairs]
    today_changes = [change for change in changes if (_aware(change.detected_at) or now).date() == today]
    reviewed = [change for change in changes if change.status in {"approved", "published"}]
    published = [change for change in changes if change.status == "published"]
    type_counts = Counter(change.change_type for change in changes)
    status_counts = Counter(change.status for change in changes)
    materiality_counts = Counter(change.materiality for change in changes)
    country_activity: dict[Any, list[RegulatoryChange]] = defaultdict(list)
    for change in changes:
        country_activity[change.jurisdiction_id].append(change)
    source_counts = Counter(source.jurisdiction_id for source in sources_list if source.jurisdiction_id)
    rule_counts = Counter(rule.jurisdiction_id for rule in active_rules if rule.jurisdiction_id)

    selected_authority = authorities.get(authority_id) if authority_id else None
    heatmap = []
    for jurisdiction in jurisdictions_list:
        jurisdiction_coverage = _coverage_state(coverage_entries.get(jurisdiction.id))
        if coverage != "all" and jurisdiction_coverage != coverage:
            continue
        if selected_authority and selected_authority.jurisdiction_id != jurisdiction.id:
            continue
        if authority_id and selected_authority is None:
            continue
        rows = country_activity.get(jurisdiction.id, [])
        heatmap.append({
            "jurisdiction_id": jurisdiction.id,
            "code": jurisdiction.code,
            "country": jurisdiction.name,
            "jurisdiction_type": jurisdiction.jurisdiction_type,
            "region": jurisdiction.region,
            "coverage": jurisdiction_coverage,
            "activity_count": len(rows),
            "activity_level": _activity_level(len(rows)),
            "pending_review": sum(row.status == "pending_review" for row in rows),
            "published": sum(row.status == "published" for row in rows),
            "critical": sum(row.materiality == "critical" for row in rows),
            "official_sources": source_counts[jurisdiction.id],
            "active_verified_rules": rule_counts[jurisdiction.id],
            "last_detected_at": max((row.detected_at for row in rows), default=None),
        })
    heatmap.sort(key=lambda row: (-row["activity_count"], row["country"]))

    radar_weights = {
        "new_program": 5,
        "occupation_list_change": 3,
        "processing_time_change": 2,
        "policy_change": 1,
        "quota_change": 1,
        "salary_threshold_change": 1,
        "investment_threshold_change": 1,
    }
    radar_by_country: dict[Any, list[RegulatoryChange]] = defaultdict(list)
    for change in published:
        if change.change_type in radar_weights:
            radar_by_country[change.jurisdiction_id].append(change)
    payload_by_id = {payload["id"]: payload for payload in payloads}
    radar = []
    for jurisdiction_id, rows in radar_by_country.items():
        jurisdiction = jurisdictions.get(jurisdiction_id)
        score = sum(radar_weights.get(row.change_type, 0) for row in rows)
        evidence = [payload_by_id[row.id] for row in rows[:10] if row.id in payload_by_id]
        radar.append({
            "jurisdiction_id": jurisdiction_id,
            "country": jurisdiction.name if jurisdiction else "Unknown",
            "region": jurisdiction.region if jurisdiction else None,
            "activity_score": score,
            "signal_level": _activity_level(score),
            "evidence_count": len(rows),
            "evidence": evidence,
            "classification": "evidence_based_activity_signal",
            "explanation": (
                f"{len(rows)} human-published regulatory event(s) contributed to an activity score of {score}. "
                "This is a reviewed activity summary, not a prediction or destination recommendation."
            ),
        })
    radar.sort(key=lambda row: (-row["activity_score"], row["country"]))

    def items(change_types: set[str], limit: int = 100) -> list[dict[str, Any]]:
        return [payload for payload in payloads if payload["change_type"] in change_types][:limit]

    countries_updated_today = {
        jurisdictions[change.jurisdiction_id].name
        for change in today_changes
        if change.jurisdiction_id in jurisdictions
    }
    country_types = Counter(row.jurisdiction_type for row in jurisdictions_list)
    registry_summary = registry["summary"]
    registry_gate = registry["release_gate"]

    base_payloads = [payload for _change, payload in base_pairs]
    authority_counts = Counter(payload["authority_id"] for payload in base_payloads if payload["authority_id"])
    authority_options = [
        {
            "id": authority.id,
            "name": authority.name,
            "jurisdiction_id": authority.jurisdiction_id,
            "count": authority_counts[authority.id],
        }
        for authority in authorities_list
        if authority_counts[authority.id]
    ]
    authority_options.sort(key=lambda row: row["name"])
    freshness_options = Counter(payload["freshness"] for payload in base_payloads)
    coverage_options = Counter(payload["coverage"] for payload in base_payloads)
    confidence_options = Counter(payload["confidence_band"] for payload in base_payloads)
    base_materiality_options = Counter(payload["materiality"] for payload in base_payloads)
    base_review_options = Counter(payload["status"] for payload in base_payloads)

    return {
        "generated_at": now,
        "window_days": normalized_window,
        "filters": {
            "applied": {
                "freshness": freshness,
                "coverage": coverage,
                "authority_id": authority_id,
                "authority_name": selected_authority.name if selected_authority else None,
                "confidence": confidence,
                "materiality": materiality,
                "review_state": review_state,
            },
            "matched_changes": len(changes),
            "available_changes": len(base_changes),
            "options": {
                "authorities": authority_options,
                "freshness": {value: freshness_options[value] for value in FRESHNESS_FILTERS if value != "all"},
                "coverage": {value: coverage_options[value] for value in COVERAGE_FILTERS if value != "all"},
                "confidence": {value: confidence_options[value] for value in CONFIDENCE_FILTERS if value != "all"},
                "materiality": {value: base_materiality_options[value] for value in MATERIALITY_FILTERS if value != "all"},
                "review_state": {value: base_review_options[value] for value in REVIEW_STATE_FILTERS if value != "all"},
            },
        },
        "scope": {
            "registered_jurisdictions": len(jurisdictions_list),
            "registered_countries": registry_summary.get("countries", country_types["country"]),
            "registered_territories": registry_summary.get("territories", country_types["territory"]),
            "registered_autonomous_jurisdictions": registry_summary.get(
                "autonomous_jurisdictions", country_types["autonomous_jurisdiction"]
            ),
            "official_sources": len(sources_list),
            "active_verified_rules": len(active_rules),
            "global_coverage_claim_ready": registry_gate["global_coverage_claim_ready"],
            "coverage_warning": registry_gate.get(
                "message",
                "Counts cover onboarded jurisdictions only until the canonical global registry release gate is complete.",
            ),
            "registry_version": (registry.get("release") or {}).get("version"),
            "registry_entries": registry_summary.get("registry_entries", 0),
            "coverage_ready": registry_summary.get("coverage_ready", 0),
        },
        "today": {
            "changes_detected": len(today_changes),
            "countries_updated": len(countries_updated_today),
            "country_names": sorted(countries_updated_today),
        },
        "counts": {
            "changes": len(changes),
            "reviewed_changes": len(reviewed),
            "published_changes": len(published),
            "new_programs": type_counts["new_program"],
            "program_removals": type_counts["program_removed"],
            "processing_time_changes": type_counts["processing_time_change"],
            "occupation_list_changes": type_counts["occupation_list_change"],
            "salary_threshold_changes": type_counts["salary_threshold_change"],
            "investment_threshold_changes": type_counts["investment_threshold_change"],
        },
        "change_type_counts": {change_type: type_counts[change_type] for change_type in TRACKED_CHANGE_TYPES},
        "status_counts": dict(status_counts),
        "materiality_counts": dict(materiality_counts),
        "new_programs": items({"new_program", "program_removed"}),
        "immigration_changes": payloads[:200],
        "processing_times": items({"processing_time_change"}),
        "skilled_occupations": items({"occupation_list_change"}),
        "thresholds": items({"salary_threshold_change", "investment_threshold_change"}),
        "country_heatmap": heatmap,
        "opportunity_radar": radar,
        "safety": {
            "reviewed_activity_only_for_radar": True,
            "predictive": False,
            "client_recommendation": False,
            "message": "Dashboard signals summarize sourced regulatory activity and require human interpretation.",
        },
    }
