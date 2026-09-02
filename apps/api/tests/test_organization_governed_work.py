from __future__ import annotations

import json

import pytest
from sqlalchemy import event, func
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from app.core.db import register_models
from app.core.organization_constitution import AutonomyLevel, MaterialActionType, RiskTier
from app.models.domain import AuditLog, OrganizationActivity, OrganizationActorType, OrganizationalWorkItem
from app.services.organization_command import OrganizationCommandContext
from app.services.organization_governance_kernel import (
    CapabilityAuthority,
    GatewayOutcome,
    GatewayReason,
    PolicyDisposition,
)
from app.services.organization_governed_work import (
    GOVERNED_WORK_CAPABILITY,
    governed_assign_work_item,
    work_item_precondition_version,
)
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
        objective="Exercise the governed WorkItem assignment path",
        department="operations",
        authority_level="L2",
        assigned_position_key="coo",
    )


def _governance_activity(session: Session, key: str) -> OrganizationActivity | None:
    return session.exec(
        select(OrganizationActivity).where(
            OrganizationActivity.tenant_key == "default",
            OrganizationActivity.activity_key == f"governance:{key}",
        )
    ).first()


def test_governed_assignment_auto_executes_and_records_trace_atomically(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    agent_context: OrganizationCommandContext,
    authority: CapabilityAuthority,
) -> None:
    work = _work(organization_session, human_context, "b2-work")
    expected_version = work_item_precondition_version(work)

    result = governed_assign_work_item(
        organization_session,
        agent_context,
        authority,
        work_item_id=work.id,
        assigned_position_key="case_operations_specialist",
        expected_version=expected_version,
        idempotency_key="b2-assign",
        reason="Route the case to the specialist.",
    )

    assert result.evaluation.outcome is GatewayOutcome.AUTO_EXECUTE
    assert result.evaluation.reason is GatewayReason.AUTHORIZED
    assert result.mutated is True
    assert result.work_item.assigned_position_key == "case_operations_specialist"
    assert result.governance_activity is not None
    assert result.governance_activity.work_item_id == work.id
    assert result.governance_activity.correlation_key == str(result.evaluation.trace_id)

    payload = json.loads(result.governance_activity.payload_json)
    assert payload["action_type"] == MaterialActionType.WORK_ITEM_ASSIGNMENT.value
    assert payload["action_fingerprint"] == result.evaluation.action_fingerprint
    assert payload["outcome"] == GatewayOutcome.AUTO_EXECUTE.value

    assignment_audits = organization_session.exec(
        select(func.count()).select_from(AuditLog).where(AuditLog.action == "organization.work.assign")
    ).one()
    assert assignment_audits == 1


def test_exact_retry_replays_after_first_execution_advances_work_item_state(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    agent_context: OrganizationCommandContext,
    authority: CapabilityAuthority,
) -> None:
    work = _work(organization_session, human_context, "b2-replay-work")
    expected_version = work_item_precondition_version(work)
    command = dict(
        work_item_id=work.id,
        assigned_position_key="case_operations_specialist",
        expected_version=expected_version,
        idempotency_key="b2-replay",
        reason="Route the case to the specialist.",
    )

    first = governed_assign_work_item(organization_session, agent_context, authority, **command)
    advanced_version = work_item_precondition_version(first.work_item)
    assert advanced_version > expected_version

    activity_count_before = organization_session.exec(
        select(func.count()).select_from(OrganizationActivity)
    ).one()
    replay = governed_assign_work_item(organization_session, agent_context, authority, **command)
    activity_count_after = organization_session.exec(
        select(func.count()).select_from(OrganizationActivity)
    ).one()

    assert replay.evaluation.outcome is GatewayOutcome.IDEMPOTENT_REPLAY
    assert replay.evaluation.reason is GatewayReason.IDEMPOTENT_REPLAY
    assert replay.mutated is False
    assert replay.governance_activity is not None
    assert first.governance_activity is not None
    assert replay.governance_activity.id == first.governance_activity.id
    assert activity_count_after == activity_count_before


