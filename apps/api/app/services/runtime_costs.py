from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import UUID

from sqlalchemy import func
from sqlmodel import Session, select

from app.models.domain import OrganizationalWorkItem
from app.models.runtime_cost import RuntimeBudget, RuntimeProviderCall
from app.services.audit_log import record_audit


CONTROLLED_AGENT_BUDGET_SCOPE_TYPE = "global"
CONTROLLED_AGENT_BUDGET_SCOPE_KEY = "controlled_agents_llm"
RUNTIME_BUDGET_SOURCE = "phase_16_runtime_budget"
MONEY_QUANTUM = Decimal("0.000001")

RESERVED_STATUS = "reserved"
OBSERVED_STATUS = "observed"
ACTUAL_STATUS = "actual"
UNATTRIBUTED_STATUS = "unattributed"
RELEASED_STATUS = "released"


class RuntimeCostControlError(RuntimeError):
    pass


class RuntimeBudgetNotConfigured(RuntimeCostControlError):
    pass


class RuntimeBudgetExceeded(RuntimeCostControlError):
    pass


class RuntimeProviderCallAlreadyRecorded(RuntimeCostControlError):
    pass


def _money(value: Decimal | float | int | str) -> Decimal:
    return Decimal(str(value)).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _budget_query(*, active_only: bool = False):
    statement = select(RuntimeBudget).where(
        RuntimeBudget.scope_type == CONTROLLED_AGENT_BUDGET_SCOPE_TYPE,
        RuntimeBudget.scope_key == CONTROLLED_AGENT_BUDGET_SCOPE_KEY,
    )
    if active_only:
        statement = statement.where(RuntimeBudget.status == "active")
    return statement


def get_controlled_agent_runtime_budget(
    session: Session,
    *,
    lock: bool = False,
    active_only: bool = False,
) -> RuntimeBudget | None:
    statement = _budget_query(active_only=active_only)
    if lock:
        statement = statement.with_for_update()
    return session.exec(statement).one_or_none()


def authorized_exposure_usd(session: Session, budget_id: UUID) -> Decimal:
    value = session.exec(
        select(func.coalesce(func.sum(RuntimeProviderCall.authorized_amount_usd), 0)).where(
            RuntimeProviderCall.budget_id == budget_id,
            RuntimeProviderCall.status != RELEASED_STATUS,
        )
    ).one()
    return _money(value or 0)


def runtime_budget_snapshot(session: Session, budget: RuntimeBudget) -> dict[str, Any]:
    exposure = authorized_exposure_usd(session, budget.id)
    limit = _money(budget.limit_usd)
    return {
        "id": budget.id,
        "scope_type": budget.scope_type,
        "scope_key": budget.scope_key,
        "currency": budget.currency,
        "limit_usd": limit,
        "reservation_usd_per_call": _money(budget.reservation_usd_per_call),
        "authorized_exposure_usd": exposure,
        "remaining_authorized_usd": max(Decimal("0"), limit - exposure),
        "status": budget.status,
        "created_by": budget.created_by,
        "updated_by": budget.updated_by,
        "created_at": budget.created_at,
        "updated_at": budget.updated_at,
    }


def configure_controlled_agent_runtime_budget(
    session: Session,
    *,
    limit_usd: Decimal,
    reservation_usd_per_call: Decimal,
    status: str,
    actor: str,
) -> RuntimeBudget:
    limit = _money(limit_usd)
    reservation = _money(reservation_usd_per_call)
    normalized_status = status.strip().lower()
    if limit <= 0:
        raise ValueError("Runtime budget limit_usd must be greater than zero.")
    if reservation <= 0:
        raise ValueError("Runtime budget reservation_usd_per_call must be greater than zero.")
    if reservation > limit:
        raise ValueError("Runtime per-call reservation cannot exceed the budget limit.")
    if normalized_status not in {"active", "inactive"}:
        raise ValueError("Runtime budget status must be active or inactive.")

    budget = get_controlled_agent_runtime_budget(session, lock=True)
    before_state = runtime_budget_snapshot(session, budget) if budget is not None else None
    if budget is None:
        budget = RuntimeBudget(
            scope_type=CONTROLLED_AGENT_BUDGET_SCOPE_TYPE,
            scope_key=CONTROLLED_AGENT_BUDGET_SCOPE_KEY,
            currency="USD",
            limit_usd=limit,
            reservation_usd_per_call=reservation,
            status=normalized_status,
            created_by=actor,
            updated_by=actor,
        )
        session.add(budget)
        session.flush()
    else:
        exposure = authorized_exposure_usd(session, budget.id)
        if limit < exposure:
            raise ValueError(
                "Runtime budget limit cannot be reduced below already-authorized exposure."
            )
        budget.limit_usd = limit
        budget.reservation_usd_per_call = reservation
        budget.status = normalized_status
        budget.updated_by = actor
        budget.updated_at = _now()
        session.add(budget)

    record_audit(
        session,
        actor=actor,
        action="runtime_budget_configured",
        entity_type="runtime_budget",
        entity_id=budget.id,
        before_state=before_state,
        after_state=runtime_budget_snapshot(session, budget),
        reason="Human-admin runtime allocation configured for controlled LLM execution.",
        source=RUNTIME_BUDGET_SOURCE,
    )
    return budget


