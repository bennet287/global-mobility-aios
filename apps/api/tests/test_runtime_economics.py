from decimal import Decimal
from datetime import datetime, timedelta, timezone

import pytest
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from billiard.exceptions import SoftTimeLimitExceeded
from sqlmodel import Session, select

from app.models.domain import AgentRun, AgentRunStatus, AuditLog
from app.models.runtime_economics import AgentRunProviderAttempt, ProviderCallAllocation, ProviderCallAttempt
from app.schemas import ControlledAgentRunRequest
from app.services.controlled_agents import run_controlled_agent
from app.services.llm_client import (
    LLMProviderConfigurationError, LLMProviderTransportError, LLMResponse,
)
from app.services.runtime_economics import (
    RuntimeEconomicsError, _settle, complete_recorded, reconcile_stranded_provider_attempts,
)
from app.tasks.agent_tasks import reconcile_stale_agent_runs_task


def test_cost_evidence_is_admin_only_and_empty_spend_is_unknown(client) -> None:
    endpoint = "/api/v1/runtime-economics/cost-evidence"
    client.headers["X-GMAI-Role"] = "read_only"
    assert client.get(endpoint).status_code == 403
    client.headers["X-GMAI-Role"] = "admin"
    report = client.get(endpoint).json()
    assert report["scope"] == "direct_model_calls_only"
    assert report["providers"] == []
    assert report["paid_tool_cost_coverage"] == "unreconciled"
    assert report["monetary_budget"]["enforceable"] is False
    assert report["monetary_budget"]["actual_spend_usd"] is None
    assert report["monetary_budget"]["remaining_usd"] is None


def test_cost_evidence_separates_partial_estimates_from_unverified_billing(
    client, db_session: Session,
) -> None:
    db_session.add_all([
        ProviderCallAttempt(
            operation_key="economics:deepseek:1", attempt_no=1, provider="deepseek",
            status="observed", total_tokens=20, provider_response_id="chatcmpl-observed",
            estimated_cost_usd=Decimal("0.000002000"),
        ),
        ProviderCallAttempt(
            operation_key="economics:deepseek:2", attempt_no=1, provider="deepseek",
            status="outcome_unknown",
            # An unattributed column value is still not an invoice or proof.
            billed_cost_usd=Decimal("1.230000000"), cost_basis="provider_billed",
        ),
        ProviderCallAttempt(
            operation_key="economics:gemini:1", attempt_no=1, provider="gemini",
            status="observed", total_tokens=10,
        ),
    ])
    db_session.commit()

    report = client.get("/api/v1/runtime-economics/cost-evidence").json()
    deepseek, gemini = report["providers"]
    assert deepseek == {
        "provider": "deepseek", "attempts": 2,
        "unsettled_or_unknown_attempts": 1,
        "usage_observed_attempts": 1,
        "response_id_available_attempts": 1,
        "estimate_available_attempts": 1,
        "estimated_cost_usd_partial": "0.000002000",
        "unverified_billed_value_attempts": 1,
        "actual_billed_cost_usd": None,
    }
    assert gemini["estimated_cost_usd_partial"] is None
    assert gemini["actual_billed_cost_usd"] is None
    assert report["monetary_budget"]["actual_spend_usd"] is None
    assert report["monetary_budget"]["enforceable"] is False


def test_controlled_run_records_usage_even_when_output_is_malformed(
    client, db_session: Session, monkeypatch
) -> None:
    class Provider:
        name = "deepseek"
        default_model = "deepseek-chat"

        def complete(self, **kwargs):
            return LLMResponse(
                content="not JSON", provider=self.name, model=self.default_model,
                prompt_tokens=12, completion_tokens=3, total_tokens=15,
            )

    monkeypatch.setattr("app.services.controlled_agents._should_use_llm", lambda: True)
    monkeypatch.setattr("app.services.controlled_agents.LLMProviderFactory.get_provider", Provider)
    result = client.post(
        "/api/v1/controlled-agents/run",
        json={"agent_name": "sales_summary_agent", "task": "Test malformed output."},
    )
    assert result.status_code == 200
    entry = db_session.exec(select(AgentRunProviderAttempt)).one()
    assert str(entry.agent_run_id) == result.json()["run_id"]
    assert entry.attempt_no == 1
    assert entry.status == "observed"
    assert entry.total_tokens == 15
    assert entry.cost_basis == "estimated"
    assert entry.estimated_cost_usd is not None
    assert entry.billed_cost_usd is None


