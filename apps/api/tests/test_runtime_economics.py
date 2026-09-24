from decimal import Decimal

import pytest
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from billiard.exceptions import SoftTimeLimitExceeded
from sqlmodel import Session, select

from app.models.domain import AgentRun, AgentRunStatus, AuditLog
from app.models.runtime_economics import AgentRunProviderAttempt, ProviderCallAllocation, ProviderCallAttempt
from app.schemas import ControlledAgentRunRequest
from app.services.controlled_agents import run_controlled_agent
from app.services.llm_client import LLMResponse
from app.services.runtime_economics import RuntimeEconomicsError, complete_recorded


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
            status="observed", total_tokens=20,
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
