from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlmodel import Session, select

from app.core import db as db_module
from app.models.runtime_economics import ProviderCallAttempt
from app.services.llm_client import LLMProvider, LLMResponse


class RuntimeEconomicsError(RuntimeError):
    """A paid call must not proceed without durable accounting identity."""


def complete_recorded(
    *,
    provider: LLMProvider,
    system_prompt: str,
    messages: list[dict[str, str]],
    response_format: dict | None,
    run_id: UUID | None = None,
    attempt_no: int = 1,
    context_kind: str | None = None,
    context_id: str | None = None,
    operation_key: str | None = None,
) -> LLMResponse:
    if (run_id is None) == (context_kind is None):
        raise RuntimeEconomicsError("Exactly one paid-call context is required")
    if run_id is None:
        operation_key = operation_key or f"{context_kind}:{uuid4()}"
    elif operation_key is not None:
        raise RuntimeEconomicsError("AgentRun attempt identity cannot be overridden")
    # Commit before crossing the network boundary. An interrupted call remains
    # 'started' with unknown spend, rather than silently disappearing.
    with Session(db_module.engine) as session:
        prior = (
            select(ProviderCallAttempt).where(
                ProviderCallAttempt.agent_run_id == run_id,
                ProviderCallAttempt.attempt_no == attempt_no,
            )
            if run_id is not None
            else select(ProviderCallAttempt).where(ProviderCallAttempt.operation_key == operation_key)
        )
        if session.exec(prior).first():
            raise RuntimeEconomicsError("Provider attempt already recorded; refusing duplicate paid call")
        entry = ProviderCallAttempt(
            agent_run_id=run_id,
            operation_key=operation_key,
            context_kind=context_kind,
            context_id=context_id,
            attempt_no=attempt_no,
            provider=provider.name,
            requested_model=getattr(provider, "default_model", None),
        )
        session.add(entry)
        try:
            session.commit()
            entry_id = entry.id
        except Exception as exc:
            raise RuntimeEconomicsError("Could not persist provider attempt before paid call") from exc

    try:
        response = provider.complete(
            system_prompt=system_prompt,
            messages=messages,
            response_format=response_format,
        )
    except Exception:
        _settle(entry_id, None)
        raise
    _settle(entry_id, response)
    return response


def _settle(entry_id: UUID, response: LLMResponse | None) -> None:
    with Session(db_module.engine) as session:
        entry = session.get(ProviderCallAttempt, entry_id)
        if entry is None or entry.status != "started":
            raise RuntimeEconomicsError("Provider attempt settlement identity was lost")
        entry.settled_at = datetime.now(timezone.utc)
        if response is None:
            entry.status = "outcome_unknown"
        else:
            entry.status = "observed"
            entry.provider = response.provider
            entry.model = response.model
            entry.prompt_tokens = response.prompt_tokens
            entry.completion_tokens = response.completion_tokens
            entry.total_tokens = response.total_tokens
            if response.estimated_cost_usd is not None:
                entry.estimated_cost_usd = Decimal(str(response.estimated_cost_usd))
                entry.cost_basis = "estimated"
            # Current adapters expose no authoritative billed amount. NULL is not zero.
        session.add(entry)
        try:
            session.commit()
        except Exception as exc:
            raise RuntimeEconomicsError("Could not settle provider attempt") from exc