def _provider_call_by_key(session: Session, call_key: str) -> RuntimeProviderCall | None:
    return session.exec(
        select(RuntimeProviderCall).where(RuntimeProviderCall.call_key == call_key)
    ).one_or_none()


def _raise_if_provider_call_recorded(session: Session, call_key: str) -> None:
    if _provider_call_by_key(session, call_key) is not None:
        raise RuntimeProviderCallAlreadyRecorded(
            f"Provider call {call_key} already has durable runtime-cost evidence."
        )


def reserve_runtime_provider_call(
    session: Session,
    *,
    call_key: str,
    agent_run_id: UUID | None,
    work_item_id: UUID | None,
    agent_name: str,
    department: str,
    provider: str,
    model: str,
    attempt_number: int,
    actor: str,
) -> RuntimeProviderCall:
    _raise_if_provider_call_recorded(session, call_key)

    if work_item_id is not None and session.get(OrganizationalWorkItem, work_item_id) is None:
        raise ValueError(f"OrganizationalWorkItem {work_item_id} not found.")

    budget = get_controlled_agent_runtime_budget(session, lock=True, active_only=True)
    if budget is None:
        record_audit(
            session,
            actor=actor,
            action="runtime_budget_missing",
            entity_type="runtime_budget",
            entity_id=CONTROLLED_AGENT_BUDGET_SCOPE_KEY,
            after_state={
                "scope_type": CONTROLLED_AGENT_BUDGET_SCOPE_TYPE,
                "scope_key": CONTROLLED_AGENT_BUDGET_SCOPE_KEY,
                "provider": provider,
                "model": model,
                "agent_name": agent_name,
            },
            reason="Paid provider execution was blocked because no active runtime budget exists.",
            source=RUNTIME_BUDGET_SOURCE,
        )
        session.commit()
        raise RuntimeBudgetNotConfigured(
            "No active controlled-agent runtime budget is configured."
        )

    # The first check avoids locking for obvious redeliveries. Re-check after acquiring
    # the canonical budget row lock so concurrent deliveries cannot race through the
    # unique key and accidentally present a database IntegrityError as runtime truth.
    _raise_if_provider_call_recorded(session, call_key)

    exposure = authorized_exposure_usd(session, budget.id)
    reservation = _money(budget.reservation_usd_per_call)
    limit = _money(budget.limit_usd)
    if exposure + reservation > limit:
        record_audit(
            session,
            actor=actor,
            action="runtime_budget_denied",
            entity_type="runtime_budget",
            entity_id=budget.id,
            after_state={
                "limit_usd": limit,
                "authorized_exposure_usd": exposure,
                "required_reservation_usd": reservation,
                "remaining_authorized_usd": max(Decimal("0"), limit - exposure),
                "provider": provider,
                "model": model,
                "agent_name": agent_name,
                "attempt_number": attempt_number,
            },
            reason="Paid provider execution was blocked before the external boundary.",
            source=RUNTIME_BUDGET_SOURCE,
        )
        session.commit()
        raise RuntimeBudgetExceeded(
            "Controlled-agent runtime budget does not have enough authorized allocation for another provider call."
        )

    call = RuntimeProviderCall(
        call_key=call_key,
        budget_id=budget.id,
        agent_run_id=agent_run_id,
        work_item_id=work_item_id,
        agent_name=agent_name,
        department=department,
        provider=provider,
        model=model,
        attempt_number=max(1, int(attempt_number)),
        status=RESERVED_STATUS,
        authorized_amount_usd=reservation,
    )
    session.add(call)
    session.flush()
    record_audit(
        session,
        actor=actor,
        action="runtime_budget_reserved",
        entity_type="runtime_provider_call",
        entity_id=call.id,
        after_state={
            "call_key": call.call_key,
            "budget_id": budget.id,
            "authorized_amount_usd": reservation,
            "authorized_exposure_before_usd": exposure,
            "authorized_exposure_after_usd": exposure + reservation,
            "budget_limit_usd": limit,
            "provider": provider,
            "model": model,
            "agent_name": agent_name,
            "department": department,
            "work_item_id": work_item_id,
            "agent_run_id": agent_run_id,
            "attempt_number": call.attempt_number,
        },
        reason="Runtime allocation reserved before crossing the paid provider boundary.",
        source=RUNTIME_BUDGET_SOURCE,
    )
    session.commit()
    session.refresh(call)
    return call


