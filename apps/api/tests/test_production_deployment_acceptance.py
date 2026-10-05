from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, func, select

from app.models.domain import (
    ExecutiveDecision,
    OrganizationActivity,
    OrganizationActorType,
    OrganizationDecisionType,
    OrganizationalWorkItem,
    now_utc,
)
from app.models.production_deployment_acceptance import (
    ProductionDeploymentAcceptanceCheckReceipt,
    ProductionDeploymentAcceptanceRun,
)
from app.services.organization_command import (
    AuthorityDenied,
    IdempotencyConflict,
    InvalidReference,
    InvalidTransition,
    OrganizationCommandContext,
    canonical_json,
)
from app.services.production_deployment_acceptance import (
    CANARY_ENVIRONMENT_CONSTRAINTS,
    DEPLOYMENT_ACCEPTANCE_ACTIVITY_TYPE,
    DEPLOYMENT_ACCEPTANCE_GATES,
    DEPLOYMENT_ACCEPTANCE_SOURCE_TYPE,
    NETWORKING_CONTRACT_KEY,
    NETWORKING_CONTRACT_VERSION,
    TARGET_HOST_FOUNDATION_EXECUTOR_ACTOR,
    TARGET_HOST_RELEASE_NETWORKING_EXECUTOR_ACTOR,
    TARGET_HOST_RELEASE_NETWORKING_EXECUTOR_CONTRACT_KEY,
    TARGET_HOST_RELEASE_NETWORKING_EXECUTOR_CONTRACT_VERSION,
    TARGET_HOST_RELEASE_NETWORKING_VERIFIER_REF,
    _prepared_activity_payload,
    _run_fingerprint,
    deployment_acceptance_receipt_fingerprint,
    networking_contract_fingerprint,
    prepare_deployment_acceptance_run,
    project_deployment_acceptance_run,
    record_target_host_foundation_receipt,
    record_target_host_release_networking_receipt,
)
from app.services.organization_activity import stage_activity



BASE = "/api/v1/production-operations/deployment-acceptance"
RELEASE_SHA = "a" * 40
ROLLBACK_SHA = "b" * 40
RELEASE_CONFIG_FP = "c" * 64
ROLLBACK_CONFIG_FP = "d" * 64
ENVIRONMENT_FP = "e" * 64
VERIFIER_KEY_FP = "f" * 64
NETWORKING_CONTRACT = {
    "web_hostname": "app.globalmobility.example.eu",
    "api_hostname": "api.globalmobility.example.eu",
    "expected_public_ipv4": "8.8.8.8",
    "allowed_public_tcp_ports": [80, 443],
    "external_verifier_public_key_fingerprint": VERIFIER_KEY_FP,
}


def _context(
    *,
    position_key: str = "board",
    role: str = "admin",
    authority_level: str = "L4",
) -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key="default",
        actor_id=f"pytest-{position_key}",
        actor_type=OrganizationActorType.human,
        authenticated_user_id=f"pytest-{position_key}",
        role=role,
        department="executive" if position_key == "board" else "Technology",
        position_key=position_key,
        authority_level=authority_level,
    )


def _work_and_decision(
    session: Session,
    *,
    position_key: str = "board",
    authority_level: str = "L4",
    decision_status: str = "approved",
    source_version: str = RELEASE_SHA,
) -> tuple[OrganizationalWorkItem, ExecutiveDecision]:
    suffix = str(uuid4())
    work = OrganizationalWorkItem(
        idempotency_key=f"phase22-deploy-work-{suffix}",
        tenant_key="default",
        work_type="production_deployment_acceptance",
        objective_key=f"phase22-deploy-{suffix}",
        phase_key="22",
        title="Prepare bounded canary deployment acceptance",
        objective="Pin exact release/environment/rollback identity without claiming deployment.",
        department="Technology",
        authority_level=authority_level,
        assigned_position_key=position_key,
        risk_level="high",
        source_object_type="release_request",
        source_object_id=f"release-request-{suffix}",
        source_object_version=source_version,
        created_by="pytest",
    )
    session.add(work)
    session.commit()
    session.refresh(work)

    decision = ExecutiveDecision(
        decision_key=f"phase22-deploy-decision-{suffix}",
        tenant_key="default",
        decision_type=OrganizationDecisionType.board_reserved,
        work_item_id=work.id,
        source_object_type=work.source_object_type,
        source_object_id=work.source_object_id,
        source_object_version=work.source_object_version,
        authority_level=authority_level,
        requested_by_position="cto",
        decision_owner_position="board",
        title="Admit bounded canary preparation",
        question="May this exact deployment acceptance run be prepared?",
        recommendation="Prepare identity and acceptance contract only; do not deploy.",
        status=decision_status,
        decided_by="pytest-board" if decision_status == "approved" else None,
        decision_reason="Pytest governed deployment preparation." if decision_status == "approved" else None,
    )
    session.add(decision)
    session.commit()
    session.refresh(decision)
    return work, decision


