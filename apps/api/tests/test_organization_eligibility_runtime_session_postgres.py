from __future__ import annotations

import os
from time import sleep

import pytest
from sqlmodel import Session, select

from app.models.organization_presence import OrganizationExecutionHeartbeat
from app.services.organization_eligibility_runtime_session import (
    execute_fenced_governed_eligibility_transition_intent,
)
from tests.test_organization_eligibility_runtime_session import POSITION_KEY, _fixture
from tests.test_organization_independent_eligibility_verification import (
    FakeProvider,
    _authority,
    _proposer_output,
)


pytestmark = pytest.mark.skipif(
    not os.getenv("GMAI_TEST_DATABASE_URL", "").startswith("postgresql"),
    reason="real PostgreSQL contract requires GMAI_TEST_DATABASE_URL",
)


def test_postgres_fenced_e2_runtime_renews_while_provider_is_active(db_session: Session) -> None:
    graph, work, runtime = _fixture(db_session)
    provider = FakeProvider(
        name="deepseek",
        model="deepseek-reasoner",
        content=_proposer_output(graph),
        on_complete=lambda: sleep(0.08),
    )

    wrapped = execute_fenced_governed_eligibility_transition_intent(
        db_session,
        tenant_key="tenant-a",
        position_key=POSITION_KEY,
        work_item_id=work.id,
        runtime_profile=runtime,
        authority=_authority(),
        provider=provider,
        idempotency_key="fenced-e2-postgres-renewal",
        lease_seconds=15,
        renewal_interval_seconds=0.01,
    )

    assert wrapped.fence_token == 1
    assert wrapped.renewal_count >= 1
    events = list(
        db_session.exec(
            select(OrganizationExecutionHeartbeat)
            .where(
                OrganizationExecutionHeartbeat.execution_attempt_id
                == wrapped.execution_attempt_id
            )
            .order_by(OrganizationExecutionHeartbeat.sequence)
        ).all()
    )
    checkpoints = [event.checkpoint for event in events]
    assert checkpoints[0] == "attempt_started"
    assert checkpoints[-1] == "agent_completed"
    assert "runtime_session_renewed" in checkpoints
    assert all(event.writer == "eligibility-runtime-worker" for event in events)
