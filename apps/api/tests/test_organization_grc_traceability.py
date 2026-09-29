from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from sqlmodel import Session, select

from app.models.domain import (
    ExecutiveDecision,
    OrganizationActivity,
    OrganizationActivityClass,
    OrganizationActivityStream,
    OrganizationActorType,
    OrganizationControl,
    OrganizationDecisionType,
    OrganizationalWorkItem,
    RiskEscalation,
)
from app.services.organization_grc_traceability import project_organization_grc_traceability


_BASE_TIME = datetime(2026, 9, 29, 8, 0, tzinfo=timezone.utc)


def _work(
    session: Session,
    *,
    tenant_key: str,
    key: str,
    position_key: str = "security_grc_lead",
) -> OrganizationalWorkItem:
    work = OrganizationalWorkItem(
        idempotency_key=key,
        tenant_key=tenant_key,
        work_type="organizational",
        objective_key=f"objective:{key}",
        phase_key="18A",
        title=f"GRC work {key}",
        objective="Trace governed risk lineage without inferring authority or controls.",
        department="Security",
        authority_level="L2",
        assigned_position_key=position_key,
        risk_level="high",
    )
    session.add(work)
    session.flush()
    return work


def _risk(
    session: Session,
    *,
    key: str,
    work_item_id: UUID | None,
    position_key: str = "security_grc_lead",
) -> RiskEscalation:
    risk = RiskEscalation(
        risk_key=key,
        work_item_id=work_item_id,
        category="security",
        severity="high",
        title=f"Risk {key}",
        description="Bounded test risk.",
        accountable_position_key=position_key,
        escalated_to_position_key="ciso",
    )
    session.add(risk)
    session.flush()
    return risk


def _decision(
    session: Session,
    *,
    work: OrganizationalWorkItem,
    key: str,
    owner_position: str = "security_grc_lead",
) -> ExecutiveDecision:
    decision = ExecutiveDecision(
        decision_key=key,
        tenant_key=work.tenant_key,
        decision_type=OrganizationDecisionType.risk,
        work_item_id=work.id,
        authority_level="L2",
        requested_by_position="security_grc_lead",
        decision_owner_position=owner_position,
        title=f"Decision {key}",
        question="Should the governed risk response proceed?",
        recommendation="Keep the response bounded and evidence-backed.",
    )
    session.add(decision)
    session.flush()
    return decision


def _activity(
    session: Session,
    *,
    tenant_key: str,
    work: OrganizationalWorkItem,
    activity_key: str,
    source_object_type: str,
    source_object_id: str,
    occurred_at: datetime,
    activity_type: str = "organization.decision.created.v1",
    activity_class: OrganizationActivityClass = OrganizationActivityClass.decision,
) -> OrganizationActivity:
    stream = OrganizationActivityStream(
        tenant_key=tenant_key,
        stream_key=f"test:{activity_key}",
        last_sequence=1,
    )
    session.add(stream)
    session.flush()

    activity = OrganizationActivity(
        activity_key=activity_key,
        record_fingerprint=hashlib.sha256(activity_key.encode("utf-8")).hexdigest(),
        tenant_key=tenant_key,
        activity_stream_id=stream.id,
        stream_sequence=1,
        activity_class=activity_class,
        activity_type=activity_type,
        title=f"Activity {activity_key}",
        summary="Durable traceability test activity.",
        department=work.department,
        position_key=work.assigned_position_key,
        authority_level=work.authority_level,
        actor_type=OrganizationActorType.system,
        actor_id="pytest",
        work_item_id=work.id,
        source_object_type=source_object_type,
        source_object_id=source_object_id,
        payload_json="{}",
        occurred_at=occurred_at,
        created_by="pytest",
    )
    session.add(activity)
    session.flush()
    return activity


def _row_counts(session: Session) -> dict[type[object], int]:
    models = (
        OrganizationalWorkItem,
        RiskEscalation,
        ExecutiveDecision,
        OrganizationActivityStream,
        OrganizationActivity,
        OrganizationControl,
    )
    return {model: len(session.exec(select(model)).all()) for model in models}


