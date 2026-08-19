from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.core.db import register_models
from app.core.organization_constitution import (
    AutonomyLevel,
    MaterialActionType,
    OrganizationActivityClass as ConstitutionalActivityClass,
    RiskTier,
)
from app.models.domain import OrganizationActivityClass, OrganizationActorType, now_utc
from app.services.organization_activity import append_activity
from app.services.organization_command import OrganizationCommandContext
from app.services.organization_governance_kernel import CapabilityAuthority, GatewayOutcome
from app.services.organization_governed_work import (
    GOVERNED_WORK_CAPABILITY,
    governed_assign_work_item,
    work_item_precondition_version,
)
from app.services.organization_transparency import (
    TransparencyDataError,
    TransparencyRecordRole,
    activities_for_trace,
    activities_for_work_item,
    governed_action_trace,
    transparency_activity_record,
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


def _governed_assignment(
    session: Session,
    human_context: OrganizationCommandContext,
    agent_context: OrganizationCommandContext,
    authority: CapabilityAuthority,
    *,
    key: str,
):
    work = create_work_item(
        session,
        human_context,
        idempotency_key=f"{key}-work",
        title=f"{key}-work",
        objective="Exercise the V1.3-C transparency foundation",
        department="operations",
        authority_level="L2",
        assigned_position_key="coo",
    )
    result = governed_assign_work_item(
        session,
        agent_context,
        authority,
        work_item_id=work.id,
        assigned_position_key="case_operations_specialist",
        expected_version=work_item_precondition_version(work),
        idempotency_key=key,
        reason="Route the case through the governed transparency trace.",
    )
    assert result.evaluation.outcome is GatewayOutcome.AUTO_EXECUTE
    return work, result


def test_governed_assignment_correlates_authorization_and_organization_effect(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    agent_context: OrganizationCommandContext,
    authority: CapabilityAuthority,
) -> None:
    work, result = _governed_assignment(
        organization_session,
        human_context,
        agent_context,
        authority,
        key="c1-correlated",
    )
    trace_id = str(result.evaluation.trace_id)

    records = activities_for_trace(
        organization_session,
        tenant_key="default",
        trace_id=trace_id,
    )

    assert len(records) == 2
    assert {record.correlation_key for record in records} == {trace_id}
    assert {record.work_item_id for record in records} == {work.id}

    governance = next(
        record for record in records if record.role is TransparencyRecordRole.GOVERNANCE
    )
    effect = next(
        record
        for record in records
        if record.role is TransparencyRecordRole.ORGANIZATION_EFFECT
    )

    assert governance.constitutional_activity_class is ConstitutionalActivityClass.MATERIAL
    assert governance.board_inspectable is True
    assert governance.requires_durable_record is True
    assert governance.requires_full_lineage is True
    assert governance.may_compact_after_policy_window is False
    assert governance.payload["action_type"] == MaterialActionType.WORK_ITEM_ASSIGNMENT.value
    assert governance.payload["effective_risk_tier"] == RiskTier.R1.value

    assert effect.activity_type == "organization.work.assigned.v1"
    assert effect.constitutional_activity_class is None
    assert effect.board_inspectable is True
    assert effect.requires_full_lineage is None


def test_governed_action_trace_reconstructs_one_material_action(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    agent_context: OrganizationCommandContext,
    authority: CapabilityAuthority,
) -> None:
    _, result = _governed_assignment(
        organization_session,
        human_context,
        agent_context,
        authority,
        key="c1-trace",
    )

    trace = governed_action_trace(
        organization_session,
        tenant_key="default",
        trace_id=result.evaluation.trace_id,
    )

    assert trace is not None
    assert trace.trace_id == str(result.evaluation.trace_id)
    assert trace.board_inspectable is True
    assert trace.governance.role is TransparencyRecordRole.GOVERNANCE
    assert trace.governance.payload["outcome"] == GatewayOutcome.AUTO_EXECUTE.value
    assert len(trace.organization_effects) == 1
    assert trace.organization_effects[0].activity_type == "organization.work.assigned.v1"


def test_trace_queries_are_strictly_tenant_scoped(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    agent_context: OrganizationCommandContext,
    authority: CapabilityAuthority,
) -> None:
    _, result = _governed_assignment(
        organization_session,
        human_context,
        agent_context,
        authority,
        key="c1-tenant",
    )
    trace_id = str(result.evaluation.trace_id)
    other_context = OrganizationCommandContext(
        tenant_key="tenant-b",
        actor_id="tenant-b-human",
        actor_type=OrganizationActorType.human,
        authenticated_user_id="tenant-b-human",
        role="admin",
        department="operations",
    )
    append_activity(
        organization_session,
        other_context,
        activity_key="tenant-b-same-correlation",
        stream_key="tenant-b",
        activity_class=OrganizationActivityClass.operational,
        activity_type="tenant-b.supporting.v1",
        title="Other tenant activity",
        summary="Must never appear in the default tenant trace.",
        source_object_type="tenant_test",
        source_object_id="tenant-b",
        occurred_at=now_utc(),
        correlation_key=trace_id,
    )

    default_records = activities_for_trace(
        organization_session,
        tenant_key="default",
        trace_id=trace_id,
    )
    other_records = activities_for_trace(
        organization_session,
        tenant_key="tenant-b",
        trace_id=trace_id,
    )

    assert len(default_records) == 2
    assert all(record.tenant_key == "default" for record in default_records)
    assert len(other_records) == 1
    assert other_records[0].tenant_key == "tenant-b"


def test_legacy_activity_is_board_inspectable_without_fake_constitutional_class(
    organization_session: Session,
    human_context: OrganizationCommandContext,
) -> None:
    legacy = append_activity(
        organization_session,
        human_context,
        activity_key="c1-legacy",
        stream_key="legacy",
        activity_class=OrganizationActivityClass.operational,
        activity_type="legacy.runtime.activity.v1",
        title="Legacy activity",
        summary="Existing activity without V1.3 constitutional classification.",
        source_object_type="legacy",
        source_object_id="legacy-1",
        occurred_at=now_utc(),
        correlation_key=str(uuid4()),
    )

    record = transparency_activity_record(legacy)

    assert record.board_inspectable is True
    assert record.constitutional_activity_class is None
    assert record.requires_durable_record is None
    assert record.requires_full_lineage is None
    assert record.may_compact_after_policy_window is None


def test_malformed_governance_trace_fails_closed(
    organization_session: Session,
    human_context: OrganizationCommandContext,
) -> None:
    malformed = append_activity(
        organization_session,
        human_context,
        activity_key="governance:c1-malformed",
        stream_key="governance:malformed",
        activity_class=OrganizationActivityClass.operational,
        activity_type="governance.work_item.assignment.auto_execute",
        title="Malformed governance activity",
        summary="Trace identity is intentionally inconsistent for the test.",
        source_object_type="organizational_work_item",
        source_object_id="missing",
        occurred_at=now_utc(),
        correlation_key="trace-a",
        payload={
            "trace_id": "trace-b",
            "constitutional_activity_class": ConstitutionalActivityClass.MATERIAL.value,
        },
    )

    with pytest.raises(TransparencyDataError, match="trace_id/correlation mismatch"):
        transparency_activity_record(malformed)


def test_work_item_history_includes_creation_effect_and_governance_record(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    agent_context: OrganizationCommandContext,
    authority: CapabilityAuthority,
) -> None:
    work, _ = _governed_assignment(
        organization_session,
        human_context,
        agent_context,
        authority,
        key="c1-work-history",
    )

    records = activities_for_work_item(
        organization_session,
        tenant_key="default",
        work_item_id=work.id,
    )

    assert len(records) == 3
    assert {record.activity_type for record in records} == {
        "organization.work.created.v1",
        "organization.work.assigned.v1",
        "governance.work_item.assignment.auto_execute",
    }
    assert all(record.board_inspectable for record in records)
