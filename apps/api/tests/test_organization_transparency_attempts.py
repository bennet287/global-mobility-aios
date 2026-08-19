from __future__ import annotations

import json

import pytest
from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.core.db import register_models
from app.core.organization_constitution import AutonomyLevel, MaterialActionType, RiskTier
from app.models.domain import OrganizationActorType
from app.services.organization_command import OrganizationCommandContext
from app.services.organization_governance_kernel import (
    CapabilityAuthority,
    GatewayOutcome,
    GatewayReason,
)
from app.services.organization_governed_work import (
    GOVERNED_WORK_CAPABILITY,
    work_item_precondition_version,
)
from app.services.organization_governed_work_transparency import (
    transparent_governed_assign_work_item,
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


def _authority(
    context: OrganizationCommandContext,
    *,
    autonomy: AutonomyLevel,
    scopes: frozenset[str] = frozenset({"operations"}),
) -> CapabilityAuthority:
    return CapabilityAuthority(
        tenant_key=context.tenant_key,
        actor_id=context.actor_id,
        capability=GOVERNED_WORK_CAPABILITY,
        allowed_action_types=frozenset({MaterialActionType.WORK_ITEM_ASSIGNMENT}),
        max_risk_tier=RiskTier.R1,
        autonomy_level=autonomy,
        allowed_scopes=scopes,
    )


def _work(
    session: Session,
    context: OrganizationCommandContext,
    key: str,
):
    return create_work_item(
        session,
        context,
        idempotency_key=key,
        title=key,
        objective="Exercise non-executing governance transparency",
        department="operations",
        authority_level="L2",
        assigned_position_key="coo",
    )


def test_review_required_material_attempt_is_persisted_without_mutation(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    agent_context: OrganizationCommandContext,
) -> None:
    work = _work(organization_session, human_context, "c2-review-work")
    expected_version = work_item_precondition_version(work)

    result = transparent_governed_assign_work_item(
        organization_session,
        agent_context,
        _authority(agent_context, autonomy=AutonomyLevel.A2),
        work_item_id=work.id,
        assigned_position_key="case_operations_specialist",
        expected_version=expected_version,
        idempotency_key="c2-review",
        reason="A2 must route this material attempt to review.",
    )

    assert result.assignment.evaluation.outcome is GatewayOutcome.REVIEW_REQUIRED
    assert result.assignment.evaluation.reason is GatewayReason.AUTONOMY_REVIEW_REQUIRED
    assert result.mutated is False
    assert result.assignment.work_item.assigned_position_key == "coo"
    assert result.assignment.governance_activity is None
    assert result.attempt_activity is not None
    assert result.attempt_activity.activity_key == (
        f"governance:attempt:{result.assignment.evaluation.trace_id}"
    )

    payload = json.loads(result.attempt_activity.payload_json)
    assert payload["governance_record_kind"] == "attempt"
    assert payload["outcome"] == GatewayOutcome.REVIEW_REQUIRED.value
    assert payload["requested_assigned_position_key"] == "case_operations_specialist"
    assert payload["requested_expected_version"] == expected_version

    trace = governed_action_trace(
        organization_session,
        tenant_key="default",
        trace_id=result.assignment.evaluation.trace_id,
    )
    assert trace is not None
    assert trace.governance.activity_id == result.attempt_activity.id
    assert trace.organization_effects == ()
    assert trace.board_inspectable is True


def test_stale_material_attempt_is_persisted_and_does_not_change_work(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    agent_context: OrganizationCommandContext,
) -> None:
    work = _work(organization_session, human_context, "c2-stale-work")
    expected_version = work_item_precondition_version(work)
    authority = _authority(agent_context, autonomy=AutonomyLevel.A4)

    first = transparent_governed_assign_work_item(
        organization_session,
        agent_context,
        authority,
        work_item_id=work.id,
        assigned_position_key="case_operations_specialist",
        expected_version=expected_version,
        idempotency_key="c2-stale-first",
        reason="First authorized assignment.",
    )
    assert first.assignment.evaluation.outcome is GatewayOutcome.AUTO_EXECUTE
    assert first.attempt_activity is None

    stale = transparent_governed_assign_work_item(
        organization_session,
        agent_context,
        authority,
        work_item_id=work.id,
        assigned_position_key="pathway_operations_specialist",
        expected_version=expected_version,
        idempotency_key="c2-stale-second",
        reason="Competing command uses the old precondition.",
    )

    assert stale.assignment.evaluation.outcome is GatewayOutcome.BLOCK
    assert stale.assignment.evaluation.reason is GatewayReason.STALE_VERSION
    assert stale.assignment.work_item.assigned_position_key == "case_operations_specialist"
    assert stale.attempt_activity is not None

    trace = governed_action_trace(
        organization_session,
        tenant_key="default",
        trace_id=stale.assignment.evaluation.trace_id,
    )
    assert trace is not None
    assert trace.organization_effects == ()
    assert trace.governance.payload["reason"] == GatewayReason.STALE_VERSION.value


def test_scope_denied_attempt_is_visible_to_board_trace(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    agent_context: OrganizationCommandContext,
) -> None:
    work = _work(organization_session, human_context, "c2-scope-work")

    result = transparent_governed_assign_work_item(
        organization_session,
        agent_context,
        _authority(
            agent_context,
            autonomy=AutonomyLevel.A4,
            scopes=frozenset({"finance"}),
        ),
        work_item_id=work.id,
        assigned_position_key="case_operations_specialist",
        expected_version=work_item_precondition_version(work),
        idempotency_key="c2-scope",
        reason="Actor does not hold operations scope.",
    )

    assert result.assignment.evaluation.outcome is GatewayOutcome.BLOCK
    assert result.assignment.evaluation.reason is GatewayReason.SCOPE_DENIED
    assert result.mutated is False
    assert result.attempt_activity is not None

    trace = governed_action_trace(
        organization_session,
        tenant_key="default",
        trace_id=result.assignment.evaluation.trace_id,
    )
    assert trace is not None
    assert trace.governance.payload["outcome"] == GatewayOutcome.BLOCK.value
    assert trace.governance.payload["reason"] == GatewayReason.SCOPE_DENIED.value


def test_review_attempt_does_not_poison_later_successful_command_idempotency(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    agent_context: OrganizationCommandContext,
) -> None:
    work = _work(organization_session, human_context, "c2-authority-change-work")
    expected_version = work_item_precondition_version(work)
    command = dict(
        work_item_id=work.id,
        assigned_position_key="case_operations_specialist",
        expected_version=expected_version,
        idempotency_key="c2-authority-change",
        reason="Same requested change after delegated authority increases.",
    )

    review = transparent_governed_assign_work_item(
        organization_session,
        agent_context,
        _authority(agent_context, autonomy=AutonomyLevel.A2),
        **command,
    )
    assert review.assignment.evaluation.outcome is GatewayOutcome.REVIEW_REQUIRED
    assert review.attempt_activity is not None
    assert review.assignment.work_item.assigned_position_key == "coo"

    authorized = transparent_governed_assign_work_item(
        organization_session,
        agent_context,
        _authority(agent_context, autonomy=AutonomyLevel.A4),
        **command,
    )
    assert authorized.assignment.evaluation.outcome is GatewayOutcome.AUTO_EXECUTE
    assert authorized.assignment.mutated is True
    assert authorized.assignment.work_item.assigned_position_key == "case_operations_specialist"
    assert authorized.assignment.governance_activity is not None
    assert authorized.assignment.governance_activity.activity_key == "governance:c2-authority-change"
    assert authorized.attempt_activity is None


def test_attempt_activity_storage_failure_cannot_silently_hide_material_attempt(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    agent_context: OrganizationCommandContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = _work(organization_session, human_context, "c2-storage-failure-work")

    def _fail_attempt_storage(*_args, **_kwargs):
        raise RuntimeError("simulated attempt Activity storage failure")

    monkeypatch.setattr(
        "app.services.organization_governed_work_transparency.stage_activity",
        _fail_attempt_storage,
    )

    with pytest.raises(RuntimeError, match="simulated attempt Activity storage failure"):
        transparent_governed_assign_work_item(
            organization_session,
            agent_context,
            _authority(agent_context, autonomy=AutonomyLevel.A2),
            work_item_id=work.id,
            assigned_position_key="case_operations_specialist",
            expected_version=work_item_precondition_version(work),
            idempotency_key="c2-storage-failure",
            reason="Review attempt must not disappear silently.",
        )

    organization_session.refresh(work)
    assert work.assigned_position_key == "coo"
