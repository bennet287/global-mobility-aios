from __future__ import annotations

import json

from fastapi.testclient import TestClient
from sqlmodel import Session
from sqlmodel import select

from app.models.domain import AgentRun, AuditLog

from .conftest import create_lead


def test_controlled_agents_registry_exposes_five_review_gated_agents(client: TestClient) -> None:
    response = client.get("/api/v1/controlled-agents")

    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == "v4.0"
    assert payload["automatic_actions_enabled"] is False
    assert set(payload["agents"]) == {
        "truth_explanation_agent",
        "document_checklist_agent",
        "client_drafting_agent",
        "sales_summary_agent",
        "application_readiness_agent",
    }


def test_controlled_client_drafting_agent_persists_run_and_blocks_send(
    client: TestClient,
    db_session: Session,
) -> None:
    lead = create_lead(db_session)

    response = client.post(
        "/api/v1/controlled-agents/run",
        json={
            "agent_name": "client_drafting_agent",
            "task": "Draft a safe client update.",
            "lead_id": str(lead.id),
            "context": {"subject": "Application update"},
            "actor": "pytest-reviewer",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["agent_name"] == "client_drafting_agent"
    assert payload["requires_human_review"] is True
    assert payload["output"]["send_allowed"] is False
    assert "email_send" in payload["output"]["blocked_actions"]

    run = db_session.exec(select(AgentRun)).one()
    assert run.agent_name == "client_drafting_agent"
    assert run.lead_id == lead.id
    output = json.loads(run.output_json)
    assert output["send_allowed"] is False

    audit = db_session.exec(select(AuditLog).where(AuditLog.action == "controlled_agent_run")).one()
    assert audit.actor == "pytest-reviewer"
    assert audit.entity_type == "agent_run"
    assert audit.source == "controlled_agents_v4.0"


def test_legacy_agent_endpoint_routes_through_controlled_service(
    client: TestClient,
    db_session: Session,
) -> None:
    response = client.post(
        "/api/v1/agents/run",
        json={
            "agent_name": "visa_truth_agent",
            "task": "Explain the truth check.",
            "context": {"verdict": "rejected", "confidence": 0.95},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["agent_name"] == "truth_explanation_agent"
    assert payload["status"] == "completed"
    assert payload["output"]["resolved_agent_name"] == "truth_explanation_agent"
    assert payload["output"]["requires_human_review"] is True
    assert db_session.exec(select(AgentRun)).one().agent_name == "truth_explanation_agent"


def test_unknown_controlled_agent_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/controlled-agents/run",
        json={
            "agent_name": "auto_submit_everything_agent",
            "task": "Submit without review.",
            "context": {},
        },
    )

    assert response.status_code == 404