def test_failed_provider_call_remains_unattributed_and_duplicate_attempt_fails_closed(
    db_session: Session,
) -> None:
    run = AgentRun(agent_name="sales_summary_agent", task="Test retry", status=AgentRunStatus.running.value)
    db_session.add(run)
    db_session.commit()

    class Provider:
        name = "gemini"
        default_model = "gemini-test"
        calls = 0

        def complete(self, **kwargs):
            self.calls += 1
            raise ConnectionError("Provider outcome is unknown")

    provider = Provider()
    arguments = dict(
        run_id=run.id, attempt_no=1, provider=provider,
        system_prompt="test", messages=[], response_format=None,
    )
    with pytest.raises(ConnectionError):
        complete_recorded(**arguments)
    entry = db_session.exec(select(AgentRunProviderAttempt)).one()
    assert entry.status == "outcome_unknown"
    assert entry.cost_basis == "unattributed"
    assert entry.estimated_cost_usd is None
    assert entry.billed_cost_usd is None
    with pytest.raises(RuntimeEconomicsError, match="duplicate paid call"):
        complete_recorded(**arguments)
    assert provider.calls == 1

    class SuccessfulProvider(Provider):
        def complete(self, **kwargs):
            self.calls += 1
            return LLMResponse(content="{}", provider=self.name, model=self.default_model, total_tokens=7)

    second = SuccessfulProvider()
    complete_recorded(**{**arguments, "attempt_no": 2, "provider": second})
    entries = db_session.exec(select(AgentRunProviderAttempt).order_by(AgentRunProviderAttempt.attempt_no)).all()
    assert [entry.attempt_no for entry in entries] == [1, 2]
    assert entries[1].status == "observed"
    assert entries[1].cost_basis == "unattributed"  # Unknown Gemini billing tier.
    assert entries[1].billed_cost_usd is None


def test_soft_timeout_keeps_unknown_cost_and_reaches_worker_boundary(
    db_session: Session, monkeypatch
) -> None:
    class TimedOutProvider:
        name = "deepseek"
        default_model = "deepseek-chat"

        def complete(self, **kwargs):
            raise SoftTimeLimitExceeded()

    monkeypatch.setattr("app.services.controlled_agents._should_use_llm", lambda: True)
    monkeypatch.setattr("app.services.controlled_agents.LLMProviderFactory.get_provider", TimedOutProvider)
    with pytest.raises(SoftTimeLimitExceeded):
        run_controlled_agent(
            db_session,
            ControlledAgentRunRequest(agent_name="sales_summary_agent", task="Timeout"),
        )
    entry = db_session.exec(select(AgentRunProviderAttempt)).one()
    assert entry.status == "outcome_unknown"
    assert entry.billed_cost_usd is None


def test_non_agent_call_records_usage_and_rejects_replayed_operation_key(db_session: Session) -> None:
    class Provider:
        name = "deepseek"
        default_model = "deepseek-chat"
        calls = 0

        def complete(self, **kwargs):
            self.calls += 1
            return LLMResponse(
                content="{}", provider=self.name, model=self.default_model,
                prompt_tokens=8, completion_tokens=2, total_tokens=10,
                provider_response_id=" chatcmpl-123 ",
            )

    provider = Provider()
    arguments = dict(
        context_kind="regulatory_change", context_id="change-123",
        operation_key="regulatory_change:change-123:classification:1",
        provider=provider, system_prompt="classify", messages=[], response_format=None,
    )
    complete_recorded(**arguments)
    entry = db_session.exec(select(ProviderCallAttempt)).one()
    assert entry.agent_run_id is None
    assert entry.operation_key == arguments["operation_key"]
    assert (entry.context_kind, entry.context_id) == ("regulatory_change", "change-123")
    assert entry.status == "observed"
    assert entry.total_tokens == 10
    assert entry.provider_response_id == "chatcmpl-123"
    assert entry.billed_cost_usd is None
    with pytest.raises(RuntimeEconomicsError, match="duplicate paid call"):
        complete_recorded(**arguments)
    assert provider.calls == 1


