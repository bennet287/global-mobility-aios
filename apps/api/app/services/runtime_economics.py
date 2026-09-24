from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.core.config import settings
from app.models.domain import AgentRun
from app.models.runtime_economics import AgentRunBudget, AgentRunCostEntry
from app.services.audit_log import record_audit


MONEY_QUANTUM = Decimal("0.000001")


class RuntimeBudgetError(RuntimeError):
    """Base class for fail-closed runtime economic admission errors."""


class RuntimeBudgetUnavailable(RuntimeBudgetError):
    """Paid execution has no configured authorized economic envelope."""


class RuntimeBudgetExceeded(RuntimeBudgetError):
    """The next reserved exposure would exceed the AgentRun allocation."""


class RuntimeBudgetAttemptConflict(RuntimeBudgetError):
    """The same AgentRun attempt already has economic evidence.

    Repeating the provider call would risk double spend, so execution fails closed
    until reconciliation decides what happened to the earlier attempt.
    """


def _money(value: Any) -> Decimal:
    try:
        return Decimal(str(value or 0)).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise RuntimeBudgetUnavailable("Runtime budget policy contains an invalid monetary value.") from exc


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _entry_accounted_cost(entry: AgentRunCostEntry) -> Decimal:
    if entry.status == "released":
        return Decimal("0")
    if entry.billing_evidence and entry.actual_cost_usd is not None:
        return _money(entry.actual_cost_usd)
    if entry.unattributed_cost_usd and entry.unattributed_cost_usd > 0:
        return _money(entry.unattributed_cost_usd)
    if entry.status == "reserved":
        return _money(entry.reserved_usd)
    return Decimal("0")


def _entries_for_run(session: Session, run_id: UUID) -> list[AgentRunCostEntry]:
    return list(
        session.exec(
            select(AgentRunCostEntry)
            .where(AgentRunCostEntry.agent_run_id == run_id)
            .order_by(AgentRunCostEntry.attempt_number.asc())
        ).all()
    )


def initialize_agent_run_budget(
    session: Session,
    run: AgentRun,
    *,
    actor: str,
) -> AgentRunBudget | None:
    """Snapshot deployment-authorized capital onto one AgentRun exactly once.

    Zero or missing policy values mean no paid execution is authorized. We do not
    fabricate a default monetary allowance.
    """

    existing = session.exec(
        select(AgentRunBudget).where(AgentRunBudget.agent_run_id == run.id)
    ).one_or_none()
    if existing is not None:
        return existing

    authorized = _money(getattr(settings, "llm_agent_run_budget_usd", 0))
    reservation = _money(getattr(settings, "llm_attempt_reservation_usd", 0))
    if authorized <= 0 or reservation <= 0:
        return None

    # Serialize competing initializers at canonical AgentRun truth. The budget table
    # is economic authority, not a second execution-state store.
    session.exec(
        select(AgentRun)
        .where(AgentRun.id == run.id)
        .with_for_update()
    ).one()
    existing = session.exec(
        select(AgentRunBudget).where(AgentRunBudget.agent_run_id == run.id)
    ).one_or_none()
    if existing is not None:
        return existing

    budget = AgentRunBudget(
        agent_run_id=run.id,
        authorized_budget_usd=authorized,
        attempt_reservation_usd=reservation,
        allocation_source="runtime_policy",
        allocated_by=actor or "system",
    )
    session.add(budget)
    session.flush()
    record_audit(
        session,
        actor=actor or "system",
        action="agent_run_budget_allocated",
        entity_type="agent_run",
        entity_id=str(run.id),
        after_state={
            "authorized_budget_usd": str(authorized),
            "attempt_reservation_usd": str(reservation),
            "allocation_source": budget.allocation_source,
            "billing_truth_claimed": False,
        },
        reason="Runtime policy allocated a bounded paid-execution envelope to the AgentRun.",
        source="phase_16_runtime_economics",
    )
    return budget