def _prepare(
    session: Session,
    *,
    key: str,
    context: OrganizationCommandContext,
    work: OrganizationalWorkItem,
    decision: ExecutiveDecision,
    reason: str | None = None,
) -> ProductionDeploymentAcceptanceRun:
    return prepare_deployment_acceptance_run(
        session,
        context,
        deployment_run_key=key,
        environment_key="canary-single-vps",
        target_environment_fingerprint=ENVIRONMENT_FP,
        release_commit_sha=RELEASE_SHA,
        release_configuration_fingerprint=RELEASE_CONFIG_FP,
        rollback_release_commit_sha=ROLLBACK_SHA,
        rollback_configuration_fingerprint=ROLLBACK_CONFIG_FP,
        networking_contract=NETWORKING_CONTRACT,
        work_item_id=work.id,
        admission_decision_id=decision.id,
        reason=reason or "Prepare exact canary identity for synthetic-only target-host acceptance.",
    )


def _count(session: Session, model) -> int:
    return session.exec(select(func.count()).select_from(model)).one()


def _add_receipt(
    session: Session,
    run: ProductionDeploymentAcceptanceRun,
    gate_key: str,
    *,
    status: str = "satisfied",
) -> ProductionDeploymentAcceptanceCheckReceipt:
    gate = next(item for item in DEPLOYMENT_ACCEPTANCE_GATES if item.gate_key == gate_key)
    observed_at = run.created_at
    details = {"synthetic_test": True, "secret_values_recorded": False}
    receipt = ProductionDeploymentAcceptanceCheckReceipt(
        tenant_key=run.tenant_key,
        deployment_run_id=run.id,
        gate_key=gate.gate_key,
        gate_version=gate.gate_version,
        status=status,
        observed_target_environment_fingerprint=run.target_environment_fingerprint,
        observed_release_commit_sha=run.release_commit_sha,
        observed_release_configuration_fingerprint=run.release_configuration_fingerprint,
        executor_contract_key="pytest-target-host-executor",
        executor_contract_version=1,
        executor_identity_fingerprint="f" * 64,
        evidence_digest="1" * 64,
        evidence_reference=f"pytest://deployment/{run.id}/{gate.gate_key}",
        redacted_details_json=canonical_json(details),
        observed_at=observed_at,
        record_fingerprint="0" * 64,
        created_by="pytest-target-host-executor",
    )
    receipt.record_fingerprint = deployment_acceptance_receipt_fingerprint(
        tenant_key=receipt.tenant_key,
        deployment_run_id=receipt.deployment_run_id,
        gate_key=receipt.gate_key,
        gate_version=receipt.gate_version,
        status=receipt.status,
        observed_target_environment_fingerprint=receipt.observed_target_environment_fingerprint,
        observed_release_commit_sha=receipt.observed_release_commit_sha,
        observed_release_configuration_fingerprint=receipt.observed_release_configuration_fingerprint,
        executor_contract_key=receipt.executor_contract_key,
        executor_contract_version=receipt.executor_contract_version,
        executor_identity_fingerprint=receipt.executor_identity_fingerprint,
        evidence_digest=receipt.evidence_digest,
        evidence_reference=receipt.evidence_reference,
        redacted_details=details,
        observed_at=receipt.observed_at,
        created_by=receipt.created_by,
    )
    session.add(receipt)
    session.commit()
    session.refresh(receipt)
    return receipt


def test_deployment_acceptance_prepare_is_identity_only_and_authority_neutral(
    db_session: Session,
) -> None:
    context = _context()
    work, decision = _work_and_decision(db_session)
    before_receipts = _count(db_session, ProductionDeploymentAcceptanceCheckReceipt)

    run = _prepare(
        db_session,
        key=f"phase22-run-{uuid4()}",
        context=context,
        work=work,
        decision=decision,
    )
    read = project_deployment_acceptance_run(db_session, context, run)

    assert read.execution_mode == "canary"
    assert read.environment_class == "canary"
    assert read.environment_constraints == CANARY_ENVIRONMENT_CONSTRAINTS
    assert read.release_commit_sha == RELEASE_SHA
    assert read.rollback_release_commit_sha == ROLLBACK_SHA
    assert read.networking_contract_key == NETWORKING_CONTRACT_KEY
    assert read.networking_contract_version == NETWORKING_CONTRACT_VERSION
    assert read.networking_contract_fingerprint == networking_contract_fingerprint(NETWORKING_CONTRACT)
    assert read.networking_contract is not None
    assert read.networking_contract.model_dump() == NETWORKING_CONTRACT
    assert [item.gate_key for item in read.gates] == [
        "release_networking",
        "identity_boundaries",
        "core_journey",
        "documents_integrations",
        "failure_recovery",
        "operations",
    ]
    assert {item.status for item in read.gates} == {"absent"}
    assert read.deployment_observed is False
    assert read.checks_complete is False
    assert read.canary_evidence_status == "absent"
    assert read.canary_evidence_satisfied is False
    assert read.authority_conclusion == "none_granted"
    assert read.deployment_authorized_by_receipt is False
    assert read.promotion_authorized is False
    assert read.production_ready is False
    assert read.real_client_data_admitted is False
    assert _count(db_session, ProductionDeploymentAcceptanceCheckReceipt) == before_receipts

    activity = db_session.get(OrganizationActivity, run.prepared_activity_id)
    assert activity is not None
    assert getattr(activity.activity_class, "value", activity.activity_class) == "operational"
    assert activity.activity_type == DEPLOYMENT_ACCEPTANCE_ACTIVITY_TYPE
    assert activity.source_object_type == DEPLOYMENT_ACCEPTANCE_SOURCE_TYPE
    assert activity.source_object_id == str(run.id)
    assert activity.source_object_version == RELEASE_SHA
    assert activity.work_item_id == work.id
    activity_payload = __import__("json").loads(activity.payload_json)
    assert activity_payload["networking_contract"]["contract_key"] == NETWORKING_CONTRACT_KEY
    assert activity_payload["networking_contract"]["contract_version"] == NETWORKING_CONTRACT_VERSION
    assert activity_payload["networking_contract"]["contract"] == NETWORKING_CONTRACT


