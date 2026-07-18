from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import EligibilityAssessment, LeadIntent


def _create_lead(session: Session, **kwargs) -> Any:
    from app.models.domain import Lead, LeadStatus

    lead = Lead(
        full_name=kwargs.get("full_name", "Test Lead"),
        email=kwargs.get("email"),
        target_country=kwargs.get("target_country"),
        intent=kwargs.get("intent", LeadIntent.unknown),
        status=LeadStatus.new,
        notes=kwargs.get("notes"),
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead


from typing import Any


def test_evaluate_eligibility_creates_assessment(client: TestClient, db_session: Session) -> None:
    lead = _create_lead(
        db_session,
        full_name="Aisha Patel",
        target_country="Germany",
        intent=LeadIntent.overseas_job,
        notes="5 years experience as a registered nurse. IELTS 7.0. Bachelor's degree.",
    )

    response = client.post(
        "/api/v1/eligibility/evaluate",
        json={"lead_id": str(lead.id), "profile": {"budget_eur": 10000}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["lead_id"] == str(lead.id)
    assert data["target_country"] == "germany"
    assert data["domain"] == "work"
    assert data["overall_score"] > 0
    assert data["status"] in {"eligible", "likely_eligible"}
    assert len(data["required_documents"]) > 0
    assert len(data["pathways"]) > 0
    assert "agent_run_id" in data
    assert data["agent_run_id"] is not None

    # Assessment is persisted.
    statement = select(EligibilityAssessment).where(EligibilityAssessment.lead_id == lead.id)
    rows = db_session.exec(statement).all()
    assert len(rows) == 1
    assert rows[0].status == data["status"]


def test_evaluate_eligibility_missing_country(client: TestClient, db_session: Session) -> None:
    lead = _create_lead(
        db_session,
        full_name="No Country",
        intent=LeadIntent.overseas_job,
        target_country=None,
    )

    response = client.post(
        "/api/v1/eligibility/evaluate",
        json={"lead_id": str(lead.id)},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "insufficient_profile"
    assert data["overall_score"] == 0.0
    assert any("Target country is missing" in r for r in data["risks"])


def test_list_eligibility_assessments(client: TestClient, db_session: Session) -> None:
    lead = _create_lead(
        db_session,
        full_name="List Test",
        target_country="Canada",
        intent=LeadIntent.study_abroad,
    )

    client.post("/api/v1/eligibility/evaluate", json={"lead_id": str(lead.id)})

    response = client.get(f"/api/v1/eligibility/{lead.id}/assessments")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["lead_id"] == str(lead.id)


def test_latest_eligibility_assessment_not_found(client: TestClient) -> None:
    import uuid

    response = client.get(f"/api/v1/eligibility/{uuid.uuid4()}/latest")
    assert response.status_code == 404
