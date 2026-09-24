import pytest
from billiard.exceptions import SoftTimeLimitExceeded
from sqlmodel import Session, select

from app.models.domain import AgentRun, AgentRunStatus
from app.models.runtime_economics import AgentRunProviderAttempt, ProviderCallAttempt
from app.schemas import ControlledAgentRunRequest
from app.services.controlled_agents import run_controlled_agent
from app.services.llm_client import LLMResponse
from app.services.runtime_economics import RuntimeEconomicsError, complete_recorded


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