def test_deployment_acceptance_requires_current_approved_matching_decision(
    db_session: Session,
) -> None:
    context = _context()
    work, pending = _work_and_decision(db_session, decision_status="pending_board")
    with pytest.raises(InvalidTransition, match="approved decision"):
        _prepare(
            db_session,
            key=f"phase22-run-pending-{uuid4()}",
            context=context,
            work=work,
            decision=pending,
        )

    work2, approved = _work_and_decision(db_session)
    superseding = ExecutiveDecision(
        decision_key=f"phase22-superseding-{uuid4()}",
        tenant_key="default",
        decision_type=OrganizationDecisionType.board_reserved,
        work_item_id=work2.id,
        source_object_type=work2.source_object_type,
        source_object_id=work2.source_object_id,
        source_object_version=work2.source_object_version,
        supersedes_decision_id=approved.id,
        authority_level=work2.authority_level,
        requested_by_position="cto",
        decision_owner_position="board",
        title="Withdraw prior deployment admission",
        question="Should the prior canary preparation decision be superseded?",
        recommendation="Do not use the prior decision.",
        status="rejected",
        decided_by="pytest-board",
        decision_reason="Superseded for test.",
    )
    db_session.add(superseding)
    db_session.commit()
    with pytest.raises(InvalidTransition, match="superseded"):
        _prepare(
            db_session,
            key=f"phase22-run-stale-{uuid4()}",
            context=context,
            work=work2,
            decision=approved,
        )


def test_deployment_acceptance_requires_assigned_canonical_deployment_position(
    db_session: Session,
) -> None:
    work, decision = _work_and_decision(
        db_session,
        position_key="platform_engineer",
        authority_level="L2",
    )
    with pytest.raises(AuthorityDenied, match="assigned position"):
        _prepare(
            db_session,
            key=f"phase22-run-wrong-actor-{uuid4()}",
            context=_context(),
            work=work,
            decision=decision,
        )

    platform_context = _context(
        position_key="platform_engineer",
        role="operator",
        authority_level="L2",
    )
    run = _prepare(
        db_session,
        key=f"phase22-run-platform-{uuid4()}",
        context=platform_context,
        work=work,
        decision=decision,
    )
    assert run.created_by == platform_context.actor_id


def test_deployment_acceptance_run_key_is_idempotent(db_session: Session) -> None:
    context = _context()
    work, decision = _work_and_decision(db_session)
    key = f"phase22-run-idempotent-{uuid4()}"
    first = _prepare(db_session, key=key, context=context, work=work, decision=decision)
    replay = _prepare(db_session, key=key, context=context, work=work, decision=decision)
    assert replay.id == first.id

    with pytest.raises(IdempotencyConflict):
        _prepare(
            db_session,
            key=key,
            context=context,
            work=work,
            decision=decision,
            reason="Changed semantics under the same deployment run key.",
        )


def test_deployment_acceptance_projection_reads_immutable_receipts_without_granting_production(
    db_session: Session,
) -> None:
    context = _context()
    work, decision = _work_and_decision(db_session)
    run = _prepare(
        db_session,
        key=f"phase22-run-receipts-{uuid4()}",
        context=context,
        work=work,
        decision=decision,
    )
    for gate in DEPLOYMENT_ACCEPTANCE_GATES:
        _add_receipt(db_session, run, gate.gate_key)

    read = project_deployment_acceptance_run(db_session, context, run)
    assert read.deployment_observed is True
    assert read.checks_complete is True
    assert read.canary_evidence_status == "satisfied"
    assert read.canary_evidence_satisfied is True
    assert read.production_ready is False
    assert read.promotion_authorized is False
    assert read.authority_conclusion == "none_granted"
    assert read.real_client_data_admitted is False
    assert read.consequential_external_actions_enabled is False
    assert read.paid_autonomous_execution_enabled is False


def test_deployment_acceptance_api_is_no_store_and_has_no_receipt_write_route(
    client: TestClient,
    db_session: Session,
) -> None:
    work, decision = _work_and_decision(db_session)
    key = f"phase22-run-api-{uuid4()}"
    payload = {
        "deployment_run_key": key,
        "environment_key": "canary-single-vps",
        "target_environment_fingerprint": ENVIRONMENT_FP,
        "release_commit_sha": RELEASE_SHA,
        "release_configuration_fingerprint": RELEASE_CONFIG_FP,
        "rollback_release_commit_sha": ROLLBACK_SHA,
        "rollback_configuration_fingerprint": ROLLBACK_CONFIG_FP,
        "networking_contract": NETWORKING_CONTRACT,
        "work_item_id": str(work.id),
        "admission_decision_id": str(decision.id),
        "reason": "Prepare only; no deployment evidence is asserted.",
    }
    response = client.post(f"{BASE}/runs", json=payload)
    assert response.status_code == 201, response.text
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body["deployment_run_key"] == key
    assert body["canary_evidence_status"] == "absent"
    assert body["production_ready"] is False

    run_id = UUID(body["id"])
    read = client.get(f"{BASE}/runs/{run_id}")
    assert read.status_code == 200, read.text
    assert read.headers["cache-control"] == "no-store"

    forbidden_receipt_write = client.post(
        f"{BASE}/runs/{run_id}/receipts",
        json={"status": "satisfied"},
    )
    assert forbidden_receipt_write.status_code == 404

