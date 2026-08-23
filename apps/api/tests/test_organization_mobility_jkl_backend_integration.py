from __future__ import annotations

import json
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    AgentRun,
    OrganizationActivity,
    OrganizationExecutionAttempt,
    OrganizationalActionOutput,
    OrganizationalWorkItem,
)
from app.services.organization_governance import ensure_foundation_positions
from app.services.organization_mobility_live_organization import (
    austria_owner_synthesis_activity_key,
    austria_owner_synthesis_output_key,
)
from app.services.organization_mobility_objective_execution import execute_austria_specialists
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_SPECIALIST_POSITIONS,
    austria_specialist_output_key,
    create_austria_mobility_objective,
)
from tests.test_organization_mobility_context_provenance import (
    _authority_graph,
    _force_deterministic,
    _human_context,
    _profiles,
    _reference_payload,
)


def test_grounded_j_k_l_backend_vertical_persists_exact_lineage_across_fresh_session(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prove the real grounded J -> K -> L backend path without API response mocking.

    Deterministic specialist execution is intentional here: this is a backend integration
    and durable-lineage proof, not a live-provider quality claim.
    """

    ensure_foundation_positions(db_session, actor="pytest-jkl-integration", repair_contracts=True)
    _force_deterministic(monkeypatch)
    graph = _authority_graph(db_session)
    pathway_version = graph["pathway_version"]
    context = _human_context()

    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key="at-rwr-shortage-2026-grounded-jkl-backend-integration",
        pathway_version_id=pathway_version.id,
    )
    specialist_results = execute_austria_specialists(
        db_session,
        context,
        plan,
        runtime_profiles=_profiles(),
    )

    assert len(specialist_results) == len(AUSTRIA_MOBILITY_SPECIALIST_POSITIONS)
    assert all(result.replayed is False for result in specialist_results)

    command_path = (
        f"/api/v1/organization/live-organization/austria/"
        f"{plan.root_work_item.id}/owner-synthesis"
    )
    first_owner = client.post(command_path)
    assert first_owner.status_code == 200
    first_owner_body = first_owner.json()
    assert first_owner_body["root_work_item_id"] == str(plan.root_work_item.id)
    assert first_owner_body["replayed"] is False

    expected_evidence = _reference_payload(
        "mobility_pathway_version_evidence",
        graph["evidence"],
    )
    expected_rules = _reference_payload("verified_rule", graph["rule"])
    expected_snapshots = _reference_payload("source_snapshot", graph["snapshot"])
    expected_evidence_tokens = [
        f"{item['kind']}:{item['identifier']}@{item['version']}"
        for item in expected_evidence
    ]
    expected_rule_tokens = [
        f"{item['kind']}:{item['identifier']}@{item['version']}"
        for item in expected_rules
    ]

    engine = db_session.get_bind()
    with Session(engine) as verification_session:
        root = verification_session.get(OrganizationalWorkItem, plan.root_work_item.id)
        assert root is not None
        assert root.status == "completed"

        child_rows = verification_session.exec(
            select(OrganizationalWorkItem).where(
                OrganizationalWorkItem.parent_work_item_id == root.id
            )
        ).all()
        assert len(child_rows) == len(AUSTRIA_MOBILITY_SPECIALIST_POSITIONS)
        assert {row.assigned_position_key for row in child_rows} == set(
            AUSTRIA_MOBILITY_SPECIALIST_POSITIONS
        )
        assert all(row.status == "completed" for row in child_rows)
        assert all(row.source_object_type == "mobility_pathway_version" for row in child_rows)
        assert all(row.source_object_id == str(pathway_version.id) for row in child_rows)
        assert all(
            row.source_object_version == str(pathway_version.version_number)
            for row in child_rows
        )

        for result in specialist_results:
            work = verification_session.get(OrganizationalWorkItem, result.work_item_id)
            attempt = verification_session.get(
                OrganizationExecutionAttempt,
                result.execution_attempt_id,
            )
            run = verification_session.get(AgentRun, result.agent_run_id)
            output = verification_session.get(
                OrganizationalActionOutput,
                result.action_output_id,
            )
            assert work is not None
            assert attempt is not None
            assert run is not None
            assert output is not None

            assert work.parent_work_item_id == root.id
            assert work.assigned_position_key == result.position_key
            assert work.status == "completed"
            assert attempt.work_item_id == work.id
            assert attempt.status == "completed"
            assert output.work_item_id == work.id
            assert output.output_key == austria_specialist_output_key(work.id)
            assert output.accountable_position_key == result.position_key

            payload = json.loads(output.output_json)
            assert UUID(payload["execution_attempt_id"]) == attempt.id
            assert UUID(payload["agent_run_id"]) == run.id
            assert payload["execution_token"] == attempt.execution_token
            assert payload["context_hash"] == result.context_hash
            assert payload["runtime_binding_hash"] == result.runtime_binding_hash
            assert payload["context_evidence_refs"] == expected_evidence
            assert payload["context_verified_rule_refs"] == expected_rules
            assert payload["context_source_snapshot_refs"] == expected_snapshots
            assert payload["provider_model_authority"] is False

            impact = json.loads(output.impact_json)
            assert impact["external_action_authorized"] is False
            assert impact["human_review_required"] is True

            run_input = json.loads(run.input_json)
            provenance = run_input["context"]["k1_provenance"]
            assert provenance["execution_attempt_id"] == str(attempt.id)
            assert provenance["execution_token"] == attempt.execution_token
            assert provenance["context_hash"] == result.context_hash
            assert provenance["context_evidence_refs"] == expected_evidence
            assert provenance["context_verified_rule_refs"] == expected_rules
            assert provenance["context_source_snapshot_refs"] == expected_snapshots
            assert provenance["provider_model_authority"] is False

        owner_output_key = austria_owner_synthesis_output_key(root.id)
        owner_activity_key = austria_owner_synthesis_activity_key(root.id)
        owner_outputs = verification_session.exec(
            select(OrganizationalActionOutput).where(
                OrganizationalActionOutput.output_key == owner_output_key
            )
        ).all()
        owner_activities = verification_session.exec(
            select(OrganizationActivity).where(
                OrganizationActivity.activity_key == owner_activity_key
            )
        ).all()
        assert len(owner_outputs) == 1
        assert len(owner_activities) == 1
        assert str(owner_outputs[0].id) == first_owner_body["action_output_id"]
        assert str(owner_activities[0].id) == first_owner_body["activity_id"]

    projection = client.get(
        f"/api/v1/organization/transparency/live-organization/austria/"
        f"{plan.root_work_item.id}"
    )
    assert projection.status_code == 200
    projection_body = projection.json()
    assert projection_body["root_status"] == "completed"
    assert projection_body["cycle_status"] == "completed"
    assert projection_body["owner_synthesis_state"] == "completed"
    assert projection_body["external_action_authorized"] is False
    assert projection_body["provider_model_authority"] is False
    assert projection_body["domain_evidence_refs"] == expected_evidence_tokens
    assert projection_body["verified_rule_refs"] == expected_rule_tokens
    assert len(projection_body["specialist_outputs"]) == len(
        AUSTRIA_MOBILITY_SPECIALIST_POSITIONS
    )
    assert all(
        specialist["evidence_valid"] is True
        and specialist["external_action_authorized"] is False
        and specialist["provider_model_authority"] is False
        for specialist in projection_body["specialist_outputs"]
    )
    assert projection_body["owner_synthesis"]["action_output_id"] == first_owner_body[
        "action_output_id"
    ]
    assert projection_body["owner_synthesis"]["activity_id"] == first_owner_body[
        "activity_id"
    ]

    replay = client.post(command_path)
    assert replay.status_code == 200
    replay_body = replay.json()
    assert replay_body["replayed"] is True
    assert replay_body["action_output_id"] == first_owner_body["action_output_id"]
    assert replay_body["activity_id"] == first_owner_body["activity_id"]

    with Session(engine) as replay_verification_session:
        assert len(
            replay_verification_session.exec(
                select(OrganizationalActionOutput).where(
                    OrganizationalActionOutput.output_key
                    == austria_owner_synthesis_output_key(plan.root_work_item.id)
                )
            ).all()
        ) == 1
        assert len(
            replay_verification_session.exec(
                select(OrganizationActivity).where(
                    OrganizationActivity.activity_key
                    == austria_owner_synthesis_activity_key(plan.root_work_item.id)
                )
            ).all()
        ) == 1
