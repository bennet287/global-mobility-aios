from __future__ import annotations

import pytest
from sqlmodel import Session, select

from app.models.domain import OrganizationExecutionAttempt, OrganizationalWorkItem
from app.models.organization_presence import OrganizationExecutionHeartbeat
from app.services.organization_command import canonical_fingerprint
from app.services.organization_eligibility_verifier_runtime_session import (
    DEFAULT_ELIGIBILITY_VERIFIER_RUNTIME_WRITER,
    ELIGIBILITY_VERIFIER_RUNTIME_SESSION_CONTRACT_VERSION,
    execute_fenced_independent_eligibility_verification,
)
from app.services.organization_execution_failure import RUNTIME_SESSION_FAILED
from app.services.organization_independent_eligibility_verification import (
    IndependentEligibilityVerificationRuntimeError,
    IndependentVerificationDisposition,
)
from tests.test_organization_independent_eligibility_verification import (
    FakeProvider,
    _setup,
    _verifier_output,
    _verifier_runtime,
)


def _attempts(
    session: Session,
    *,
    work_item_id,
) -> list[OrganizationExecutionAttempt]:
    return list(
        session.exec(
            select(OrganizationExecutionAttempt)
            .where(OrganizationExecutionAttempt.work_item_id == work_item_id)
            .order_by(OrganizationExecutionAttempt.attempt_number)
        ).all()
    )


def _events(
    session: Session,
    *,
    attempt_id,
) -> list[OrganizationExecutionHeartbeat]:
    return list(
        session.exec(
            select(OrganizationExecutionHeartbeat)
            .where(
                OrganizationExecutionHeartbeat.execution_attempt_id == attempt_id
            )
            .order_by(OrganizationExecutionHeartbeat.sequence)
        ).all()
    )


def test_fenced_g1_runtime_binds_token_to_consumed_verifier_context(
    db_session: Session,
) -> None:
    proposal, readiness, _, _, graph, _, verification_work, _ = _setup(db_session)

    wrapped = execute_fenced_independent_eligibility_verification(
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
        ),
        idempotency_key="g1-fenced-success",
    )

    assert wrapped.result.disposition is IndependentVerificationDisposition.AGREES
    assert wrapped.writer == DEFAULT_ELIGIBILITY_VERIFIER_RUNTIME_WRITER
    assert wrapped.fence_token == 1

    work = db_session.get(OrganizationalWorkItem, verification_work.id)
    assert work is not None
    assert work.status == "completed"
    assert work.execution_started_at is None
    assert work.last_error is None
    assert work.execution_attempts == 1

    attempts = _attempts(db_session, work_item_id=verification_work.id)
    assert len(attempts) == 1
    attempt = attempts[0]
    assert attempt.id == wrapped.execution_attempt_id
    assert attempt.status == "completed"
    assert attempt.actor == DEFAULT_ELIGIBILITY_VERIFIER_RUNTIME_WRITER

    expected_token = canonical_fingerprint(
        {
            "contract_version": ELIGIBILITY_VERIFIER_RUNTIME_SESSION_CONTRACT_VERSION,
            "work_item_id": verification_work.id,
            "position_key": "austria_independent_verifier",
            "attempt_number": attempt.attempt_number,
            "context_hash": wrapped.result.verifier_context.context_hash,
            "runtime_binding_hash": wrapped.result.verifier_runtime_binding.binding_hash,
            "proposal_trace_id": proposal.evaluation.trace_id,
            "proposal_activity_id": proposal.attempt_activity.id,
            "proposal_intent_fingerprint": proposal.intent_fingerprint,
            "readiness_fingerprint": readiness.readiness_fingerprint,
            "verification_idempotency_fingerprint": canonical_fingerprint(
                {"idempotency_key": "g1-fenced-success"}
            ),
        }
    )
    assert expected_token == wrapped.execution_token
    assert attempt.execution_token == expected_token
    assert work.execution_token == expected_token
    assert (
        wrapped.result.verifier_runtime_binding.context_hash
        == wrapped.result.verifier_context.context_hash
    )

    events = _events(db_session, attempt_id=attempt.id)
    assert [event.sequence for event in events] == [1, 2]
    assert [event.checkpoint for event in events] == [
        "attempt_started",
        "agent_completed",
    ]
    assert all(event.writer == DEFAULT_ELIGIBILITY_VERIFIER_RUNTIME_WRITER for event in events)


def test_fenced_g1_runtime_uses_shared_failure_finalizer(
    db_session: Session,
) -> None:
    proposal, readiness, _, _, graph, _, verification_work, _ = _setup(db_session)

    with pytest.raises(
        IndependentEligibilityVerificationRuntimeError,
        match="response model",
    ):
        execute_fenced_independent_eligibility_verification(
            db_session,
            proposal=proposal,
            readiness=readiness,
            verification_work_item_id=verification_work.id,
            verifier_position_key="austria_independent_verifier",
            verifier_runtime_profile=_verifier_runtime(),
            provider=FakeProvider(
                name="openai",
                model="gpt-verifier",
                response_model="drifted-verifier-model",
                content=_verifier_output(graph),
            ),
            idempotency_key="g1-fenced-failure",
        )

    work = db_session.get(OrganizationalWorkItem, verification_work.id)
    assert work is not None
    assert work.status == "running"
    assert work.execution_started_at is None
    assert work.last_error is not None
    assert "IndependentEligibilityVerificationRuntimeError" in work.last_error
    assert work.execution_attempts == 1

    attempts = _attempts(db_session, work_item_id=verification_work.id)
    assert len(attempts) == 1
    attempt = attempts[0]
    assert attempt.status == "failed"
    assert attempt.completed_at is not None
    assert attempt.error is not None
    assert "IndependentEligibilityVerificationRuntimeError" in attempt.error

    events = _events(db_session, attempt_id=attempt.id)
    assert [event.sequence for event in events] == [1, 2]
    assert [event.checkpoint for event in events] == [
        "attempt_started",
        RUNTIME_SESSION_FAILED,
    ]
    assert all(event.writer == DEFAULT_ELIGIBILITY_VERIFIER_RUNTIME_WRITER for event in events)