def test_deployment_acceptance_networking_contract_fails_closed(
    db_session: Session,
) -> None:
    context = _context()
    work, decision = _work_and_decision(db_session)
    base = dict(NETWORKING_CONTRACT)

    invalid_contracts = (
        {**base, "expected_public_ipv4": "2001:4860:4860::8888"},
        {**base, "expected_public_ipv4": "127.0.0.1"},
        {**base, "web_hostname": "localhost"},
        {**base, "api_hostname": "api.example.com"},
        {**base, "api_hostname": "8.8.8.8"},
        {**base, "api_hostname": base["web_hostname"]},
        {**base, "allowed_public_tcp_ports": [443]},
        {**base, "allowed_public_tcp_ports": [22, 80, 443, 8443]},
        {**base, "allowed_public_tcp_ports": [80, 80, 443]},
    )
    for index, networking_contract in enumerate(invalid_contracts):
        with pytest.raises(InvalidReference):
            prepare_deployment_acceptance_run(
                db_session,
                context,
                deployment_run_key=f"phase22-network-invalid-{index}-{uuid4()}",
                environment_key="canary-single-vps",
                target_environment_fingerprint=ENVIRONMENT_FP,
                release_commit_sha=RELEASE_SHA,
                release_configuration_fingerprint=RELEASE_CONFIG_FP,
                rollback_release_commit_sha=ROLLBACK_SHA,
                rollback_configuration_fingerprint=ROLLBACK_CONFIG_FP,
                networking_contract=networking_contract,
                work_item_id=work.id,
                admission_decision_id=decision.id,
                reason="Invalid networking contract must fail closed.",
            )


def test_deployment_acceptance_legacy_pre_0100_run_remains_readable(
    db_session: Session,
) -> None:
    context = _context()
    work, decision = _work_and_decision(db_session)
    run_id = uuid4()
    run_key = f"phase22-legacy-run-{uuid4()}"
    reason = "Legacy pre-0100 prepared run."
    fingerprint = _run_fingerprint(
        tenant_key=context.tenant_key,
        deployment_run_key=run_key,
        environment_key="canary-single-vps",
        target_environment_fingerprint=ENVIRONMENT_FP,
        release_commit_sha=RELEASE_SHA,
        release_configuration_fingerprint=RELEASE_CONFIG_FP,
        rollback_release_commit_sha=ROLLBACK_SHA,
        rollback_configuration_fingerprint=ROLLBACK_CONFIG_FP,
        work_item_id=work.id,
        admission_decision_id=decision.id,
        reason=reason,
    )
    occurred_at = now_utc()
    activity = stage_activity(
        db_session,
        context,
        activity_key=f"production-deployment-acceptance:{run_id}:prepared",
        stream_key="production-deployment-acceptance:canary-single-vps",
        activity_class="operational",
        activity_type=DEPLOYMENT_ACCEPTANCE_ACTIVITY_TYPE,
        title="Deployment acceptance run prepared",
        summary=(
            "Prepared an exact canary release/environment/rollback identity and acceptance contract; "
            "no deployment or target-host acceptance is asserted."
        ),
        source_object_type=DEPLOYMENT_ACCEPTANCE_SOURCE_TYPE,
        source_object_id=str(run_id),
        source_object_version=RELEASE_SHA,
        work_item_id=work.id,
        occurred_at=occurred_at,
        payload=_prepared_activity_payload(
            run_id=run_id,
            deployment_run_key=run_key,
            environment_key="canary-single-vps",
            target_environment_fingerprint=ENVIRONMENT_FP,
            release_commit_sha=RELEASE_SHA,
            release_configuration_fingerprint=RELEASE_CONFIG_FP,
            rollback_release_commit_sha=ROLLBACK_SHA,
            rollback_configuration_fingerprint=ROLLBACK_CONFIG_FP,
            work_item_id=work.id,
            admission_decision_id=decision.id,
            reason=reason,
            record_fingerprint=fingerprint,
        ),
    )
    run = ProductionDeploymentAcceptanceRun(
        id=run_id,
        tenant_key=context.tenant_key,
        deployment_run_key=run_key,
        execution_mode="canary",
        environment_key="canary-single-vps",
        environment_class="canary",
        target_environment_fingerprint=ENVIRONMENT_FP,
        environment_constraints_json=canonical_json(CANARY_ENVIRONMENT_CONSTRAINTS),
        release_commit_sha=RELEASE_SHA,
        release_configuration_fingerprint=RELEASE_CONFIG_FP,
        rollback_release_commit_sha=ROLLBACK_SHA,
        rollback_configuration_fingerprint=ROLLBACK_CONFIG_FP,
        acceptance_contract_key="phase22.single_vps_compose.canary_acceptance",
        acceptance_contract_version=1,
        acceptance_contract_fingerprint=__import__(
            "app.services.production_deployment_acceptance",
            fromlist=["deployment_acceptance_contract_fingerprint"],
        ).deployment_acceptance_contract_fingerprint(),
        required_gate_keys_json=canonical_json(
            [gate.gate_key for gate in DEPLOYMENT_ACCEPTANCE_GATES]
        ),
        work_item_id=work.id,
        admission_decision_id=decision.id,
        reason=reason,
        record_fingerprint=fingerprint,
        prepared_activity_id=activity.id,
        prepared_activity_fingerprint=activity.record_fingerprint,
        created_by=context.actor_id,
        created_at=occurred_at,
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    read = project_deployment_acceptance_run(db_session, context, run)
    assert read.networking_contract_key is None
    assert read.networking_contract_version is None
    assert read.networking_contract_fingerprint is None
    assert read.networking_contract is None
    assert read.canary_evidence_status == "absent"


def test_deployment_acceptance_partial_networking_contract_drift_fails_closed(
    db_session: Session,
) -> None:
    context = _context()
    work, decision = _work_and_decision(db_session)
    run = _prepare(
        db_session,
        key=f"phase22-network-drift-{uuid4()}",
        context=context,
        work=work,
        decision=decision,
    )
    run.networking_contract_json = None
    with db_session.no_autoflush:
        with pytest.raises(InvalidTransition, match="partially populated"):
            project_deployment_acceptance_run(db_session, context, run)
    db_session.rollback()


def _executor_context() -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key="default",
        actor_id=TARGET_HOST_FOUNDATION_EXECUTOR_ACTOR,
        actor_type=OrganizationActorType.system,
        authenticated_user_id="system",
        role="operator",
        department="Technology",
    )


