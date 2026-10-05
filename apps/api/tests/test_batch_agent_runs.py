from __future__ import annotations

import asyncio
from unittest.mock import patch
from uuid import UUID
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request
from sqlmodel import Session, SQLModel, create_engine, select

from app.models.domain import AgentRun, AgentRunStatus
from app.routers.controlled_agents import admin_run_controlled_agent_batch, run_controlled_agent_batch
from app.schemas import ControlledAgentRunBatchRequest

from .conftest import create_lead


@pytest.fixture
def batch_engine(tmp_path):
    # A file database and independent sessions reproduce worker visibility;
    # the normal shared in-memory test connection cannot expose this race.
    engine = create_engine(f"sqlite:///{tmp_path / 'batch-publication.db'}")
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


def _batch_payload(session):
    leads = [create_lead(session), create_lead(session)]
    return ControlledAgentRunBatchRequest(
        agent_name="sales_summary_agent",
        lead_ids=[lead.id for lead in leads],
        task_template="Prepare a synthetic internal sales summary.",
        actor="pytest-operator",
    )


def _submit_batch(payload, session, entrypoint):
    if entrypoint == "api":
        return run_controlled_agent_batch(payload, session)
    body = urlencode({
        "agent_name": payload.agent_name,
        "lead_ids": [str(lead_id) for lead_id in payload.lead_ids],
        "task_template": payload.task_template,
        "actor": payload.actor,
    }, doseq=True).encode()

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    request = Request({"type": "http", "method": "POST", "path": "/admin/controlled-agents/run-batch", "headers": []}, receive)
    return asyncio.run(admin_run_controlled_agent_batch(request, session))


@pytest.mark.parametrize("entrypoint", ["api", "admin"])
def test_fast_consumer_sees_entire_committed_batch_at_first_publication(batch_engine, monkeypatch, entrypoint):
    observed = []

    def consume(run_id):
        with Session(batch_engine) as consumer:
            runs = consumer.exec(select(AgentRun)).all()
            assert len(runs) == 2
            assert consumer.get(AgentRun, UUID(run_id)) is not None
            assert all(run.status == AgentRunStatus.queued.value for run in runs)
        observed.append(run_id)

    monkeypatch.setattr("app.routers.controlled_agents.run_agent_task.delay", consume)
    with Session(batch_engine) as producer:
        response = _submit_batch(_batch_payload(producer), producer, entrypoint)
    assert len(observed) == 2
    if entrypoint == "api":
        assert observed == [str(run_id) for run_id in response.run_ids]
        assert response.queued == 2
    else:
        assert response.status_code == 303
        assert response.headers["location"] == "/admin/agent-output-reviews"


@pytest.mark.parametrize("entrypoint", ["api", "admin"])
def test_failed_batch_commit_does_not_publish_any_task(batch_engine, monkeypatch, entrypoint):
    published = []
    monkeypatch.setattr("app.routers.controlled_agents.run_agent_task.delay", published.append)
    with Session(batch_engine) as producer:
        payload = _batch_payload(producer)

        def fail_commit():
            raise RuntimeError("synthetic database commit failure")

        monkeypatch.setattr(producer, "commit", fail_commit)
        with pytest.raises(RuntimeError, match="database commit failure"):
            _submit_batch(payload, producer, entrypoint)
        producer.rollback()
    with Session(batch_engine) as consumer:
        assert consumer.exec(select(AgentRun)).all() == []
    assert published == []


@pytest.mark.parametrize("fail_after", [0, 1])
@pytest.mark.parametrize("entrypoint", ["api", "admin"])
def test_broker_failure_keeps_committed_intent_without_inventing_execution(batch_engine, monkeypatch, fail_after, entrypoint):
    attempted = []

    def publish(run_id):
        attempted.append(run_id)
        if len(attempted) > fail_after:
            raise RuntimeError("synthetic broker publication failure")

    monkeypatch.setattr("app.routers.controlled_agents.run_agent_task.delay", publish)
    with Session(batch_engine) as producer:
        payload = _batch_payload(producer)
        with pytest.raises(RuntimeError, match="broker publication failure"):
            _submit_batch(payload, producer, entrypoint)
        producer.rollback()
    with Session(batch_engine) as consumer:
        runs = consumer.exec(select(AgentRun)).all()
        assert len(runs) == 2
        assert all(run.status == AgentRunStatus.queued.value for run in runs)
        assert all(run.agent_name == "sales_summary_agent" for run in runs)
    assert len(attempted) == fail_after + 1


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
