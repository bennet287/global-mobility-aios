from __future__ import annotations

import uuid

from sqlmodel import select

from app.models.agent_lifecycle import OrganizationAgent
from app.models.domain import AuditLog


def _agent() -> OrganizationAgent:
    return OrganizationAgent(
        agent_key="security_lead_api",
        registry_key="security_lead_agent",
        registry_version="v13.8",
        display_name="Security Lead",
        department="security",
        lifecycle_reason="Governed lifecycle API test.",
        created_by="pytest-admin",
    )


def test_admin_can_transition_agent_without_receiving_authority(
    client,
    db_session,
) -> None:
    agent = _agent()
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    response = client.post(
        f"/api/v1/organization/agents/{agent.id}/transitions",
        json={
            "target_status": "onboarding",
            "reason": "Begin explicit governed onboarding.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(agent.id)
    assert payload["status"] == "onboarding"
    assert payload["lifecycle_reason"] == "Begin explicit governed onboarding."
    assert payload["authority_granted"] is False
    assert payload["permissions_granted"] is False
    assert payload["credentials_granted"] is False
    assert payload["autonomy_granted"] is False
    assert payload["tool_access_granted"] is False
    assert payload["work_assignment_granted"] is False
    assert payload["execution_granted"] is False

    audit = db_session.exec(select(AuditLog)).one()
    assert audit.actor == "pytest-admin"
    assert audit.reason == "Begin explicit governed onboarding."


def test_operator_cannot_mutate_agent_lifecycle(
    raw_client,
    db_session,
) -> None:
    agent = _agent()
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    raw_client.headers.update({
        "X-GMAI-Role": "operator",
        "X-GMAI-User": "pytest-operator",
    })

    response = raw_client.post(
        f"/api/v1/organization/agents/{agent.id}/transitions",
        json={
            "target_status": "onboarding",
            "reason": "Operator must not cross the admin boundary.",
        },
    )

    assert response.status_code == 403
    db_session.refresh(agent)
    assert agent.status == "created"
    assert db_session.exec(select(AuditLog)).all() == []


def test_invalid_api_transition_returns_conflict_without_mutation(
    client,
    db_session,
) -> None:
    agent = _agent()
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    response = client.post(
        f"/api/v1/organization/agents/{agent.id}/transitions",
        json={
            "target_status": "active",
            "reason": "Skipping onboarding and inactivity must fail closed.",
        },
    )

    assert response.status_code == 409
    db_session.refresh(agent)
    assert agent.status == "created"
    assert db_session.exec(select(AuditLog)).all() == []


def test_unknown_agent_transition_returns_not_found(client) -> None:
    response = client.post(
        f"/api/v1/organization/agents/{uuid.uuid4()}/transitions",
        json={
            "target_status": "onboarding",
            "reason": "Unknown identity must fail closed.",
        },
    )

    assert response.status_code == 404
