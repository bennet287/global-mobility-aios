from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    AuditLog, DocumentRecord, Lead, LeadIntent, MobilityPathway,
    MobilityPathwayVersion, OfficialSource, SourceSnapshot,
)


def _grounding(session: Session):
    source = OfficialSource(country="portugal", domain="investment", name="Portugal investment authority", url="https://investment.gov.pt/program", active=True)
    session.add(source); session.commit(); session.refresh(source)
    snapshot = SourceSnapshot(official_source_id=source.id, url=source.url, content_hash="pt-suitability-snapshot", content_text="Official threshold and conditions.", status="captured", retrieval_method="http")
    pathway = MobilityPathway(pathway_key="pt-suitability-investor-route", name="Portugal Investor Route", country="portugal", domain="investment", catalogue_status="active", created_by="pathway-proposer")
    session.add(snapshot); session.add(pathway); session.commit(); session.refresh(snapshot); session.refresh(pathway)
    version = MobilityPathwayVersion(pathway_id=pathway.id, version_number=1, lifecycle_status="published", official_source_id=source.id, source_snapshot_id=snapshot.id, created_by="pathway-proposer", approved_by="pathway-reviewer")
    session.add(version); session.commit(); session.refresh(version)
    return pathway, version, source, snapshot


def _payload(pathway, version, source, snapshot):
    return {
        "program_key": "pt-suitability-governed-route", "name": "Portugal Governed Investor Route",
        "country": "Portugal", "program_type": "residence_by_investment", "pathway_id": str(pathway.id),
        "pathway_version_id": str(version.id), "official_source_id": str(source.id), "source_snapshot_id": str(snapshot.id),
        "minimum_commitment_minor": 50000000, "currency": "EUR",
        "investment_options": [{"type": "regulated_fund"}], "family_scope": ["spouse", "dependent_children"],
        "due_diligence": ["lawful source of funds", "sanctions screening"], "fees": {},
        "benefits": ["Residence route subject to approval"], "risks": ["Capital at risk", "Rules can change"],
    }


def _lead(session: Session, name: str = "Investor Client") -> Lead:
    row = Lead(full_name=name, email=f"{name.lower().replace(' ', '.')}@example.com", intent=LeadIntent.visa, target_country="Portugal", source="pytest")
    session.add(row); session.commit(); session.refresh(row)
    return row


def _published_program(client: TestClient, session: Session):
    pathway, version, source, snapshot = _grounding(session)
    draft = client.post("/api/v1/investment-mobility/programs", json=_payload(pathway, version, source, snapshot)).json()
    client.headers["X-GMAI-User"] = "program-independent-reviewer"
    response = client.post(
        f"/api/v1/investment-mobility/versions/{draft['current_version']['id']}/publish",
        json={"review_notes": "Program conditions independently checked against official evidence."},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _assessment_payload(lead: Lead, program: dict) -> dict:
    return {
        "lead_id": str(lead.id), "program_ids": [program["id"]], "target_countries": [],
        "available_capital_minor": 75000000, "liquid_capital_minor": 90000000,
        "net_worth_minor": 250000000, "currency": "EUR", "risk_tolerance": "balanced",
        "family_members": 3, "timeline_months": 18, "capital_preservation_required": False,
        "lawful_source_of_funds_confirmed": True, "disclosed_constraints": [], "document_record_ids": [],
    }


def test_suitability_ranks_only_published_programs_and_explains_scores(client: TestClient, db_session: Session):
    program = _published_program(client, db_session)
    lead = _lead(db_session)
    document = DocumentRecord(lead_id=lead.id, document_type="bank_statement", filename="wealth.pdf", status="verified")
    db_session.add(document); db_session.commit(); db_session.refresh(document)
    payload = _assessment_payload(lead, program)
    payload["document_record_ids"] = [str(document.id)]
    client.headers["X-GMAI-User"] = "suitability-proposer"
    response = client.post("/api/v1/investment-mobility/suitability/assessments", json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "pending_review"
    assert body["human_review_required"] is True
    assert body["ranked_programs"][0]["program_id"] == program["id"]
    assert body["ranked_programs"][0]["capital_coverage_score"] == 100
    assert body["ranked_programs"][0]["source_snapshot_id"] == program["current_version"]["source_snapshot_id"]
    assert "not investment advice" in body["score_semantics"].lower()
    actions = {item.action for item in db_session.exec(select(AuditLog)).all()}
    assert "investment_mobility_suitability_created" in actions


def test_suitability_does_not_apply_unverified_currency_conversion(client: TestClient, db_session: Session):
    program = _published_program(client, db_session)
    lead = _lead(db_session)
    payload = _assessment_payload(lead, program)
    payload["currency"] = "USD"
    client.headers["X-GMAI-User"] = "currency-comparison-proposer"
    response = client.post("/api/v1/investment-mobility/suitability/assessments", json=payload)
    assert response.status_code == 201, response.text
    result = response.json()["ranked_programs"][0]
    assert result["capital_coverage_score"] == 15
    assert any("currencies differ" in blocker for blocker in result["blockers"])


def test_suitability_rejects_cross_client_evidence(client: TestClient, db_session: Session):
    program = _published_program(client, db_session)
    lead = _lead(db_session)
    other = _lead(db_session, "Other Investor")
    document = DocumentRecord(lead_id=other.id, document_type="bank_statement", filename="other.pdf", status="verified")
    db_session.add(document); db_session.commit(); db_session.refresh(document)
    payload = _assessment_payload(lead, program)
    payload["document_record_ids"] = [str(document.id)]
    response = client.post("/api/v1/investment-mobility/suitability/assessments", json=payload)
    assert response.status_code == 400
    assert "selected lead" in response.json()["detail"]


def test_suitability_requires_independent_review(client: TestClient, db_session: Session):
    program = _published_program(client, db_session)
    lead = _lead(db_session)
    client.headers["X-GMAI-User"] = "assessment-proposer"
    assessment = client.post(
        "/api/v1/investment-mobility/suitability/assessments", json=_assessment_payload(lead, program),
    ).json()
    rejected = client.post(
        f"/api/v1/investment-mobility/suitability/assessments/{assessment['id']}/reviews",
        json={"decision": "approved", "reason": "The comparison evidence and limitations were reviewed."},
    )
    assert rejected.status_code == 400
    client.headers["X-GMAI-User"] = "assessment-reviewer"
    reviewed = client.post(
        f"/api/v1/investment-mobility/suitability/assessments/{assessment['id']}/reviews",
        json={"decision": "approved", "reason": "The comparison evidence and limitations were reviewed."},
    )
    assert reviewed.status_code == 201, reviewed.text


def test_read_only_role_cannot_create_suitability(raw_client: TestClient, client: TestClient, db_session: Session):
    program = _published_program(client, db_session)
    lead = _lead(db_session)
    raw_client.headers.update({"X-GMAI-Role": "read_only", "X-GMAI-User": "readonly-suitability"})
    response = raw_client.post(
        "/api/v1/investment-mobility/suitability/assessments", json=_assessment_payload(lead, program),
    )
    assert response.status_code == 403
