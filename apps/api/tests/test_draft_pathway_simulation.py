from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models.domain import (
    AuditLog,
    Jurisdiction,
    JurisdictionSourceCertification,
    Lead,
    LeadIntent,
    OfficialSource,
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


def _lead_with_profile(client: TestClient, session: Session) -> Lead:
    lead = Lead(
        full_name="Draft Simulation Lead",
        email="draft.sim@example.com",
        intent=LeadIntent.overseas_job,
        target_country="Germany",
        source="pytest",
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)
    from app.models.domain import DocumentRecord
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
    return lead


def _create_published_pathway(client: TestClient, session: Session) -> tuple[dict, dict]:
    jurisdiction, source, snapshot, rule = _evidence(session)
    payload = _pathway_payload(jurisdiction, source, snapshot, rule)
    response = client.post("/api/v1/pathways", json=payload)
    assert response.status_code == 201, response.text
    created = response.json()
    publish = client.post(
        f"/api/v1/pathways/versions/{created['current_version']['id']}/publish",
        json={"review_notes": "Official evidence independently reviewed."},
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "pytest-pathway-reviewer"},
    )
    assert publish.status_code == 200, publish.text
    return publish.json(), payload


def _create_draft_version(client: TestClient, pathway: dict, payload: dict) -> dict:
    response = client.post(f"/api/v1/pathways/{pathway['id']}/versions", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _create_published_pathway_with_draft(client: TestClient, session: Session) -> tuple[dict, dict]:
    pathway, payload = _create_published_pathway(client, session)
    draft = _create_draft_version(client, pathway, payload)
    session.add(JurisdictionSourceCertification(
        jurisdiction_id=UUID(payload["jurisdiction_id"]),
        registry_entry_id=uuid4(),
        regulatory_authority_id=uuid4(),
        official_source_id=UUID(payload["official_source_id"]),
        certification_version=1,
        certification_scope="supplemental_work",
        coverage_domains_json='["work"]',
        evidence_notes="Pending independent source-certification review.",
        status="pending_review",
        proposed_by="pytest-certification-proposer",
    ))
    session.commit()
    return pathway, draft


def test_setting_disabled_rejects_internal_draft_request(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "allow_internal_draft_pathway_simulation", False)
    monkeypatch.setattr(settings, "app_env", "production")
    lead = _lead_with_profile(client, db_session)
    response = client.post(
        f"/api/v1/pathways/match/{lead.id}",
            params={"include_draft_pathways": True, "simulation_context": "pytest draft matching"},
    )
    assert response.status_code == 403
    assert "not permitted" in response.json()["detail"].lower()


@pytest.mark.parametrize("role", ["sales", "read_only"])
def test_non_internal_role_rejected_for_draft_simulation(
    client: TestClient,
    raw_client: TestClient,
    db_session: Session,
    monkeypatch,
    role: str,
) -> None:
    monkeypatch.setattr(settings, "allow_internal_draft_pathway_simulation", True)
    lead = _lead_with_profile(client, db_session)
    raw_client.headers.update({"X-GMAI-Role": role, "X-GMAI-User": f"pytest-{role}"})
    response = raw_client.post(
        f"/api/v1/pathways/match/{lead.id}",
        params={"include_draft_pathways": True, "simulation_context": "pytest draft matching"},
    )
    assert response.status_code == 403
    assert "not allowed" in response.json()["detail"].lower()


def test_public_user_rejected_for_draft_simulation(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "allow_internal_draft_pathway_simulation", True)
    lead = _lead_with_profile(client, db_session)
    client.headers.pop("X-GMAI-Role", None)
    client.headers.pop("X-GMAI-User", None)

    response = client.post(
        f"/api/v1/pathways/match/{lead.id}",
        params={"include_draft_pathways": True},
    )
    assert response.status_code == 401


@pytest.mark.parametrize("role", ["admin", "operator", "reviewer"])
def test_internal_role_with_enabled_setting_includes_draft_candidate(
    client: TestClient,
    db_session: Session,
    monkeypatch,
    role: str,
) -> None:
    monkeypatch.setattr(settings, "allow_internal_draft_pathway_simulation", True)
    pathway, draft_version = _create_published_pathway_with_draft(client, db_session)
    lead = _lead_with_profile(client, db_session)
    client.headers.update({"X-GMAI-Role": role, "X-GMAI-User": f"pytest-{role}"})

    match_response = client.post(
        f"/api/v1/pathways/match/{lead.id}",
        params={"include_draft_pathways": True, "simulation_context": "pytest draft matching"},
    )
    assert match_response.status_code == 200, match_response.text
    data = match_response.json()
    assert len(data["matches"]) == 1
    match = data["matches"][0]
    assert match["pathway"]["id"] == pathway["id"]
    assert match["pathway"]["current_version"]["id"] == draft_version["id"]
    assert match["lifecycle_status"] == "draft"
    assert match["candidate_status"] == "internal_draft"
    assert match["simulation_only"] is True
    assert match["production_recommendation"] is False
    assert match["publication_ready"] is False
    assert match["certification_statuses"]["core_route"] == "pending_review"
    assert any("certification" in blocker.lower() for blocker in match["publication_blockers"])
    assert "draft" in data["summary"].lower()


def test_without_flag_only_published_returned(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "allow_internal_draft_pathway_simulation", True)
    pathway, _ = _create_published_pathway_with_draft(client, db_session)
    lead = _lead_with_profile(client, db_session)

    match_response = client.post(f"/api/v1/pathways/match/{lead.id}")
    assert match_response.status_code == 200, match_response.text
    data = match_response.json()
    assert len(data["matches"]) == 1
    assert data["matches"][0]["pathway"]["id"] == pathway["id"]
    assert data["matches"][0]["lifecycle_status"] == "published"


def test_pathways_compare_respects_gate(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "allow_internal_draft_pathway_simulation", True)
    _create_published_pathway_with_draft(client, db_session)
    lead = _lead_with_profile(client, db_session)

    monkeypatch.setattr(settings, "allow_internal_draft_pathway_simulation", False)
    monkeypatch.setattr(settings, "app_env", "production")
    denied = client.post(
        f"/api/v1/pathways/compare/{lead.id}",
        params={"include_draft_pathways": True, "simulation_context": "pytest draft comparison"},
    )
    assert denied.status_code == 403


def test_eligibility_evaluate_passes_flag_and_includes_governance(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "allow_internal_draft_pathway_simulation", True)
    _create_published_pathway_with_draft(client, db_session)
    lead = _lead_with_profile(client, db_session)

    response = client.post(
        "/api/v1/eligibility/evaluate",
        json={
            "lead_id": str(lead.id),
            "profile": {},
            "include_draft_pathways": True,
            "simulation_context": "pytest eligibility simulation",
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    factors = data["factors"]
    assert factors["catalogue_pathways_count"] == 1
    evidence = factors["pathway_evidence"][0]
    assert evidence["lifecycle_status"] == "draft"
    assert evidence["candidate_status"] == "internal_draft"
    assert evidence["simulation_only"] is True
    assert evidence["production_recommendation"] is False
    audit = db_session.exec(
        select(AuditLog).where(AuditLog.action == "internal_draft_eligibility_simulation_generated")
    ).one()
    assert audit.actor == "pytest-admin"
    assert "pytest eligibility simulation" in (audit.reason or "")
    assert evidence["publication_ready"] is False
    assert evidence["certification_statuses"]["core_route"] == "pending_review"
    assert any("certification" in blocker.lower() for blocker in evidence["publication_blockers"])


def test_publish_endpoint_unchanged_and_only_publishes_draft(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "allow_internal_draft_pathway_simulation", True)
    pathway, payload = _create_published_pathway(client, db_session)
    draft_version = _create_draft_version(client, pathway, payload)
    version_id = draft_version["id"]

    publish = client.post(
        f"/api/v1/pathways/versions/{version_id}/publish",
        json={"review_notes": "Reviewed and approved."},
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "pytest-pathway-reviewer"},
    )
    assert publish.status_code == 200, publish.text
    published = publish.json()
    assert published["current_version"]["lifecycle_status"] == "published"

    # Republishing the same version is rejected because it is no longer draft.
    republish = client.post(
        f"/api/v1/pathways/versions/{version_id}/publish",
        json={"review_notes": "Cannot republish."},
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "pytest-pathway-reviewer"},
    )
    assert republish.status_code == 400
    assert "draft" in republish.json()["detail"].lower()
