from __future__ import annotations

from copy import deepcopy

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import AuditLog, DocumentRecord, Lead, LeadIntent, PathwayComparisonAssessment, Profile


def _lead(session: Session, name: str = "Universal Profile Lead") -> Lead:
    lead = Lead(
        full_name=name,
        email=f"{name.lower().replace(' ', '.')}@example.com",
        intent=LeadIntent.overseas_job,
        target_country="Germany",
        source="pytest",
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead


def _document(session: Session, lead: Lead) -> DocumentRecord:
    document = DocumentRecord(
        lead_id=lead.id,
        document_type="passport",
        filename="passport.pdf",
        status="verified",
    )
    session.add(document)
    session.commit()
    session.refresh(document)
    return document


def _payload(document: DocumentRecord) -> dict:
    return {
        "current_country": "India",
        "education": [{
            "qualification": "Bachelor of Science",
            "field_of_study": "Nursing",
            "institution": "Example University",
            "country": "India",
            "completion_year": 2020,
        }],
        "employment": [{
            "role": "Registered Nurse",
            "employer": "Example Hospital",
            "country": "India",
            "years": 4,
            "current": True,
        }],
        "years_experience": 4,
        "skills": ["nursing", "patient care"],
        "languages": [{"language": "English", "level": "C1", "test_name": "IELTS", "test_score": "7.5"}],
        "family_status": "single",
        "family_details_confirmed": True,
        "finances": {"budget_eur": 15000, "funding_source": "savings"},
        "goals": [{
            "domain": "work",
            "target_country": "Germany",
            "desired_role_or_program": "Registered Nurse",
            "priority": "high",
        }],
        "constraints": [{"type": "timeline", "value": "within 12 months"}],
        "constraints_confirmed": True,
        "consent_status": "granted",
        "consent_purposes": ["eligibility", "opportunity_matching"],
        "evidence_document_ids": [str(document.id)],
    }


def test_profile_versions_completeness_history_and_audit(
    client: TestClient,
    db_session: Session,
) -> None:
    lead = _lead(db_session)
    document = _document(db_session, lead)
    payload = _payload(document)

    response = client.put(f"/api/v1/profiles/leads/{lead.id}/current", json=payload)
    assert response.status_code == 200, response.text
    version_one = response.json()
    assert version_one["profile_version"] == 1
    assert version_one["lifecycle_status"] == "active"
    assert version_one["completeness_score"] == 100.0
    assert version_one["readiness_stage"] == "evidence_ready"
    assert version_one["missing_sections"] == []
    assert version_one["updated_by"] == "pytest-admin"

    changed = deepcopy(payload)
    changed["years_experience"] = 5
    response = client.put(f"/api/v1/profiles/leads/{lead.id}/current", json=changed)
    assert response.status_code == 200, response.text
    version_two = response.json()
    assert version_two["profile_version"] == 2
    assert version_two["supersedes_profile_id"] == version_one["id"]

    current = client.get(f"/api/v1/profiles/leads/{lead.id}/current")
    history = client.get(f"/api/v1/profiles/leads/{lead.id}/history")
    assert current.status_code == 200
    assert current.json()["id"] == version_two["id"]
    assert history.status_code == 200
    assert [item["profile_version"] for item in history.json()] == [2, 1]
    assert history.json()[1]["lifecycle_status"] == "superseded"

    audits = list(db_session.exec(
        select(AuditLog).where(AuditLog.action == "mobility_profile_version_created")
    ).all())
    assert len(audits) == 2
    assert all(audit.actor == "pytest-admin" for audit in audits)


def test_profile_rejects_evidence_owned_by_another_lead(
    client: TestClient,
    db_session: Session,
) -> None:
    lead = _lead(db_session, "First Lead")
    other = _lead(db_session, "Second Lead")
    other_document = _document(db_session, other)

    response = client.put(
        f"/api/v1/profiles/leads/{lead.id}/current",
        json=_payload(other_document),
    )
    assert response.status_code == 400
    assert "belongs to another lead" in response.json()["detail"]
    assert db_session.exec(select(Profile).where(Profile.lead_id == lead.id)).first() is None


def test_withdrawn_consent_restricts_eligibility_and_matching(
    client: TestClient,
    db_session: Session,
) -> None:
    lead = _lead(db_session, "Consent Withdrawn")
    document = _document(db_session, lead)
    payload = _payload(document)
    payload["consent_status"] = "withdrawn"

    profile_response = client.put(f"/api/v1/profiles/leads/{lead.id}/current", json=payload)
    assert profile_response.status_code == 200, profile_response.text
    profile = profile_response.json()
    assert profile["lifecycle_status"] == "restricted"
    assert profile["readiness_stage"] == "restricted"

    eligibility = client.post("/api/v1/eligibility/evaluate", json={"lead_id": str(lead.id)})
    assert eligibility.status_code == 200, eligibility.text
    assessment = eligibility.json()
    assert assessment["status"] == "insufficient_profile"
    assert assessment["overall_score"] == 0.0
    assert assessment["pathways"] == []
    assert assessment["profile_id"] == profile["id"]
    assert assessment["profile_version"] == 1
    assert assessment["factors"]["consent_status"] == "withdrawn"

    client.post("/api/v1/opportunities/seed")
    matching = client.post(f"/api/v1/opportunities/match/{lead.id}")
    assert matching.status_code == 200, matching.text
    matches = matching.json()
    assert matches["matches"] == []
    assert matches["profile_id"] == profile["id"]
    assert matches["profile_version"] == 1
    assert "restricted" in matches["summary"].lower()

    comparison = client.post(f"/api/v1/pathways/compare/{lead.id}")
    assert comparison.status_code == 200, comparison.text
    comparison_data = comparison.json()
    assert comparison_data["status"] == "restricted"
    assert comparison_data["assessment_id"] is None
    assert db_session.exec(
        select(PathwayComparisonAssessment).where(PathwayComparisonAssessment.lead_id == lead.id)
    ).first() is None
    restricted_audit = db_session.exec(
        select(AuditLog).where(AuditLog.action == "pathway_comparison_restricted")
    ).first()
    assert restricted_audit is not None
