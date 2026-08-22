from __future__ import annotations

import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import OrganizationalActionOutput
from app.services.organization_agent_runtime import AgentRuntimeProfile, RuntimeClass
from app.services.organization_governance import ensure_foundation_positions
from app.services.organization_mobility_live_organization import (
    austria_owner_synthesis_output_key,
    synthesize_austria_objective_owner,
)
from app.services.organization_mobility_objective_execution import execute_austria_specialists
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_PATHWAY_POSITION,
    AUSTRIA_MOBILITY_REGULATORY_POSITION,
    create_austria_mobility_objective,
)
from app.services.organization_command import OrganizationCommandContext
from app.models.domain import OrganizationActorType


def _human_context() -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key="default",
        actor_id="api-l1-owner",
        actor_type=OrganizationActorType.human,
        authenticated_user_id="api-l1-owner",
        role="admin",
        department="Global Mobility Operations",
        position_key="board",
        authority_level="L4",
    )


def _runtime(provider: str) -> AgentRuntimeProfile:
    return AgentRuntimeProfile(
        profile_key=f"{provider}-api-l1-v1",
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


def _establish_completed_cycle(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    *,
    objective_key: str,
):
    monkeypatch.setattr("app.services.controlled_agents.is_llm_enabled", lambda: False)
    ensure_foundation_positions(db_session, actor="api-l1", repair_contracts=True)
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
    result = synthesize_austria_objective_owner(
        db_session,
        tenant_key="default",
        root_work_item_id=plan.root_work_item.id,
    )
    return plan, result


def test_live_organization_latest_is_board_safe_when_not_established(client: TestClient) -> None:
    response = client.get("/api/v1/organization/transparency/live-organization/austria/latest")
    assert response.status_code == 200
    assert response.json() == {"established": False, "snapshot": None}


def test_board_reads_completed_live_organization_latest_and_exact_snapshot(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, result = _establish_completed_cycle(
        db_session,
        monkeypatch,
        objective_key="at-rwr-shortage-2026-l1-api",
    )

    latest = client.get("/api/v1/organization/transparency/live-organization/austria/latest")
    assert latest.status_code == 200
    latest_body = latest.json()
    assert latest_body["established"] is True
    snapshot = latest_body["snapshot"]
    assert snapshot["root_work_item_id"] == str(plan.root_work_item.id)
    assert snapshot["root_status"] == "completed"
    assert snapshot["cycle_status"] == "completed"
    assert snapshot["owner_synthesis_state"] == "completed"
    assert snapshot["provider_model_authority"] is False
    assert snapshot["external_action_authorized"] is False
    assert len(snapshot["specialist_outputs"]) == 2
    assert all(item["evidence_valid"] for item in snapshot["specialist_outputs"])
    assert snapshot["owner_synthesis"]["action_output_id"] == str(result.action_output_id)
    assert snapshot["owner_synthesis"]["activity_id"] == str(result.activity_id)

    exact = client.get(
        f"/api/v1/organization/transparency/live-organization/austria/{plan.root_work_item.id}"
    )
    assert exact.status_code == 200
    exact_body = exact.json()
    assert exact_body["root_work_item_id"] == str(plan.root_work_item.id)
    assert exact_body["owner_synthesis"]["action_output_id"] == str(result.action_output_id)
    assert exact_body["domain_evidence_refs"] == []
    assert exact_body["verified_rule_refs"] == []
    assert exact_body["autonomy_profile_state"] is None


def test_live_organization_transparency_requires_board_role(
    raw_client: TestClient,
) -> None:
    raw_client.headers.update({
        "X-GMAI-Role": "operator",
        "X-GMAI-User": "pytest-operator",
    })
    response = raw_client.get("/api/v1/organization/transparency/live-organization/austria/latest")
    assert response.status_code == 403


def test_live_organization_exact_snapshot_missing_root_is_non_disclosing_404(
    client: TestClient,
) -> None:
    response = client.get(
        f"/api/v1/organization/transparency/live-organization/austria/{uuid4()}"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Organization transparency resource not found."


def test_live_organization_http_projection_fails_closed_on_tampered_owner_lineage(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, _ = _establish_completed_cycle(
        db_session,
        monkeypatch,
        objective_key="at-rwr-shortage-2026-l1-api-tamper",
    )
    output = db_session.exec(
        select(OrganizationalActionOutput).where(
            OrganizationalActionOutput.output_key
            == austria_owner_synthesis_output_key(plan.root_work_item.id)
        )
    ).one()
    payload = json.loads(output.output_json)
    payload["provider_model_authority"] = True
    output.output_json = json.dumps(payload, sort_keys=True)
    db_session.add(output)
    db_session.commit()

    response = client.get(
        f"/api/v1/organization/transparency/live-organization/austria/{plan.root_work_item.id}"
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Live organization transparency data is inconsistent."
