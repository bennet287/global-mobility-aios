from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    AuditLog,
    Jurisdiction,
    MobilityPathway,
    MobilityPathwayVersion,
    MobilityScenario,
    MobilityScenarioStage,
    OfficialSource,
    PathwayRegulatoryImpact,
    RegulatoryChange,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from tests.test_pathway_catalogue import _lead_with_profile


def _published_pathway(
    session: Session,
    *,
    code: str,
    country: str,
    domain: str,
    pathway_key: str,
    name: str,
    version_number: int = 1,
    pathway: MobilityPathway | None = None,
) -> tuple[MobilityPathway, MobilityPathwayVersion, VerifiedRule, SourceSnapshot]:
    jurisdiction = session.exec(select(Jurisdiction).where(Jurisdiction.code == code)).first()
    if jurisdiction is None:
        jurisdiction = Jurisdiction(code=code, name=country, region="Europe")
        session.add(jurisdiction)
        session.commit()
        session.refresh(jurisdiction)
    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        country=country.lower(),
        domain=domain,
        name=f"{country} {domain} authority",
        url=f"https://{code.lower()}.example.gov/{pathway_key}/{version_number}",
        source_type="government",
        active=True,
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash=f"{pathway_key}-{version_number}-snapshot",
        content_text=f"Reviewed {name} rules version {version_number}.",
        retrieval_method="http",
        status="captured",
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    rule = VerifiedRule(
        country=country,
        domain=domain,
        rule_key=f"{pathway_key}-rule-v{version_number}",
        statement=f"Reviewed rule for {name} version {version_number}.",
        official_source_id=source.id,
        jurisdiction_id=jurisdiction.id,
        source_snapshot_id=snapshot.id,
        confidence=0.98,
        active=True,
        approved_by="pytest-reviewer",
        published_at=now_utc(),
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)
    if pathway is None:
        pathway = MobilityPathway(
            pathway_key=pathway_key,
            name=name,
            country=country,
            domain=domain,
            jurisdiction_id=jurisdiction.id,
            catalogue_status="active",
            created_by="pytest-admin",
        )
        session.add(pathway)
        session.commit()
        session.refresh(pathway)
    previous = session.exec(
        select(MobilityPathwayVersion)
        .where(MobilityPathwayVersion.pathway_id == pathway.id)
        .order_by(MobilityPathwayVersion.version_number.desc())
    ).first()
    if previous and previous.lifecycle_status == "published":
        previous.lifecycle_status = "superseded"
        session.add(previous)
    version = MobilityPathwayVersion(
        pathway_id=pathway.id,
        version_number=version_number,
        lifecycle_status="published",
        supersedes_version_id=previous.id if previous else None,
        official_source_id=source.id,
        source_snapshot_id=snapshot.id,
        verified_rule_ids_json=f'["{rule.id}"]',
        processing_time_json='{"minimum_weeks": 4, "maximum_weeks": 12}',
        metadata_json='{"long_term_mobility": {}}',
        human_review_required=True,
        approved_by="pytest-admin",
        review_notes="Reviewed official evidence.",
        published_at=now_utc(),
        created_by="pytest-admin",
    )
    session.add(version)
    session.commit()
    session.refresh(version)
    return pathway, version, rule, snapshot


def _scenario_payload(lead_id: UUID, study_version: UUID, work_version: UUID) -> dict:
    return {
        "lead_id": str(lead_id),
        "title": "Austria to Germany reviewed mobility scenario",
        "start_date": "2026-09-01T00:00:00Z",
        "stages": [
            {
                "stage_type": "study",
                "pathway_version_id": str(study_version),
                "duration_months": 24,
                "gap_months_before": 0,
            },
            {
                "stage_type": "graduate_rights",
                "pathway_version_id": str(study_version),
                "duration_months": 12,
                "gap_months_before": 0,
            },
            {
                "stage_type": "work_permit",
                "pathway_version_id": str(work_version),
                "duration_months": 36,
                "gap_months_before": 1,
            },
            {
                "stage_type": "permanent_residence",
                "pathway_version_id": str(work_version),
                "duration_months": 12,
                "gap_months_before": 0,
            },
            {
                "stage_type": "citizenship_review",
                "pathway_version_id": str(work_version),
                "duration_months": 12,
                "gap_months_before": 0,
            },
        ],
        "explicit_user_acceptance": True,
        "user_attestation": "The client accepts this reviewed planning scenario and its uncertainty boundary.",
        "review_notes": "A human operator reviewed every stage, source, rule, duration, and non-guarantee warning.",
    }


