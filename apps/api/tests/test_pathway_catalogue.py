from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    AuditLog,
    DocumentRecord,
    Jurisdiction,
    Lead,
    LeadIntent,
    MobilityPathwayVersion,
    MobilityTimeline,
    OfficialSource,
    PathwayComparisonAssessment,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)


def _evidence(session: Session) -> tuple[Jurisdiction, OfficialSource, SourceSnapshot, VerifiedRule]:
    jurisdiction = Jurisdiction(code="DE", name="Germany", region="Europe")
    session.add(jurisdiction)
    session.commit()
    session.refresh(jurisdiction)
    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        country="germany",
        domain="work",
        name="German Skilled Migration Authority",
        url="https://example.gov.de/skilled-work",
        source_type="government",
        active=True,
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="pathway-snapshot-hash",
        content_text="Official skilled work pathway requirements.",
        status="captured",
        retrieval_method="http",
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    rule = VerifiedRule(
        country="germany",
        domain="work",
        rule_key="de-skilled-work-experience",
        statement="Applicants must meet the published skilled employment requirements.",
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
    return jurisdiction, source, snapshot, rule


def _pathway_payload(
    jurisdiction: Jurisdiction,
    source: OfficialSource,
    snapshot: SourceSnapshot,
    rule: VerifiedRule,
) -> dict:
    return {
        "pathway_key": "de-skilled-worker",
        "name": "Germany Skilled Worker Pathway",
        "country": "Germany",
        "domain": "work",
        "jurisdiction_id": str(jurisdiction.id),
        "description": "Evidence-backed route for qualified skilled workers.",
        "official_source_id": str(source.id),
        "source_snapshot_id": str(snapshot.id),
        "verified_rule_ids": [str(rule.id)],
        "eligibility_criteria": {
            "minimum_years_experience": 2,
            "required_skills": ["nursing"],
            "qualification_keywords": ["bachelor", "degree"],
            "required_languages": ["english"],
            "minimum_funds_eur": 5000,
            "required_evidence": ["passport"],
        },
        "required_documents": ["passport", "degree", "employment evidence"],
        "costs": {"currency": "EUR", "government_fee": 100},
        "processing_time": {"minimum_weeks": 4, "maximum_weeks": 12},
        "benefits": ["Skilled employment", "Family reunification may be available"],
        "risks": ["Qualification recognition may be required"],
    }


def _lead_with_profile(client: TestClient, session: Session) -> tuple[Lead, DocumentRecord, dict]:
    lead = Lead(
        full_name="Pathway Match Lead",
        email="pathway.match@example.com",
        intent=LeadIntent.overseas_job,
        target_country="Germany",
        source="pytest",
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)
    document = DocumentRecord(
        lead_id=lead.id,
        document_type="passport",
        filename="passport.pdf",
        status="verified",
    )
    session.add(document)
    session.commit()
    session.refresh(document)
    profile = {
        "current_country": "India",
        "education": [{"qualification": "Bachelor degree", "field_of_study": "Nursing"}],
        "employment": [{"role": "Registered Nurse", "years": 4, "current": True}],
        "years_experience": 4,
        "skills": ["nursing", "patient care"],
        "languages": [{"language": "English", "level": "C1"}],
        "family_status": "single",
        "family_details_confirmed": True,
        "finances": {"budget_eur": 10000},
        "goals": [{"domain": "work", "target_country": "Germany", "priority": "high"}],
        "constraints": [],
        "constraints_confirmed": True,
        "consent_status": "granted",
        "consent_purposes": ["eligibility", "opportunity_matching"],
        "evidence_document_ids": [str(document.id)],
    }
    response = client.put(f"/api/v1/profiles/leads/{lead.id}/current", json=profile)
    assert response.status_code == 200, response.text
    return lead, document, profile


def test_pathway_requires_governed_evidence_before_publication(
    client: TestClient,
    db_session: Session,
) -> None:
    response = client.post("/api/v1/pathways", json={
        "pathway_key": "draft-without-evidence",
        "name": "Draft Without Evidence",
        "country": "Germany",
        "domain": "work",
    })
    assert response.status_code == 201, response.text
    draft = response.json()
    assert draft["catalogue_status"] == "draft"
    assert draft["current_version"]["lifecycle_status"] == "draft"
    publish = client.post(
        f"/api/v1/pathways/versions/{draft['current_version']['id']}/publish",
        json={"review_notes": "Reviewed by operator"},
    )
    assert publish.status_code == 400
    assert "official source" in publish.json()["detail"].lower()


def test_pathway_version_publication_matching_and_retirement(
    client: TestClient,
    db_session: Session,
) -> None:
    jurisdiction, source, snapshot, rule = _evidence(db_session)
    payload = _pathway_payload(jurisdiction, source, snapshot, rule)
    created = client.post("/api/v1/pathways", json=payload)
    assert created.status_code == 201, created.text
    draft = created.json()
    assert draft["current_version"]["version_number"] == 1

    self_review = client.post(
        f"/api/v1/pathways/versions/{draft['current_version']['id']}/publish",
        json={"review_notes": "The pathway proposer cannot independently publish this draft."},
    )
    assert self_review.status_code == 400
    assert "independent reviewer" in self_review.json()["detail"].lower()

    published = client.post(
        f"/api/v1/pathways/versions/{draft['current_version']['id']}/publish",
        json={"review_notes": "Official snapshot and verified rule reviewed."},
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "pytest-pathway-reviewer"},
    )
    assert published.status_code == 200, published.text
    pathway = published.json()
    assert pathway["catalogue_status"] == "active"
    assert pathway["current_version"]["lifecycle_status"] == "published"
    assert pathway["current_version"]["approved_by"] == "pytest-pathway-reviewer"

    lead, _, profile_payload = _lead_with_profile(client, db_session)
    matching = client.post(f"/api/v1/pathways/match/{lead.id}")
    assert matching.status_code == 200, matching.text
    match_data = matching.json()
    assert match_data["profile_id"] is not None
    assert match_data["profile_version"] == 1
    assert match_data["consent_status"] == "granted"
    assert len(match_data["matches"]) == 1
    assert match_data["matches"][0]["pathway"]["id"] == pathway["id"]
    assert match_data["matches"][0]["match_score"] >= 0.9
    assert match_data["matches"][0]["verified_rule_ids"] == [str(rule.id)]

    eligibility = client.post("/api/v1/eligibility/evaluate", json={"lead_id": str(lead.id)})
    assert eligibility.status_code == 200, eligibility.text
    assessment = eligibility.json()
    assert assessment["pathways"] == ["Germany Skilled Worker Pathway"]
    assert assessment["factors"]["catalogue_pathways_count"] == 1
    evidence = assessment["factors"]["pathway_evidence"][0]
    assert evidence["official_source_id"] == str(source.id)
    assert evidence["source_snapshot_id"] == str(snapshot.id)
    assert evidence["verified_rule_ids"] == [str(rule.id)]

    alternative_payload = _pathway_payload(jurisdiction, source, snapshot, rule)
    alternative_payload["pathway_key"] = "de-skilled-worker-alternative"
    alternative_payload["name"] = "Germany Alternative Skilled Route"
    alternative_payload["eligibility_criteria"] = {
        **alternative_payload["eligibility_criteria"],
        "required_skills": ["software engineering"],
    }
    alternative_payload["costs"] = {"currency": "EUR", "government_fee": 220}
    alternative = client.post("/api/v1/pathways", json=alternative_payload)
    assert alternative.status_code == 201, alternative.text
    alternative_published = client.post(
        f"/api/v1/pathways/versions/{alternative.json()['current_version']['id']}/publish",
        json={"review_notes": "Alternative route evidence reviewed."},
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "pytest-pathway-reviewer"},
    )
    assert alternative_published.status_code == 200, alternative_published.text

    comparison = client.post(f"/api/v1/pathways/compare/{lead.id}")
    assert comparison.status_code == 200, comparison.text
    plan = comparison.json()
    assert plan["assessment_id"] is not None
    assert plan["status"] == "ready_for_review"
    assert plan["human_review_required"] is True
    assert plan["primary"]["pathway"]["id"] == pathway["id"]
    assert plan["primary"]["cost"]["currency"] == "EUR"
    assert plan["primary"]["cost"]["one_time_total"] == 100.0
    assert plan["primary"]["cost"]["minimum_funds"] == 5000.0
    assert plan["primary"]["risk"]["declared_risks"] == ["Qualification recognition may be required"]
    assert len(plan["alternatives"]) == 1
    assert plan["alternatives"][0]["pathway"]["id"] == alternative.json()["id"]
    assert any("software engineering" in gap for gap in plan["alternatives"][0]["missing_evidence"])

    latest_comparison = client.get(f"/api/v1/pathways/comparisons/{lead.id}/latest")
    comparison_history = client.get(f"/api/v1/pathways/comparisons/{lead.id}")
    assert latest_comparison.status_code == 200
    assert latest_comparison.json()["assessment_id"] == plan["assessment_id"]
    assert comparison_history.status_code == 200
    assert len(comparison_history.json()) == 1
    stored = db_session.exec(
        select(PathwayComparisonAssessment).where(PathwayComparisonAssessment.lead_id == lead.id)
    ).all()
    assert len(stored) == 1

    timeline_response = client.post(
        f"/api/v1/mobility-timelines/from-comparison/{plan['assessment_id']}",
        json={},
    )
    assert timeline_response.status_code == 201, timeline_response.text
    timeline = timeline_response.json()
    assert timeline["status"] == "draft"
    assert timeline["profile_version"] == 1
    assert timeline["primary_pathway_version_id"] == draft["current_version"]["id"]
    assert len(timeline["milestones"]) == 11
    assert timeline["milestones"][3]["stage_key"] == "employment_or_sponsorship"
    assert timeline["milestones"][1]["dependencies"] == ["profile_readiness"]
    assert "passport" in timeline["milestones"][1]["required_evidence"]

    idempotent = client.post(
        f"/api/v1/mobility-timelines/from-comparison/{plan['assessment_id']}",
        json={},
    )
    assert idempotent.status_code == 201
    assert idempotent.json()["id"] == timeline["id"]
    assert len(db_session.exec(select(MobilityTimeline)).all()) == 1

    activated = client.post(f"/api/v1/mobility-timelines/{timeline['id']}/activate")
    assert activated.status_code == 200, activated.text
    active_timeline = activated.json()
    assert active_timeline["status"] == "active"
    assert active_timeline["milestones"][0]["status"] == "ready"

    first = active_timeline["milestones"][0]
    second = active_timeline["milestones"][1]
    premature = client.post(
        f"/api/v1/mobility-timelines/{timeline['id']}/milestones/{second['id']}/transition",
        json={"action": "start"},
    )
    assert premature.status_code == 400
    started = client.post(
        f"/api/v1/mobility-timelines/{timeline['id']}/milestones/{first['id']}/transition",
        json={"action": "start"},
    )
    assert started.status_code == 200, started.text
    completed = client.post(
        f"/api/v1/mobility-timelines/{timeline['id']}/milestones/{first['id']}/transition",
        json={"action": "complete"},
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["milestones"][1]["status"] == "ready"

    second_complete = client.post(
        f"/api/v1/mobility-timelines/{timeline['id']}/milestones/{second['id']}/transition",
        json={"action": "complete"},
    )
    assert second_complete.status_code == 200, second_complete.text
    eligibility_review = second_complete.json()["milestones"][2]
    missing_approval = client.post(
        f"/api/v1/mobility-timelines/{timeline['id']}/milestones/{eligibility_review['id']}/transition",
        json={"action": "complete"},
    )
    assert missing_approval.status_code == 400
    approved = client.post(
        f"/api/v1/mobility-timelines/{timeline['id']}/milestones/{eligibility_review['id']}/transition",
        json={"action": "complete", "note": "Eligibility evidence reviewed by the assigned consultant."},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["milestones"][2]["approved_by"] == "pytest-admin"

    version_two_payload = {
        key: value for key, value in payload.items()
        if key not in {"pathway_key", "name", "country", "domain", "jurisdiction_id", "description"}
    }
    version_two_payload["costs"] = {"currency": "EUR", "government_fee": 120}
    version_two = client.post(f"/api/v1/pathways/{pathway['id']}/versions", json=version_two_payload)
    assert version_two.status_code == 201, version_two.text
    assert version_two.json()["version_number"] == 2
    republished = client.post(
        f"/api/v1/pathways/versions/{version_two.json()['id']}/publish",
        json={"review_notes": "Updated fee reviewed against official evidence."},
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "pytest-pathway-reviewer"},
    )
    assert republished.status_code == 200, republished.text
    old_version = db_session.get(MobilityPathwayVersion, UUID(draft["current_version"]["id"]))
    db_session.refresh(old_version)
    assert old_version.lifecycle_status == "superseded"

    detail = client.get(f"/api/v1/pathways/{pathway['id']}")
    assert detail.status_code == 200
    assert [item["version_number"] for item in detail.json()["versions"]] == [2, 1]

    retired = client.post(
        f"/api/v1/pathways/{pathway['id']}/retire",
        json={"reason": "Program closed by the competent authority."},
    )
    assert retired.status_code == 200, retired.text
    assert retired.json()["catalogue_status"] == "retired"
    after_retirement = client.post(f"/api/v1/pathways/match/{lead.id}")
    assert after_retirement.status_code == 200
    remaining_matches = after_retirement.json()["matches"]
    assert len(remaining_matches) == 1
    assert remaining_matches[0]["pathway"]["id"] == alternative.json()["id"]

    withdrawn_profile = {**profile_payload, "consent_status": "withdrawn"}
    withdrawal = client.put(f"/api/v1/profiles/leads/{lead.id}/current", json=withdrawn_profile)
    assert withdrawal.status_code == 200, withdrawal.text
    route_stage = approved.json()["milestones"][3]
    restricted_transition = client.post(
        f"/api/v1/mobility-timelines/{timeline['id']}/milestones/{route_stage['id']}/transition",
        json={"action": "start"},
    )
    assert restricted_transition.status_code == 400
    restricted_timeline = client.get(f"/api/v1/mobility-timelines/{timeline['id']}")
    assert restricted_timeline.status_code == 200
    assert restricted_timeline.json()["status"] == "restricted"

    actions = {
        audit.action for audit in db_session.exec(
            select(AuditLog).where(AuditLog.entity_type.in_([
                "mobility_pathway",
                "mobility_pathway_version",
                "pathway_comparison_assessment",
                "mobility_timeline",
                "mobility_timeline_milestone",
            ]))
        ).all()
    }
    assert {
        "mobility_pathway_created",
        "mobility_pathway_version_created",
        "mobility_pathway_version_published",
        "mobility_pathway_retired",
        "pathway_comparison_generated",
        "mobility_timeline_generated",
        "mobility_timeline_activated",
        "mobility_timeline_milestone_transitioned",
        "mobility_timeline_restricted",
    } <= actions
