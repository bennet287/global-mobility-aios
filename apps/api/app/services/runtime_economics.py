from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import case, func, update
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core import db as db_module
from app.models.domain import AgentRun, AgentRunStatus, AuditLog
from app.models.runtime_economics import ProviderCallAllocation, ProviderCallAttempt
from app.services.audit_log import record_audit
from app.services.llm_client import LLMProvider, LLMProviderTransportError, LLMResponse


class RuntimeEconomicsError(RuntimeError):
    """A paid call must not proceed without durable accounting identity."""


# Operational provider admission for admin-enrolled call allocations. This is
# never a USD ceiling and does not retrospectively cancel admitted attempts.
PROVIDER_BREAKER_FAILURE_THRESHOLD = 3
REQUEST_OPERATION_FINISHED_ACTION = "provider_request_operation_finished"


_FINISHED_RUN_STATUSES = (
    AgentRunStatus.pending_review.value,
    AgentRunStatus.completed.value,
    AgentRunStatus.approved.value,
    AgentRunStatus.rejected.value,
    AgentRunStatus.converted.value,
    AgentRunStatus.failed.value,
    AgentRunStatus.cancelled.value,
)


def reconcile_stranded_provider_attempts(
    session: Session, *, hard_limit_seconds: int, grace_seconds: int = 60,
    limit: int = 100, now: datetime | None = None,
) -> dict:
    """Close stranded attempts only when their owning execution is durably finished.

    AgentRun-linked attempts retain the hard-limit-plus-grace guard. Request-local
    attempts require an explicit owner completion audit record; age alone never
    closes them. Every reconciliation remains an unknown provider outcome and does
    not release a call slot, classify a provider failure, or assert a refund/charge.
    """
    observed_at = now or datetime.now(timezone.utc)
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=timezone.utc)
    bounded_limit = max(1, min(int(limit), 500))

    stale_after_seconds: int | None = None
    agent_candidates: list[ProviderCallAttempt] = []
    if hard_limit_seconds > 0:
        stale_after_seconds = int(hard_limit_seconds) + max(0, int(grace_seconds))
        cutoff = observed_at - timedelta(seconds=stale_after_seconds)
        agent_candidates = session.exec(
            select(ProviderCallAttempt)
            .join(AgentRun, AgentRun.id == ProviderCallAttempt.agent_run_id)
            .where(ProviderCallAttempt.status == "started")
            .where(ProviderCallAttempt.started_at < cutoff)
            .where(AgentRun.status.in_(_FINISHED_RUN_STATUSES))
            .order_by(ProviderCallAttempt.started_at, ProviderCallAttempt.id)
            .limit(bounded_limit)
        ).all()

    remaining = bounded_limit - len(agent_candidates)
    request_candidates: list[tuple[ProviderCallAttempt, AuditLog]] = []
    if remaining > 0:
        # AuditLog is already the canonical durable evidence boundary. Scan a
        # bounded completion window and keep only still-started request attempts.
        finish_logs = session.exec(
            select(AuditLog)
            .where(AuditLog.entity_type == "provider_call_attempt")
            .where(AuditLog.action == REQUEST_OPERATION_FINISHED_ACTION)
            .order_by(AuditLog.created_at, AuditLog.id)
            .limit(min(500, max(remaining, remaining * 5)))
        ).all()
        seen_attempts: set[UUID] = set()
        for finish_log in finish_logs:
            if len(request_candidates) >= remaining:
                break
            try:
                attempt_id = UUID(str(finish_log.entity_id))
            except (TypeError, ValueError):
                continue
            if attempt_id in seen_attempts:
                continue
            seen_attempts.add(attempt_id)
            entry = session.get(ProviderCallAttempt, attempt_id)
            if entry is None or entry.status != "started" or entry.agent_run_id is not None:
                continue
            request_candidates.append((entry, finish_log))

    reconciled = 0
    candidates: list[tuple[ProviderCallAttempt, AuditLog | None]] = [
        *((entry, None) for entry in agent_candidates),
        *request_candidates,
    ]
    for entry, finish_log in candidates:
        is_request_local = finish_log is not None
        statement = (
            update(ProviderCallAttempt)
            .where(ProviderCallAttempt.id == entry.id)
            .where(ProviderCallAttempt.status == "started")
        )
        if is_request_local:
            statement = statement.where(ProviderCallAttempt.agent_run_id.is_(None))
        else:
            if stale_after_seconds is None:
                continue
            cutoff = observed_at - timedelta(seconds=stale_after_seconds)
            statement = (
                statement
                .where(ProviderCallAttempt.started_at < cutoff)
                .where(
                    ProviderCallAttempt.agent_run_id.in_(
                        select(AgentRun.id).where(AgentRun.status.in_(_FINISHED_RUN_STATUSES))
                    )
                )
            )
        changed = session.execute(
            statement
            .values(status="outcome_unknown", settled_at=observed_at)
            .returning(ProviderCallAttempt.id)
        ).scalar_one_or_none()
        if changed is None:
            continue

        after_state = {
            "status": "outcome_unknown",
            "provider": entry.provider,
            "attempt_no": entry.attempt_no,
            "cause_inferred": False,
            "failure_class_inferred": False,
            "billed_cost_known": False,
            "call_slot_released": False,
        }
        if is_request_local:
            after_state.update({
                "operation_key": entry.operation_key,
                "context_kind": entry.context_kind,
                "execution_end_signal": REQUEST_OPERATION_FINISHED_ACTION,
                "execution_end_signal_id": str(finish_log.id),
                "execution_finished_at": finish_log.created_at,
            })
            reason = (
                "Request-local owner recorded execution completion, but its provider attempt "
                "was never settled."
            )
        else:
            after_state.update({
                "agent_run_id": str(entry.agent_run_id),
                "stale_after_seconds": stale_after_seconds,
                "execution_end_signal": "finished_agent_run",
            })
            reason = "Linked AgentRun finished, but its old provider attempt was never settled."
        record_audit(
            session, actor="worker", action="provider_attempt_stranded_reconciled",
            entity_type="provider_call_attempt", entity_id=str(entry.id),
            after_state=after_state,
            reason=reason,
            source="phase_16_provider_attempt_reconciliation",
        )
        session.commit()
        reconciled += 1
    return {
        "scanned": len(agent_candidates) + len(request_candidates),
        "reconciled": reconciled,
        "stale_after_seconds": stale_after_seconds,
    }


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