def test_multi_country_scenario_is_human_confirmed_immutable_and_idempotent(
    client: TestClient,
    db_session: Session,
) -> None:
    lead, _, _ = _lead_with_profile(client, db_session)
    _, study, _, _ = _published_pathway(
        db_session,
        code="AT",
        country="Austria",
        domain="study",
        pathway_key="at-reviewed-study",
        name="Austria Reviewed Study Route",
    )
    _, work, _, _ = _published_pathway(
        db_session,
        code="DE2",
        country="Germany",
        domain="work",
        pathway_key="de-reviewed-work",
        name="Germany Reviewed Work Route",
    )
    rejected = _scenario_payload(lead.id, study.id, work.id)
    rejected["explicit_user_acceptance"] = False
    assert client.post("/api/v1/mobility-timelines/scenarios", json=rejected).status_code == 400

    payload = _scenario_payload(lead.id, study.id, work.id)
    created = client.post("/api/v1/mobility-timelines/scenarios", json=payload)
    assert created.status_code == 201, created.text
    scenario = created.json()
    assert scenario["scenario_version"] == 1
    assert scenario["countries"] == ["Austria", "Germany"]
    assert scenario["status"] == "human_confirmed"
    assert scenario["original_scenario_preserved"] is True
    assert scenario["human_confirmation_required"] is True
    assert scenario["global_coverage_claim_ready"] is False
    assert "not eligibility guarantees" in scenario["warning"]
    assert len(scenario["stages"]) == 5
    assert scenario["stages"][0]["planned_start"].startswith("2026-09-01")
    assert scenario["stages"][1]["planned_start"].startswith("2028-09-01")
    assert scenario["stages"][2]["planned_start"].startswith("2029-10-01")
    assert scenario["stages"][4]["uncertainty"]["future_eligibility_guaranteed"] is False
    assert scenario["stages"][4]["human_confirmation_required"] is True

    repeated = client.post("/api/v1/mobility-timelines/scenarios", json=payload)
    assert repeated.status_code == 201, repeated.text
    assert repeated.json()["id"] == scenario["id"]
    assert len(db_session.exec(select(MobilityScenario)).all()) == 1
    assert len(db_session.exec(select(MobilityScenarioStage)).all()) == 5


