from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import Enum as SQLAlchemyEnum, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.core.db import register_models
from app.models.domain import (
    AgentRun,
    ExecutiveDecision,
    OrganizationActivity,
    OrganizationActivityClass,
    OrganizationActivityStream,
    OrganizationActorType,
    OrganizationBlocker,
    OrganizationBlockerStatus,
    OrganizationBlockerType,
    OrganizationContribution,
    OrganizationContributionImpactKind,
    OrganizationContributionRecordKind,
    OrganizationContributionVerificationMethod,
    OrganizationHumanAction,
    OrganizationHumanActionType,
    OrganizationRecordReference,
    OrganizationWorkItemDependency,
    OrganizationDependencyType,
    OrganizationalWorkItem,
    RiskEscalation,
)


NOW = datetime(2026, 8, 13, tzinfo=timezone.utc)
FINGERPRINT = "a" * 64


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


def _work(key: str, tenant: str = "default") -> OrganizationalWorkItem:
    return OrganizationalWorkItem(
        idempotency_key=key,
        idempotency_fingerprint=FINGERPRINT,
        tenant_key=tenant,
        title=key,
        objective="Persistence test",
        department="engineering",
        authority_level="operational",
        assigned_position_key="cto",
    )


def _contribution(key: str, *, work: OrganizationalWorkItem | None = None) -> OrganizationContribution:
    return OrganizationContribution(
        contribution_key=key,
        record_fingerprint=FINGERPRINT,
        tenant_key=work.tenant_key if work else "default",
        contribution_type="verified_state_transition",
        title="Verified outcome",
        outcome_summary="An authoritative state changed.",
        actor_type=OrganizationActorType.human,
        actor_id="human-1",
        department="operations",
        accountable_position_key="coo",
        authority_level="operational",
        work_item_id=work.id if work else None,
        source_object_type="eligibility_assessment",
        source_object_id="assessment-1",
        source_object_version="1",
        source_state="approved",
        verification_method=OrganizationContributionVerificationMethod.human_attestation,
        record_kind=OrganizationContributionRecordKind.outcome,
        verified_by="human-1",
        verified_at=NOW,
        human_review_state="completed",
        impact_kind=OrganizationContributionImpactKind.state_change,
        effective_at=NOW,
        created_by="human-1",
    )


def test_durable_organization_tables_are_registered() -> None:
    register_models()
    expected = {
        "organization_activity_streams",
        "organization_activities",
        "organization_contributions",
        "organization_work_item_dependencies",
        "organization_blockers",
        "organization_human_action_requests",
        "organization_human_actions",
        "organization_record_references",
    }
    assert expected <= set(SQLModel.metadata.tables)


def test_append_only_records_have_no_mutable_lifecycle_columns() -> None:
    for model in (
        OrganizationActivity,
        OrganizationContribution,
        OrganizationHumanAction,
        OrganizationRecordReference,
    ):
        columns = set(model.__table__.columns.keys())
        assert "updated_at" not in columns
        assert "status" not in columns


def test_work_item_and_blocker_lifecycles_remain_mutable(organization_session: Session) -> None:
    work = _work("mutable-work")
    organization_session.add(work)
    organization_session.commit()
    work.status = "completed"
    organization_session.add(work)
    organization_session.commit()
    assert work.status == "completed"

    blocker = OrganizationBlocker(
        blocker_key="blocker-1",
        record_fingerprint=FINGERPRINT,
        tenant_key=work.tenant_key,
        blocker_type=OrganizationBlockerType.dependency,
        severity="high",
        title="Dependency missing",
        description="Required governed work is incomplete.",
        work_item_id=work.id,
        created_by="system",
        updated_by="system",
    )
    organization_session.add(blocker)
    organization_session.commit()
    blocker.status = OrganizationBlockerStatus.resolved
    blocker.resolved_at = NOW
    blocker.resolution_summary = "Dependency completed."
    blocker.resolving_actor_type = OrganizationActorType.human
    blocker.resolving_actor_id = "human-1"
    blocker.updated_by = "human-1"
    organization_session.add(blocker)
    organization_session.commit()
    assert blocker.status == OrganizationBlockerStatus.resolved


