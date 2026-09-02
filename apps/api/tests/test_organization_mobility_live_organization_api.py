from __future__ import annotations

import json
from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    OrganizationActorType,
    OrganizationBlockerType,
    OrganizationalActionOutput,
    RiskEscalation,
    now_utc,
)
from app.services.organization_activity import establish_activity_coverage_epoch
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
from app.services.organization_conversation import open_conversation
from app.services.organization_decision import (
    create_executive_decision,
    record_executive_decision_outcome,
    supersede_executive_decision,
)
from app.services.organization_human_action import create_human_action_request
from app.services.organization_work import assign_work_item, open_blocker


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
    seed_m5: bool = False,
):
    monkeypatch.setattr("app.services.controlled_agents.is_llm_enabled", lambda: False)
    ensure_foundation_positions(db_session, actor="api-l1", repair_contracts=True)
    plan = create_austria_mobility_objective(
        db_session,
        _human_context(),
        objective_key=objective_key,
    )
    if seed_m5:
        open_conversation(
            db_session,
            _human_context(),
            conversation_id=f"conversation:{plan.pathway_work_item.id}",
            work_item_id=plan.pathway_work_item.id,
            participant_position_keys=(
                plan.pathway_work_item.assigned_position_key,
                plan.root_work_item.assigned_position_key,
            ),
            summary="Coordinate pathway evidence before owner synthesis.",
            occurred_at=now_utc(),
        )
        original_position_key = plan.pathway_work_item.assigned_position_key
        assign_work_item(
            db_session,
            _human_context(),
            work_item_id=plan.pathway_work_item.id,
            assigned_position_key=plan.root_work_item.assigned_position_key,
            reason="Exercise a real governed M.5 handoff.",
        )
        assign_work_item(
            db_session,
            _human_context(),
            work_item_id=plan.pathway_work_item.id,
            assigned_position_key=original_position_key,
            reason="Return governed work to its execution position.",
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

    scene = client.get("/api/v1/organization/transparency/live-organization/scene/austria/latest")
    assert scene.status_code == 200
    assert scene.json() == {"established": False, "scene": None}


def test_m8_replay_is_board_safe_coverage_bounded_and_never_backfilled(
    client: TestClient,
    raw_client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    epoch = establish_activity_coverage_epoch(
        db_session,
        _human_context(),
        reason="Establish semantic history coverage before the bounded M.8 acceptance cycle.",
    )
    plan, _ = _establish_completed_cycle(
        db_session,
        monkeypatch,
        objective_key="at-rwr-shortage-2026-m8-replay",
        seed_m5=True,
    )

    response = client.get(
        "/api/v1/organization/transparency/live-organization/replay/austria/latest"
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["established"] is True
    replay = body["replay"]
    assert replay["contract_version"] == "organization-replay.v1"
    assert replay["root_work_item_id"] == str(plan.root_work_item.id)
    assert replay["objective_key"] == plan.root_work_item.objective_key
    assert set(replay["work_item_ids"]) == {
        str(plan.root_work_item.id),
        str(plan.pathway_work_item.id),
        str(plan.regulatory_work_item.id),
    }
    assert replay["canonical_projection"] is True
    assert replay["authoritative"] is False
    assert replay["mutations_allowed"] is False
    assert replay["coverage"]["activity_history_basis"] == "explicit_activity_coverage_epoch"
    assert replay["coverage"]["activity_history_established"] is True
    assert replay["coverage"]["activity_history_coverage_start"] == epoch.occurred_at.isoformat().replace("+00:00", "Z")
    assert replay["coverage"]["pre_epoch_history"] == "partial_no_backfill"
    assert replay["coverage"]["risk_escalation_history"] == "unavailable_no_semantic_activity_adapter"
    assert replay["coverage"]["source_snapshot_history"] == "unavailable_not_linked_to_replay_activity"
    assert replay["coverage"]["conversation_history"] == "lifecycle_only_transcript_not_persisted"
    assert replay["total_events"] == replay["returned_events"]
    assert replay["truncated"] is False
    assert replay["events"]
    assert all(event["coverage_state"] == "covered" for event in replay["events"])
    assert all("payload" not in event for event in replay["events"])
    assert [event["occurred_at"] for event in replay["events"]] == sorted(
        event["occurred_at"] for event in replay["events"]
    )
    event_types = {event["activity_type"] for event in replay["events"]}
    assert "organization.work.created.v1" in event_types
    assert "organization.conversation.opened.v1" in event_types
    assert "organization.work.assigned.v1" in event_types
    assert any(event["event_kind"] == "handoff" for event in replay["events"])
    assert any(event["event_kind"] == "conversation" for event in replay["events"])
    # Direct authenticated-human transitions need not have a governance causation
    # Activity. Replay must preserve that absence rather than manufacture lineage.
    assert all("causation_activity_id" in event for event in replay["events"])

    raw_client.headers.update({
        "X-GMAI-Role": "operator",
        "X-GMAI-User": "m8-operator",
    })
    denied = raw_client.get(
        "/api/v1/organization/transparency/live-organization/replay/austria/latest"
    )
    assert denied.status_code == 403


def test_board_reads_completed_live_organization_latest_and_exact_snapshot(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, result = _establish_completed_cycle(
        db_session,
        monkeypatch,
        objective_key="at-rwr-shortage-2026-l1-api",
        seed_m5=True,
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
    assert exact_body["source_snapshot_refs"] == []
    assert exact_body["autonomy_profile_state"] is None

    decision = client.post(
        "/api/v1/organization/decisions/records",
        json={
            "decision_key": "m3-scene-board-decision",
            "decision_type": "board_reserved",
            "title": "Board review for scene foundation",
            "question": "Should the bounded internal recommendation advance to Board review?",
            "recommendation": "Inspect canonical evidence before any external action.",
            "work_item_id": str(plan.root_work_item.id),
            "evidence": [{"kind": "scene-test"}],
        },
    )
    assert decision.status_code == 201, decision.text

    historical_decision = create_executive_decision(
        db_session,
        _human_context(),
        decision_key="m7-historical-decision",
        decision_type="operational",
        authority_level="L2",
        requested_by_position="mobility_operations_lead",
        decision_owner_position="ceo",
        title="Historical Austria routing decision",
        question="Should the earlier bounded routing recommendation be retained?",
        recommendation="Retain until a governed successor is recorded.",
        work_item_id=plan.root_work_item.id,
    )
    record_executive_decision_outcome(
        db_session,
        _human_context(),
        decision_id=historical_decision.id,
        outcome="approved",
        reason="Settle the historical decision so supersession can be proven.",
    )
    successor_decision = supersede_executive_decision(
        db_session,
        _human_context(),
        original_decision_id=historical_decision.id,
        new_decision_key="m7-historical-decision-v2",
        title="Updated Austria routing decision",
        question="Should the updated bounded routing recommendation replace the settled version?",
        recommendation="Use the governed successor while preserving historical lineage.",
        reason="M.7.3 acceptance proves bounded supersession timing.",
    )
    assert successor_decision.authority_level == "L2"
    assert successor_decision.decision_owner_position == "ceo"

    blocker = open_blocker(
        db_session,
        _human_context(),
        blocker_key="m6-shared-friction",
        blocker_type=OrganizationBlockerType.human_input,
        severity="high",
        title="Missing employer declaration",
        description="Canonical employer declaration evidence is required before the next governed step.",
        work_item_id=plan.pathway_work_item.id,
        department=plan.pathway_work_item.department,
        accountable_position_key=plan.pathway_work_item.assigned_position_key,
        authority_level=plan.pathway_work_item.authority_level,
        requires_human_action=True,
    )
    blocker.opened_at = blocker.opened_at - timedelta(minutes=25)
    db_session.add(blocker)
    db_session.commit()
    db_session.refresh(blocker)

    human_request = create_human_action_request(
        db_session,
        _human_context(),
        request_key="m6-owner-inbox-review",
        request_type="review",
        title="Review missing employer declaration",
        instructions="Inspect the blocker evidence and provide the required declaration or governed disposition.",
        required_role="board",
        priority="high",
        authority_level="L4",
        work_item_id=plan.pathway_work_item.id,
        blocker_id=blocker.id,
    )
    risk = RiskEscalation(
        risk_key="m6-board-risk",
        work_item_id=plan.root_work_item.id,
        category="evidence",
        severity="high",
        title="Evidence gap requires Board visibility",
        description="The canonical blocker remains unresolved and is visible to the Board.",
        evidence_json='[{"kind":"m6-risk-proof"}]',
        accountable_position_key=plan.root_work_item.assigned_position_key,
        escalated_to_position_key="board",
        status="open",
        requires_board_attention=True,
        is_emergency=False,
    )
    db_session.add(risk)
    db_session.commit()
    db_session.refresh(risk)

    scene = client.get("/api/v1/organization/transparency/live-organization/scene/austria/latest")
    assert scene.status_code == 200, scene.text
    scene_body = scene.json()
    assert scene_body["established"] is True
    projection = scene_body["scene"]
    assert projection["contract_version"] == "living-organization-scene.v5"
    assert projection["root_work_item_id"] == str(plan.root_work_item.id)
    assert projection["objective_key"] == plan.root_work_item.objective_key
    assert projection["coverage"] == {
        "departments": "projected_from_canonical_positions_and_work",
        "missions": "workitem_objective_topology_projection",
        "conversations": "organization_activity_conversation_lifecycle_v1",
        "handoffs": "organization_work_assigned_activity_v1",
        "blockers": "organization_blocker_canonical_records",
        "human_actions": "organization_human_action_request_open_records",
        "risk_escalations": "risk_escalation_open_records",
        "incidents": "unavailable_no_canonical_incident_model",
        "smart_objects": "m6_read_only_canonical_projections",
        "runtime_costs": "unavailable_no_canonical_organization_cost_ledger",
        "presence": "not_asserted_m6",
    }

    deterministic = projection["deterministic"]
    assert deterministic["canonical_projection"] is True
    assert deterministic["authoritative"] is False
    expected_department_counts: dict[str, int] = {}
    for work_item in (
        plan.root_work_item,
        plan.pathway_work_item,
        plan.regulatory_work_item,
    ):
        expected_department_counts[work_item.department] = (
            expected_department_counts.get(work_item.department, 0) + 1
        )

    departments_by_key = {
        item["department_key"]: item for item in deterministic["departments"]
    }
    assert set(departments_by_key) == set(expected_department_counts)
    assert sum(item["employee_count"] for item in deterministic["departments"]) == 3
    assert sum(item["work_item_count"] for item in deterministic["departments"]) == 3
    assert sum(item["active_blocker_count"] for item in deterministic["departments"]) == 1
    for department_key, expected_count in expected_department_counts.items():
        department = departments_by_key[department_key]
        assert department["employee_count"] == expected_count
        assert department["work_item_count"] == expected_count
        assert (
            department["canonical_basis"]
            == "OrganizationPosition.department + OrganizationalWorkItem.department"
        )

    assert len(deterministic["missions"]) == 1
    mission = deterministic["missions"][0]
    assert mission["root_work_item_id"] == str(plan.root_work_item.id)
    assert mission["objective_key"] == plan.root_work_item.objective_key
    assert len(mission["participant_position_keys"]) == 3
    assert len(mission["work_item_ids"]) == 3
    assert mission["projection_only"] is True

    assert len(deterministic["employees"]) == 3
    assert len(deterministic["work_items"]) == 3
    work_by_id = {item["work_item_id"]: item for item in deterministic["work_items"]}
    root_work = work_by_id[str(plan.root_work_item.id)]
    assert root_work["created_at"] is not None
    assert root_work["updated_at"] is not None
    assert root_work["elapsed_seconds"] is None or root_work["elapsed_seconds"] >= 0
    assert isinstance(root_work["overdue"], bool)
    assert root_work["specialist_evidence_valid"] is None
    assert root_work["specialist_evidence_reason"] is None
    specialist_work = [
        item for item in deterministic["work_items"]
        if item["work_item_id"] != str(plan.root_work_item.id)
    ]
    assert specialist_work
    assert all(item["specialist_evidence_valid"] is True for item in specialist_work)
    assert all(item["specialist_evidence_reason"] is None for item in specialist_work)
    assert len(deterministic["conversations"]) == 1
    conversation = deterministic["conversations"][0]
    assert conversation["status"] == "open"
    assert conversation["participant_position_keys"] == [
        plan.pathway_work_item.assigned_position_key,
        plan.root_work_item.assigned_position_key,
    ]
    assert conversation["authority_effect"] == "none"
    assert conversation["transcript_persisted"] is False
    assert conversation["opened_activity_id"] == conversation["latest_activity_id"]
    assert len(deterministic["handoffs"]) == 2
    assert all(
        item["canonical_basis"] == "organization.work.assigned.v1 OrganizationActivity"
        for item in deterministic["handoffs"]
    )
    assert deterministic["incidents"] == []
    assert {item["presence_state"] for item in deterministic["employees"]} == {"not_asserted"}
    assert deterministic["blockers"][0]["blocker_id"] == str(blocker.id)
    assert deterministic["blockers"][0]["blocker_type"] == "human_input"
    assert deterministic["blockers"][0]["description"].startswith("Canonical employer declaration")
    assert deterministic["blockers"][0]["opened_at"] is not None
    assert deterministic["blockers"][0]["open_elapsed_seconds"] >= 20 * 60
    assert isinstance(deterministic["blockers"][0]["overdue"], bool)
    assert deterministic["human_actions"][0]["request_id"] == str(human_request.id)
    assert deterministic["human_actions"][0]["status"] == "required"
    assert deterministic["risk_escalations"][0]["risk_id"] == str(risk.id)
    assert deterministic["risk_escalations"][0]["requires_board_attention"] is True
    assert {item["object_type"] for item in deterministic["smart_objects"]} == {
        "mission_board",
        "evidence_shelf",
        "regulatory_monitor",
        "blocker_wall",
        "board_desk",
        "owner_inbox",
        "risk_beacon",
        "immune_center",
        "model_terminal",
        "incident_beacon",
        "cost_display",
    }
    regulatory = next(
        item for item in deterministic["smart_objects"] if item["object_type"] == "regulatory_monitor"
    )
    immune = next(
        item for item in deterministic["smart_objects"] if item["object_type"] == "immune_center"
    )
    model_terminal = next(
        item for item in deterministic["smart_objects"] if item["object_type"] == "model_terminal"
    )
    incident = next(
        item for item in deterministic["smart_objects"] if item["object_type"] == "incident_beacon"
    )
    cost = next(
        item for item in deterministic["smart_objects"] if item["object_type"] == "cost_display"
    )
    assert regulatory["state"] == "no_snapshot_provenance"
    assert regulatory["metric_value"] == 0
    assert immune["state"] == "unavailable" and immune["metric_value"] is None
    assert model_terminal["metric_value"] >= 0
    assert "no organizational authority" in model_terminal["canonical_basis"]
    assert incident["state"] == "unavailable" and incident["metric_value"] is None
    assert cost["state"] == "unavailable" and cost["metric_value"] is None
    assert {item["room_type"] for item in deterministic["rooms"]} == {
        "mission_room",
        "evidence_lab",
        "board_room",
    }
    board_room = next(item for item in deterministic["rooms"] if item["room_type"] == "board_room")
    assert board_room["state"] == "attention"
    assert board_room["metric_value"] == 3
    assert any(item["relationship_type"] == "assigned_to" for item in deterministic["relationships"])
    assert any(item["relationship_type"] == "belongs_to" for item in deterministic["relationships"])
    assert any(
        item["relationship_type"] == "participates_in_conversation"
        for item in deterministic["relationships"]
    )
    assert any(
        item["relationship_type"] == "governed_handoff"
        for item in deterministic["relationships"]
    )
    decisions_by_key = {
        item["decision_key"]: item for item in deterministic["decisions"]
    }
    scene_decision = decisions_by_key["m3-scene-board-decision"]
    assert scene_decision["decision_id"] == decision.json()["id"]
    assert scene_decision["is_current"] is True
    assert scene_decision["required_owner_action"] is True
    assert scene_decision["evidence_items"] == [{"kind": "scene-test"}]
    historical_projection = decisions_by_key["m7-historical-decision"]
    successor_projection = decisions_by_key["m7-historical-decision-v2"]
    assert historical_projection["is_current"] is False
    assert historical_projection["superseded_by_decision_id"] == successor_projection["decision_id"]
    assert historical_projection["created_at"] is not None
    assert historical_projection["superseded_by_created_at"] == successor_projection["created_at"]
    assert historical_projection["superseded_in_projection_week"] is True
    assert successor_projection["supersedes_decision_id"] == historical_projection["decision_id"]
    assert any(
        item["relationship_type"] == "requires_human_action"
        for item in deterministic["relationships"]
    )
    assert any(
        item["relationship_type"] == "escalates_risk"
        for item in deterministic["relationships"]
    )

    assert projection["predictive"] == {
        "enabled": False,
        "canonical_projection": False,
        "authoritative": False,
        "status": "reserved_for_m9_phantom_futures",
        "items": [],
    }
    assert projection["environmental"] == {
        "enabled": False,
        "canonical_projection": False,
        "authoritative": False,
        "status": "reserved_for_m9_environmental_memory",
        "items": [],
    }
    assert projection["truth"]["canonical_authority"] == "AIOS canonical records and accepted projections"
    assert projection["truth"]["scene_authoritative"] is False
    assert projection["truth"]["renderer_authoritative"] is False
    assert projection["truth"]["prediction_authoritative"] is False
    assert projection["truth"]["environmental_authoritative"] is False
    assert projection["truth"]["scene_mutations_allowed"] is False


def test_live_organization_transparency_requires_board_role(
    raw_client: TestClient,
) -> None:
    raw_client.headers.update({
        "X-GMAI-Role": "operator",
        "X-GMAI-User": "pytest-operator",
    })
    response = raw_client.get("/api/v1/organization/transparency/live-organization/austria/latest")
    assert response.status_code == 403
    scene = raw_client.get("/api/v1/organization/transparency/live-organization/scene/austria/latest")
    assert scene.status_code == 403
    replay = raw_client.get("/api/v1/organization/transparency/live-organization/replay/austria/latest")
    assert replay.status_code == 403


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