def _foundation_details() -> dict:
    return {
        "target_environment_fingerprint_verified": True,
        "release_identity_verified": True,
        "gate_probe_implemented": False,
        "blocker": "foundation v1 deliberately cannot satisfy this gate",
        "secret_values_recorded": False,
    }


def test_target_host_foundation_receipt_is_internal_fail_closed_and_idempotent(
    db_session: Session,
) -> None:
    context = _context()
    work, decision = _work_and_decision(db_session)
    run = _prepare(
        db_session,
        key=f"phase22-foundation-{uuid4()}",
        context=context,
        work=work,
        decision=decision,
    )
    executor = _executor_context()

    with pytest.raises(InvalidReference, match="satisfied acceptance gate"):
        record_target_host_foundation_receipt(
            db_session,
            executor,
            deployment_run_id=run.id,
            gate_key="release_networking",
            status="satisfied",
            observed_target_environment_fingerprint=run.target_environment_fingerprint,
            observed_release_commit_sha=run.release_commit_sha,
            observed_release_configuration_fingerprint=run.release_configuration_fingerprint,
            redacted_details=_foundation_details(),
        )

    first = record_target_host_foundation_receipt(
        db_session,
        executor,
        deployment_run_id=run.id,
        gate_key="release_networking",
        status="blocked",
        observed_target_environment_fingerprint=run.target_environment_fingerprint,
        observed_release_commit_sha=run.release_commit_sha,
        observed_release_configuration_fingerprint=run.release_configuration_fingerprint,
        redacted_details=_foundation_details(),
    )
    replay = record_target_host_foundation_receipt(
        db_session,
        executor,
        deployment_run_id=run.id,
        gate_key="release_networking",
        status="blocked",
        observed_target_environment_fingerprint=run.target_environment_fingerprint,
        observed_release_commit_sha=run.release_commit_sha,
        observed_release_configuration_fingerprint=run.release_configuration_fingerprint,
        redacted_details=_foundation_details(),
    )
    assert replay.id == first.id

    with pytest.raises(IdempotencyConflict):
        record_target_host_foundation_receipt(
            db_session,
            executor,
            deployment_run_id=run.id,
            gate_key="release_networking",
            status="failed",
            observed_target_environment_fingerprint=run.target_environment_fingerprint,
            observed_release_commit_sha=run.release_commit_sha,
            observed_release_configuration_fingerprint=run.release_configuration_fingerprint,
            redacted_details=_foundation_details(),
        )


def test_target_host_foundation_receipt_requires_exact_prepared_identity_and_executor(
    db_session: Session,
) -> None:
    context = _context()
    work, decision = _work_and_decision(db_session)
    run = _prepare(
        db_session,
        key=f"phase22-foundation-identity-{uuid4()}",
        context=context,
        work=work,
        decision=decision,
    )

    with pytest.raises(AuthorityDenied, match="canonical target-host executor"):
        record_target_host_foundation_receipt(
            db_session,
            context,
            deployment_run_id=run.id,
            gate_key="operations",
            status="blocked",
            observed_target_environment_fingerprint=run.target_environment_fingerprint,
            observed_release_commit_sha=run.release_commit_sha,
            observed_release_configuration_fingerprint=run.release_configuration_fingerprint,
            redacted_details=_foundation_details(),
        )

    with pytest.raises(InvalidReference, match="does not match the prepared run"):
        record_target_host_foundation_receipt(
            db_session,
            _executor_context(),
            deployment_run_id=run.id,
            gate_key="operations",
            status="blocked",
            observed_target_environment_fingerprint="9" * 64,
            observed_release_commit_sha=run.release_commit_sha,
            observed_release_configuration_fingerprint=run.release_configuration_fingerprint,
            redacted_details=_foundation_details(),
        )
    assert _count(db_session, ProductionDeploymentAcceptanceCheckReceipt) == 0