def reset_provider_circuit(
    session: Session, *, provider: str, actor: str, reason: str,
) -> ProviderCallAllocation:
    """Admin review reopens a tripped provider; it grants no calls or spend."""
    allocation = session.get(ProviderCallAllocation, provider)
    if allocation is None:
        raise RuntimeEconomicsError("Provider call capacity has not been authorized")
    if not allocation.breaker_open:
        return allocation
    before_failures = allocation.breaker_failures
    changed = session.execute(
        update(ProviderCallAllocation)
        .where(ProviderCallAllocation.provider == provider)
        .where(ProviderCallAllocation.breaker_open.is_(True))
        .values(
            breaker_open=False, breaker_failures=0, breaker_opened_at=None,
            updated_at=datetime.now(timezone.utc),
        )
        .returning(ProviderCallAllocation.provider)
    ).scalar_one_or_none()
    if changed is None:
        raise RuntimeEconomicsError("Concurrent circuit reset changed; refresh provider state")
    record_audit(
        session, action="provider_circuit_reset", entity_type="provider_call_allocation",
        entity_id=provider, actor=actor, reason=reason,
        before_state={"breaker_open": True, "breaker_failures": before_failures},
        after_state={"breaker_open": False, "breaker_failures": 0,
                     "authorized_calls_unchanged": True, "used_calls_unchanged": True},
        source="phase_16_provider_circuit_breaker",
    )
    session.commit()
    session.refresh(allocation)
    return allocation


def mark_request_operation_finished(*, operation_key: str, context_kind: str) -> bool:
    """Persist owner execution-end evidence without guessing the provider outcome.

    False means the paid-call attempt did not exist (for example, admission failed
    before a call row was created). Repeated marking is idempotent for the same
    request-local attempt.
    """
    if not operation_key or not context_kind:
        raise RuntimeEconomicsError("Request-local operation identity is required")
    with Session(db_module.engine) as session:
        attempt = session.exec(
            select(ProviderCallAttempt).where(ProviderCallAttempt.operation_key == operation_key)
        ).first()
        if attempt is None:
            return False
        if attempt.agent_run_id is not None or attempt.context_kind != context_kind:
            raise RuntimeEconomicsError("Request-local operation identity does not match provider attempt")
        existing = session.exec(
            select(AuditLog)
            .where(AuditLog.entity_type == "provider_call_attempt")
            .where(AuditLog.entity_id == str(attempt.id))
            .where(AuditLog.action == REQUEST_OPERATION_FINISHED_ACTION)
            .order_by(AuditLog.created_at.desc())
        ).first()
        if existing is not None:
            return True
        record_audit(
            session,
            actor="request_owner",
            action=REQUEST_OPERATION_FINISHED_ACTION,
            entity_type="provider_call_attempt",
            entity_id=str(attempt.id),
            after_state={
                "operation_key": attempt.operation_key,
                "context_kind": attempt.context_kind,
                "provider": attempt.provider,
                "provider_outcome_inferred": False,
                "failure_class_inferred": False,
                "billed_cost_known": False,
                "call_slot_released": False,
            },
            reason="Owning request-local operation finished after the provider-call boundary.",
            source="phase_16_request_local_completion",
        )
        session.commit()
        return True


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
                .where(ProviderCallAllocation.breaker_open.is_(False))
                .where(ProviderCallAllocation.used_calls < ProviderCallAllocation.authorized_calls)
                .values(used_calls=ProviderCallAllocation.used_calls + 1)
                .returning(ProviderCallAllocation.provider)
            ).scalar_one_or_none()
            if reserved is None:
                session.refresh(allocation)
                if allocation.breaker_open:
                    raise RuntimeEconomicsError("Provider circuit open; refusing paid call")
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
    except Exception as exc:
        _settle(entry_id, None, transport_failure=isinstance(exc, LLMProviderTransportError))
        raise
    _settle(entry_id, response)
    return response


