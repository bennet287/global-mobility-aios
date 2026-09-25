from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from app.models.domain import AuditLog
from app.models.runtime_economics import ProviderCallAllocation, ProviderCallAttempt
from app.services.runtime_economics import (
    mark_request_operation_finished,
    reconcile_stranded_provider_attempts,
)


def test_request_owner_completion_reconciles_unknown_without_releasing_call_slot(
    db_session: Session,
) -> None:
    now = datetime.now(timezone.utc)
    allocation = ProviderCallAllocation(
        provider="deepseek",
        authorized_calls=2,
        used_calls=1,
        authorized_by="admin",
        reason="Bounded request-local proof",
    )
    finished = ProviderCallAttempt(
        operation_key="inhouse_consultant_request:finished",
        context_kind="inhouse_consultant_request",
        attempt_no=1,
        provider="deepseek",
        allocation_provider="deepseek",
        started_at=now,
    )
    unfinished = ProviderCallAttempt(
        operation_key="inhouse_consultant_request:unfinished",
        context_kind="inhouse_consultant_request",
        attempt_no=1,
        provider="gemini",
        started_at=now - timedelta(hours=2),
    )
    db_session.add_all([allocation, finished, unfinished])
    db_session.commit()

    assert mark_request_operation_finished(
        operation_key=finished.operation_key,
        context_kind="inhouse_consultant_request",
    ) is True
    # The owner signal is idempotent and a pre-admission operation has no row to mark.
    assert mark_request_operation_finished(
        operation_key=finished.operation_key,
        context_kind="inhouse_consultant_request",
    ) is True
    assert mark_request_operation_finished(
        operation_key="inhouse_consultant_request:not-admitted",
        context_kind="inhouse_consultant_request",
    ) is False

    db_session.expire_all()
    finished = db_session.exec(
        select(ProviderCallAttempt).where(
            ProviderCallAttempt.operation_key == "inhouse_consultant_request:finished"
        )
    ).one()
    completion_logs = db_session.exec(
        select(AuditLog)
        .where(AuditLog.action == "provider_request_operation_finished")
        .where(AuditLog.entity_type == "provider_call_attempt")
        .where(AuditLog.entity_id == str(finished.id))
    ).all()
    assert len(completion_logs) == 1
    assert finished.status == "started"

    # A request-local completion audit is the execution-end signal, so it does
    # not borrow the AgentRun hard-limit clock. Age alone still cannot close the
    # unmarked request-local attempt.
    result = reconcile_stranded_provider_attempts(
        db_session,
        hard_limit_seconds=0,
        now=now + timedelta(seconds=1),
    )
    assert result == {"scanned": 1, "reconciled": 1, "stale_after_seconds": None}

    db_session.expire_all()
    finished = db_session.exec(
        select(ProviderCallAttempt).where(
            ProviderCallAttempt.operation_key == "inhouse_consultant_request:finished"
        )
    ).one()
    unfinished = db_session.exec(
        select(ProviderCallAttempt).where(
            ProviderCallAttempt.operation_key == "inhouse_consultant_request:unfinished"
        )
    ).one()
    allocation = db_session.get(ProviderCallAllocation, "deepseek")

    assert finished.status == "outcome_unknown"
    assert finished.settled_at is not None
    assert finished.billed_cost_usd is None
    assert finished.cost_basis == "unattributed"
    assert unfinished.status == "started"
    assert allocation is not None and allocation.used_calls == 1

    log = db_session.exec(
        select(AuditLog)
        .where(AuditLog.action == "provider_attempt_stranded_reconciled")
        .where(AuditLog.entity_id == str(finished.id))
    ).one()
    evidence = log.after_state_json or ""
    assert '"execution_end_signal": "provider_request_operation_finished"' in evidence
    assert '"cause_inferred": false' in evidence
    assert '"failure_class_inferred": false' in evidence
    assert '"billed_cost_known": false' in evidence
    assert '"call_slot_released": false' in evidence

    assert reconcile_stranded_provider_attempts(
        db_session,
        hard_limit_seconds=0,
        now=now + timedelta(seconds=2),
    )["reconciled"] == 0
