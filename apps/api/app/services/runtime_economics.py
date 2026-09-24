from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlmodel import Session, select

from app.core import db as db_module
from app.models.runtime_economics import AgentRunProviderAttempt
from app.services.llm_client import LLMProvider, LLMResponse


class RuntimeEconomicsError(RuntimeError):
    """A paid call must not proceed without durable accounting identity."""


def complete_recorded(
    *,
    run_id: UUID,
    attempt_no: int,
    provider: LLMProvider,
    system_prompt: str,
    messages: list[dict[str, str]],
    response_format: dict | None,
) -> LLMResponse:
    # Commit before crossing the network boundary. An interrupted call remains
    # 'started' with unknown spend, rather than silently disappearing.
    with Session(db_module.engine) as session:
        if session.exec(
            select(AgentRunProviderAttempt).where(
                AgentRunProviderAttempt.agent_run_id == run_id,
                AgentRunProviderAttempt.attempt_no == attempt_no,
            )
        ).first():
            raise RuntimeEconomicsError("Provider attempt already recorded; refusing duplicate paid call")
        entry = AgentRunProviderAttempt(
            agent_run_id=run_id,
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
        entry = session.get(AgentRunProviderAttempt, entry_id)
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