def test_six_foundation_receipts_complete_observation_but_keep_canary_blocked(
    db_session: Session,
) -> None:
    context = _context()
    work, decision = _work_and_decision(db_session)
    run = _prepare(
        db_session,
        key=f"phase22-foundation-six-{uuid4()}",
        context=context,
        work=work,
        decision=decision,
    )
    executor = _executor_context()
    for gate in DEPLOYMENT_ACCEPTANCE_GATES:
        record_target_host_foundation_receipt(
            db_session,
            executor,
            deployment_run_id=run.id,
            gate_key=gate.gate_key,
            status="blocked",
            observed_target_environment_fingerprint=run.target_environment_fingerprint,
            observed_release_commit_sha=run.release_commit_sha,
            observed_release_configuration_fingerprint=run.release_configuration_fingerprint,
            redacted_details=_foundation_details(),
        )

    read = project_deployment_acceptance_run(db_session, context, run)
    assert read.deployment_observed is True
    assert read.checks_complete is True
    assert {gate.status for gate in read.gates} == {"blocked"}
    assert read.canary_evidence_status == "blocked"
    assert read.canary_evidence_satisfied is False
    assert read.deployment_authorized_by_receipt is False
    assert read.promotion_authorized is False
    assert read.production_ready is False
    assert read.real_client_data_admitted is False
    assert read.consequential_external_actions_enabled is False
    assert read.paid_autonomous_execution_enabled is False


def _release_networking_executor_context() -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key="default",
        actor_id=TARGET_HOST_RELEASE_NETWORKING_EXECUTOR_ACTOR,
        actor_type=OrganizationActorType.system,
        authenticated_user_id="system",
        role="operator",
        department="Technology",
        position_key=None,
        authority_level=None,
    )


def _release_networking_details(
    run: ProductionDeploymentAcceptanceRun,
    *,
    executor_commit_sha: str = "1" * 40,
    satisfied: bool = True,
) -> dict:
    revision = "0100_phase22_release_networking_contract"
    return {
        "executor_commit_sha": executor_commit_sha,
        "target_environment_fingerprint_verified": True,
        "candidate_release_identity_verified": True,
        "candidate_restart_verified": True,
        "candidate_restart_health_verified": True,
        "external_network_manifest_sha256": "2" * 64,
        "external_verifier_public_key_fingerprint": VERIFIER_KEY_FP,
        "external_verifier_ref": TARGET_HOST_RELEASE_NETWORKING_VERIFIER_REF,
        "external_verifier_commit_sha": "3" * 40,
        "external_network_contract_satisfied": satisfied,
        "external_network_observed_after_restore": satisfied,
        "rollback_release_commit_sha": run.rollback_release_commit_sha,
        "rollback_configuration_fingerprint": run.rollback_configuration_fingerprint,
        "rollback_image_identity_verified": True,
        "rollback_retained_schema_verified": True,
        "rollback_release_identity_verified": True,
        "rollback_schema_compatibility_verified": True,
        "rollback_stable_data_verified": True,
        "rollback_health_verified": True,
        "candidate_restore_retained_schema_verified": True,
        "candidate_restored": True,
        "candidate_restore_identity_verified": True,
        "candidate_restore_schema_compatibility_verified": True,
        "candidate_restore_stable_data_verified": True,
        "candidate_restore_health_verified": True,
        "candidate_schema_revision_before": revision,
        "rollback_schema_revision": revision,
        "candidate_schema_revision_after_restore": revision,
        "failure_stage": None if satisfied else "external_network",
        "failure_code": None if satisfied else "external_network_contract_failed",
        "secret_values_recorded": False,
    }


def test_release_networking_v2_is_only_satisfied_capable_for_exact_evidence(
    db_session: Session,
) -> None:
    context = _context()
    work, decision = _work_and_decision(db_session)
    run = _prepare(
        db_session,
        key=f"phase22-release-networking-v2-{uuid4()}",
        context=context,
        work=work,
        decision=decision,
    )
    executor = _release_networking_executor_context()
    details = _release_networking_details(run)

    receipt = record_target_host_release_networking_receipt(
        db_session,
        executor,
        deployment_run_id=run.id,
        status="satisfied",
        observed_target_environment_fingerprint=run.target_environment_fingerprint,
        observed_release_commit_sha=run.release_commit_sha,
        observed_release_configuration_fingerprint=run.release_configuration_fingerprint,
        executor_commit_sha=details["executor_commit_sha"],
        redacted_details=details,
    )
    assert receipt.status == "satisfied"
    assert receipt.gate_key == "release_networking"
    assert receipt.executor_contract_key == TARGET_HOST_RELEASE_NETWORKING_EXECUTOR_CONTRACT_KEY
    assert receipt.executor_contract_version == TARGET_HOST_RELEASE_NETWORKING_EXECUTOR_CONTRACT_VERSION
    read = project_deployment_acceptance_run(db_session, context, run)
    release_gate = next(item for item in read.gates if item.gate_key == "release_networking")
    assert release_gate.status == "satisfied"
    assert read.canary_evidence_status == "partial"
    assert read.canary_evidence_satisfied is False
    assert read.production_ready is False
    assert read.promotion_authorized is False


