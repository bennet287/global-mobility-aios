from __future__ import annotations

from copy import deepcopy
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    AuditLog,
    Lead,
    LeadIntent,
    MobilityPathwayVersion,
    MobilityTimeline,
    PathwayComparisonAssessment,
    PathwayRegulatoryImpact,
    VerifiedRule,
)


def _onboard_and_publish_initial_rule(client: TestClient) -> dict:
    onboarded = client.post(
        "/api/v1/regulatory-intelligence/source-onboarding",
        json={
            "jurisdiction_code": "AT",
            "jurisdiction_name": "Austria",
            "jurisdiction_type": "country",
            "region": "Europe",
            "authority_name": "Federal immigration authority impact fixture",
            "authority_website_url": "https://www.bmi.gv.at/",
            "authority_domains": ["work"],
            "source_name": "Skilled residence pathway impact fixture",
            "source_url": "https://www.bmi.gv.at/example-pathway-impact",
            "source_domain": "work",
            "source_type": "government",
            "allowed_domains": ["bmi.gv.at"],
        },
    )
    assert onboarded.status_code == 201, onboarded.text
    source_id = onboarded.json()["official_source"]["id"]
    baseline = client.post(
        f"/api/v1/regulatory-intelligence/sources/{source_id}/snapshots",
        json={"content_text": "The skilled residence salary requirement is EUR 40,000."},
    )
    assert baseline.status_code == 201, baseline.text
    changed = client.post(
        f"/api/v1/regulatory-intelligence/sources/{source_id}/snapshots",
        json={
            "content_text": "The skilled residence salary requirement is EUR 45,000.",
            "materiality": "critical",
        },
    )
    assert changed.status_code == 201, changed.text
    return _review_and_publish_change(
        client,
        changed.json(),
        rule_key="at-skilled-salary-v1",
        statement="The skilled residence salary requirement is EUR 45,000.",
    )


def _review_and_publish_change(
    client: TestClient,
    capture_payload: dict,
    *,
    rule_key: str,
    statement: str,
    supersedes_rule_id: str | None = None,
) -> dict:
    change = capture_payload["change"]
    proposal = capture_payload["classification_proposal"]
    accepted = client.post(
        f"/api/v1/regulatory-intelligence/classification-proposals/{proposal['id']}/review",
        json={
            "decision": "accepted",
            "reviewer": "impact-classification-reviewer",
            "notes": "The immutable before and after evidence supports this classification.",
        },
    )
    assert accepted.status_code == 200, accepted.text
    reviewed = client.post(
        f"/api/v1/regulatory-intelligence/changes/{change['id']}/review",
        json={
            "decision": "approved",
            "reviewer": "impact-change-reviewer",
            "notes": "Reviewed against the official source snapshot.",
        },
    )
    assert reviewed.status_code == 200, reviewed.text
    payload = {
        "rule_key": rule_key,
        "statement": statement,
        "reviewer": "impact-rule-publisher",
        "confidence": 1.0,
    }
    if supersedes_rule_id:
        payload["supersedes_rule_id"] = supersedes_rule_id
    published = client.post(
        f"/api/v1/regulatory-intelligence/changes/{change['id']}/publish",
        json=payload,
    )
    assert published.status_code == 200, published.text
    return published.json()["verified_rule"]


def _create_published_pathway(client: TestClient, rule: dict) -> dict:
    created = client.post(
        "/api/v1/pathways",
        json={
            "pathway_key": "at-skilled-residence-impact",
            "name": "Austria Skilled Residence Impact Pathway",
            "country": "Austria",
            "domain": "work",
            "jurisdiction_id": rule["jurisdiction_id"],
            "description": "Fixture for reviewed regulatory-to-pathway impact links.",
            "official_source_id": rule["official_source_id"],
            "source_snapshot_id": rule["source_snapshot_id"],
            "verified_rule_ids": [rule["id"]],
            "eligibility_criteria": {"minimum_years_experience": 2},
            "required_documents": ["passport"],
            "costs": {"currency": "EUR", "government_fee": 160},
            "processing_time": {"minimum_weeks": 4, "maximum_weeks": 12},
            "benefits": ["Skilled residence route"],
            "risks": ["Salary threshold may change"],
        },
    )
    assert created.status_code == 201, created.text
    published = client.post(
        f"/api/v1/pathways/versions/{created.json()['current_version']['id']}/publish",
        json={"review_notes": "Initial official rule and snapshot reviewed."},
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "pytest-pathway-reviewer"},
    )
    assert published.status_code == 200, published.text
    return published.json()


