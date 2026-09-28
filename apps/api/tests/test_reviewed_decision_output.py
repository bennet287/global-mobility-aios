"""Explicit human acceptance of one bounded K.1 internal execution output."""

import hashlib
import json
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    AgentRun, OrganizationContribution, OrganizationExecutionAttempt,
    OrganizationalActionOutput, OrganizationalWorkItem, now_utc,
)
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_PATHWAY_POSITION, AUSTRIA_MOBILITY_SPECIALIST_AGENT_NAMES,
    AUSTRIA_MOBILITY_SPECIALIST_EXECUTION_CONTRACT_VERSION,
    austria_completed_work_fingerprint, austria_specialist_output_key,
)


BASE = "/api/v1/organization/decisions/records"


def _lineage(session: Session):
    root = OrganizationalWorkItem(
        idempotency_key=f"review-root:{uuid4()}", work_type="mobility_objective",
        title="Internal objective", objective="Analyze Austria pathway", department="operations",
        authority_level="L1", assigned_position_key="mobility_operations_lead", status="running",
    )
    child = OrganizationalWorkItem(
        idempotency_key=f"review-child:{uuid4()}", parent_work_item_id=root.id,
        work_type="mobility_specialist_work", objective_key="austria", phase_key="analysis",
        title="Internal specialist analysis", objective="Analyze Austria pathway",
        department="operations", authority_level="L1",
        assigned_position_key=AUSTRIA_MOBILITY_PATHWAY_POSITION,
        status="completed", completed_at=now_utc(),
    )
    attempt = OrganizationExecutionAttempt(
        attempt_key=f"review-attempt:{child.id}", work_item_id=child.id,
        attempt_number=1, execution_token="reviewed-attempt", status="completed",
        completed_at=now_utc(),
    )
    run = AgentRun(
        agent_name=AUSTRIA_MOBILITY_SPECIALIST_AGENT_NAMES[AUSTRIA_MOBILITY_PATHWAY_POSITION],
        task="Internal analysis", status="pending_review",
        input_json=json.dumps({"context": {"k1_provenance": {
            "work_item_id": str(child.id), "position_key": AUSTRIA_MOBILITY_PATHWAY_POSITION,
            "context_hash": "context-1", "runtime_binding_hash": "runtime-1",
        }}}),
    )
    payload = {
        "contract_version": AUSTRIA_MOBILITY_SPECIALIST_EXECUTION_CONTRACT_VERSION,
        "root_work_item_id": str(root.id), "work_item_id": str(child.id),
        "position_key": AUSTRIA_MOBILITY_PATHWAY_POSITION,
        "completed_work_fingerprint": austria_completed_work_fingerprint(child),
        "agent_name": run.agent_name, "agent_run_id": str(run.id),
        "execution_attempt_id": str(attempt.id), "execution_token": attempt.execution_token,
        "context_hash": "context-1", "runtime_binding_hash": "runtime-1",
    }
    output = OrganizationalActionOutput(
        output_key=austria_specialist_output_key(child.id), work_item_id=child.id,
        accountable_position_key=AUSTRIA_MOBILITY_PATHWAY_POSITION,
        authority_basis="Bounded internal analysis", confidence_basis="Human review required",
        rollback_posture="Discard internal output", status="completed",
        output_json=json.dumps(payload),
        impact_json='{"external_action_authorized":false,"client_facing":false}',
    )
    session.add_all([root, child, attempt, run, output])
    session.commit()
    return child, output, run


def _decision(client: TestClient, work_id):
    response = client.post(BASE, json={
        "decision_key": f"reviewed-output:{uuid4()}", "decision_type": "operational",
        "title": "Review internal analysis", "question": "Accept this analysis?",
        "recommendation": "Accept after review", "work_item_id": str(work_id),
    })
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _approve(client: TestClient, decision_id, output_id):
    return client.post(f"{BASE}/{decision_id}/outcome", json={
        "outcome": "approved", "reason": "The owner reviewed this exact internal analysis.",
        "accepted_action_output_id": str(output_id),
    })


def test_explicit_acceptance_is_atomic_linked_and_idempotent(client: TestClient, db_session: Session) -> None:
    child, output, _ = _lineage(db_session)
    decision_id = _decision(client, child.id)
    accepted = _approve(client, decision_id, output.id)
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["accepted_action_output_id"] == str(output.id)
    assert accepted.json()["accepted_action_output_sha256"] == hashlib.sha256(output.output_json.encode()).hexdigest()
    contributions = db_session.exec(select(OrganizationContribution)).all()
    assert len(contributions) == 1
    contribution = contributions[0]
    assert str(contribution.decision_id) == decision_id
    assert contribution.work_item_id == child.id
    assert contribution.source_object_type == "executive_decision"
    assert contribution.contribution_type == "reviewed_internal_analysis_accepted"
    assert json.loads(contribution.evidence_summary_json)[0]["accepted_action_output_id"] == str(output.id)
    assert _approve(client, decision_id, output.id).status_code == 200
    assert len(db_session.exec(select(OrganizationContribution)).all()) == 1
    assert _approve(client, decision_id, uuid4()).status_code == 409


def test_acceptance_rejects_unrelated_stale_and_failed_lineage(client: TestClient, db_session: Session) -> None:
    child, output, run = _lineage(db_session)
    decision_id = _decision(client, child.id)
    assert _approve(client, decision_id, uuid4()).status_code == 409
    run.status = "failed"
    db_session.add(run)
    db_session.commit()
    assert _approve(client, decision_id, output.id).status_code == 409
    run.status = "pending_review"
    child.context_json = '{"changed":true}'
    db_session.add_all([run, child])
    db_session.commit()
    assert _approve(client, decision_id, output.id).status_code == 409
    assert db_session.exec(select(OrganizationContribution)).all() == []


def test_rejection_cannot_accept_output(client: TestClient, db_session: Session) -> None:
    child, output, _ = _lineage(db_session)
    decision_id = _decision(client, child.id)
    response = client.post(f"{BASE}/{decision_id}/outcome", json={
        "outcome": "rejected", "reason": "Not accepted",
        "accepted_action_output_id": str(output.id),
    })
    assert response.status_code == 409
    assert db_session.exec(select(OrganizationContribution)).all() == []