def test_release_networking_v2_satisfied_fails_closed_on_incomplete_rollback(
    db_session: Session,
) -> None:
    context = _context()
    work, decision = _work_and_decision(db_session)
    run = _prepare(
        db_session,
        key=f"phase22-release-networking-v2-incomplete-{uuid4()}",
        context=context,
        work=work,
        decision=decision,
    )
    details = _release_networking_details(run)
    details["rollback_schema_compatibility_verified"] = False
    with pytest.raises(InvalidReference, match="every v2 proof"):
        record_target_host_release_networking_receipt(
            db_session,
            _release_networking_executor_context(),
            deployment_run_id=run.id,
            status="satisfied",
            observed_target_environment_fingerprint=run.target_environment_fingerprint,
            observed_release_commit_sha=run.release_commit_sha,
            observed_release_configuration_fingerprint=run.release_configuration_fingerprint,
            executor_commit_sha=details["executor_commit_sha"],
            redacted_details=details,
        )
    assert _count(db_session, ProductionDeploymentAcceptanceCheckReceipt) == 0


def test_release_networking_v2_requires_protected_verifier_ref_and_fresh_run(
    db_session: Session,
) -> None:
    context = _context()
    work, decision = _work_and_decision(db_session)
    run = _prepare(
        db_session,
        key=f"phase22-release-networking-v2-ref-{uuid4()}",
        context=context,
        work=work,
        decision=decision,
    )
    details = _release_networking_details(run)
    details["external_verifier_ref"] = "refs/heads/design/aios-v2-complete-redesign"
    with pytest.raises(InvalidReference, match="protected main verifier ref"):
        record_target_host_release_networking_receipt(
            db_session,
            _release_networking_executor_context(),
            deployment_run_id=run.id,
            status="satisfied",
            observed_target_environment_fingerprint=run.target_environment_fingerprint,
            observed_release_commit_sha=run.release_commit_sha,
            observed_release_configuration_fingerprint=run.release_configuration_fingerprint,
            executor_commit_sha=details["executor_commit_sha"],
            redacted_details=details,
        )

    foundation = _executor_context()
    record_target_host_foundation_receipt(
        db_session,
        foundation,
        deployment_run_id=run.id,
        gate_key="release_networking",
        status="blocked",
        observed_target_environment_fingerprint=run.target_environment_fingerprint,
        observed_release_commit_sha=run.release_commit_sha,
        observed_release_configuration_fingerprint=run.release_configuration_fingerprint,
        redacted_details=_foundation_details(),
    )
    clean_details = _release_networking_details(run)
    with pytest.raises(IdempotencyConflict, match="immutable evidence"):
        record_target_host_release_networking_receipt(
            db_session,
            _release_networking_executor_context(),
            deployment_run_id=run.id,
            status="satisfied",
            observed_target_environment_fingerprint=run.target_environment_fingerprint,
            observed_release_commit_sha=run.release_commit_sha,
            observed_release_configuration_fingerprint=run.release_configuration_fingerprint,
            executor_commit_sha=clean_details["executor_commit_sha"],
            redacted_details=clean_details,
        )


def test_release_networking_v2_rejects_noncanonical_executor(
    db_session: Session,
) -> None:
    context = _context()
    work, decision = _work_and_decision(db_session)
    run = _prepare(
        db_session,
        key=f"phase22-release-networking-v2-executor-{uuid4()}",
        context=context,
        work=work,
        decision=decision,
    )
    details = _release_networking_details(run)
    with pytest.raises(AuthorityDenied, match="canonical v2 target-host executor"):
        record_target_host_release_networking_receipt(
            db_session,
            context,
            deployment_run_id=run.id,
            status="satisfied",
            observed_target_environment_fingerprint=run.target_environment_fingerprint,
            observed_release_commit_sha=run.release_commit_sha,
            observed_release_configuration_fingerprint=run.release_configuration_fingerprint,
            executor_commit_sha=details["executor_commit_sha"],
            redacted_details=details,
        )


def test_release_networking_freshness_checked_before_drill(db_session: Session) -> None:
    from app.services.production_deployment_acceptance import validated_deployment_networking_contract
    context = _context()
    work, decision = _work_and_decision(db_session)
    run = _prepare(db_session, key=f"fresh-check-{uuid4()}", context=context, work=work, decision=decision)
    executor = _release_networking_executor_context()
    validated_deployment_networking_contract(db_session, executor, deployment_run_id=run.id, require_fresh_release_networking=True)
    record_target_host_foundation_receipt(
        db_session, _executor_context(), deployment_run_id=run.id,
        gate_key="release_networking", status="blocked",
        observed_target_environment_fingerprint=run.target_environment_fingerprint,
        observed_release_commit_sha=run.release_commit_sha,
        observed_release_configuration_fingerprint=run.release_configuration_fingerprint,
        redacted_details=_foundation_details(),
    )
    with pytest.raises(InvalidTransition, match="fresh run"):
        validated_deployment_networking_contract(db_session, executor, deployment_run_id=run.id, require_fresh_release_networking=True)


