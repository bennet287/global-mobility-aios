from __future__ import annotations

from sqlmodel import Session, select

from app.models.domain import OrganizationExecutionAttempt, OrganizationalWorkItem
from app.models.organization_presence import OrganizationExecutionHeartbeat
from app.services.organization_command import canonical_fingerprint
from app.services.llm_client import LLMProvider, LLMProviderTransportError
from app.services.organization_eligibility_runtime_session import (
    ELIGIBILITY_RUNTIME_SESSION_CONTRACT_VERSION,
    execute_fenced_governed_eligibility_transition_intent,
)
from app.services.organization_execution_failure import RUNTIME_SESSION_FAILED
from tests.test_organization_independent_eligibility_verification import (
    FakeProvider,
    _authority,
    _authority_graph,
    _case,
    _position,
    _proposer_output,
    _runtime,
    _work,
)


POSITION_KEY = "austria_mobility_specialist"


def _fixture(session: Session):
    _position(
        session,
        position_key=POSITION_KEY,
        title="Austria Mobility Specialist",
        version=31,
    )
    lead, profile = _case(session)
    graph = _authority_graph(session)
    work = _work(
        session,
        position_key=POSITION_KEY,
        lead=lead,
        profile=profile,
        version=graph["version"],
        title="Fenced eligibility runtime producer",
    )
    runtime = _runtime(
        profile_key="fenced-e2-producer",
        provider_key="deepseek",
        model_key="deepseek-reasoner",
        independence_group="fenced-e2-producer",
    )
    return graph, work, runtime


def _events(session: Session, attempt_id):
    return list(
        session.exec(
            select(OrganizationExecutionHeartbeat)
            .where(OrganizationExecutionHeartbeat.execution_attempt_id == attempt_id)
            .order_by(OrganizationExecutionHeartbeat.sequence)
        ).all()
    )


def test_fenced_e2_runtime_records_attempt_and_terminal_fence(db_session: Session) -> None:
    graph, work, runtime = _fixture(db_session)
    provider = FakeProvider(
        name="deepseek",
        model="deepseek-reasoner",
        content=_proposer_output(graph),
    )

    wrapped = execute_fenced_governed_eligibility_transition_intent(
        db_session,
        tenant_key="tenant-a",
        position_key=POSITION_KEY,
        work_item_id=work.id,
        runtime_profile=runtime,
        authority=_authority(),
        provider=provider,
        idempotency_key="fenced-e2-success",
    )

    assert wrapped.result.mutated is False
    assert wrapped.fence_token == 1
    assert wrapped.writer == "eligibility-runtime-worker"
    assert len(wrapped.execution_token) == 64
    assert len(provider.calls) == 1

    persisted_work = db_session.get(OrganizationalWorkItem, work.id)
    attempt = db_session.get(OrganizationExecutionAttempt, wrapped.execution_attempt_id)
    assert persisted_work is not None and attempt is not None
    assert persisted_work.status == "completed"
    assert persisted_work.execution_started_at is None
    assert persisted_work.execution_token == wrapped.execution_token
    assert attempt.status == "completed"
    assert attempt.execution_token == wrapped.execution_token

    events = _events(db_session, attempt.id)
    assert [event.sequence for event in events] == [1, 2]
    assert [event.checkpoint for event in events] == ["attempt_started", "agent_completed"]
    assert all(event.writer == "eligibility-runtime-worker" for event in events)

    expected_token = canonical_fingerprint(
        {
            "contract_version": ELIGIBILITY_RUNTIME_SESSION_CONTRACT_VERSION,
            "work_item_id": work.id,
            "position_key": POSITION_KEY,
            "attempt_number": attempt.attempt_number,
            "context_hash": wrapped.result.context.context_hash,
            "runtime_binding_hash": wrapped.result.runtime_binding.binding_hash,
        }
    )
    assert expected_token == wrapped.execution_token
    assert wrapped.result.runtime_binding.context_hash == wrapped.result.context.context_hash


class FailingProvider(LLMProvider):
    name = "deepseek"

    def complete(self, system_prompt, messages, response_format=None):
        raise LLMProviderTransportError("synthetic E.2 transport failure")


def test_fenced_e2_runtime_uses_shared_failure_finalizer(db_session: Session) -> None:
    _, work, runtime = _fixture(db_session)

    try:
        execute_fenced_governed_eligibility_transition_intent(
            db_session,
            tenant_key="tenant-a",
            position_key=POSITION_KEY,
            work_item_id=work.id,
            runtime_profile=runtime,
            authority=_authority(),
            provider=FailingProvider(),
            idempotency_key="fenced-e2-provider-failure",
        )
    except Exception as exc:
        assert "transport" in str(exc).casefold() or "runtime" in str(exc).casefold()
    else:  # pragma: no cover - provider is deterministic failure
        raise AssertionError("failing provider unexpectedly succeeded")

    persisted_work = db_session.get(OrganizationalWorkItem, work.id)
    assert persisted_work is not None
    attempts = list(
        db_session.exec(
            select(OrganizationExecutionAttempt).where(
                OrganizationExecutionAttempt.work_item_id == work.id
            )
        ).all()
    )
    assert len(attempts) == 1
    attempt = attempts[0]
    assert attempt.status == "failed"
    assert attempt.error is not None and "transport" in attempt.error.casefold()
    assert persisted_work.status == "running"
    assert persisted_work.execution_started_at is None
    assert persisted_work.last_error is not None

    events = _events(db_session, attempt.id)
    assert [event.sequence for event in events] == [1, 2]
    assert [event.checkpoint for event in events] == ["attempt_started", RUNTIME_SESSION_FAILED]
    assert all(event.writer == "eligibility-runtime-worker" for event in events)
