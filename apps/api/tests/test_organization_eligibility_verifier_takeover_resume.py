from __future__ import annotations

from datetime import timedelta

import pytest
from sqlmodel import Session, select

import app.services.organization_eligibility_verifier_runtime_session as runtime_service
from app.models.domain import (
    OrganizationActivity,
    OrganizationExecutionAttempt,
    OrganizationalWorkItem,
    now_utc,
)
from app.models.organization_presence import OrganizationExecutionHeartbeat
from app.services.organization_command import DependencyConflict, InvalidTransition
from app.services.organization_execution_heartbeat import claim_execution_runtime_session
from tests.test_organization_independent_eligibility_verification import (
    FakeProvider,
    _setup,
    _verifier_output,
    _verifier_runtime,
)


def _interrupted_attempt(
    session: Session,
    *,
    idempotency_key: str,
    actor: str = "g1-worker-a",
):
    proposal, readiness, _, _, graph, _, verification_work, _ = _setup(session)
    runtime_profile = _verifier_runtime()
    work = runtime_service._canonical_work(
        session,
        tenant_key=proposal.context.tenant_key,
        work_item_id=verification_work.id,
        position_key="austria_independent_verifier",
    )
    work, binding = runtime_service._ensure_running_work(
        session,
        proposal=proposal,
        readiness=readiness,
        work=work,
        position_key="austria_independent_verifier",
        runtime_profile=runtime_profile,
    )
    attempt = runtime_service._start_attempt(
        session,
        proposal=proposal,
        readiness=readiness,
        work=work,
        position_key="austria_independent_verifier",
        binding=binding,
        idempotency_key=idempotency_key,
        actor=actor,
    )
    return proposal, readiness, graph, work, runtime_profile, attempt


def _expire_current_lease(
    session: Session,
    attempt_id,
) -> OrganizationExecutionHeartbeat:
    heartbeat = session.exec(
        select(OrganizationExecutionHeartbeat)
        .where(OrganizationExecutionHeartbeat.execution_attempt_id == attempt_id)
        .order_by(OrganizationExecutionHeartbeat.sequence.desc())
    ).first()
    assert heartbeat is not None
    expired_at = now_utc()
    heartbeat.observed_at = expired_at - timedelta(seconds=2)
    heartbeat.fresh_until = expired_at - timedelta(seconds=1)
    session.add(heartbeat)
    session.commit()
    session.refresh(heartbeat)
    return heartbeat


def test_g1_takeover_reexecutes_same_attempt_under_new_fence(
    db_session: Session,
) -> None:
    idempotency_key = "g1-takeover-success"
    proposal, readiness, graph, work, runtime_profile, attempt = _interrupted_attempt(
        db_session,
        idempotency_key=idempotency_key,
    )
    _expire_current_lease(db_session, attempt.id)

    wrapped = (
        runtime_service.resume_fenced_independent_eligibility_verification_with_takeover(
            db_session,
            proposal=proposal,
            readiness=readiness,
            verification_work_item_id=work.id,
            verifier_position_key="austria_independent_verifier",
            verifier_runtime_profile=runtime_profile,
            provider=FakeProvider(
                name="openai",
                model="gpt-verifier",
                content=_verifier_output(graph),
            ),
            idempotency_key=idempotency_key,
            execution_attempt_id=attempt.id,
            expected_execution_token=attempt.execution_token,
            expected_previous_fence_token=1,
            actor="g1-worker-b",
        )
    )

    assert wrapped.takeover_resume is True
    assert wrapped.previous_fence_token == 1
    assert wrapped.fence_token == 2
    assert wrapped.execution_attempt_id == attempt.id

    attempts = list(
        db_session.exec(
            select(OrganizationExecutionAttempt).where(
                OrganizationExecutionAttempt.work_item_id == work.id
            )
        ).all()
    )
    assert len(attempts) == 1
    assert attempts[0].status == "completed"

    completed_work = db_session.get(OrganizationalWorkItem, work.id)
    assert completed_work is not None
    assert completed_work.status == "completed"
    assert completed_work.execution_attempts == 1

    events = list(
        db_session.exec(
            select(OrganizationExecutionHeartbeat)
            .where(OrganizationExecutionHeartbeat.execution_attempt_id == attempt.id)
            .order_by(OrganizationExecutionHeartbeat.sequence)
        ).all()
    )
    assert [event.sequence for event in events] == [1, 2, 3]
    assert [event.checkpoint for event in events] == [
        "attempt_started",
        "runtime_session_claimed",
        "agent_completed",
    ]
    assert events[0].writer == "g1-worker-a"
    assert all(event.writer == "g1-worker-b" for event in events[1:])


def test_g1_takeover_refuses_fresh_original_session(
    db_session: Session,
) -> None:
    idempotency_key = "g1-takeover-fresh"
    proposal, readiness, graph, work, runtime_profile, attempt = _interrupted_attempt(
        db_session,
        idempotency_key=idempotency_key,
    )
    provider = FakeProvider(
        name="openai",
        model="gpt-verifier",
        content=_verifier_output(graph),
    )

    with pytest.raises(InvalidTransition, match="requires an expired runtime session"):
        runtime_service.resume_fenced_independent_eligibility_verification_with_takeover(
            db_session,
            proposal=proposal,
            readiness=readiness,
            verification_work_item_id=work.id,
            verifier_position_key="austria_independent_verifier",
            verifier_runtime_profile=runtime_profile,
            provider=provider,
            idempotency_key=idempotency_key,
            execution_attempt_id=attempt.id,
            expected_execution_token=attempt.execution_token,
            expected_previous_fence_token=1,
            actor="g1-worker-b",
        )

    assert provider.calls == []

