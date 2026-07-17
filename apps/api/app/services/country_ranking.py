from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    CountryRankingAssessment,
    Lead,
    MobilityPathwayVersion,
    Profile,
    now_utc,
)
from app.schemas import (
    CountryLongTermDependencyRead,
    CountryRankingCreate,
    CountryRankingItemRead,
    CountryRankingRead,
    CountryRankingScopeRead,
    CountryRankingUncertaintyRead,
    PathwayComparisonItem,
)
from app.services.audit_log import record_audit
from app.services.jurisdiction_registry import jurisdiction_registry_coverage
from app.services.mobility_profiles import current_mobility_profile
from app.services.pathway_catalogue import _comparison_item, _load, match_pathways_for_lead


def _dump(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True)


def _normal(value: str | None) -> str:
    return (value or "").strip().lower()


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _registry_scope(session: Session, *, catalogue_countries: int, pathway_versions: int) -> tuple[CountryRankingScopeRead, dict[str, Any]]:
    coverage = jurisdiction_registry_coverage(session)
    gate = coverage.get("release_gate", {})
    summary = coverage.get("summary", {})
    release = coverage.get("release") or {}
    ready = bool(gate.get("global_coverage_claim_ready"))
    scope = CountryRankingScopeRead(
        ranking_scope="complete_global_catalogue" if ready else "reviewed_published_catalogue_only",
        global_coverage_claim_ready=ready,
        complete_global_ranking_claim_allowed=ready,
        registry_release_version=release.get("version"),
        registry_entries=int(summary.get("registry_entries") or 0),
        coverage_required=int(summary.get("coverage_required") or 0),
        coverage_ready=int(summary.get("coverage_ready") or 0),
        published_catalogue_countries=catalogue_countries,
        published_pathway_versions=pathway_versions,
        message=(
            "The global coverage release gate passed; this assessment may describe its scope as the complete reviewed global catalogue."
            if ready
            else "This assessment ranks only countries represented by current human-published pathway versions. It is not a complete global ranking because the jurisdiction coverage release gate has not passed."
        ),
    )
    return scope, coverage


def _coverage_rows(coverage: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[UUID, dict[str, Any]]]:
    by_name: dict[str, dict[str, Any]] = {}
    by_jurisdiction: dict[UUID, dict[str, Any]] = {}
    for row in coverage.get("entries", []):
        name = _normal(row.get("name"))
        if name:
            by_name[name] = row
        jurisdiction_id = row.get("jurisdiction_id")
        if jurisdiction_id:
            by_jurisdiction[UUID(str(jurisdiction_id))] = row
    return by_name, by_jurisdiction


def _long_term_raw(version: MobilityPathwayVersion, stage: str) -> dict[str, Any] | None:
    metadata = _load(version.metadata_json, {})
    roots = [
        metadata.get("long_term_mobility"),
        metadata.get("long_term_residence"),
        metadata.get("settlement"),
    ]
    aliases = {
        "permanent_residence": ("permanent_residence", "pr", "settlement"),
        "citizenship": ("citizenship", "naturalisation", "naturalization"),
    }
    for root in roots:
        if not isinstance(root, dict):
            continue
        for key in aliases[stage]:
            value = root.get(key)
            if isinstance(value, dict):
                return value
    for key in aliases[stage]:
        value = metadata.get(key)
        if isinstance(value, dict):
            return value
    return None