def get_agent_run_budget_snapshot(session: Session, run_id: UUID) -> dict[str, Any]:
    budget = session.exec(
        select(AgentRunBudget).where(AgentRunBudget.agent_run_id == run_id)
    ).one_or_none()
    entries = _entries_for_run(session, run_id)

    actual = sum(
        (_money(entry.actual_cost_usd) for entry in entries if entry.billing_evidence and entry.actual_cost_usd is not None),
        Decimal("0"),
    )
    estimated = sum(
        (_money(entry.estimated_cost_usd) for entry in entries if entry.estimated_cost_usd is not None),
        Decimal("0"),
    )
    unattributed = sum(
        (_money(entry.unattributed_cost_usd) for entry in entries),
        Decimal("0"),
    )
    reserved = sum(
        (_money(entry.reserved_usd) for entry in entries if entry.status == "reserved"),
        Decimal("0"),
    )
    accounted = sum((_entry_accounted_cost(entry) for entry in entries), Decimal("0"))

    authorized = _money(budget.authorized_budget_usd) if budget is not None else None
    remaining = max(Decimal("0"), authorized - accounted) if authorized is not None else None
    return {
        "agent_run_id": str(run_id),
        "budget_configured": budget is not None,
        "authorized_budget_usd": str(authorized) if authorized is not None else None,
        "attempt_reservation_usd": (
            str(_money(budget.attempt_reservation_usd)) if budget is not None else None
        ),
        "accounted_cost_usd": str(_money(accounted)),
        "actual_spend_usd": str(_money(actual)),
        "estimated_spend_usd": str(_money(estimated)),
        "unattributed_exposure_usd": str(_money(unattributed)),
        "reserved_exposure_usd": str(_money(reserved)),
        "remaining_budget_usd": str(_money(remaining)) if remaining is not None else None,
        "attempts_recorded": len(entries),
        "billing_truth_complete": bool(entries) and all(entry.billing_evidence for entry in entries),
    }


def reserve_agent_run_attempt(
    session: Session,
    run: AgentRun,
    *,
    attempt_number: int,
    agent_name: str,
    department: str | None,
    provider: str,
    model: str | None,
    actor: str,
) -> AgentRunCostEntry:
    if attempt_number < 1:
        raise ValueError("attempt_number must be >= 1")

    budget = initialize_agent_run_budget(session, run, actor=actor)
    if budget is None:
        record_audit(
            session,
            actor=actor or "system",
            action="agent_run_budget_denied",
            entity_type="agent_run",
            entity_id=str(run.id),
            after_state={
                "attempt_number": attempt_number,
                "reason": "budget_policy_not_configured",
                "provider": provider,
                "model": model,
                "paid_call_started": False,
            },
            reason="Paid provider execution was blocked because no positive runtime budget policy is configured.",
            source="phase_16_runtime_economics",
        )
        session.flush()
        raise RuntimeBudgetUnavailable(
            "Paid provider execution requires positive LLM_AGENT_RUN_BUDGET_USD and LLM_ATTEMPT_RESERVATION_USD policy values."
        )

    budget = session.exec(
        select(AgentRunBudget)
        .where(AgentRunBudget.id == budget.id)
        .with_for_update()
    ).one()

    existing = session.exec(
        select(AgentRunCostEntry)
        .where(AgentRunCostEntry.agent_run_id == run.id)
        .where(AgentRunCostEntry.attempt_number == attempt_number)
    ).one_or_none()
    if existing is not None:
        record_audit(
            session,
            actor=actor or "system",
            action="agent_run_budget_attempt_conflict",
            entity_type="agent_run",
            entity_id=str(run.id),
            after_state={
                "attempt_number": attempt_number,
                "existing_cost_entry_id": str(existing.id),
                "existing_status": existing.status,
                "paid_call_started": False,
            },
            reason="A cost record already exists for this AgentRun attempt; provider execution was not repeated.",
            source="phase_16_runtime_economics",
        )
        session.flush()
        raise RuntimeBudgetAttemptConflict(
            f"AgentRun {run.id} attempt {attempt_number} already has runtime economic evidence."
        )

    snapshot = get_agent_run_budget_snapshot(session, run.id)
    remaining = _money(snapshot["remaining_budget_usd"])
    reservation = _money(budget.attempt_reservation_usd)
    if remaining < reservation:
        record_audit(
            session,
            actor=actor or "system",
            action="agent_run_budget_exhausted",
            entity_type="agent_run",
            entity_id=str(run.id),
            after_state={
                "attempt_number": attempt_number,
                "authorized_budget_usd": snapshot["authorized_budget_usd"],
                "accounted_cost_usd": snapshot["accounted_cost_usd"],
                "remaining_budget_usd": snapshot["remaining_budget_usd"],
                "required_reservation_usd": str(reservation),
                "paid_call_started": False,
            },
            reason="The next paid provider reservation would exceed the AgentRun budget.",
            source="phase_16_runtime_economics",
        )
        session.flush()
        raise RuntimeBudgetExceeded(
            f"AgentRun {run.id} has {remaining} USD remaining; {reservation} USD is required for the next paid attempt."
        )

    entry = AgentRunCostEntry(
        agent_run_id=run.id,
        attempt_number=attempt_number,
        agent_name=agent_name,
        department=department,
        provider=provider,
        model=model,
        status="reserved",
        reserved_usd=reservation,
        unattributed_cost_usd=Decimal("0"),
    )
    session.add(entry)
    session.flush()
    after = get_agent_run_budget_snapshot(session, run.id)
    record_audit(
        session,
        actor=actor or "system",
        action="agent_run_budget_reserved",
        entity_type="agent_run",
        entity_id=str(run.id),
        after_state={
            "attempt_number": attempt_number,
            "cost_entry_id": str(entry.id),
            "provider": provider,
            "model": model,
            "reserved_usd": str(reservation),
            "remaining_budget_usd": after["remaining_budget_usd"],
            "billing_truth_claimed": False,
        },
        reason="A bounded provider-call exposure was reserved before paid execution.",
        source="phase_16_runtime_economics",
    )
    return entry


