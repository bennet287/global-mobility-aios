"""Reproducibility proof for future learned-skill candidate generation."""

import json
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    AgentRun,
    OrganizationExecutionAttempt,
    OrganizationalActionOutput,
    OrganizationalWorkItem,
    now_utc,
)
from app.models.skill_registry import OrganizationSkill
from app.services.organization_learning_reproducibility import (
    evaluate_learned_procedure_reproducibility,
)
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_PATHWAY_POSITION,
    AUSTRIA_MOBILITY_SPECIALIST_AGENT_NAMES,
    AUSTRIA_MOBILITY_SPECIALIST_EXECUTION_CONTRACT_VERSION,
    austria_completed_work_fingerprint,
    austria_specialist_output_key,
)


BASE = "/api/v1/organization/decisions/records"


def _lineage(
    session: Session,
    *,
    phase_key: str = "J.1.pathway",
    provider_key: str = "provider-a",
    model_key: str = "model-a",
    allowed_tools: tuple[str, ...] = (),
):
    root = OrganizationalWorkItem(
        idempotency_key=f"repro-root:{uuid4()}",
        work_type="mobility_objective",
        objective_key=f"repro-objective:{uuid4()}",
        phase_key="J.1",
        title="Internal objective",
        objective="Analyze Austria pathway",
        department="operations",
        authority_level="L1",
        assigned_position_key="mobility_operations_lead",
        status="running",
    )
    child = OrganizationalWorkItem(
        idempotency_key=f"repro-child:{uuid4()}",
        parent_work_item_id=root.id,
        work_type="mobility_specialist_work",
        objective_key=root.objective_key,
        phase_key=phase_key,
        title="Internal specialist analysis",
        objective="Analyze Austria pathway",
        department="operations",
        authority_level="L1",
        assigned_position_key=AUSTRIA_MOBILITY_PATHWAY_POSITION,
        status="completed",
        completed_at=now_utc(),
    )
    attempt = OrganizationExecutionAttempt(
        attempt_key=f"repro-attempt:{child.id}",
        work_item_id=child.id,
        attempt_number=1,
        execution_token=f"repro-token:{uuid4()}",
        status="completed",
        completed_at=now_utc(),
    )
    context_hash = f"context:{uuid4()}"
    runtime_binding_hash = f"runtime:{uuid4()}"
    run = AgentRun(
        agent_name=AUSTRIA_MOBILITY_SPECIALIST_AGENT_NAMES[AUSTRIA_MOBILITY_PATHWAY_POSITION],
        task="Internal analysis",
        status="pending_review",
        input_json=json.dumps(
            {
                "context": {
                    "k1_provenance": {
                        "work_item_id": str(child.id),
                        "position_key": AUSTRIA_MOBILITY_PATHWAY_POSITION,
                        "context_hash": context_hash,
                        "runtime_binding_hash": runtime_binding_hash,
                        "provider_key": provider_key,
                        "model_key": model_key,
                        "allowed_tools": list(allowed_tools),
                    }
                }
            }
        ),
    )
    payload = {
        "contract_version": AUSTRIA_MOBILITY_SPECIALIST_EXECUTION_CONTRACT_VERSION,
        "root_work_item_id": str(root.id),
        "work_item_id": str(child.id),
        "position_key": AUSTRIA_MOBILITY_PATHWAY_POSITION,
        "completed_work_fingerprint": austria_completed_work_fingerprint(child),
        "agent_name": run.agent_name,
        "agent_run_id": str(run.id),
        "execution_attempt_id": str(attempt.id),
        "execution_token": attempt.execution_token,
        "context_hash": context_hash,
        "runtime_binding_hash": runtime_binding_hash,
        "provider_key": provider_key,
        "model_key": model_key,
        "allowed_tools": list(allowed_tools),
    }
    output = OrganizationalActionOutput(
        output_key=austria_specialist_output_key(child.id),
        work_item_id=child.id,
        accountable_position_key=AUSTRIA_MOBILITY_PATHWAY_POSITION,
        authority_basis="Bounded internal analysis",
        confidence_basis="Human review required",
        rollback_posture="Discard internal output",
        status="completed",
        output_json=json.dumps(payload, sort_keys=True),
        impact_json='{"external_action_authorized":false,"client_facing":false}',
    )
    session.add_all([root, child, attempt, run, output])
    session.commit()
    return root, child, output