def test_g1_takeover_rejects_different_logical_verification_before_claim(
    db_session: Session,
) -> None:
    idempotency_key = "g1-takeover-original-identity"
    proposal, readiness, graph, work, runtime_profile, attempt = _interrupted_attempt(
        db_session,
        idempotency_key=idempotency_key,
    )
    _expire_current_lease(db_session, attempt.id)
    provider = FakeProvider(
        name="openai",
        model="gpt-verifier",
        content=_verifier_output(graph),
    )

    with pytest.raises(DependencyConflict, match="interrupted G.1 identity"):
        runtime_service.resume_fenced_independent_eligibility_verification_with_takeover(
            db_session,
            proposal=proposal,
            readiness=readiness,
            verification_work_item_id=work.id,
            verifier_position_key="austria_independent_verifier",
            verifier_runtime_profile=runtime_profile,
            provider=provider,
            idempotency_key="g1-takeover-different-identity",
            execution_attempt_id=attempt.id,
            expected_execution_token=attempt.execution_token,
            expected_previous_fence_token=1,
            actor="g1-worker-b",
        )

    assert provider.calls == []
    events = list(
        db_session.exec(
            select(OrganizationExecutionHeartbeat).where(
                OrganizationExecutionHeartbeat.execution_attempt_id == attempt.id
            )
        ).all()
    )
    assert len(events) == 1


def test_g1_takeover_rejects_blind_claim_after_fence_advanced(
    db_session: Session,
) -> None:
    idempotency_key = "g1-takeover-stale-observation"
    proposal, readiness, graph, work, runtime_profile, attempt = _interrupted_attempt(
        db_session,
        idempotency_key=idempotency_key,
    )
    _expire_current_lease(db_session, attempt.id)
    claimed = claim_execution_runtime_session(
        db_session,
        tenant_key=proposal.context.tenant_key,
        work_item_id=work.id,
        execution_attempt_id=attempt.id,
        position_key="austria_independent_verifier",
        expected_execution_token=attempt.execution_token,
        writer="g1-worker-b",
    )
    assert claimed.fence_token == 2
    provider = FakeProvider(
        name="openai",
        model="gpt-verifier",
        content=_verifier_output(graph),
    )

    with pytest.raises(DependencyConflict, match="stale previous fence token"):
        runtime_service.resume_fenced_independent_eligibility_verification_with_takeover(
            db_session,
            proposal=proposal,
            readiness=readiness,
            verification_work_item_id=work.id,
            verifier_position_key="austria_independent_verifier",
            verifier_runtime_profile=runtime_profile,
            provider=provider,
            idempotency_key=idempotency_key,
            execution_attempt_id=attempt.id,
            expected_execution_token=attempt.execution_token,
            expected_previous_fence_token=1,
            actor="g1-worker-c",
        )

    assert provider.calls == []

def test_superseded_g1_worker_cannot_commit_verification_activity(
    db_session: Session,
) -> None:
    proposal, readiness, _, _, graph, _, verification_work, _ = _setup(db_session)

    def claim_new_fence() -> None:
        attempt = db_session.exec(
            select(OrganizationExecutionAttempt).where(
                OrganizationExecutionAttempt.work_item_id == verification_work.id,
                OrganizationExecutionAttempt.status == "running",
            )
        ).one()
        _expire_current_lease(db_session, attempt.id)
        claimed = claim_execution_runtime_session(
            db_session,
            tenant_key=proposal.context.tenant_key,
            work_item_id=verification_work.id,
            execution_attempt_id=attempt.id,
            position_key="austria_independent_verifier",
            expected_execution_token=attempt.execution_token,
            writer="g1-worker-b",
        )
        assert claimed.fence_token == 2

    with pytest.raises(DependencyConflict, match="completion fence token is stale"):
        runtime_service.execute_fenced_independent_eligibility_verification(
            db_session,
            proposal=proposal,
            readiness=readiness,
            verification_work_item_id=verification_work.id,
            verifier_position_key="austria_independent_verifier",
            verifier_runtime_profile=_verifier_runtime(),
            provider=FakeProvider(
                name="openai",
                model="gpt-verifier",
                content=_verifier_output(graph),
                on_complete=claim_new_fence,
            ),
            idempotency_key="g1-superseded-worker",
        )

    verification_activities = list(
        db_session.exec(
            select(OrganizationActivity).where(
                OrganizationActivity.work_item_id == verification_work.id,
                OrganizationActivity.activity_type
                == "verification.eligibility.independent.v1",
            )
        ).all()
    )
    assert verification_activities == []

    work = db_session.get(OrganizationalWorkItem, verification_work.id)
    assert work is not None
    assert work.status == "running"

    attempt = db_session.exec(
        select(OrganizationExecutionAttempt).where(
            OrganizationExecutionAttempt.work_item_id == verification_work.id
        )
    ).one()
    assert attempt.status == "running"

    events = list(
        db_session.exec(
            select(OrganizationExecutionHeartbeat)
            .where(OrganizationExecutionHeartbeat.execution_attempt_id == attempt.id)
            .order_by(OrganizationExecutionHeartbeat.sequence)
        ).all()
    )
    assert [event.checkpoint for event in events] == [
        "attempt_started",
        "runtime_session_claimed",
    ]
    assert events[-1].writer == "g1-worker-b"
