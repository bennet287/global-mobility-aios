from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlmodel import Session, select

from app.models.domain import Jurisdiction, OfficialSource, RegulatoryChange, VerifiedRule, now_utc
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


def _change_payload(
    change: RegulatoryChange,
    jurisdictions: dict,
    sources: dict,
) -> dict[str, Any]:
    jurisdiction = jurisdictions.get(change.jurisdiction_id)
    source = sources.get(change.official_source_id)
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
        "source_name": source.name if source else None,
        "source_url": source.url if source else None,
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


def global_intelligence_dashboard(session: Session, *, window_days: int = 90) -> dict[str, Any]:
    now = now_utc()
    since = now - timedelta(days=max(1, min(window_days, 730)))
    today = now.date()
    jurisdictions_list = list(session.exec(select(Jurisdiction).where(Jurisdiction.active == True)).all())  # noqa: E712
    sources_list = list(session.exec(select(OfficialSource).where(OfficialSource.active == True)).all())  # noqa: E712
    changes = list(session.exec(
        select(RegulatoryChange)
        .where(RegulatoryChange.detected_at >= since.replace(tzinfo=None))
        .order_by(RegulatoryChange.detected_at.desc())
    ).all())
    rules = list(session.exec(select(VerifiedRule).where(VerifiedRule.active == True)).all())  # noqa: E712
    jurisdictions = {row.id: row for row in jurisdictions_list}
    sources = {row.id: row for row in sources_list}
    payloads = [_change_payload(change, jurisdictions, sources) for change in changes]
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
    rule_counts = Counter(rule.jurisdiction_id for rule in rules if rule.jurisdiction_id)
    heatmap = []
    for jurisdiction in jurisdictions_list:
        rows = country_activity.get(jurisdiction.id, [])
        heatmap.append({
            "jurisdiction_id": jurisdiction.id,
            "code": jurisdiction.code,
            "country": jurisdiction.name,
            "jurisdiction_type": jurisdiction.jurisdiction_type,
            "region": jurisdiction.region,
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
    radar = []
    for jurisdiction_id, rows in radar_by_country.items():
        jurisdiction = jurisdictions.get(jurisdiction_id)
        score = sum(radar_weights.get(row.change_type, 0) for row in rows)
        evidence = [_change_payload(row, jurisdictions, sources) for row in rows[:10]]
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
    registry = jurisdiction_registry_coverage(session)
    registry_summary = registry["summary"]
    registry_gate = registry["release_gate"]
    return {
        "generated_at": now,
        "window_days": max(1, min(window_days, 730)),
        "scope": {
            "registered_jurisdictions": len(jurisdictions_list),
            "registered_countries": registry_summary.get("countries", country_types["country"]),
            "registered_territories": registry_summary.get("territories", country_types["territory"]),
            "registered_autonomous_jurisdictions": registry_summary.get(
                "autonomous_jurisdictions", country_types["autonomous_jurisdiction"]
            ),
            "official_sources": len(sources_list),
            "active_verified_rules": len(rules),
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
