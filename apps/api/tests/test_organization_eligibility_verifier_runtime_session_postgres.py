from __future__ import annotations

import os
import time

import pytest
from sqlmodel import Session, select

from app.models.domain import OrganizationExecutionAttempt, OrganizationalWorkItem
from app.models.organization_presence import OrganizationExecutionHeartbeat
from app.services.organization_eligibility_verifier_runtime_session import (
    DEFAULT_ELIGIBILITY_VERIFIER_RUNTIME_WRITER,
    execute_fenced_independent_eligibility_verification,
)
from tests.test_organization_independent_eligibility_verification import (
    FakeProvider,
    _setup,
    _verifier_output,
    _verifier_runtime,
)


pytestmark = pytest.mark.skipif(
    not os.getenv("GMAI_TEST_DATABASE_URL", "").startswith("postgresql"),
    reason="real PostgreSQL G.1 runtime renewal requires GMAI_TEST_DATABASE_URL",
)


def test_postgres_fenced_g1_runtime_renews_active_verifier_lease(
    db_session: Session,
) -> None:
    proposal, readiness, _, _, graph, _, verification_work, _ = _setup(db_session)

    wrapped = execute_fenced_independent_eligibility_verification(
        db_session,
        proposal=proposal,
        readiness=readiness,
        verification_work_item_id=verification_work.id,
        verifier_position_key="austria_independent_verifier",
        verifier_runtime_profile=_verifier_runtime(),
        provider=FakeProvider(
            name="openai",
            model="gpt-verifier",
            content=_verifier_output(graph),
            on_complete=lambda: time.sleep(0.08),
        ),
        idempotency_key="g1-postgres-active-renewal",
        lease_seconds=15,
        renewal_interval_seconds=0.01,
    )

    assert wrapped.fence_token == 1
    assert wrapped.renewal_count >= 1

    work = db_session.get(OrganizationalWorkItem, verification_work.id)
    assert work is not None
    assert work.status == "completed"

    attempt = db_session.exec(
        select(OrganizationExecutionAttempt).where(
            OrganizationExecutionAttempt.id == wrapped.execution_attempt_id
        )
    ).one()
    assert attempt.status == "completed"
    assert attempt.actor == DEFAULT_ELIGIBILITY_VERIFIER_RUNTIME_WRITER

    events = list(
        db_session.exec(
            select(OrganizationExecutionHeartbeat)
            .where(
                OrganizationExecutionHeartbeat.execution_attempt_id == attempt.id
            )
            .order_by(OrganizationExecutionHeartbeat.sequence)
        ).all()
    )
    checkpoints = [event.checkpoint for event in events]
    assert checkpoints[0] == "attempt_started"
    assert "runtime_session_renewed" in checkpoints
    assert checkpoints[-1] == "agent_completed"
    assert all(
        event.writer == DEFAULT_ELIGIBILITY_VERIFIER_RUNTIME_WRITER
        for event in events
    )