def test_dependency_rejects_self_duplicate_and_cross_tenant_edges(organization_session: Session) -> None:
    work_a = _work("work-a", "tenant-a")
    work_b = _work("work-b", "tenant-a")
    work_other = _work("work-other", "tenant-b")
    organization_session.add_all([work_a, work_b, work_other])
    organization_session.commit()

    self_edge = OrganizationWorkItemDependency(
        dependency_key="self-edge",
        record_fingerprint=FINGERPRINT,
        tenant_key="tenant-a",
        work_item_id=work_a.id,
        depends_on_work_item_id=work_a.id,
        dependency_type=OrganizationDependencyType.blocks,
        created_by="human-1",
        updated_by="human-1",
    )
    organization_session.add(self_edge)
    with pytest.raises(IntegrityError):
        organization_session.commit()
    organization_session.rollback()

    edge = OrganizationWorkItemDependency(
        dependency_key="edge-a-b",
        record_fingerprint=FINGERPRINT,
        tenant_key="tenant-a",
        work_item_id=work_a.id,
        depends_on_work_item_id=work_b.id,
        dependency_type=OrganizationDependencyType.blocks,
        created_by="human-1",
        updated_by="human-1",
    )
    organization_session.add(edge)
    organization_session.commit()

    duplicate = OrganizationWorkItemDependency(
        dependency_key="edge-a-b-duplicate",
        record_fingerprint=FINGERPRINT,
        tenant_key="tenant-a",
        work_item_id=work_a.id,
        depends_on_work_item_id=work_b.id,
        dependency_type=OrganizationDependencyType.blocks,
        created_by="human-1",
        updated_by="human-1",
    )
    organization_session.add(duplicate)
    with pytest.raises(IntegrityError):
        organization_session.commit()
    organization_session.rollback()

    cross_tenant = OrganizationWorkItemDependency(
        dependency_key="cross-tenant-edge",
        record_fingerprint=FINGERPRINT,
        tenant_key="tenant-a",
        work_item_id=work_a.id,
        depends_on_work_item_id=work_other.id,
        dependency_type=OrganizationDependencyType.requires,
        created_by="human-1",
        updated_by="human-1",
    )
    organization_session.add(cross_tenant)
    with pytest.raises(IntegrityError):
        organization_session.commit()
    organization_session.rollback()


def test_activity_and_contribution_idempotency_keys_are_unique(organization_session: Session) -> None:
    stream = OrganizationActivityStream(tenant_key="default", stream_key="organization")
    organization_session.add(stream)
    organization_session.commit()

    def activity(sequence: int, fingerprint: str) -> OrganizationActivity:
        return OrganizationActivity(
            activity_key="same-activity-key",
            record_fingerprint=fingerprint,
            tenant_key="default",
            activity_stream_id=stream.id,
            stream_sequence=sequence,
            activity_class=OrganizationActivityClass.operational,
            activity_type="persistence.checked.v1",
            title="Persistence checked",
            summary="A bounded schema check occurred.",
            actor_type=OrganizationActorType.system,
            actor_id="pytest",
            source_object_type="verified_rule",
            source_object_id="rule-1",
            occurred_at=NOW,
            created_by="pytest",
        )

    organization_session.add(activity(1, FINGERPRINT))
    organization_session.commit()
    organization_session.add(activity(2, "b" * 64))
    with pytest.raises(IntegrityError):
        organization_session.commit()
    organization_session.rollback()

    organization_session.add(_contribution("same-contribution-key"))
    organization_session.commit()
    organization_session.add(_contribution("same-contribution-key"))
    with pytest.raises(IntegrityError):
        organization_session.commit()
    organization_session.rollback()


def test_human_action_rejects_agent_actor(organization_session: Session) -> None:
    work = _work("human-action-work")
    organization_session.add(work)
    organization_session.commit()
    action = OrganizationHumanAction(
        action_key="agent-cannot-act",
        record_fingerprint=FINGERPRINT,
        tenant_key=work.tenant_key,
        action_type=OrganizationHumanActionType.reviewed,
        actor_type=OrganizationActorType.agent,
        human_actor_id="agent-1",
        work_item_id=work.id,
        outcome="Attempted review",
        occurred_at=NOW,
        created_by="agent-1",
    )
    organization_session.add(action)
    with pytest.raises(IntegrityError):
        organization_session.commit()
    organization_session.rollback()


def test_contribution_requires_authoritative_provenance(organization_session: Session) -> None:
    invalid = _contribution("telemetry-is-not-contribution")
    invalid.source_object_type = "agent_run"
    organization_session.add(invalid)
    with pytest.raises(IntegrityError):
        organization_session.commit()
    organization_session.rollback()

    source_columns = OrganizationContribution.__table__.columns
    for name in ("source_object_type", "source_object_id", "source_object_version", "source_state"):
        assert source_columns[name].nullable is False


def test_existing_canonical_boundaries_remain_separate() -> None:
    assert ExecutiveDecision.__tablename__ == "executive_decisions"
    assert RiskEscalation.__tablename__ == "risk_escalations"
    assert OrganizationBlocker.__tablename__ != RiskEscalation.__tablename__
    agent_columns = set(AgentRun.__table__.columns.keys())
    assert "contribution_key" not in agent_columns
    assert "record_fingerprint" not in agent_columns
    assert "verification_method" not in agent_columns


def test_authoritative_history_foreign_keys_do_not_cascade() -> None:
    for model in (OrganizationActivity, OrganizationContribution, OrganizationHumanAction, OrganizationRecordReference):
        for foreign_key in model.__table__.foreign_keys:
            assert foreign_key.ondelete in (None, "NO ACTION", "RESTRICT")


def test_controlled_values_are_portable_non_native_enums() -> None:
    models = (
        OrganizationalWorkItem,
        ExecutiveDecision,
        OrganizationActivity,
        OrganizationContribution,
        OrganizationWorkItemDependency,
        OrganizationBlocker,
        OrganizationHumanAction,
        OrganizationRecordReference,
    )
    enum_columns = [
        column
        for model in models
        for column in model.__table__.columns
        if isinstance(column.type, SQLAlchemyEnum)
    ]
    assert enum_columns
    assert all(column.type.native_enum is False for column in enum_columns)