def _accept(client: TestClient, child: OrganizationalWorkItem, output: OrganizationalActionOutput):
    created = client.post(
        BASE,
        json={
            "decision_key": f"repro-review:{uuid4()}",
            "decision_type": "operational",
            "title": "Review internal analysis",
            "question": "Accept this analysis?",
            "recommendation": "Accept after review",
            "work_item_id": str(child.id),
        },
    )
    assert created.status_code == 201, created.text
    accepted = client.post(
        f"{BASE}/{created.json()['id']}/outcome",
        json={
            "outcome": "approved",
            "reason": "The owner reviewed this exact internal analysis.",
            "accepted_action_output_id": str(output.id),
        },
    )
    assert accepted.status_code == 200, accepted.text
    return accepted


def test_two_independent_human_accepted_k1_runs_satisfy_reproducibility_without_creating_skill(
    client: TestClient,
    db_session: Session,
) -> None:
    skills_before = list(db_session.exec(select(OrganizationSkill)).all())

    root_a, child_a, output_a = _lineage(
        db_session,
        provider_key="provider-a",
        model_key="model-a",
        allowed_tools=("browser",),
    )
    _accept(client, child_a, output_a)

    root_b, child_b, output_b = _lineage(
        db_session,
        provider_key="provider-b",
        model_key="model-b",
        allowed_tools=("shell", "browser"),
    )
    _accept(client, child_b, output_b)

    proofs = evaluate_learned_procedure_reproducibility(
        db_session,
        tenant_key="default",
        position_key=AUSTRIA_MOBILITY_PATHWAY_POSITION,
    )

    assert len(proofs) == 1
    proof = proofs[0]
    assert proof.contract_version == AUSTRIA_MOBILITY_SPECIALIST_EXECUTION_CONTRACT_VERSION
    assert proof.position_key == AUSTRIA_MOBILITY_PATHWAY_POSITION
    assert proof.phase_key == "J.1.pathway"
    assert proof.work_type == "mobility_specialist_work"
    assert proof.agent_name == AUSTRIA_MOBILITY_SPECIALIST_AGENT_NAMES[AUSTRIA_MOBILITY_PATHWAY_POSITION]
    assert proof.independent_support_count == 2
    assert proof.required_independent_supports == 2
    assert proof.reproducibility_requirement_satisfied is True
    assert proof.reasons == ()
    assert {support.root_work_item_id for support in proof.supports} == {root_a.id, root_b.id}
    assert {support.work_item_id for support in proof.supports} == {child_a.id, child_b.id}
    assert {support.action_output_id for support in proof.supports} == {output_a.id, output_b.id}

    # Technical routing and allowed-tool entitlement differ, but neither defines the procedure.
    assert json.loads(output_a.output_json)["provider_key"] != json.loads(output_b.output_json)["provider_key"]
    assert json.loads(output_a.output_json)["allowed_tools"] != json.loads(output_b.output_json)["allowed_tools"]

    # This slice is proof-only: it must not create, validate, activate or bind a learned skill.
    assert list(db_session.exec(select(OrganizationSkill)).all()) == skills_before


def test_reacceptance_is_not_an_independent_sample_and_phase_drift_forms_separate_procedure(
    client: TestClient,
    db_session: Session,
) -> None:
    _, child, output = _lineage(db_session)
    _accept(client, child, output)
    _accept(client, child, output)

    _, drift_child, drift_output = _lineage(db_session, phase_key="J.1.experimental")
    _accept(client, drift_child, drift_output)

    # A completed execution without explicit human acceptance is not support.
    _lineage(db_session)

    proofs = evaluate_learned_procedure_reproducibility(
        db_session,
        tenant_key="default",
        position_key=AUSTRIA_MOBILITY_PATHWAY_POSITION,
    )

    assert {proof.phase_key for proof in proofs} == {"J.1.pathway", "J.1.experimental"}
    assert all(proof.independent_support_count == 1 for proof in proofs)
    assert all(proof.reproducibility_requirement_satisfied is False for proof in proofs)
    assert all(proof.reasons == ("insufficient_independent_human_accepted_executions",) for proof in proofs)


def test_reproducibility_gate_requires_at_least_two_independent_supports(db_session: Session) -> None:
    try:
        evaluate_learned_procedure_reproducibility(
            db_session,
            tenant_key="default",
            position_key=AUSTRIA_MOBILITY_PATHWAY_POSITION,
            required_independent_supports=1,
        )
    except ValueError as exc:
        assert "at least two" in str(exc)
    else:
        raise AssertionError("single-run learned-procedure reproducibility must remain fail-closed")
