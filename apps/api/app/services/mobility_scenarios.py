from __future__ import annotations

import calendar
import hashlib
import json
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    Lead,
    MobilityPathway,
    MobilityPathwayVersion,
    MobilityScenario,
    MobilityScenarioStage,
    MobilityTimeline,
    PathwayRegulatoryImpact,
    VerifiedRule,
    now_utc,
)
from app.schemas import (
    MobilityScenarioCreate,
    MobilityScenarioImpactRead,
    MobilityScenarioRead,
    MobilityScenarioRecalculationCandidateRead,
    MobilityScenarioRecalculateRequest,
    MobilityScenarioStageCreate,
    MobilityScenarioStageRead,
)
from app.services.audit_log import record_audit
from app.services.jurisdiction_registry import jurisdiction_registry_coverage
from app.services.mobility_profiles import current_mobility_profile
from app.services.pathway_evidence import pathway_version_evidence_snapshot_ids

SCENARIO_WARNING = (
    "All dates are human-confirmed planning estimates, not eligibility guarantees. "
    "Authority decisions, residence accrual, permanent residence, and citizenship eligibility "
    "must be re-verified against effective official rules before action."
)

_STAGE_TITLES = {
    "study": "Study permission",
    "graduate_rights": "Graduate rights",
    "work_permit": "Work permit",
    "skilled_migration": "Skilled migration",
    "settlement": "Settlement route",
    "permanent_residence": "Permanent residence review",
    "citizenship_review": "Citizenship eligibility review",
}


def _dump(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True)