def test_non_agent_failed_call_preserves_unknown_outcome(db_session: Session) -> None:
    class Provider:
        name = "gemini"
        default_model = "gemini-test"

        def complete(self, **kwargs):
            raise ConnectionError("outcome unknown")

    with pytest.raises(ConnectionError):
        complete_recorded(
            context_kind="inhouse_consultant_request", provider=Provider(),
            system_prompt="review", messages=[], response_format=None,
        )
    entry = db_session.exec(select(ProviderCallAttempt)).one()
    assert entry.agent_run_id is None
    assert entry.operation_key.startswith("inhouse_consultant_request:")
    assert entry.status == "outcome_unknown"
    assert entry.cost_basis == "unattributed"
    assert entry.billed_cost_usd is None


def test_admin_authorizes_call_slots_without_inflating_replayed_grants(client, db_session: Session) -> None:
    endpoint = "/api/v1/runtime-economics/providers/deepseek/capacity"
    client.headers["X-GMAI-Role"] = "read_only"
    assert client.put(endpoint, json={"authorized_calls": 1, "reason": "Admin authorizes one call"}).status_code == 403
    assert client.get(endpoint).status_code == 403
    client.headers["X-GMAI-Role"] = "admin"
    payload = {"authorized_calls": 1, "reason": "Admin authorizes one call"}
    assert client.put(endpoint, json=payload).json()["remaining_calls"] == 1
    assert client.put(endpoint, json=payload).json()["remaining_calls"] == 1
    assert client.put(endpoint, json={"authorized_calls": 0, "reason": "Try to retract"}).status_code == 409
    assert len(db_session.exec(select(AuditLog).where(AuditLog.action == "provider_call_capacity_authorized")).all()) == 1

    class Provider:
        name = "deepseek"
        default_model = "deepseek-chat"
        calls = 0

        def complete(self, **kwargs):
            self.calls += 1
            return LLMResponse(content="{}", provider=self.name, model=self.default_model, total_tokens=6)

    provider = Provider()
    arguments = dict(
        context_kind="business_advisory_request", provider=provider,
        operation_key="business_advisory_request:bounded-1",
        system_prompt="test", messages=[], response_format=None,
    )
    complete_recorded(**arguments)
    assert client.get(endpoint).json()["remaining_calls"] == 0
    with pytest.raises(RuntimeEconomicsError, match="duplicate paid call"):
        complete_recorded(**arguments)
    with pytest.raises(RuntimeEconomicsError, match="exhausted or paused"):
        complete_recorded(**{**arguments, "operation_key": "business_advisory_request:bounded-2"})
    assert provider.calls == 1
    paid_call = db_session.exec(select(ProviderCallAttempt)).one()
    assert paid_call.allocation_provider == "deepseek"
    assert paid_call.billed_cost_usd is None

    assert client.put(endpoint, json={"authorized_calls": 2, "reason": "Admin granted one more"}).json()["remaining_calls"] == 1
    assert client.put(endpoint, json={"authorized_calls": 2, "paused": True, "reason": "Pause"}).json()["paused"] is True
    with pytest.raises(RuntimeEconomicsError, match="exhausted or paused"):
        complete_recorded(**{**arguments, "operation_key": "business_advisory_request:bounded-2"})
    assert provider.calls == 1
    assert client.put(endpoint, json={"authorized_calls": 2, "paused": False, "reason": "Resume"}).json()["remaining_calls"] == 1
    complete_recorded(**{**arguments, "operation_key": "business_advisory_request:bounded-2"})
    assert provider.calls == 2
    assert client.get(endpoint).json()["remaining_calls"] == 0


