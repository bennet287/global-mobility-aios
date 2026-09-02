from __future__ import annotations

from unittest.mock import patch
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.domain import AgentRun, AgentRunStatus

from .conftest import create_lead


def test_batch_submission_creates_queued_runs(client: TestClient, db_session: Session) -> None:
    lead1 = create_lead(db_session)
    lead2 = create_lead(db_session)

    with patch("app.routers.controlled_agents.run_agent_task") as mock_task:
        mock_task.delay.return_value = None
        response = client.post(
            "/api/v1/controlled-agents/run-batch",
            json={
                "agent_name": "sales_summary_agent",
                "lead_ids": [str(lead1.id), str(lead2.id)],
                "task_template": "Prepare sales summary.",
                "context_per_lead": {str(lead1.id): {"source": "web"}},
                "actor": "pytest-operator",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["agent_name"] == "sales_summary_agent"
    assert data["queued"] == 2
    assert len(data["run_ids"]) == 2
    assert mock_task.delay.call_count == 2

    for run_id in data["run_ids"]:
        run = db_session.get(AgentRun, UUID(run_id))
        assert run is not None
        assert run.status == AgentRunStatus.queued.value
        assert run.agent_name == "sales_summary_agent"


def test_batch_submission_rejects_unknown_agent(client: TestClient) -> None:
    response = client.post(
        "/api/v1/controlled-agents/run-batch",
        json={
            "agent_name": "unknown_agent",
            "lead_ids": [],
            "task_template": "Do something.",
        },
    )
    assert response.status_code == 404


def test_batch_approve_and_convert(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session)

    with patch("app.routers.controlled_agents.run_agent_task") as mock_task:
        mock_task.delay.return_value = None
        batch_response = client.post(
            "/api/v1/controlled-agents/run-batch",
            json={
                "agent_name": "sales_summary_agent",
                "lead_ids": [str(lead.id)],
                "task_template": "Prepare sales summary.",
            },
        )

    run_id = batch_response.json()["run_ids"][0]
    run = db_session.get(AgentRun, UUID(run_id))
    run.status = AgentRunStatus.pending_review.value
    run.output_json = '{"summary": "test summary"}'
    db_session.add(run)
    db_session.commit()

    approve_response = client.post(
        "/api/v1/agent-output-reviews/batch-approve",
        json={"run_ids": [run_id], "actor": "pytest-reviewer", "note": "LGTM"},
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["results"][0]["status"] == AgentRunStatus.approved.value

    convert_response = client.post(
        "/api/v1/agent-output-reviews/batch-convert",
        json={"run_ids": [run_id], "actor": "pytest-reviewer"},
    )
    assert convert_response.status_code == 200
    assert convert_response.json()["results"][0]["status"] == "converted"


def test_batch_reject(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session)

    with patch("app.routers.controlled_agents.run_agent_task") as mock_task:
        mock_task.delay.return_value = None
        batch_response = client.post(
            "/api/v1/controlled-agents/run-batch",
            json={
                "agent_name": "sales_summary_agent",
                "lead_ids": [str(lead.id)],
                "task_template": "Prepare sales summary.",
            },
        )

    run_id = batch_response.json()["run_ids"][0]
    run = db_session.get(AgentRun, UUID(run_id))
    run.status = AgentRunStatus.pending_review.value
    run.output_json = '{"summary": "test summary"}'
    db_session.add(run)
    db_session.commit()

    response = client.post(
        "/api/v1/agent-output-reviews/batch-reject",
        json={"run_ids": [run_id], "actor": "pytest-reviewer", "note": "Not good"},
    )
    assert response.status_code == 200
    assert response.json()["results"][0]["status"] == AgentRunStatus.rejected.value