def _load(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return fallback


def _add_months(value: datetime, months: int) -> datetime:
    total = value.year * 12 + value.month - 1 + months
    year, month_index = divmod(total, 12)
    month = month_index + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def _scenario_stages(session: Session, scenario_id: UUID) -> list[MobilityScenarioStage]:
    return list(session.exec(
        select(MobilityScenarioStage)
        .where(MobilityScenarioStage.scenario_id == scenario_id)
        .order_by(MobilityScenarioStage.stage_order)
    ).all())


def scenario_read(session: Session, scenario: MobilityScenario) -> MobilityScenarioRead:
    stages = _scenario_stages(session, scenario.id)
    return MobilityScenarioRead(
        **scenario.model_dump(exclude={
            "scenario_key",
            "input_sha256",
            "countries_json",
            "pathway_version_ids_json",
            "verified_rule_ids_json",
            "regulatory_impact_ids_json",
        }),
        countries=_load(scenario.countries_json, []),
        pathway_version_ids=[UUID(value) for value in _load(scenario.pathway_version_ids_json, [])],
        verified_rule_ids=[UUID(value) for value in _load(scenario.verified_rule_ids_json, [])],
        regulatory_impact_ids=[UUID(value) for value in _load(scenario.regulatory_impact_ids_json, [])],
        stages=[
            MobilityScenarioStageRead(
                **stage.model_dump(exclude={
                    "dependencies_json",
                    "verified_rule_ids_json",
                    "source_snapshot_ids_json",
                    "timing_basis_json",
                    "uncertainty_json",
                }),
                dependencies=_load(stage.dependencies_json, []),
                verified_rule_ids=[UUID(value) for value in _load(stage.verified_rule_ids_json, [])],
                source_snapshot_ids=[UUID(value) for value in _load(stage.source_snapshot_ids_json, [])],
                timing_basis=_load(stage.timing_basis_json, {}),
                uncertainty=_load(stage.uncertainty_json, {}),
            )
            for stage in stages
        ],
    )


def _coverage_ready(session: Session) -> bool:
    coverage = jurisdiction_registry_coverage(session)
    return bool(coverage.get("release_gate", {}).get("global_coverage_claim_ready"))


def _validate_acceptance(explicit_user_acceptance: bool, user_attestation: str, review_notes: str) -> None:
    if not explicit_user_acceptance:
        raise ValueError("Explicit user acceptance is required before a multi-year scenario is stored")
    if len(user_attestation.strip()) < 10:
        raise ValueError("A specific user attestation is required")
    if len(review_notes.strip()) < 3:
        raise ValueError("Human review notes are required")


def _stage_basis(
    session: Session,
    stage: MobilityScenarioStageCreate,
) -> tuple[MobilityPathway, MobilityPathwayVersion, list[VerifiedRule], list[UUID]]:
    version = session.get(MobilityPathwayVersion, stage.pathway_version_id)
    if version is None:
        raise ValueError("Scenario pathway version not found")
    pathway = session.get(MobilityPathway, version.pathway_id)
    if pathway is None:
        raise ValueError("Scenario pathway provenance is incomplete")
    if version.lifecycle_status != "published" or pathway.catalogue_status != "active":
        raise ValueError("Every scenario stage requires a currently human-published pathway version")
    if not version.official_source_id or not version.source_snapshot_id or not version.approved_by or not version.published_at:
        raise ValueError("Every scenario stage requires reviewed official-source and publication provenance")
    rule_ids = [UUID(str(value)) for value in _load(version.verified_rule_ids_json, [])]
    if not rule_ids:
        raise ValueError("Every scenario stage requires at least one human-published verified rule")
    rules: list[VerifiedRule] = []
    snapshots: list[UUID] = pathway_version_evidence_snapshot_ids(session, version)
    if not snapshots:
        raise ValueError("Every scenario stage requires pathway-version source evidence")
    for rule_id in rule_ids:
        rule = session.get(VerifiedRule, rule_id)
        if rule is None or not rule.active or not rule.approved_by or not rule.published_at or not rule.source_snapshot_id:
            raise ValueError("Scenario stages can use only active human-published verified rules with snapshots")
        if rule.country.strip().lower() != pathway.country.strip().lower():
            raise ValueError("Verified-rule country does not match the scenario pathway")
        rules.append(rule)
        snapshots.append(rule.source_snapshot_id)
    return pathway, version, rules, list(dict.fromkeys(snapshots))


def _input_payload(
    *,
    lead_id: UUID,
    profile_id: UUID,
    profile_version: int,
    title: str,
    start_date: datetime,
    baseline_timeline_id: UUID | None,
    stages: list[MobilityScenarioStageCreate],
    regulatory_impact_ids: list[UUID],
    supersedes_scenario_id: UUID | None,
) -> dict[str, Any]:
    return {
        "lead_id": str(lead_id),
        "profile_id": str(profile_id),
        "profile_version": profile_version,
        "title": title.strip(),
        "start_date": start_date.isoformat(),
        "baseline_timeline_id": str(baseline_timeline_id) if baseline_timeline_id else None,
        "supersedes_scenario_id": str(supersedes_scenario_id) if supersedes_scenario_id else None,
        "regulatory_impact_ids": sorted(str(value) for value in regulatory_impact_ids),
        "stages": [
            {
                "stage_type": stage.stage_type,
                "pathway_version_id": str(stage.pathway_version_id),
                "duration_months": stage.duration_months,
                "gap_months_before": stage.gap_months_before,
                "title": stage.title,
            }
            for stage in stages
        ],
    }


def _create_scenario(
    session: Session,
    *,
    payload: MobilityScenarioCreate,
    actor: str,
    scenario_version: int = 1,
    supersedes_scenario_id: UUID | None = None,
    regulatory_impact_ids: list[UUID] | None = None,
) -> MobilityScenarioRead:
    _validate_acceptance(payload.explicit_user_acceptance, payload.user_attestation, payload.review_notes)
    lead = session.get(Lead, payload.lead_id)
    if lead is None:
        raise ValueError("Lead not found")
    profile = current_mobility_profile(session, payload.lead_id)
    if profile is None or profile.consent_status != "granted":
        raise ValueError("Current profile consent must be granted before scenario generation")
    if payload.baseline_timeline_id:
        timeline = session.get(MobilityTimeline, payload.baseline_timeline_id)
        if timeline is None or timeline.lead_id != payload.lead_id:
            raise ValueError("Baseline timeline not found for this lead")
    bases = [_stage_basis(session, stage) for stage in payload.stages]
    impact_ids = regulatory_impact_ids or []
    input_payload = _input_payload(
        lead_id=payload.lead_id,
        profile_id=profile.id,
        profile_version=profile.profile_version,
        title=payload.title,
        start_date=payload.start_date,
        baseline_timeline_id=payload.baseline_timeline_id,
        stages=payload.stages,
        regulatory_impact_ids=impact_ids,
        supersedes_scenario_id=supersedes_scenario_id,
    )
    input_sha256 = hashlib.sha256(_dump(input_payload).encode("utf-8")).hexdigest()
    scenario_key = f"mobility-scenario:{payload.lead_id}:{input_sha256}"
    existing = session.exec(select(MobilityScenario).where(MobilityScenario.scenario_key == scenario_key)).first()
    if existing:
        return scenario_read(session, existing)

    now = now_utc()
    countries = list(dict.fromkeys(pathway.country for pathway, _, _, _ in bases))
    pathway_version_ids = [version.id for _, version, _, _ in bases]
    verified_rule_ids = list(dict.fromkeys(rule.id for _, _, rules, _ in bases for rule in rules))
    scenario = MobilityScenario(
        scenario_key=scenario_key,
        lead_id=payload.lead_id,
        profile_id=profile.id,
        profile_version=profile.profile_version,
        baseline_timeline_id=payload.baseline_timeline_id,
        scenario_version=scenario_version,
        supersedes_scenario_id=supersedes_scenario_id,
        title=payload.title.strip(),
        start_date=payload.start_date,
        input_sha256=input_sha256,
        countries_json=_dump(countries),
        pathway_version_ids_json=_dump([str(value) for value in pathway_version_ids]),
        verified_rule_ids_json=_dump([str(value) for value in verified_rule_ids]),
        regulatory_impact_ids_json=_dump([str(value) for value in impact_ids]),
        explicit_user_acceptance=True,
        user_attestation=payload.user_attestation.strip(),
        review_notes=payload.review_notes.strip(),
        global_coverage_claim_ready=_coverage_ready(session),
        warning=SCENARIO_WARNING,
        reviewed_by=actor,
        reviewed_at=now,
        created_at=now,
    )
    session.add(scenario)
    session.flush()

    cursor = payload.start_date
    previous_key: str | None = None
    for order, (stage, basis) in enumerate(zip(payload.stages, bases, strict=True), start=1):
        pathway, version, rules, source_snapshot_ids = basis
        planned_start = _add_months(cursor, stage.gap_months_before)
        planned_end = _add_months(planned_start, stage.duration_months)
        stage_key = f"{stage.stage_type}_{order}"
        session.add(MobilityScenarioStage(
            scenario_id=scenario.id,
            stage_order=order,
            stage_type=stage.stage_type,
            title=(stage.title or _STAGE_TITLES[stage.stage_type]).strip(),
            country=pathway.country,
            domain=pathway.domain,
            pathway_id=pathway.id,
            pathway_version_id=version.id,
            planned_start=planned_start,
            planned_end=planned_end,
            duration_months=stage.duration_months,
            gap_months_before=stage.gap_months_before,
            dependencies_json=_dump([previous_key] if previous_key else []),
            verified_rule_ids_json=_dump([str(rule.id) for rule in rules]),
            source_snapshot_ids_json=_dump([str(value) for value in source_snapshot_ids]),
            timing_basis_json=_dump({
                "basis": "operator_confirmed_duration",
                "duration_months": stage.duration_months,
                "gap_months_before": stage.gap_months_before,
                "pathway_processing_time": _load(version.processing_time_json, {}),
                "authority_outcome_predicted": False,
            }),
            uncertainty_json=_dump({
                "future_eligibility_guaranteed": False,
                "requires_rule_reverification": True,
                "requires_human_confirmation": True,
                "coverage_scope": "complete_global_catalogue" if scenario.global_coverage_claim_ready else "reviewed_published_catalogue_only",
            }),
            created_at=now,
        ))
        previous_key = stage_key
        cursor = planned_end

    record_audit(
        session,
        action="mobility_scenario_generated" if scenario_version == 1 else "mobility_scenario_recalculated",
        entity_type="mobility_scenario",
        entity_id=scenario.id,
        after_state={
            "lead_id": str(scenario.lead_id),
            "profile_version": scenario.profile_version,
            "scenario_version": scenario.scenario_version,
            "supersedes_scenario_id": str(supersedes_scenario_id) if supersedes_scenario_id else None,
            "countries": countries,
            "pathway_version_ids": [str(value) for value in pathway_version_ids],
            "regulatory_impact_ids": [str(value) for value in impact_ids],
            "stage_count": len(payload.stages),
            "original_scenario_preserved": True,
            "future_eligibility_guaranteed": False,
        },
        reason=payload.review_notes.strip(),
        actor=actor,
        source="multi_year_mobility_scenarios_v10_14",
    )
    session.commit()
    session.refresh(scenario)
    return scenario_read(session, scenario)


def create_scenario(session: Session, payload: MobilityScenarioCreate, *, actor: str) -> MobilityScenarioRead:
    return _create_scenario(session, payload=payload, actor=actor)


def list_scenarios(session: Session, *, lead_id: UUID | None = None, limit: int = 100) -> list[MobilityScenarioRead]:
    statement = select(MobilityScenario).order_by(MobilityScenario.created_at.desc())
    if lead_id:
        statement = statement.where(MobilityScenario.lead_id == lead_id)
    rows = session.exec(statement.limit(max(1, min(limit, 200)))).all()
    return [scenario_read(session, row) for row in rows]


def recalculation_candidate(session: Session, scenario_id: UUID) -> MobilityScenarioRecalculationCandidateRead:
    scenario = session.get(MobilityScenario, scenario_id)
    if scenario is None:
        raise ValueError("Mobility scenario not found")
    stages = _scenario_stages(session, scenario.id)
    version_orders: dict[UUID, list[int]] = {}
    for stage in stages:
        version_orders.setdefault(stage.pathway_version_id, []).append(stage.stage_order)
    impacts = list(session.exec(
        select(PathwayRegulatoryImpact)
        .where(
            PathwayRegulatoryImpact.pathway_version_id.in_(list(version_orders)),
            PathwayRegulatoryImpact.status == "resolved",
            PathwayRegulatoryImpact.replacement_pathway_version_id.is_not(None),
        )
        .order_by(PathwayRegulatoryImpact.event_at)
    ).all()) if version_orders else []
    consumed = set(_load(scenario.regulatory_impact_ids_json, []))
    payload: list[MobilityScenarioImpactRead] = []
    for impact in impacts:
        if str(impact.id) in consumed or impact.replacement_pathway_version_id is None:
            continue
        replacement = session.get(MobilityPathwayVersion, impact.replacement_pathway_version_id)
        if replacement is None or replacement.lifecycle_status != "published":
            continue
        payload.append(MobilityScenarioImpactRead(
            impact_id=impact.id,
            pathway_version_id=impact.pathway_version_id,
            replacement_pathway_version_id=impact.replacement_pathway_version_id,
            impact_type=impact.impact_type,
            materiality=impact.materiality,
            review_notes=impact.review_notes,
            affected_stage_orders=version_orders.get(impact.pathway_version_id, []),
            event_at=impact.event_at,
        ))
    return MobilityScenarioRecalculationCandidateRead(
        scenario_id=scenario.id,
        scenario_version=scenario.scenario_version,
        available=bool(payload),
        impacts=payload,
        message=(
            "Reviewed replacement pathway versions are available. Recalculation requires explicit acceptance and creates a new immutable scenario version."
            if payload
            else "No unconsumed reviewed pathway replacements affect this scenario."
        ),
    )


def recalculate_scenario(
    session: Session,
    scenario_id: UUID,
    payload: MobilityScenarioRecalculateRequest,
    *,
    actor: str,
) -> MobilityScenarioRead:
    _validate_acceptance(payload.explicit_user_acceptance, payload.user_attestation, payload.review_notes)
    scenario = session.get(MobilityScenario, scenario_id)
    if scenario is None:
        raise ValueError("Mobility scenario not found")
    candidate = recalculation_candidate(session, scenario_id)
    available = {row.impact_id: row for row in candidate.impacts}
    requested = list(dict.fromkeys(payload.regulatory_impact_ids))
    if not requested or any(value not in available for value in requested):
        raise ValueError("Recalculation requires only currently available reviewed regulatory impacts")
    selected = [available[value] for value in requested]
    replacements = {row.pathway_version_id: row.replacement_pathway_version_id for row in selected}
    old_stages = _scenario_stages(session, scenario.id)
    new_stages = [
        MobilityScenarioStageCreate(
            stage_type=stage.stage_type,
            pathway_version_id=replacements.get(stage.pathway_version_id, stage.pathway_version_id),
            duration_months=stage.duration_months,
            gap_months_before=stage.gap_months_before,
            title=stage.title,
        )
        for stage in old_stages
    ]
    create_payload = MobilityScenarioCreate(
        lead_id=scenario.lead_id,
        title=scenario.title,
        start_date=scenario.start_date,
        baseline_timeline_id=scenario.baseline_timeline_id,
        stages=new_stages,
        explicit_user_acceptance=True,
        user_attestation=payload.user_attestation,
        review_notes=payload.review_notes,
    )
    return _create_scenario(
        session,
        payload=create_payload,
        actor=actor,
        scenario_version=scenario.scenario_version + 1,
        supersedes_scenario_id=scenario.id,
        regulatory_impact_ids=requested,
    )