def test_unknown_outcome_consumes_authorized_slot(db_session: Session) -> None:
    db_session.add(ProviderCallAllocation(
        provider="gemini", authorized_calls=1, authorized_by="admin", reason="Bounded trial",
    ))
    db_session.commit()

    class Provider:
        name = "gemini"

        def complete(self, **kwargs):
            raise ConnectionError("Provider outcome unknown")

    args = dict(context_kind="inhouse_consultant_request", provider=Provider(),
                system_prompt="test", messages=[], response_format=None)
    with pytest.raises(ConnectionError):
        complete_recorded(**args)
    with pytest.raises(RuntimeEconomicsError, match="exhausted or paused"):
        complete_recorded(**args)
    row = db_session.exec(select(ProviderCallAttempt)).one()
    assert row.allocation_provider == "gemini"
    assert row.status == "outcome_unknown"
    db_session.refresh(db_session.get(ProviderCallAllocation, "gemini"))
    assert db_session.get(ProviderCallAllocation, "gemini").used_calls == 1


def test_simultaneous_calls_cannot_exceed_one_authorized_slot(db_session: Session) -> None:
    db_session.add(ProviderCallAllocation(
        provider="deepseek", authorized_calls=1, authorized_by="admin", reason="One call",
    ))
    db_session.commit()
    crossed = Event()
    release = Event()

    class Provider:
        name = "deepseek"

        def complete(self, **kwargs):
            crossed.set()
            assert release.wait(5)
            return LLMResponse(content="{}", provider=self.name, model="deepseek-chat")

    args = dict(context_kind="regulatory_change", provider=Provider(),
                system_prompt="test", messages=[], response_format=None)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(complete_recorded, **args)
        assert crossed.wait(5)
        with pytest.raises(RuntimeEconomicsError, match="exhausted or paused"):
            complete_recorded(**args)
        release.set()
        first.result(timeout=5)
    assert len(db_session.exec(select(ProviderCallAttempt)).all()) == 1


def test_reconciliation_requires_finished_agent_run_and_preserves_unknown_spend(
    db_session: Session,
) -> None:
    now = datetime.now(timezone.utc)
    old = (now - timedelta(seconds=361)).replace(tzinfo=None)
    finished = AgentRun(agent_name="sales_summary_agent", task="Finished", status="failed")
    active = AgentRun(agent_name="sales_summary_agent", task="Active", status="running")
    db_session.add_all([finished, active])
    db_session.commit()
    # Keep the capacity reservation even if this attempt's vendor charge is unknown.
    db_session.add(ProviderCallAllocation(
        provider="deepseek", authorized_calls=1, used_calls=1,
        authorized_by="admin", reason="One call",
    ))
    db_session.commit()
    stranded = ProviderCallAttempt(
        agent_run_id=finished.id, attempt_no=1, provider="deepseek", started_at=old,
        allocation_provider="deepseek",
    )
    db_session.add_all([
        stranded,
        ProviderCallAttempt(agent_run_id=active.id, attempt_no=1,
                            provider="gemini", started_at=old),
        ProviderCallAttempt(operation_key="request:without-terminal-signal", attempt_no=1,
                            provider="gemini", started_at=old),
        ProviderCallAttempt(agent_run_id=finished.id, attempt_no=2,
                            provider="moonshot", started_at=now.replace(tzinfo=None)),
    ])
    db_session.commit()

    result = reconcile_stranded_provider_attempts(db_session, hard_limit_seconds=300, now=now)
    assert result == {"scanned": 1, "reconciled": 1, "stale_after_seconds": 360}
    db_session.refresh(stranded)
    assert stranded.status == "outcome_unknown"
    assert stranded.settled_at is not None
    assert stranded.billed_cost_usd is None
    assert stranded.cost_basis == "unattributed"
    assert db_session.get(ProviderCallAllocation, "deepseek").used_calls == 1
    assert len(db_session.exec(select(ProviderCallAttempt)
               .where(ProviderCallAttempt.status == "started")).all()) == 3
    assert reconcile_stranded_provider_attempts(
        db_session, hard_limit_seconds=300, now=now,
    )["reconciled"] == 0
    log = db_session.exec(select(AuditLog)
        .where(AuditLog.action == "provider_attempt_stranded_reconciled")).one()
    assert log.entity_id == str(stranded.id)
    assert '"cause_inferred": false' in (log.after_state_json or "")
    assert '"billed_cost_known": false' in (log.after_state_json or "")

    with pytest.raises(RuntimeEconomicsError, match="settlement identity was lost"):
        _settle(stranded.id, LLMResponse(
            content="late response", provider="deepseek", model="deepseek-chat",
            total_tokens=5,
        ))
    db_session.refresh(stranded)
    assert stranded.status == "outcome_unknown"
    assert stranded.total_tokens is None


