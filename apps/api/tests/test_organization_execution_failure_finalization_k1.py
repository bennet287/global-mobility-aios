from __future__ import annotations

from datetime import timedelta
from uuid import UUID

import pytest
from sqlmodel import Session, select

import app.services.organization_mobility_objective_execution as execution_service
from app.models.domain import OrganizationActorType, OrganizationExecutionAttempt, OrganizationalWorkItem, now_utc
from app.models.organization_presence import OrganizationExecutionHeartbeat
from app.services.organization_agent_runtime import AgentRuntimeProfile, RuntimeClass
from app.services.organization_command import OrganizationCommandContext
from app.services.organization_execution_heartbeat import claim_execution_runtime_session
from app.services.organization_governance import ensure_foundation_positions
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_PATHWAY_POSITION,
    create_austria_mobility_objective,
)


def _human_context() -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key="default",
        actor_id="human-owner",
        actor_type=OrganizationActorType.human,
        authenticated_user_id="human-owner",
        role="admin",
        department="Global Mobility Operations",
        position_key="board",
        authority_level="L4",
    )


def _runtime() -> AgentRuntimeProfile:
    return AgentRuntimeProfile(
        profile_key="failure-finalization-k1-v1",
        runtime_class=RuntimeClass.HOSTED_API,
        adapter_key="failure-finalization-k1-adapter",
        provider_key="failure-finalization-k1-provider",
        model_key="failure-finalization-k1-model",
        technical_capabilities=("reasoning", "structured_output"),
        available_tools=("browser",),
        independence_group="failure-finalization-k1",
        profile_version=1,
        enabled=True,
    )


def test_original_k1_worker_cannot_mark_attempt_failed_after_takeover(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ensure_foundation_positions(db_session, actor="pytest", repair_contracts=True)
    context = _human_context()
    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key="at-rwr-shortage-2026-k1-stale-failure-finalization",
    )
    captured_attempt_id: UUID | None = None

    def takeover_then_fail(session, payload, existing_run=None):
        nonlocal captured_attempt_id
        del existing_run
        provenance = payload.context["k1_provenance"]
        captured_attempt_id = UUID(str(provenance["execution_attempt_id"]))
        work_item_id = UUID(str(provenance["work_item_id"]))
        execution_token = str(provenance["execution_token"])
        heartbeat = session.exec(
            select(OrganizationExecutionHeartbeat)
            .where(OrganizationExecutionHeartbeat.execution_attempt_id == captured_attempt_id)
            .order_by(OrganizationExecutionHeartbeat.sequence.desc())
        ).one()
        expired_at = now_utc()
        heartbeat.observed_at = expired_at - timedelta(seconds=2)
        heartbeat.fresh_until = expired_at - timedelta(seconds=1)
        session.add(heartbeat)
        session.commit()
        takeover = claim_execution_runtime_session(
            session,
            tenant_key="default",
            work_item_id=work_item_id,
            execution_attempt_id=captured_attempt_id,
            position_key=AUSTRIA_MOBILITY_PATHWAY_POSITION,
            expected_execution_token=execution_token,
            writer="worker-b",
            observed_at=expired_at,
            lease_seconds=60,
        )
        assert takeover.fence_token == 2
        raise RuntimeError("late original K1 failure after takeover")

    monkeypatch.setattr(execution_service, "run_controlled_agent", takeover_then_fail)

    with pytest.raises(RuntimeError, match="late original K1 failure after takeover"):
        execution_service.execute_austria_specialist_work(
            db_session,
            context,
            plan,
            position_key=AUSTRIA_MOBILITY_PATHWAY_POSITION,
            runtime_profile=_runtime(),
            actor="worker-a",
        )

    assert captured_attempt_id is not None
    attempt = db_session.get(OrganizationExecutionAttempt, captured_attempt_id)
    work = db_session.get(OrganizationalWorkItem, plan.pathway_work_item.id)
    assert attempt is not None and work is not None
    assert attempt.status == "running"
    assert attempt.error is None
    assert work.status == "running"
    assert work.last_error is None
    assert work.execution_started_at is not None

    events = list(
        db_session.exec(
            select(OrganizationExecutionHeartbeat)
            .where(OrganizationExecutionHeartbeat.execution_attempt_id == captured_attempt_id)
            .order_by(OrganizationExecutionHeartbeat.sequence)
        ).all()
    )
    assert [event.checkpoint for event in events] == ["attempt_started", "runtime_session_claimed"]
    assert [event.writer for event in events] == ["worker-a", "worker-b"]
