from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session

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
from app.services.organization_work import create_work_item


BASE = "/api/v1/organization/transparency"


def _headers(role: str, user: str = "pytest-user") -> dict[str, str]:
    return {"X-GMAI-Role": role, "X-GMAI-User": user}


def _context(
    tenant_key: str,
    *,
    actor_id: str,
    actor_type: OrganizationActorType,
    role: str,
    department: str = "operations",
    position_key: str | None = None,
    authority_level: str | None = None,
) -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key=tenant_key,
        actor_id=actor_id,
        actor_type=actor_type,
        authenticated_user_id=actor_id,
        role=role,
        department=department,
        position_key=position_key,
        authority_level=authority_level,
    )


def _seed_governed_assignment(
    session: Session,
    *,
    tenant_key: str = "default",
    key: str = "c4-trace",
):
    human = _context(
        tenant_key,
        actor_id=f"{tenant_key}-owner",
        actor_type=OrganizationActorType.human,
        role="admin",
        position_key="board",
        authority_level="L4",
    )
    agent = _context(
        tenant_key,
        actor_id=f"{tenant_key}-coo-agent",
        actor_type=OrganizationActorType.agent,
        role="operator",
        position_key="coo",
        authority_level="L2",
    )
    authority = CapabilityAuthority(
        tenant_key=tenant_key,
        actor_id=agent.actor_id,
        capability=GOVERNED_WORK_CAPABILITY,
        allowed_action_types=frozenset({MaterialActionType.WORK_ITEM_ASSIGNMENT}),
        max_risk_tier=RiskTier.R1,
        autonomy_level=AutonomyLevel.A4,
        allowed_scopes=frozenset({"operations"}),
    )
    work = create_work_item(
        session,
        human,
        idempotency_key=f"{key}-work",
        title=f"{key}-work",
        objective="Exercise the bounded Board transparency API.",
        department="operations",
        authority_level="L2",
        assigned_position_key="coo",
    )
    result = governed_assign_work_item(
        session,
        agent,
        authority,
        work_item_id=work.id,
        assigned_position_key="case_operations_specialist",
        expected_version=work_item_precondition_version(work),
        idempotency_key=key,
        reason="Expose a governed action through the Board-safe transparency contract.",
    )
    assert result.evaluation.outcome is GatewayOutcome.AUTO_EXECUTE
    assert result.governance_activity is not None
    return work, result


def test_board_trace_endpoint_returns_whitelisted_governance_and_explicit_causation(
    client: TestClient,
    db_session: Session,
) -> None:
    work, result = _seed_governed_assignment(db_session, key="c4-board-trace")

    response = client.get(f"{BASE}/traces/{result.evaluation.trace_id}")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["trace_id"] == str(result.evaluation.trace_id)
    assert body["board_inspectable"] is True
    governance = body["governance"]
    assert governance["activity_id"] == str(result.governance_activity.id)
    assert governance["action_type"] == MaterialActionType.WORK_ITEM_ASSIGNMENT.value
    assert governance["capability"] == GOVERNED_WORK_CAPABILITY
    assert governance["outcome"] == GatewayOutcome.AUTO_EXECUTE.value
    assert governance["effective_risk_tier"] == RiskTier.R1.value
    assert governance["work_item_id"] == str(work.id)
    assert len(governance["action_fingerprint"]) == 64

    effect = next(
        record
        for record in body["records"]
        if record["activity_type"] == "organization.work.assigned.v1"
    )
    assert effect["causation_activity_id"] == governance["activity_id"]
    assert effect["trace_id"] == body["trace_id"]
    assert all("payload" not in record for record in body["records"])
    assert "payload" not in governance


def test_transparency_endpoints_are_board_only(
    raw_client: TestClient,
    db_session: Session,
) -> None:
    work, result = _seed_governed_assignment(db_session, key="c4-board-only")

    for path in (
        f"{BASE}/traces/{result.evaluation.trace_id}",
        f"{BASE}/work-items/{work.id}",
    ):
        response = raw_client.get(path, headers=_headers("operator", "operator-user"))
        assert response.status_code == 403
        assert response.json() == {"detail": "Board transparency access is not permitted."}


def test_trace_endpoint_is_tenant_scoped_and_non_disclosing(
    client: TestClient,
    db_session: Session,
) -> None:
    _, foreign = _seed_governed_assignment(
        db_session,
        tenant_key="tenant-b",
        key="c4-foreign-trace",
    )

    response = client.get(f"{BASE}/traces/{foreign.evaluation.trace_id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Organization transparency resource not found."}


def test_work_item_transparency_returns_board_safe_history_and_rejects_foreign_work(
    client: TestClient,
    db_session: Session,
) -> None:
    work, result = _seed_governed_assignment(db_session, key="c4-work-history")
    foreign_work, _ = _seed_governed_assignment(
        db_session,
        tenant_key="tenant-b",
        key="c4-foreign-work",
    )

    response = client.get(f"{BASE}/work-items/{work.id}")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["work_item_id"] == str(work.id)
    assert {record["activity_type"] for record in body["records"]} == {
        "organization.work.created.v1",
        "organization.work.assigned.v1",
        "governance.work_item.assignment.auto_execute",
    }
    effect = next(
        record
        for record in body["records"]
        if record["activity_type"] == "organization.work.assigned.v1"
    )
    assert effect["causation_activity_id"] == str(result.governance_activity.id)
    assert all(record["board_inspectable"] is True for record in body["records"])
    assert client.get(f"{BASE}/work-items/{foreign_work.id}").status_code == 404
    assert client.get(f"{BASE}/work-items/{uuid4()}").status_code == 404


def test_malformed_governance_payload_fails_closed_without_internal_detail(
    client: TestClient,
    db_session: Session,
) -> None:
    context = _context(
        "default",
        actor_id="malformed-agent",
        actor_type=OrganizationActorType.agent,
        role="operator",
        position_key="coo",
        authority_level="L2",
    )
    trace_id = str(uuid4())
    append_activity(
        db_session,
        context,
        activity_key=f"governance:malformed-c4-{trace_id}",
        stream_key="governance:malformed-c4",
        activity_class=OrganizationActivityClass.operational,
        activity_type="governance.work_item.assignment.block",
        title="Malformed governance record",
        summary="The API must fail closed without leaking persistence detail.",
        source_object_type="organizational_work_item",
        source_object_id="missing",
        occurred_at=now_utc(),
        correlation_key=trace_id,
        payload={
            "trace_id": trace_id,
            "constitutional_activity_class": ConstitutionalActivityClass.MATERIAL.value,
        },
    )

    response = client.get(f"{BASE}/traces/{trace_id}")

    assert response.status_code == 409
    assert response.json() == {"detail": "Organization transparency data is inconsistent."}
    assert "action_type" not in response.text
    assert "traceback" not in response.text.lower()