def settle_agent_run_attempt(
    session: Session,
    entry: AgentRunCostEntry,
    response: Any,
    *,
    actor: str,
) -> AgentRunCostEntry:
    billed = getattr(response, "billed_cost_usd", None)
    billing_evidence = bool(getattr(response, "billing_evidence", False) and billed is not None)
    estimated = getattr(response, "estimated_cost_usd", None)

    entry.prompt_tokens = getattr(response, "prompt_tokens", None)
    entry.completion_tokens = getattr(response, "completion_tokens", None)
    entry.total_tokens = getattr(response, "total_tokens", None)
    entry.estimated_cost_usd = _money(estimated) if estimated is not None else None
    entry.settled_at = _now()

    if billing_evidence:
        entry.status = "actual"
        entry.actual_cost_usd = _money(billed)
        entry.unattributed_cost_usd = Decimal("0")
        entry.billing_evidence = True
    else:
        # A provider response proves usage, not invoice truth. Keep the conservative
        # reservation consumed as unattributed exposure until billing reconciliation.
        entry.status = "unattributed"
        entry.actual_cost_usd = None
        entry.unattributed_cost_usd = _money(entry.reserved_usd)
        entry.billing_evidence = False

    session.add(entry)
    session.flush()
    snapshot = get_agent_run_budget_snapshot(session, entry.agent_run_id)
    record_audit(
        session,
        actor=actor or "system",
        action="agent_run_cost_observed",
        entity_type="agent_run",
        entity_id=str(entry.agent_run_id),
        after_state={
            "attempt_number": entry.attempt_number,
            "cost_entry_id": str(entry.id),
            "provider": entry.provider,
            "model": entry.model,
            "status": entry.status,
            "actual_cost_usd": str(entry.actual_cost_usd) if entry.actual_cost_usd is not None else None,
            "estimated_cost_usd": str(entry.estimated_cost_usd) if entry.estimated_cost_usd is not None else None,
            "unattributed_cost_usd": str(entry.unattributed_cost_usd),
            "billing_evidence": entry.billing_evidence,
            "prompt_tokens": entry.prompt_tokens,
            "completion_tokens": entry.completion_tokens,
            "total_tokens": entry.total_tokens,
            "remaining_budget_usd": snapshot["remaining_budget_usd"],
        },
        reason=(
            "Provider billing evidence settled actual runtime cost."
            if entry.billing_evidence
            else "Provider usage was observed without billing evidence; reserved exposure remains unattributed."
        ),
        source="phase_16_runtime_economics",
    )
    return entry


def mark_agent_run_attempt_failure(
    session: Session,
    entry: AgentRunCostEntry,
    *,
    actor: str,
    failure_class: str,
    external_execution_possible: bool,
) -> AgentRunCostEntry:
    entry.settled_at = _now()
    entry.billing_evidence = False
    entry.actual_cost_usd = None
    if external_execution_possible:
        entry.status = "unattributed"
        entry.unattributed_cost_usd = _money(entry.reserved_usd)
    else:
        entry.status = "released"
        entry.unattributed_cost_usd = Decimal("0")
    session.add(entry)
    session.flush()
    snapshot = get_agent_run_budget_snapshot(session, entry.agent_run_id)
    record_audit(
        session,
        actor=actor or "system",
        action="agent_run_cost_failure_reconciled",
        entity_type="agent_run",
        entity_id=str(entry.agent_run_id),
        after_state={
            "attempt_number": entry.attempt_number,
            "cost_entry_id": str(entry.id),
            "failure_class": failure_class,
            "external_execution_possible": external_execution_possible,
            "status": entry.status,
            "unattributed_cost_usd": str(entry.unattributed_cost_usd),
            "remaining_budget_usd": snapshot["remaining_budget_usd"],
            "billing_evidence": False,
        },
        reason=(
            "Provider execution may have occurred; reserved exposure remains unattributed."
            if external_execution_possible
            else "Failure occurred before paid provider execution; the reservation was released."
        ),
        source="phase_16_runtime_economics",
    )
    return entry