def test_grc_projection_is_tenant_scoped_and_excludes_orphan_risks(
    db_session: Session,
) -> None:
    tenant_a_work = _work(db_session, tenant_key="tenant-a", key="work-a")
    tenant_b_work = _work(db_session, tenant_key="tenant-b", key="work-b")

    tenant_a_risk = _risk(
        db_session,
        key="risk-a",
        work_item_id=tenant_a_work.id,
    )
    _risk(db_session, key="risk-b", work_item_id=tenant_b_work.id)
    _risk(db_session, key="risk-orphan", work_item_id=None)

    tenant_a_decision = _decision(db_session, work=tenant_a_work, key="decision-a")
    tenant_b_decision = _decision(db_session, work=tenant_b_work, key="decision-b")
    tenant_a_activity = _activity(
        db_session,
        tenant_key="tenant-a",
        work=tenant_a_work,
        activity_key="activity-a",
        source_object_type="executive_decision",
        source_object_id=str(tenant_a_decision.id),
        occurred_at=_BASE_TIME,
    )
    _activity(
        db_session,
        tenant_key="tenant-b",
        work=tenant_b_work,
        activity_key="activity-b",
        source_object_type="executive_decision",
        source_object_id=str(tenant_b_decision.id),
        occurred_at=_BASE_TIME,
    )
    db_session.commit()

    traces = project_organization_grc_traceability(db_session, tenant_key="tenant-a")

    assert len(traces) == 1
    trace = traces[0]
    assert trace.risk_id == tenant_a_risk.id
    assert trace.risk_key == "risk-a"
    assert trace.work_item_id == tenant_a_work.id
    assert trace.accountable_capability is not None
    assert trace.accountable_capability.domain_key == "security.grc"
    assert trace.accountable_capability.name == "Governance, Risk & Compliance"
    assert trace.control_refs == ()

    assert len(trace.linked_work_item_decisions) == 1
    decision_trace = trace.linked_work_item_decisions[0]
    assert decision_trace.decision_id == tenant_a_decision.id
    assert decision_trace.owner_capability is not None
    assert decision_trace.owner_capability.domain_key == "security.grc"
    assert tuple(record.activity_id for record in decision_trace.activity_records) == (
        tenant_a_activity.id,
    )


def test_grc_projection_uses_exact_decision_activity_identity_and_never_infers_controls(
    db_session: Session,
) -> None:
    work = _work(db_session, tenant_key="tenant-a", key="work-exact")
    _risk(db_session, key="risk-exact", work_item_id=work.id)
    decision = _decision(db_session, work=work, key="decision-exact")
    other_decision = _decision(db_session, work=work, key="decision-other")

    later = _activity(
        db_session,
        tenant_key="tenant-a",
        work=work,
        activity_key="decision-exact-later",
        source_object_type="executive_decision",
        source_object_id=str(decision.id),
        occurred_at=_BASE_TIME + timedelta(minutes=5),
        activity_type="organization.decision.status.approved.v1",
    )
    earlier = _activity(
        db_session,
        tenant_key="tenant-a",
        work=work,
        activity_key="decision-exact-earlier",
        source_object_type="executive_decision",
        source_object_id=str(decision.id),
        occurred_at=_BASE_TIME,
    )
    other = _activity(
        db_session,
        tenant_key="tenant-a",
        work=work,
        activity_key="decision-other-activity",
        source_object_type="executive_decision",
        source_object_id=str(other_decision.id),
        occurred_at=_BASE_TIME + timedelta(minutes=1),
    )
    _activity(
        db_session,
        tenant_key="tenant-a",
        work=work,
        activity_key="work-item-activity",
        source_object_type="organizational_work_item",
        source_object_id=str(work.id),
        occurred_at=_BASE_TIME + timedelta(minutes=2),
        activity_type="organization.work.assigned.v1",
        activity_class=OrganizationActivityClass.work,
    )
    db_session.add(
        OrganizationControl(
            control_key="risk.security.access",
            status="active",
            changed_by="pytest",
        )
    )
    db_session.commit()

    trace = project_organization_grc_traceability(db_session, tenant_key="tenant-a")[0]

    assert trace.control_refs == ()
    decisions = {item.decision_key: item for item in trace.linked_work_item_decisions}
    assert set(decisions) == {"decision-exact", "decision-other"}
    assert tuple(record.activity_id for record in decisions["decision-exact"].activity_records) == (
        earlier.id,
        later.id,
    )
    assert tuple(record.activity_id for record in decisions["decision-other"].activity_records) == (
        other.id,
    )
    assert all(
        record.source_object_type == "executive_decision"
        for item in decisions.values()
        for record in item.activity_records
    )


def test_grc_projection_is_deterministic_and_read_only(db_session: Session) -> None:
    work_z = _work(db_session, tenant_key="tenant-a", key="work-z")
    work_a = _work(db_session, tenant_key="tenant-a", key="work-a")
    _risk(db_session, key="risk-z", work_item_id=work_z.id)
    _risk(db_session, key="risk-a", work_item_id=work_a.id)
    _decision(db_session, work=work_z, key="decision-z")
    _decision(db_session, work=work_a, key="decision-a")
    db_session.commit()

    before = _row_counts(db_session)
    first = project_organization_grc_traceability(db_session, tenant_key="tenant-a")
    second = project_organization_grc_traceability(db_session, tenant_key="tenant-a")
    after = _row_counts(db_session)

    assert first == second
    assert tuple(trace.risk_key for trace in first) == ("risk-a", "risk-z")
    assert before == after
    assert not db_session.new
    assert not db_session.dirty
    assert not db_session.deleted


def test_grc_projection_rejects_blank_tenant(db_session: Session) -> None:
    with pytest.raises(ValueError, match="tenant_key is required"):
        project_organization_grc_traceability(db_session, tenant_key="   ")
