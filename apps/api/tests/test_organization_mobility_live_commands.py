from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.domain import OrganizationActorType
from app.services.organization_agent_runtime import AgentRuntimeProfile, RuntimeClass
from app.services.organization_command import OrganizationCommandContext
from app.services.organization_governance import ensure_foundation_positions
from app.services.organization_mobility_objective_execution import execute_austria_specialists
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_PATHWAY_POSITION,
    AUSTRIA_MOBILITY_REGULATORY_POSITION,
    create_austria_mobility_objective,
)


def _human_context() -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key="default",
        actor_id="live-command-owner",
        actor_type=OrganizationActorType.human,
        authenticated_user_id="live-command-owner",
        role="admin",
        department="Global Mobility Operations",
        position_key="board",
        authority_level="L4",
    )


def _runtime(provider: str) -> AgentRuntimeProfile:
    return AgentRuntimeProfile(
        profile_key=f"{provider}-live-command-v1",
        runtime_class=RuntimeClass.HOSTED_API,
        adapter_key=f"{provider}-adapter",
        provider_key=provider,
        model_key=f"{provider}-model",
        technical_capabilities=("reasoning", "structured_output"),
        available_tools=("browser", "shell"),
        independence_group=provider,
        profile_version=1,
        enabled=True,
    )


def _ready_plan(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    *,
    objective_key: str,
):
    monkeypatch.setattr("app.services.controlled_agents.is_llm_enabled", lambda: False)
    ensure_foundation_positions(db_session, actor="live-command", repair_contracts=True)
    plan = create_austria_mobility_objective(
        db_session,
        _human_context(),
        objective_key=objective_key,
    )
    execute_austria_specialists(
        db_session,
        _human_context(),
        plan,
        runtime_profiles={
            AUSTRIA_MOBILITY_PATHWAY_POSITION: _runtime("provider-a"),
            AUSTRIA_MOBILITY_REGULATORY_POSITION: _runtime("provider-b"),
        },
    )
    return plan


def test_board_can_materialize_and_exactly_replay_ready_owner_synthesis(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _ready_plan(
        db_session,
        monkeypatch,
        objective_key="at-rwr-shortage-2026-live-command",
    )
    path = f"/api/v1/organization/live-organization/austria/{plan.root_work_item.id}/owner-synthesis"

    first = client.post(path)
    assert first.status_code == 200
    first_body = first.json()
    assert first_body["root_work_item_id"] == str(plan.root_work_item.id)
    assert first_body["disposition"] == "ready_for_human_review"
    assert first_body["replayed"] is False

    replay = client.post(path)
    assert replay.status_code == 200
    replay_body = replay.json()
    assert replay_body["replayed"] is True
    assert replay_body["action_output_id"] == first_body["action_output_id"]
    assert replay_body["activity_id"] == first_body["activity_id"]

    snapshot = client.get(
        f"/api/v1/organization/transparency/live-organization/austria/{plan.root_work_item.id}"
    )
    assert snapshot.status_code == 200
    snapshot_body = snapshot.json()
    assert snapshot_body["cycle_status"] == "completed"
    assert snapshot_body["owner_synthesis"]["action_output_id"] == first_body["action_output_id"]
    assert snapshot_body["external_action_authorized"] is False


def test_owner_synthesis_command_requires_board_admin_human(
    raw_client: TestClient,
) -> None:
    raw_client.headers.update({
        "X-GMAI-Role": "operator",
        "X-GMAI-User": "pytest-operator",
    })
    response = raw_client.post(
        f"/api/v1/organization/live-organization/austria/{uuid4()}/owner-synthesis"
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Board live-organization command access is not permitted."


def test_owner_synthesis_command_missing_root_is_non_disclosing_404(
    client: TestClient,
) -> None:
    response = client.post(
        f"/api/v1/organization/live-organization/austria/{uuid4()}/owner-synthesis"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Organization live objective not found."


def test_owner_synthesis_command_fails_closed_before_k1_readiness(
    client: TestClient,
    db_session: Session,
) -> None:
    ensure_foundation_positions(db_session, actor="live-command-not-ready", repair_contracts=True)
    plan = create_austria_mobility_objective(
        db_session,
        _human_context(),
        objective_key="at-rwr-shortage-2026-live-command-not-ready",
    )
    response = client.post(
        f"/api/v1/organization/live-organization/austria/{plan.root_work_item.id}/owner-synthesis"
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Austria objective is not ready for bounded owner synthesis."