def _add_historical_client_records(
    db_session: Session,
    *,
    pathway_id: UUID,
    pathway_version_id: UUID,
) -> tuple[PathwayComparisonAssessment, MobilityTimeline]:
    lead = Lead(
        full_name="Immutable Impact Client",
        email="immutable.impact@example.com",
        intent=LeadIntent.overseas_job,
        target_country="Austria",
        source="pytest",
    )
    db_session.add(lead)
    db_session.commit()
    db_session.refresh(lead)
    assessment = PathwayComparisonAssessment(
        lead_id=lead.id,
        primary_pathway_id=pathway_id,
        primary_pathway_version_id=pathway_version_id,
        status="ready_for_review",
        comparison_json='{"immutable": true}',
        summary="Historical assessment pinned to pathway version 1.",
        generated_by="pytest",
    )
    db_session.add(assessment)
    db_session.commit()
    db_session.refresh(assessment)
    timeline = MobilityTimeline(
        lead_id=lead.id,
        comparison_assessment_id=assessment.id,
        primary_pathway_id=pathway_id,
        primary_pathway_version_id=pathway_version_id,
        title="Historical immutable timeline",
        status="active",
        generated_by="pytest",
    )
    db_session.add(timeline)
    db_session.commit()
    db_session.refresh(timeline)
    return assessment, timeline