def test_new_idempotency_key_with_stale_precondition_is_blocked(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    agent_context: OrganizationCommandContext,
    authority: CapabilityAuthority,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = _work(organization_session, human_context, "b2-stale-work")
    expected_version = work_item_precondition_version(work)
    frozen_updated_at = work.updated_at
    monkeypatch.setattr(
        "app.services.organization_governed_work.now_utc",
        lambda: frozen_updated_at,
    )

    first = governed_assign_work_item(
        organization_session,
        agent_context,
        authority,
        work_item_id=work.id,
        assigned_position_key="case_operations_specialist",
        expected_version=expected_version,
        idempotency_key="b2-stale-first",
        reason="First assignment.",
    )
    assert first.evaluation.outcome is GatewayOutcome.AUTO_EXECUTE
    assert work_item_precondition_version(first.work_item) > expected_version

    stale = governed_assign_work_item(
        organization_session,
        agent_context,
        authority,
        work_item_id=work.id,
        assigned_position_key="pathway_operations_specialist",
        expected_version=expected_version,
        idempotency_key="b2-stale-second",
        reason="Stale competing assignment.",
    )

    assert stale.evaluation.outcome is GatewayOutcome.BLOCK
    assert stale.evaluation.reason is GatewayReason.STALE_VERSION
    assert stale.mutated is False
    assert stale.work_item.assigned_position_key == "case_operations_specialist"
    assert _governance_activity(organization_session, "b2-stale-second") is None


def test_conflicting_reuse_of_successful_idempotency_key_fails_closed(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    agent_context: OrganizationCommandContext,
    authority: CapabilityAuthority,
) -> None:
    work = _work(organization_session, human_context, "b2-conflict-work")
    expected_version = work_item_precondition_version(work)

    governed_assign_work_item(
        organization_session,
        agent_context,
        authority,
        work_item_id=work.id,
        assigned_position_key="case_operations_specialist",
        expected_version=expected_version,
        idempotency_key="b2-conflict",
        reason="First assignment.",
    )
    conflict = governed_assign_work_item(
        organization_session,
        agent_context,
        authority,
        work_item_id=work.id,
        assigned_position_key="pathway_operations_specialist",
        expected_version=expected_version,
        idempotency_key="b2-conflict",
        reason="Conflicting assignment.",
    )

    assert conflict.evaluation.outcome is GatewayOutcome.BLOCK
    assert conflict.evaluation.reason is GatewayReason.IDEMPOTENCY_CONFLICT
    assert conflict.work_item.assigned_position_key == "case_operations_specialist"


def test_review_required_authority_does_not_mutate_work_item(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    agent_context: OrganizationCommandContext,
    authority: CapabilityAuthority,
) -> None:
    work = _work(organization_session, human_context, "b2-review-work")
    expected_version = work_item_precondition_version(work)
    review_authority = CapabilityAuthority(
        tenant_key=authority.tenant_key,
        actor_id=authority.actor_id,
        capability=authority.capability,
        allowed_action_types=authority.allowed_action_types,
        max_risk_tier=authority.max_risk_tier,
        autonomy_level=AutonomyLevel.A2,
        allowed_scopes=authority.allowed_scopes,
    )

    result = governed_assign_work_item(
        organization_session,
        agent_context,
        review_authority,
        work_item_id=work.id,
        assigned_position_key="case_operations_specialist",
        expected_version=expected_version,
        idempotency_key="b2-review",
        reason="A2 must not execute directly.",
        policy_disposition=PolicyDisposition.ALLOW,
    )

    assert result.evaluation.outcome is GatewayOutcome.REVIEW_REQUIRED
    assert result.evaluation.reason is GatewayReason.AUTONOMY_REVIEW_REQUIRED
    assert result.mutated is False
    assert result.work_item.assigned_position_key == "coo"
    assert _governance_activity(organization_session, "b2-review") is None


def test_governance_activity_failure_rolls_back_assignment_and_audit(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    agent_context: OrganizationCommandContext,
    authority: CapabilityAuthority,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = _work(organization_session, human_context, "b2-rollback-work")
    expected_version = work_item_precondition_version(work)
    activity_count_before = organization_session.exec(
        select(func.count()).select_from(OrganizationActivity)
    ).one()
    audit_count_before = organization_session.exec(select(func.count()).select_from(AuditLog)).one()

    def _fail_governance_activity(*_args, **_kwargs):
        raise RuntimeError("simulated governance Activity storage failure")

    monkeypatch.setattr("app.services.organization_governed_work.stage_activity", _fail_governance_activity)

    with pytest.raises(RuntimeError, match="simulated governance Activity storage failure"):
        governed_assign_work_item(
            organization_session,
            agent_context,
            authority,
            work_item_id=work.id,
            assigned_position_key="case_operations_specialist",
            expected_version=expected_version,
            idempotency_key="b2-rollback",
            reason="Must roll back as one unit.",
        )

    organization_session.expire_all()
    persisted = organization_session.exec(
        select(OrganizationalWorkItem).where(OrganizationalWorkItem.id == work.id)
    ).one()
    activity_count_after = organization_session.exec(
        select(func.count()).select_from(OrganizationActivity)
    ).one()
    audit_count_after = organization_session.exec(select(func.count()).select_from(AuditLog)).one()

    assert persisted.assigned_position_key == "coo"
    assert activity_count_after == activity_count_before
    assert audit_count_after == audit_count_before
    assert _governance_activity(organization_session, "b2-rollback") is None