def _settle(
    entry_id: UUID, response: LLMResponse | None, *, transport_failure: bool = False,
) -> None:
    with Session(db_module.engine) as session:
        entry = session.get(ProviderCallAttempt, entry_id)
        if entry is None or entry.status != "started":
            raise RuntimeEconomicsError("Provider attempt settlement identity was lost")
        values = {"settled_at": datetime.now(timezone.utc)}
        if response is None:
            values["status"] = "outcome_unknown"
        else:
            values.update(
                status="observed", provider=response.provider, model=response.model,
                prompt_tokens=response.prompt_tokens,
                completion_tokens=response.completion_tokens,
                total_tokens=response.total_tokens,
            )
            response_id = response.provider_response_id
            if isinstance(response_id, str) and 0 < len(response_id.strip()) <= 255:
                values["provider_response_id"] = response_id.strip()
            if response.estimated_cost_usd is not None:
                values["estimated_cost_usd"] = Decimal(str(response.estimated_cost_usd))
                values["cost_basis"] = "estimated"
            # Current adapters expose no authoritative billed amount. NULL is not zero.
        try:
            changed = session.execute(
                update(ProviderCallAttempt)
                .where(ProviderCallAttempt.id == entry_id)
                .where(ProviderCallAttempt.status == "started")
                .values(**values)
                .returning(ProviderCallAttempt.id)
            ).scalar_one_or_none()
            if changed is None:
                raise RuntimeEconomicsError("Provider attempt settlement identity was lost")
            if entry.allocation_provider is not None:
                # Settlements serialize on the same provider allocation row.
                # Count only consecutive classified transport failures in
                # settlement order. Any other settled outcome breaks the streak.
                allocation_update = (
                    update(ProviderCallAllocation)
                    .where(ProviderCallAllocation.provider == entry.allocation_provider)
                    .where(ProviderCallAllocation.breaker_open.is_(False))
                    .values(updated_at=datetime.now(timezone.utc))
                )
                if transport_failure:
                    now = datetime.now(timezone.utc)
                    allocation_update = allocation_update.values(
                        breaker_failures=ProviderCallAllocation.breaker_failures + 1,
                        breaker_open=(ProviderCallAllocation.breaker_failures + 1
                                      >= PROVIDER_BREAKER_FAILURE_THRESHOLD),
                        breaker_opened_at=case(
                            (ProviderCallAllocation.breaker_failures + 1
                             >= PROVIDER_BREAKER_FAILURE_THRESHOLD, now),
                            else_=None,
                        ),
                    )
                else:
                    allocation_update = allocation_update.values(breaker_failures=0)
                breaker_state = session.execute(
                    allocation_update.returning(
                        ProviderCallAllocation.breaker_open,
                        ProviderCallAllocation.breaker_failures,
                    )
                ).one_or_none()
                if transport_failure and breaker_state is not None and breaker_state.breaker_open:
                    record_audit(
                        session, actor="worker", action="provider_circuit_opened",
                        entity_type="provider_call_allocation", entity_id=entry.allocation_provider,
                        after_state={
                            "breaker_open": True, "breaker_failures": breaker_state.breaker_failures,
                            "threshold": PROVIDER_BREAKER_FAILURE_THRESHOLD,
                            "trigger_attempt_id": str(entry_id), "failure_class": "provider_transport",
                            "in_flight_calls_not_revoked": True, "billed_cost_known": False,
                        },
                        reason="Three consecutive settled provider transport failures.",
                        source="phase_16_provider_circuit_breaker",
                    )
            session.commit()
        except RuntimeEconomicsError:
            raise
        except Exception as exc:
            raise RuntimeEconomicsError("Could not settle provider attempt") from exc
