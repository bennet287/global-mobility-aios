from __future__ import annotations

import json
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import Session
from sqlmodel import select

from app.models.domain import AgentRun, AuditLog, FollowUp, Lead

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


def test_agent_operator_console_lists_safe_actions(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session)

    response = client.get("/admin/controlled-agents")

    assert response.status_code == 200
    assert "Agent Operator Console v4.1" in response.text
    assert str(lead.id) in response.text
    assert "Generate Sales Summary" in response.text
    assert "Auto-send disabled" in response.text


def test_agent_operator_console_action_creates_review_gated_run(
    client: TestClient,
    db_session: Session,
) -> None:
    lead = create_lead(db_session)

    response = client.post(
        f"/admin/controlled-agents/leads/{lead.id}/run/application_readiness_agent",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert "/admin/controlled-agents/runs/" in response.headers["location"]

    run = db_session.exec(select(AgentRun)).one()
    assert run.lead_id == lead.id
    assert run.agent_name == "application_readiness_agent"
    output = json.loads(run.output_json)
    assert output["ready_for_submission"] is False
    assert "application_submission" in output["blocked_actions"]

    audit = db_session.exec(select(AuditLog).where(AuditLog.action == "controlled_agent_run")).one()
    assert audit.actor == "operator_console"
    assert audit.source == "controlled_agents_v4.0"

    detail = client.get(response.headers["location"])
    assert detail.status_code == 200
    assert "Requires human review" in detail.text


def test_agent_output_review_queue_approves_and_audits_output(
    client: TestClient,
    db_session: Session,
) -> None:
    lead = create_lead(db_session)
    run_response = client.post(
        "/api/v1/controlled-agents/run",
        json={
            "agent_name": "sales_summary_agent",
            "task": "Prepare sales summary.",
            "lead_id": str(lead.id),
            "context": {},
            "actor": "pytest-agent",
        },
    )
    run_id = run_response.json()["run_id"]

    queue = client.get("/api/v1/agent-output-reviews/queue")
    assert queue.status_code == 200
    assert queue.json()["items"][0]["id"] == run_id

    approve = client.post(
        f"/api/v1/agent-output-reviews/runs/{run_id}/approve",
        json={"actor": "pytest-reviewer", "note": "Approved for internal use."},
    )

    assert approve.status_code == 200
    assert approve.json()["status"] == "approved"
    run = db_session.get(AgentRun, UUID(run_id))
    assert run.status == "approved"

    actions = {audit.action for audit in db_session.exec(select(AuditLog)).all()}
    assert "controlled_agent_run" in actions
    assert "agent_output_approved" in actions


def test_unapproved_agent_output_cannot_be_converted(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session)
    run_response = client.post(
        "/api/v1/controlled-agents/run",
        json={
            "agent_name": "client_drafting_agent",
            "task": "Draft update.",
            "lead_id": str(lead.id),
            "context": {},
        },
    )
    run_id = run_response.json()["run_id"]

    convert = client.post(
        f"/api/v1/agent-output-reviews/runs/{run_id}/convert",
        json={"actor": "pytest-reviewer", "note": "Should be blocked."},
    )

    assert convert.status_code == 409
    assert db_session.exec(select(FollowUp)).all() == []


def test_approved_client_drafting_output_converts_to_pending_followup(
    client: TestClient,
    db_session: Session,
) -> None:
    lead = create_lead(db_session)
    run_response = client.post(
        "/api/v1/controlled-agents/run",
        json={
            "agent_name": "client_drafting_agent",
            "task": "Draft update.",
            "lead_id": str(lead.id),
            "context": {"subject": "Safe update"},
        },
    )
    run_id = run_response.json()["run_id"]
    client.post(
        f"/api/v1/agent-output-reviews/runs/{run_id}/approve",
        json={"actor": "pytest-reviewer", "note": "Approved draft."},
    )

    convert = client.post(
        f"/api/v1/agent-output-reviews/runs/{run_id}/convert",
        json={"actor": "pytest-reviewer", "note": "Convert to draft."},
    )

    assert convert.status_code == 200
    payload = convert.json()
    assert payload["converted_to"] == "client_communication_draft"
    follow_up = db_session.exec(select(FollowUp)).one()
    assert follow_up.lead_id == lead.id
    assert str(follow_up.status) in {"pending", "FollowUpStatus.pending"}
    assert "Subject: Safe update" in follow_up.message
    assert db_session.get(AgentRun, UUID(run_id)).status == "converted"

    actions = {audit.action for audit in db_session.exec(select(AuditLog)).all()}
    assert "agent_output_converted_to_client_draft" in actions


def test_approved_sales_summary_converts_to_internal_lead_note(
    client: TestClient,
    db_session: Session,
) -> None:
    lead = create_lead(db_session)
    run_response = client.post(
        "/api/v1/controlled-agents/run",
        json={
            "agent_name": "sales_summary_agent",
            "task": "Prepare sales summary.",
            "lead_id": str(lead.id),
            "context": {},
        },
    )
    run_id = run_response.json()["run_id"]
    client.post(
        f"/api/v1/agent-output-reviews/runs/{run_id}/approve",
        json={"actor": "pytest-reviewer", "note": "Approved note."},
    )

    convert = client.post(
        f"/api/v1/agent-output-reviews/runs/{run_id}/convert",
        json={"actor": "pytest-reviewer", "note": "Attach internally."},
    )

    assert convert.status_code == 200
    assert convert.json()["converted_to"] == "internal_lead_note"
    updated_lead = db_session.get(Lead, lead.id)
    assert "Lead summary prepared for sales-safe follow-up." in updated_lead.notes
    assert "Attach internally." in updated_lead.notes
    assert db_session.get(AgentRun, UUID(run_id)).status == "converted"


def test_agent_review_admin_page_loads_pending_outputs(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session)
    client.post(
        "/api/v1/controlled-agents/run",
        json={
            "agent_name": "sales_summary_agent",
            "task": "Prepare sales summary.",
            "lead_id": str(lead.id),
            "context": {},
        },
    )

    response = client.get("/admin/agent-output-reviews")

    assert response.status_code == 200
    assert "Agent Output Review Queue v4.2" in response.text
    assert "Approve Output" in response.text
