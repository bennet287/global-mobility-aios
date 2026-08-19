from __future__ import annotations

import pytest
from sqlalchemy import event, func
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from app.core.db import register_models
from app.core.organization_constitution import AutonomyLevel, MaterialActionType, RiskTier
from app.models.domain import OrganizationActivity, OrganizationActorType, OrganizationalWorkItem
from app.services.organization_activity import stage_activity as stage_activity_primitive
from app.services.organization_command import OrganizationCommandContext
from app.services.organization_governance_kernel import CapabilityAuthority, GatewayOutcome
from app.services.organization_governed_work import (
    GOVERNED_WORK_CAPABILITY,
    governed_assign_work_item,
    work_item_precondition_version,
)
from app.services.organization_transparency import governed_action_trace
from app.services.organization_work import create_work_item


@pytest.fixture()
def organization_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    register_models()
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture()
def human_context() -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key="default",
        actor_id="human-owner",
        actor_type=OrganizationActorType.human,
        authenticated_user_id="human-owner",
        role="admin",
        department="operations",
        position_key="board",
        authority_level="L4",
    )


@pytest.fixture()
def agent_context() -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key="default",
        actor_id="coo-agent",
        actor_type=OrganizationActorType.agent,
        authenticated_user_id="service-account",
        role="operator",
        department="operations",
        position_key="coo",
        authority_level="L2",
    )


@pytest.fixture()
def authority(agent_context: OrganizationCommandContext) -> CapabilityAuthority:
    return CapabilityAuthority(
        tenant_key=agent_context.tenant_key,
        actor_id=agent_context.actor_id,
        capability=GOVERNED_WORK_CAPABILITY,
        allowed_action_types=frozenset({MaterialActionType.WORK_ITEM_ASSIGNMENT}),
        max_risk_tier=RiskTier.R1,
        autonomy_level=AutonomyLevel.A4,
        allowed_scopes=frozenset({"operations"}),
    )


def _work(
    session: Session,
    context: OrganizationCommandContext,
    key: str,
) -> OrganizationalWorkItem:
    return create_work_item(
        session,
        context,
        idempotency_key=key,
        title=key,
        objective="Exercise explicit governance-to-effect causation",
        department="operations",
        authority_level="L2",
        assigned_position_key="coo",
    )


def test_governed_assignment_effect_explicitly_points_to_governance_authorization(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    agent_context: OrganizationCommandContext,
    authority: CapabilityAuthority,
) -> None:
    work = _work(organization_session, human_context, "c3-cause-work")

    result = governed_assign_work_item(
        organization_session,
        agent_context,
        authority,
        work_item_id=work.id,
        assigned_position_key="case_operations_specialist",
        expected_version=work_item_precondition_version(work),
        idempotency_key="c3-cause",
        reason="Make authorization-to-effect lineage explicit.",
    )

    assert result.evaluation.outcome is GatewayOutcome.AUTO_EXECUTE
    assert result.governance_activity is not None

    trace = governed_action_trace(
        organization_session,
        tenant_key="default",
        trace_id=result.evaluation.trace_id,
    )
    assert trace is not None
    assert trace.governance.activity_id == result.governance_activity.id
    assert len(trace.organization_effects) == 1

    effect = trace.organization_effects[0]
    assert effect.activity_type == "organization.work.assigned.v1"
    assert effect.causation_activity_id == trace.governance.activity_id
    assert effect.correlation_key == trace.trace_id


def test_idempotent_replay_does_not_duplicate_explicit_causal_chain(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    agent_context: OrganizationCommandContext,
    authority: CapabilityAuthority,
) -> None:
    work = _work(organization_session, human_context, "c3-replay-work")
    command = dict(
        work_item_id=work.id,
        assigned_position_key="case_operations_specialist",
        expected_version=work_item_precondition_version(work),
        idempotency_key="c3-replay",
        reason="Replay must preserve the original causal chain.",
    )

    first = governed_assign_work_item(
        organization_session,
        agent_context,
        authority,
        **command,
    )
    count_before = organization_session.exec(
        select(func.count()).select_from(OrganizationActivity)
    ).one()

    replay = governed_assign_work_item(
        organization_session,
        agent_context,
        authority,
        **command,
    )
    count_after = organization_session.exec(
        select(func.count()).select_from(OrganizationActivity)
    ).one()

    assert replay.evaluation.outcome is GatewayOutcome.IDEMPOTENT_REPLAY
    assert count_after == count_before

    trace = governed_action_trace(
        organization_session,
        tenant_key="default",
        trace_id=first.evaluation.trace_id,
    )
    assert trace is not None
    assert len(trace.organization_effects) == 1
    assert trace.organization_effects[0].causation_activity_id == trace.governance.activity_id


def test_effect_staging_failure_rolls_back_governance_authorization_and_work_mutation(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    agent_context: OrganizationCommandContext,
    authority: CapabilityAuthority,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = _work(organization_session, human_context, "c3-rollback-work")
    expected_version = work_item_precondition_version(work)
    activity_count_before = organization_session.exec(
        select(func.count()).select_from(OrganizationActivity)
    ).one()
    calls = 0

    def _stage_governance_then_fail_effect(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("simulated causally linked effect storage failure")
        return stage_activity_primitive(*args, **kwargs)

    monkeypatch.setattr(
        "app.services.organization_governed_work.stage_activity",
        _stage_governance_then_fail_effect,
    )

    with pytest.raises(RuntimeError, match="simulated causally linked effect storage failure"):
        governed_assign_work_item(
            organization_session,
            agent_context,
            authority,
            work_item_id=work.id,
            assigned_position_key="case_operations_specialist",
            expected_version=expected_version,
            idempotency_key="c3-rollback",
            reason="The authorization and effect must remain one atomic unit.",
        )

    organization_session.expire_all()
    persisted = organization_session.exec(
        select(OrganizationalWorkItem).where(OrganizationalWorkItem.id == work.id)
    ).one()
    activity_count_after = organization_session.exec(
        select(func.count()).select_from(OrganizationActivity)
    ).one()
    governance = organization_session.exec(
        select(OrganizationActivity).where(
            OrganizationActivity.tenant_key == "default",
            OrganizationActivity.activity_key == "governance:c3-rollback",
        )
    ).first()

    assert calls == 2
    assert persisted.assigned_position_key == "coo"
    assert activity_count_after == activity_count_before
    assert governance is None