def test_satisfied_receipt_requires_post_restore_external_proof(db_session: Session) -> None:
    context = _context()
    work, decision = _work_and_decision(db_session)
    run = _prepare(db_session, key=f"post-restore-{uuid4()}", context=context, work=work, decision=decision)
    details = _release_networking_details(run)
    details["external_network_observed_after_restore"] = False
    with pytest.raises(InvalidReference, match="every v2 proof"):
        record_target_host_release_networking_receipt(
            db_session, _release_networking_executor_context(), deployment_run_id=run.id, status="satisfied",
            observed_target_environment_fingerprint=run.target_environment_fingerprint,
            observed_release_commit_sha=run.release_commit_sha,
            observed_release_configuration_fingerprint=run.release_configuration_fingerprint,
            executor_commit_sha=details["executor_commit_sha"], redacted_details=details,
        )


def _identity_details(run, monkeypatch):
    from datetime import timedelta, timezone
    from app.services import production_deployment_acceptance as owner
    started = now_utc()
    completed = started + timedelta(seconds=301)
    monkeypatch.setattr(owner, 'now_utc', lambda: completed)
    return {**{key: True for key in owner.IDENTITY_REQUIRED_PROOFS}, 'executor_commit_sha': '9' * 40, 'observed_started_at': started.isoformat(), 'observed_completed_at': completed.isoformat(), 'session_ttl_seconds': 300, 'waited_seconds': 301, 'asset_files_scanned': 3, 'log_bytes_scanned': 100, 'secret_values_recorded': False, 'failure_stage': None, 'failure_code': None, 'surface_contract': 'phase22.identity.finite-surfaces.v1'}

def _identity_write(db_session, run, details, context=None, status='satisfied'):
    from app.services import production_deployment_acceptance as owner
    from scripts.phase22_identity_boundaries import executor_context
    return owner.record_target_host_identity_receipt(db_session, context or executor_context('default'), deployment_run_id=run.id, status=status, observed_target_environment_fingerprint=run.target_environment_fingerprint, observed_release_commit_sha=run.release_commit_sha, observed_release_configuration_fingerprint=run.release_configuration_fingerprint, executor_commit_sha=details['executor_commit_sha'], redacted_details=details)

def test_identity_writer_is_gate_restricted_and_immutable(db_session, monkeypatch):
    from app.services import production_deployment_acceptance as owner
    context = _context()
    work, decision = _work_and_decision(db_session)
    run = _prepare(db_session, key=f'identity-{uuid4()}', context=context, work=work, decision=decision)
    details = _identity_details(run, monkeypatch)
    with pytest.raises(AuthorityDenied):
        _identity_write(db_session, run, details, context=context)
    first = _identity_write(db_session, run, details)
    assert first.gate_key == 'identity_boundaries'
    assert _identity_write(db_session, run, details).id == first.id
    projection = project_deployment_acceptance_run(db_session, context, run)
    assert not projection.canary_evidence_satisfied and (not projection.production_ready)
    assert next((g for g in projection.gates if g.gate_key == 'release_networking')).status == 'absent'
    with pytest.raises(InvalidTransition, match='fresh run'):
        owner.validated_deployment_networking_contract(db_session, context, deployment_run_id=run.id, require_fresh_identity_boundaries=True)
    changed = {**details, 'waited_seconds': 302}
    with pytest.raises(IdempotencyConflict):
        _identity_write(db_session, run, changed)

@pytest.mark.parametrize('missing', ['browser_login_verified', 'web_compiled_request_verified', 'cookie_policy_verified', 'cors_verified', 'real_session_expiry_verified', 'expired_token_replay_denied', 'runtime_secret_read_denial_verified', 'runtime_secret_references_verified', 'client_asset_scan_verified', 'interval_log_scan_verified', 'host_release_verified_after'])
def test_identity_partial_proof_cannot_satisfy(db_session, monkeypatch, missing):
    context = _context()
    work, decision = _work_and_decision(db_session)
    run = _prepare(db_session, key=f'identity-gap-{uuid4()}', context=context, work=work, decision=decision)
    details = _identity_details(run, monkeypatch)
    details[missing] = False
    with pytest.raises(InvalidReference, match='every proof'):
        _identity_write(db_session, run, details)

@pytest.mark.parametrize('key,value', [('waited_seconds', 299), ('session_ttl_seconds', 299), ('asset_files_scanned', 0), ('log_bytes_scanned', 0), ('secret_values_recorded', True), ('failure_code', 'raw-secret:text'), ('failure_code', 'private_secret'), ('failure_stage', 'private_secret'), ('unexpected_cookie', 'secret'), ('observed_completed_at', '2099-10-01T00:00:00+00:00')])
def test_identity_writer_rejects_invalid_or_secret_bearing_evidence(db_session, monkeypatch, key, value):
    context = _context()
    work, decision = _work_and_decision(db_session)
    run = _prepare(db_session, key=f'identity-invalid-{uuid4()}', context=context, work=work, decision=decision)
    details = _identity_details(run, monkeypatch)
    details[key] = value
    with pytest.raises(InvalidReference):
        _identity_write(db_session, run, details)

def test_identity_failed_evidence_never_upgrades(db_session, monkeypatch):
    context = _context()
    work, decision = _work_and_decision(db_session)
    run = _prepare(db_session, key=f'identity-failed-{uuid4()}', context=context, work=work, decision=decision)
    details = _identity_details(run, monkeypatch)
    failed = {**details, 'real_session_expiry_verified': False, 'failure_stage': 'browser', 'failure_code': 'identity_probe_failed'}
    assert _identity_write(db_session, run, failed, status='failed').status == 'failed'
    with pytest.raises(IdempotencyConflict):
        _identity_write(db_session, run, details)