def _dependency_from_versions(
    versions: list[MobilityPathwayVersion],
    stage: str,
) -> CountryLongTermDependencyRead:
    for version in versions:
        raw = _long_term_raw(version, stage)
        if raw is None:
            continue
        raw_status = _normal(str(raw.get("status") or "recorded"))
        status = "not_applicable" if raw_status in {"not_applicable", "none"} else "recorded"
        dependencies = [str(value).strip() for value in raw.get("dependencies", []) if str(value).strip()]
        summary = str(raw.get("summary") or raw.get("dependency_summary") or "Reviewed long-term dependency metadata is recorded.").strip()
        rule_ids = [UUID(str(value)) for value in _load(version.verified_rule_ids_json, [])]
        return CountryLongTermDependencyRead(
            stage=stage,
            status=status,
            summary=summary,
            minimum_years=_number(raw.get("minimum_years")),
            dependencies=dependencies,
            pathway_version_id=version.id,
            verified_rule_ids=rule_ids,
            human_reviewed_source=bool(version.approved_by and version.published_at),
        )
    label = "Permanent-residence" if stage == "permanent_residence" else "Citizenship"
    return CountryLongTermDependencyRead(
        stage=stage,
        status="not_recorded",
        summary=f"{label} dependencies are not recorded in the reviewed pathway catalogue; no eligibility inference is made.",
        human_reviewed_source=False,
    )


def _uncertainty(
    primary: PathwayComparisonItem,
    dependencies: list[CountryLongTermDependencyRead],
    *,
    global_ready: bool,
    coverage_ready: bool,
) -> CountryRankingUncertaintyRead:
    score = 0.0
    factors: list[str] = []
    if not global_ready:
        score += 0.25
        factors.append("The global jurisdiction coverage release gate has not passed.")
    if not coverage_ready:
        score += 0.1
        factors.append("This country's complete authority, source, freshness, rule, and immigration-relationship coverage gate is not ready.")
    if primary.risk.score:
        contribution = min(0.25, primary.risk.score * 0.25)
        score += contribution
        factors.append(f"The leading pathway has a {primary.risk.level} reviewed risk level.")
    if primary.missing_evidence:
        score += min(0.15, len(primary.missing_evidence) * 0.03)
        factors.append(f"{len(primary.missing_evidence)} profile or document evidence gap(s) remain.")
    missing_long_term = [item.stage for item in dependencies if item.status == "not_recorded"]
    if missing_long_term:
        score += min(0.2, len(missing_long_term) * 0.1)
        factors.append("Reviewed long-term dependency data is incomplete for: " + ", ".join(item.replace("_", " ") for item in missing_long_term) + ".")
    if primary.cost.one_time_total is None:
        score += 0.05
        factors.append("Reviewed upfront payable costs are incomplete.")
    timing = primary.pathway.current_version.processing_time if primary.pathway.current_version else {}
    if timing.get("minimum_weeks") is None and timing.get("maximum_weeks") is None:
        score += 0.05
        factors.append("No reviewed processing-time range is recorded.")
    score = round(min(score, 1.0), 2)
    level = "high" if score >= 0.6 else "medium" if score >= 0.3 else "low"
    if not factors:
        factors.append("No material uncertainty factors were detected in the recorded catalogue fields.")
    return CountryRankingUncertaintyRead(
        level=level,
        score=score,
        factors=factors,
        global_coverage_boundary=not global_ready,
    )


def _assessment_read(row: CountryRankingAssessment) -> CountryRankingRead:
    scope = _load(row.scope_json, {})
    countries = _load(row.ranking_json, [])
    return CountryRankingRead(
        assessment_id=row.id,
        lead_id=row.lead_id,
        profile_id=row.profile_id,
        profile_version=row.profile_version,
        status=row.status,
        consent_status="granted",
        scope=scope,
        countries=countries,
        explicit_user_acceptance=row.explicit_user_acceptance,
        user_attestation=row.user_attestation,
        notes=row.notes,
        summary=row.summary,
        human_review_required=row.human_review_required,
        generated_by=row.generated_by,
        generated_at=row.created_at,
    )


