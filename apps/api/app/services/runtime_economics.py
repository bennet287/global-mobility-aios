from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import case, func, update
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core import db as db_module
from app.models.runtime_economics import ProviderCallAllocation, ProviderCallAttempt
from app.services.audit_log import record_audit
from app.services.llm_client import LLMProvider, LLMResponse


class RuntimeEconomicsError(RuntimeError):
    """A paid call must not proceed without durable accounting identity."""


def summarize_cost_evidence(session: Session) -> dict:
    """Read existing attempts without converting estimates or unaudited values into spend."""
    rows = session.execute(
        select(
            ProviderCallAttempt.provider,
            func.count(ProviderCallAttempt.id),
            func.sum(case((ProviderCallAttempt.status != "observed", 1), else_=0)),
            func.sum(case((ProviderCallAttempt.total_tokens.is_not(None), 1), else_=0)),
            func.sum(case((ProviderCallAttempt.provider_response_id.is_not(None), 1), else_=0)),
            func.sum(case((ProviderCallAttempt.estimated_cost_usd.is_not(None), 1), else_=0)),
            func.sum(ProviderCallAttempt.estimated_cost_usd),
            func.sum(case((ProviderCallAttempt.billed_cost_usd.is_not(None), 1), else_=0)),
        )
        .group_by(ProviderCallAttempt.provider)
        .order_by(ProviderCallAttempt.provider)
    ).all()
    providers = [
        {
            "provider": provider,
            "attempts": attempts,
            "unsettled_or_unknown_attempts": unknown,
            "usage_observed_attempts": with_usage,
            "response_id_available_attempts": with_response_id,
            "estimate_available_attempts": with_estimate,
            "estimated_cost_usd_partial": str(estimated_sum) if estimated_sum is not None else None,
            # A completion ID is a correlation handle, not an invoice line or
            # verified per-call attribution. A manually filled value is not proof.
            "unverified_billed_value_attempts": unverified_billed,
            "actual_billed_cost_usd": None,
        }
        for (
            provider, attempts, unknown, with_usage, with_response_id, with_estimate,
            estimated_sum, unverified_billed,
        ) in rows
    ]
    return {
        "scope": "direct_model_calls_only",
        "providers": providers,
        "paid_tool_cost_coverage": "unreconciled",
        "monetary_budget": {
            "enforceable": False,
            "authorized_usd": None,
            "actual_spend_usd": None,
            "remaining_usd": None,
            "blockers": [
                "authoritative_per_call_billing_evidence_missing",
                "paid_tool_cost_coverage_unreconciled",
                "board_monetary_allocation_not_modeled",
                "provable_pre_call_monetary_ceiling_missing",
            ],
        },
    }


def authorize_provider_calls(
    session: Session, *, provider: str, authorized_calls: int,
    paused: bool, actor: str, reason: str,
) -> ProviderCallAllocation:
    """Set the cumulative call allowance; a repeated request cannot grant extra slots."""
    if provider not in {"deepseek", "moonshot", "gemini"}:
        raise RuntimeEconomicsError("Unsupported provider for governed call capacity")
    if authorized_calls < 0 or authorized_calls > 1_000_000:
        raise RuntimeEconomicsError("Authorized call count must be between 0 and 1,000,000")
    allocation = session.get(ProviderCallAllocation, provider)
    if allocation is not None and authorized_calls < allocation.authorized_calls:
        raise RuntimeEconomicsError("An authorized call allowance cannot be reduced; pause it instead")
    if allocation is not None and authorized_calls == allocation.authorized_calls and paused == allocation.paused:
        return allocation
    before = (
        {"authorized_calls": allocation.authorized_calls, "paused": allocation.paused}
        if allocation is not None else None
    )
    if allocation is None:
        allocation = ProviderCallAllocation(
            provider=provider, authorized_calls=authorized_calls, paused=paused,
            authorized_by=actor, reason=reason,
        )
        session.add(allocation)
    else:
        # Concurrent grants cannot move the authorization backwards.
        updated = session.execute(
            update(ProviderCallAllocation)
            .where(ProviderCallAllocation.provider == provider)
            .where(ProviderCallAllocation.authorized_calls <= authorized_calls)
            .values(
                authorized_calls=authorized_calls, paused=paused,
                authorized_by=actor, reason=reason,
                updated_at=datetime.now(timezone.utc),
            )
            .returning(ProviderCallAllocation.provider)
        ).scalar_one_or_none()
        if updated is None:
            raise RuntimeEconomicsError("Concurrent authorization changed; refresh the allowance")
        session.refresh(allocation)
    record_audit(
        session, action="provider_call_capacity_authorized", entity_type="provider_call_allocation",
        entity_id=provider, actor=actor, reason=reason, before_state=before,
        after_state={"authorized_calls": authorized_calls, "used_calls": allocation.used_calls,
                     "paused": paused, "cost_basis": "call_count_not_money"},
    )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise RuntimeEconomicsError("Concurrent authorization changed; refresh the allowance") from exc
    session.refresh(allocation)
    return allocation


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
        # When an admin has enrolled this provider, reserve one call atomically
        # with the attempt row. A failed or interrupted call retains its slot:
        # there is no provider refund evidence at this boundary.
        allocation = session.get(ProviderCallAllocation, provider.name)
        if allocation is not None:
            reserved = session.execute(
                update(ProviderCallAllocation)
                .where(ProviderCallAllocation.provider == provider.name)
                .where(ProviderCallAllocation.paused.is_(False))
                .where(ProviderCallAllocation.used_calls < ProviderCallAllocation.authorized_calls)
                .values(used_calls=ProviderCallAllocation.used_calls + 1)
                .returning(ProviderCallAllocation.provider)
            ).scalar_one_or_none()
            if reserved is None:
                raise RuntimeEconomicsError("Provider call capacity exhausted or paused; refusing paid call")
        entry = ProviderCallAttempt(
            agent_run_id=run_id,
            allocation_provider=provider.name if allocation is not None else None,
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
            response_id = response.provider_response_id
            if isinstance(response_id, str) and 0 < len(response_id.strip()) <= 255:
                entry.provider_response_id = response_id.strip()
            if response.estimated_cost_usd is not None:
                entry.estimated_cost_usd = Decimal(str(response.estimated_cost_usd))
                entry.cost_basis = "estimated"
            # Current adapters expose no authoritative billed amount. NULL is not zero.
        session.add(entry)
        try:
            session.commit()
        except Exception as exc:
            raise RuntimeEconomicsError("Could not settle provider attempt") from exc