def _locked_provider_call(session: Session, call_id: UUID) -> RuntimeProviderCall:
    return session.exec(
        select(RuntimeProviderCall)
        .where(RuntimeProviderCall.id == call_id)
        .with_for_update()
    ).one()


def _require_reserved(call: RuntimeProviderCall) -> None:
    if call.status != RESERVED_STATUS:
        raise RuntimeCostControlError(
            f"Runtime provider call {call.id} cannot transition from {call.status}; expected reserved."
        )


def settle_runtime_provider_call(
    session: Session,
    *,
    call_id: UUID,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    total_tokens: int | None,
    estimated_cost_usd: Decimal | float | None,
    actual_cost_usd: Decimal | float | None = None,
    billing_evidence: bool = False,
    actor: str,
) -> RuntimeProviderCall:
    call = _locked_provider_call(session, call_id)
    _require_reserved(call)
    actual = _money(actual_cost_usd) if actual_cost_usd is not None else None
    if actual is not None and not billing_evidence:
        raise ValueError("actual_cost_usd requires real billing evidence.")
    if actual is None and billing_evidence:
        raise ValueError("billing_evidence cannot be true without actual_cost_usd.")

    call.prompt_tokens = prompt_tokens
    call.completion_tokens = completion_tokens
    call.total_tokens = total_tokens
    call.estimated_cost_usd = (
        _money(estimated_cost_usd) if estimated_cost_usd is not None else None
    )
    call.actual_cost_usd = actual
    call.billing_evidence = billing_evidence
    call.status = ACTUAL_STATUS if billing_evidence else OBSERVED_STATUS
    call.settled_at = _now()
    call.updated_at = call.settled_at
    session.add(call)
    record_audit(
        session,
        actor=actor,
        action="runtime_provider_cost_observed",
        entity_type="runtime_provider_call",
        entity_id=call.id,
        after_state={
            "provider": call.provider,
            "model": call.model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "authorized_amount_usd": call.authorized_amount_usd,
            "estimated_cost_usd": call.estimated_cost_usd,
            "actual_cost_usd": call.actual_cost_usd,
            "billing_evidence": call.billing_evidence,
            "cost_truth": "actual" if billing_evidence else "estimate_only",
        },
        reason="Provider usage settled after the external runtime boundary.",
        source=RUNTIME_BUDGET_SOURCE,
    )
    session.commit()
    session.refresh(call)
    return call


def mark_runtime_provider_call_unattributed(
    session: Session,
    *,
    call_id: UUID,
    error: Exception,
    actor: str,
) -> RuntimeProviderCall:
    call = _locked_provider_call(session, call_id)
    _require_reserved(call)
    call.status = UNATTRIBUTED_STATUS
    call.error_class = type(error).__name__
    call.settled_at = _now()
    call.updated_at = call.settled_at
    session.add(call)
    record_audit(
        session,
        actor=actor,
        action="runtime_provider_cost_unattributed",
        entity_type="runtime_provider_call",
        entity_id=call.id,
        after_state={
            "provider": call.provider,
            "model": call.model,
            "authorized_amount_usd": call.authorized_amount_usd,
            "error_class": call.error_class,
            "actual_cost_usd": None,
            "billing_evidence": False,
        },
        reason=(
            "The provider boundary may have incurred cost, but authoritative usage/billing evidence "
            "was not available; reserved exposure is retained."
        ),
        source=RUNTIME_BUDGET_SOURCE,
    )
    session.commit()
    session.refresh(call)
    return call


def release_runtime_provider_call(
    session: Session,
    *,
    call_id: UUID,
    error: Exception,
    actor: str,
) -> RuntimeProviderCall:
    call = _locked_provider_call(session, call_id)
    _require_reserved(call)
    call.status = RELEASED_STATUS
    call.error_class = type(error).__name__
    call.settled_at = _now()
    call.updated_at = call.settled_at
    session.add(call)
    record_audit(
        session,
        actor=actor,
        action="runtime_budget_reservation_released",
        entity_type="runtime_provider_call",
        entity_id=call.id,
        after_state={
            "provider": call.provider,
            "model": call.model,
            "authorized_amount_usd": call.authorized_amount_usd,
            "error_class": call.error_class,
            "external_boundary_crossed": False,
        },
        reason="The provider call failed before the external paid boundary, so its reservation was released.",
        source=RUNTIME_BUDGET_SOURCE,
    )
    session.commit()
    session.refresh(call)
    return call


def attach_runtime_provider_call_to_agent_run(
    session: Session,
    *,
    call_id: UUID,
    agent_run_id: UUID,
) -> None:
    call = session.get(RuntimeProviderCall, call_id)
    if call is None:
        return
    if call.agent_run_id is None:
        call.agent_run_id = agent_run_id
        call.updated_at = _now()
        session.add(call)