def test_beat_reuses_agent_reconciliation_and_closes_old_terminal_attempt(
    db_session: Session,
) -> None:
    run = AgentRun(agent_name="sales_summary_agent", task="Interrupted", status="failed")
    db_session.add(run)
    db_session.commit()
    attempt = ProviderCallAttempt(
        agent_run_id=run.id, attempt_no=1, provider="gemini",
        started_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db_session.add(attempt)
    db_session.commit()
    result = reconcile_stale_agent_runs_task.run()
    assert result["reconciled"] == 0
    assert result["provider_attempts"]["reconciled"] == 1
    db_session.refresh(attempt)
    assert attempt.status == "outcome_unknown"


def test_enrolled_provider_circuit_trips_without_granting_money_or_more_calls(
    client, db_session: Session,
) -> None:
    capacity = "/api/v1/runtime-economics/providers/deepseek/capacity"
    reset = "/api/v1/runtime-economics/providers/deepseek/circuit/reset"
    assert client.put(capacity, json={
        "authorized_calls": 5, "reason": "Five test calls",
    }).json()["breaker_open"] is False

    class TransportFailure:
        name = "deepseek"
        calls = 0

        def complete(self, **kwargs):
            self.calls += 1
            raise LLMProviderTransportError("transient failure")

    provider = TransportFailure()
    args = dict(context_kind="business_advisory_request", provider=provider,
                system_prompt="test", messages=[], response_format=None)
    for attempt in range(3):
        with pytest.raises(LLMProviderTransportError):
            complete_recorded(**args, operation_key=f"breaker:test:{attempt}")
    db_session.expire_all()
    state = client.get(capacity).json()
    assert state["breaker_open"] is True
    assert state["breaker_failures"] == state["breaker_failure_threshold"] == 3
    assert state["paused"] is False
    assert state["used_calls"] == 3
    assert state["remaining_calls"] == 2
    assert state["breaker_scope"] == "admin_enrolled_provider_only"
    assert state["breaker_opened_at"] is not None
    with pytest.raises(RuntimeEconomicsError, match="Provider circuit open"):
        complete_recorded(**args, operation_key="breaker:test:blocked")
    assert provider.calls == 3
    assert len(db_session.exec(select(ProviderCallAttempt)).all()) == 3
    trips = db_session.exec(select(AuditLog)
        .where(AuditLog.action == "provider_circuit_opened")).all()
    assert len(trips) == 1
    assert '"billed_cost_known": false' in (trips[0].after_state_json or "")
    assert client.get("/api/v1/runtime-economics/cost-evidence").json()[
        "monetary_budget"
    ]["enforceable"] is False

    # A call-capacity edit cannot accidentally clear the independent circuit.
    assert client.put(capacity, json={
        "authorized_calls": 6, "reason": "Increase call capacity",
    }).json()["breaker_open"] is True
    client.headers["X-GMAI-Role"] = "read_only"
    assert client.post(reset, json={"reason": "Review incident"}).status_code == 403
    client.headers["X-GMAI-Role"] = "admin"
    assert client.post(reset, json={"reason": " "}).status_code == 422
    resumed = client.post(reset, json={"reason": "Reviewed transport incident"}).json()
    assert resumed["breaker_open"] is False
    assert resumed["breaker_failures"] == 0
    assert resumed["used_calls"] == 3
    assert resumed["authorized_calls"] == 6
    assert client.post(reset, json={"reason": "Repeated reset"}).status_code == 200
    assert len(db_session.exec(select(AuditLog)
        .where(AuditLog.action == "provider_circuit_reset")).all()) == 1


def test_breaker_counts_only_consecutive_classified_failures_and_is_provider_scoped(
    db_session: Session,
) -> None:
    db_session.add(ProviderCallAllocation(
        provider="moonshot", authorized_calls=7, authorized_by="admin", reason="Trial",
    ))
    db_session.commit()

    class Provider:
        name = "moonshot"
        calls = 0

        def __init__(self):
            self.outcome = "transport"

        def complete(self, **kwargs):
            self.calls += 1
            if self.outcome == "transport":
                raise LLMProviderTransportError("temporary")
            if self.outcome == "configuration":
                raise LLMProviderConfigurationError("invalid credentials")
            return LLMResponse(content="{}", provider=self.name, model="kimi-test")

    provider = Provider()
    args = dict(context_kind="inhouse_consultant_request", provider=provider,
                system_prompt="test", messages=[], response_format=None)
    for number, outcome in enumerate(("transport", "success", "transport", "configuration",
                                      "transport", "transport", "transport")):
        provider.outcome = outcome
        call = lambda: complete_recorded(**args, operation_key=f"breaker:streak:{number}")
        if outcome == "success":
            call()
        else:
            with pytest.raises(LLMProviderTransportError if outcome == "transport"
                               else LLMProviderConfigurationError):
                call()
        db_session.refresh(db_session.get(ProviderCallAllocation, "moonshot"))
        if number < 6:
            assert db_session.get(ProviderCallAllocation, "moonshot").breaker_open is False
    allocation = db_session.get(ProviderCallAllocation, "moonshot")
    assert allocation.breaker_open is True
    assert allocation.breaker_failures == 3

    # No enrollment implies no circuit or call reservation for another provider.
    class Unenrolled(Provider):
        name = "gemini"

    other = Unenrolled()
    for number in range(3):
        with pytest.raises(LLMProviderTransportError):
            complete_recorded(**{**args, "provider": other},
                              operation_key=f"unenrolled:{number}")
    assert other.calls == 3
    assert db_session.get(ProviderCallAllocation, "gemini") is None


def test_circuit_trip_blocks_new_calls_but_does_not_revoke_in_flight_attempt(
    db_session: Session,
) -> None:
    db_session.add(ProviderCallAllocation(
        provider="deepseek", authorized_calls=5, authorized_by="admin", reason="Trial",
    ))
    db_session.commit()
    entered, release = Event(), Event()

    class Provider:
        name = "deepseek"

        def __init__(self, delayed=False):
            self.delayed = delayed

        def complete(self, **kwargs):
            if not self.delayed:
                raise LLMProviderTransportError("provider unavailable")
            entered.set()
            assert release.wait(5)
            return LLMResponse(content="{}", provider=self.name, model="deepseek-chat")

    args = dict(context_kind="business_advisory_request",
                system_prompt="test", messages=[], response_format=None)
    failure = Provider()
    for number in range(2):
        with pytest.raises(LLMProviderTransportError):
            complete_recorded(**args, provider=failure, operation_key=f"inflight:failure:{number}")
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(complete_recorded, **args, provider=Provider(delayed=True),
                             operation_key="inflight:admitted")
        assert entered.wait(5)
        with pytest.raises(LLMProviderTransportError):
            complete_recorded(**args, provider=failure, operation_key="inflight:trip")
        with pytest.raises(RuntimeEconomicsError, match="Provider circuit open"):
            complete_recorded(**args, provider=failure, operation_key="inflight:blocked")
        release.set()
        assert future.result(timeout=5).total_tokens is None
    db_session.refresh(db_session.get(ProviderCallAllocation, "deepseek"))
    state = db_session.get(ProviderCallAllocation, "deepseek")
    assert state.breaker_open is True
    assert state.used_calls == 4
    assert len(db_session.exec(select(ProviderCallAttempt)).all()) == 4