def test_reviewed_rule_change_creates_new_scenario_version_without_mutating_original(
    client: TestClient,
    db_session: Session,
) -> None:
    lead, _, _ = _lead_with_profile(client, db_session)
    study_pathway, study_v1, old_rule, old_snapshot = _published_pathway(
        db_session,
        code="AT",
        country="Austria",
        domain="study",
        pathway_key="at-scenario-study",
        name="Austria Scenario Study Route",
    )
    _, work_v1, _, _ = _published_pathway(
        db_session,
        code="DE2",
        country="Germany",
        domain="work",
        pathway_key="de-scenario-work",
        name="Germany Scenario Work Route",
    )
    created = client.post(
        "/api/v1/mobility-timelines/scenarios",
        json=_scenario_payload(lead.id, study_v1.id, work_v1.id),
    )
    assert created.status_code == 201, created.text
    original = created.json()
    original_row = db_session.get(MobilityScenario, UUID(original["id"]))
    original_snapshot = deepcopy(original_row.model_dump(mode="json"))
    original_stages = [deepcopy(row.model_dump(mode="json")) for row in db_session.exec(
        select(MobilityScenarioStage)
        .where(MobilityScenarioStage.scenario_id == original_row.id)
        .order_by(MobilityScenarioStage.stage_order)
    ).all()]

    _, study_v2, new_rule, new_snapshot = _published_pathway(
        db_session,
        code="AT",
        country="Austria",
        domain="study",
        pathway_key="at-scenario-study",
        name="Austria Scenario Study Route",
        version_number=2,
        pathway=study_pathway,
    )
    change = RegulatoryChange(
        jurisdiction_id=new_rule.jurisdiction_id,
        official_source_id=new_rule.official_source_id,
        previous_snapshot_id=old_snapshot.id,
        current_snapshot_id=new_snapshot.id,
        domain="study",
        change_type="policy_change",
        title="Reviewed study-route replacement",
        summary="A reviewed replacement pathway version is available.",
        materiality="material",
        status="published",
        reviewed_by="pytest-reviewer",
        reviewed_at=now_utc(),
        review_notes="Reviewed official change.",
        published_at=now_utc(),
    )
    db_session.add(change)
    db_session.commit()
    db_session.refresh(change)
    impact = PathwayRegulatoryImpact(
        impact_key=f"scenario:{study_v1.id}:{new_rule.id}",
        pathway_id=study_pathway.id,
        pathway_version_id=study_v1.id,
        verified_rule_id=new_rule.id,
        superseded_rule_id=old_rule.id,
        regulatory_change_id=change.id,
        source_snapshot_id=new_snapshot.id,
        impact_type="rule_supersession",
        status="resolved",
        materiality="material",
        reviewed_by="pytest-reviewer",
        reviewed_at=now_utc(),
        review_notes="Use reviewed pathway version 2 for future planning.",
        replacement_pathway_version_id=study_v2.id,
        event_at=now_utc(),
    )
    db_session.add(impact)
    db_session.commit()
    db_session.refresh(impact)

    candidate = client.get(
        f"/api/v1/mobility-timelines/scenarios/{original['id']}/recalculation-candidate"
    )
    assert candidate.status_code == 200, candidate.text
    assert candidate.json()["available"] is True
    assert candidate.json()["automatic_recalculation_performed"] is False
    assert candidate.json()["impacts"][0]["affected_stage_orders"] == [1, 2]

    recalculated = client.post(
        f"/api/v1/mobility-timelines/scenarios/{original['id']}/recalculate",
        json={
            "regulatory_impact_ids": [str(impact.id)],
            "explicit_user_acceptance": True,
            "user_attestation": "The client accepts a new scenario version using the reviewed replacement.",
            "review_notes": "The replacement was explained and the original scenario must remain unchanged.",
        },
    )
    assert recalculated.status_code == 201, recalculated.text
    version_two = recalculated.json()
    assert version_two["scenario_version"] == 2
    assert version_two["supersedes_scenario_id"] == original["id"]
    assert version_two["regulatory_impact_ids"] == [str(impact.id)]
    assert version_two["stages"][0]["pathway_version_id"] == str(study_v2.id)
    assert version_two["stages"][1]["pathway_version_id"] == str(study_v2.id)
    assert version_two["stages"][2]["pathway_version_id"] == str(work_v1.id)

    db_session.refresh(original_row)
    assert original_row.model_dump(mode="json") == original_snapshot
    after_stages = [row.model_dump(mode="json") for row in db_session.exec(
        select(MobilityScenarioStage)
        .where(MobilityScenarioStage.scenario_id == original_row.id)
        .order_by(MobilityScenarioStage.stage_order)
    ).all()]
    assert after_stages == original_stages
    assert len(db_session.exec(select(MobilityScenario)).all()) == 2
    actions = {row.action for row in db_session.exec(
        select(AuditLog).where(AuditLog.entity_type == "mobility_scenario")
    ).all()}
    assert {"mobility_scenario_generated", "mobility_scenario_recalculated"} <= actions