def test_rule_supersession_creates_reviewable_impact_without_mutating_client_records(
    client: TestClient,
    db_session: Session,
) -> None:
    first_rule = _onboard_and_publish_initial_rule(client)
    pathway = _create_published_pathway(client, first_rule)
    version_one_id = UUID(pathway["current_version"]["id"])
    assessment, timeline = _add_historical_client_records(
        db_session,
        pathway_id=UUID(pathway["id"]),
        pathway_version_id=version_one_id,
    )
    db_session.refresh(assessment)
    db_session.refresh(timeline)
    assessment_before = deepcopy(assessment.model_dump(mode="json"))
    timeline_before = deepcopy(timeline.model_dump(mode="json"))
    version_before = deepcopy(db_session.get(MobilityPathwayVersion, version_one_id).model_dump(mode="json"))

    source_id = first_rule["official_source_id"]
    changed = client.post(
        f"/api/v1/regulatory-intelligence/sources/{source_id}/snapshots",
        json={
            "content_text": "The skilled residence salary requirement is EUR 50,000.",
            "materiality": "critical",
        },
    )
    assert changed.status_code == 201, changed.text
    second_rule = _review_and_publish_change(
        client,
        changed.json(),
        rule_key="at-skilled-salary-v2",
        statement="The skilled residence salary requirement is EUR 50,000.",
        supersedes_rule_id=first_rule["id"],
    )

    queue = client.get("/api/v1/pathways/regulatory-impacts")
    assert queue.status_code == 200, queue.text
    payload = queue.json()
    assert payload["client_assessments_unchanged"] is True
    assert payload["pending_review"] == 1
    assert payload["total_returned"] == 1
    impact = payload["impacts"][0]
    assert impact["impact_type"] == "rule_supersession"
    assert impact["pathway_version_id"] == str(version_one_id)
    assert impact["verified_rule_id"] == second_rule["id"]
    assert impact["superseded_rule_id"] == first_rule["id"]
    assert impact["graph_rule_node_id"] is not None
    assert impact["graph_projection_version"] == "regulatory-graph-v1"
    assert "superseded_rule_reference" in impact["match_basis"]
    assert impact["client_assessment_count_at_detection"] == 1
    assert impact["timeline_count_at_detection"] == 1

    db_session.refresh(assessment)
    db_session.refresh(timeline)
    db_session.refresh(db_session.get(MobilityPathwayVersion, version_one_id))
    assert assessment.model_dump(mode="json") == assessment_before
    assert timeline.model_dump(mode="json") == timeline_before
    assert db_session.get(MobilityPathwayVersion, version_one_id).model_dump(mode="json") == version_before

    review = client.post(
        f"/api/v1/pathways/regulatory-impacts/{impact['id']}/review",
        json={
            "decision": "new_version_required",
            "notes": "The salary criterion must be reviewed in a new immutable pathway version.",
        },
    )
    assert review.status_code == 200, review.text
    assert review.json()["status"] == "new_version_required"
    assert len(db_session.exec(select(MobilityPathwayVersion)).all()) == 1

    version_two = client.post(
        f"/api/v1/pathways/{pathway['id']}/versions",
        json={
            "official_source_id": second_rule["official_source_id"],
            "source_snapshot_id": second_rule["source_snapshot_id"],
            "verified_rule_ids": [second_rule["id"]],
            "eligibility_criteria": {"minimum_years_experience": 2, "minimum_salary_eur": 50000},
            "required_documents": ["passport"],
            "costs": {"currency": "EUR", "government_fee": 160},
            "processing_time": {"minimum_weeks": 4, "maximum_weeks": 12},
            "benefits": ["Skilled residence route"],
            "risks": ["Salary threshold requires evidence"],
        },
    )
    assert version_two.status_code == 201, version_two.text
    published_two = client.post(
        f"/api/v1/pathways/versions/{version_two.json()['id']}/publish",
        json={"review_notes": "Updated salary evidence reviewed against the superseding rule."},
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "pytest-pathway-reviewer"},
    )
    assert published_two.status_code == 200, published_two.text
    resolved = client.post(
        f"/api/v1/pathways/regulatory-impacts/{impact['id']}/review",
        json={
            "decision": "resolved",
            "notes": "Published pathway version 2 incorporates the reviewed superseding rule.",
            "replacement_pathway_version_id": version_two.json()["id"],
        },
    )
    assert resolved.status_code == 200, resolved.text
    assert resolved.json()["status"] == "resolved"
    assert resolved.json()["replacement_pathway_version_id"] == version_two.json()["id"]

    synced = client.post(
        "/api/v1/regulatory-intelligence/knowledge-graph/sync",
        json={"actor": "impact-sync-reviewer"},
    )
    assert synced.status_code == 200, synced.text
    rows = db_session.exec(select(PathwayRegulatoryImpact)).all()
    assert len(rows) == 1
    db_session.refresh(rows[0])
    assert rows[0].status == "resolved"

    actions = {row.action for row in db_session.exec(select(AuditLog)).all()}
    assert "pathway_regulatory_impacts_linked" in actions
    assert "pathway_regulatory_impact_reviewed" in actions


def test_explicit_rule_retirement_creates_retirement_impact(
    client: TestClient,
    db_session: Session,
) -> None:
    rule = _onboard_and_publish_initial_rule(client)
    pathway = _create_published_pathway(client, rule)
    retired = client.post(
        f"/api/v1/regulatory-intelligence/verified-rules/{rule['id']}/retire",
        json={
            "reviewer": "impact-retirement-reviewer",
            "reason": "The authority withdrew this route requirement.",
        },
    )
    assert retired.status_code == 200, retired.text

    queue = client.get(
        "/api/v1/pathways/regulatory-impacts",
        params={"pathway_id": pathway["id"], "impact_type": "rule_retired"},
    )
    assert queue.status_code == 200, queue.text
    assert queue.json()["total_returned"] == 1
    impact = queue.json()["impacts"][0]
    assert impact["rule_active"] is False
    assert impact["impact_type"] == "rule_retired"
    assert "direct_rule_reference" in impact["match_basis"]