def generate_country_ranking(
    session: Session,
    lead_id: UUID,
    payload: CountryRankingCreate,
    *,
    actor: str,
) -> CountryRankingRead:
    lead = session.get(Lead, lead_id)
    if lead is None:
        raise ValueError("Lead not found")
    if payload.explicit_user_acceptance is not True:
        raise ValueError("Explicit user acceptance must be affirmed before generating a country ranking")
    profile = current_mobility_profile(session, lead_id)
    consent = profile.consent_status if profile else "not_recorded"
    if profile is None:
        raise ValueError("A current Universal Mobility Profile is required for country ranking")
    if consent != "granted":
        record_audit(
            session,
            action="country_ranking_restricted",
            entity_type="lead",
            entity_id=lead_id,
            reason=f"Current profile consent is {consent}",
            actor=actor,
            source="country_ranking_v10_13",
        )
        session.commit()
        raise ValueError("Current profile consent must be granted for country ranking")

    match_result = match_pathways_for_lead(
        session,
        lead_id,
        limit=1000,
        profile_override=profile,
        country_scope="global",
    )
    grouped: dict[str, list[tuple[PathwayComparisonItem, MobilityPathwayVersion]]] = defaultdict(list)
    version_ids: list[UUID] = []
    for match in match_result.get("matches", []):
        item = _comparison_item(session, match)
        version_id = item.pathway.current_version.id if item.pathway.current_version else None
        version = session.get(MobilityPathwayVersion, version_id) if version_id else None
        if version is None:
            continue
        grouped[item.pathway.country].append((item, version))
        if version.id not in version_ids:
            version_ids.append(version.id)

    scope, coverage = _registry_scope(
        session,
        catalogue_countries=len(grouped),
        pathway_versions=len(version_ids),
    )
    by_name, by_jurisdiction = _coverage_rows(coverage)
    ranked: list[CountryRankingItemRead] = []
    for country, pairs in grouped.items():
        pairs.sort(key=lambda pair: (pair[0].match_score, pair[0].confidence), reverse=True)
        primary, primary_version = pairs[0]
        top_pairs = pairs[:3]
        versions = [version for _, version in top_pairs]
        dependencies = [
            _dependency_from_versions(versions, "permanent_residence"),
            _dependency_from_versions(versions, "citizenship"),
        ]
        coverage_row = by_jurisdiction.get(primary.pathway.jurisdiction_id) if primary.pathway.jurisdiction_id else None
        if coverage_row is None:
            coverage_row = by_name.get(_normal(country))
        coverage_ready = bool(coverage_row and coverage_row.get("coverage_ready"))
        uncertainty = _uncertainty(
            primary,
            dependencies,
            global_ready=scope.global_coverage_claim_ready,
            coverage_ready=coverage_ready,
        )
        ranking_score = round(
            min(1.0, primary.match_score * 0.72 + primary.confidence * 0.18 + (1 - primary.risk.score) * 0.10),
            3,
        )
        tradeoffs = list(primary.tradeoffs)
        tradeoffs.append(f"{len(pairs)} current human-published pathway version(s) are available for this country.")
        if not coverage_ready:
            tradeoffs.append("Complete country-level coverage certification is not yet ready; absence of other routes or requirements must not be inferred.")
        for dependency in dependencies:
            if dependency.status == "not_recorded":
                tradeoffs.append(dependency.summary)
        explanation = (
            f"{country.title()} ranks from the leading published pathway's {round(primary.match_score * 100)}% profile fit, "
            f"{round(primary.confidence * 100)}% deterministic confidence, and {primary.risk.level} reviewed risk level. "
            "The result is an internal evidence summary, not a destination recommendation or eligibility guarantee."
        )
        ranked.append(CountryRankingItemRead(
            rank=0,
            country=country,
            ranking_score=ranking_score,
            profile_match_score=primary.match_score,
            confidence=primary.confidence,
            reviewed_coverage_ready=coverage_ready,
            pathway_count=len(pairs),
            primary_pathway=primary,
            alternative_pathways=[item for item, _ in top_pairs[1:]],
            tradeoffs=list(dict.fromkeys(tradeoffs)),
            long_term_dependencies=dependencies,
            uncertainty=uncertainty,
            explanation=explanation,
        ))

    ranked.sort(key=lambda item: (item.ranking_score, item.profile_match_score, item.confidence, item.country), reverse=True)
    ranked = ranked[: payload.limit_countries]
    ranked = [item.model_copy(update={"rank": index}) for index, item in enumerate(ranked, start=1)]
    if not ranked:
        status = "insufficient_catalogue"
        summary = "No human-published pathway versions are available to produce a reviewed country ranking."
    elif scope.global_coverage_claim_ready:
        status = "ready_for_review"
        summary = f"Ranked {len(ranked)} countries across the complete reviewed global catalogue; human review remains required."
    else:
        status = "reviewed_catalogue_only"
        summary = (
            f"Ranked {len(ranked)} countries represented by current human-published pathway versions. "
            "This is not a complete global ranking because the Phase 10B coverage release gate remains blocked."
        )

    input_payload = {
        "lead_id": str(lead_id),
        "profile_id": str(profile.id),
        "profile_version": profile.profile_version,
        "catalogue_version_ids": sorted(str(value) for value in version_ids),
        "registry_release_version": scope.registry_release_version,
        "global_coverage_claim_ready": scope.global_coverage_claim_ready,
        "limit_countries": payload.limit_countries,
        "user_attestation": payload.user_attestation.strip(),
        "notes": payload.notes.strip(),
    }
    input_sha256 = hashlib.sha256(_dump(input_payload).encode("utf-8")).hexdigest()
    existing = session.exec(
        select(CountryRankingAssessment).where(CountryRankingAssessment.ranking_key == input_sha256)
    ).first()
    if existing is not None:
        return _assessment_read(existing)

    now = now_utc()
    row = CountryRankingAssessment(
        ranking_key=input_sha256,
        lead_id=lead_id,
        profile_id=profile.id,
        profile_version=profile.profile_version,
        status=status,
        input_sha256=input_sha256,
        catalogue_version_ids_json=_dump([str(value) for value in version_ids]),
        scope_json=_dump(scope.model_dump(mode="json")),
        ranking_json=_dump([item.model_dump(mode="json") for item in ranked]),
        explicit_user_acceptance=True,
        user_attestation=payload.user_attestation.strip(),
        notes=payload.notes.strip(),
        global_coverage_claim_ready=scope.global_coverage_claim_ready,
        human_review_required=True,
        generated_by=actor,
        summary=summary,
        created_at=now,
    )
    session.add(row)
    session.flush()
    record_audit(
        session,
        action="country_ranking_generated",
        entity_type="country_ranking_assessment",
        entity_id=row.id,
        after_state={
            "lead_id": str(lead_id),
            "profile_id": str(profile.id),
            "profile_version": profile.profile_version,
            "country_count": len(ranked),
            "catalogue_version_count": len(version_ids),
            "global_coverage_claim_ready": scope.global_coverage_claim_ready,
            "ranking_scope": scope.ranking_scope,
            "explicit_user_acceptance": True,
        },
        reason=payload.notes,
        actor=actor,
        source="country_ranking_v10_13",
    )
    session.commit()
    session.refresh(row)
    return _assessment_read(row)


def latest_country_ranking(session: Session, lead_id: UUID) -> CountryRankingRead:
    row = session.exec(
        select(CountryRankingAssessment)
        .where(CountryRankingAssessment.lead_id == lead_id)
        .order_by(CountryRankingAssessment.created_at.desc())
    ).first()
    if row is None:
        raise ValueError("No country ranking found for this lead")
    return _assessment_read(row)


def country_ranking_history(session: Session, lead_id: UUID, *, limit: int = 50) -> list[CountryRankingRead]:
    rows = session.exec(
        select(CountryRankingAssessment)
        .where(CountryRankingAssessment.lead_id == lead_id)
        .order_by(CountryRankingAssessment.created_at.desc())
        .limit(max(1, min(limit, 200)))
    ).all()
    return [_assessment_read(row) for row in rows]
