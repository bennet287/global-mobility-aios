from __future__ import annotations

import json

import pytest
from sqlmodel import select

from app.models.agent_lifecycle import OrganizationAgent
from app.models.domain import AuditLog
from app.services.organization_agent_lifecycle import (
    AGENT_LIFECYCLE_AUDIT_ACTION,
    AGENT_LIFECYCLE_AUDIT_SOURCE,
    transition_organization_agent,
)
from app.services.organization_command import InvalidTransition


def _agent(*, status: str = "created") -> OrganizationAgent:
    return OrganizationAgent(
        agent_key=f"security_lead_{status}",
        registry_key="security_lead_agent",
        registry_version="v13.8",
        display_name="Security Lead",
        department="security",
        status=status,
        lifecycle_reason="Governed lifecycle transition test.",
        created_by="pytest-admin",
    )


@pytest.mark.parametrize(
    ("source_status", "target_status", "timestamp_field"),
    [
        ("created", "onboarding", None),
        ("onboarding", "inactive", None),
        ("inactive", "active", "activated_at"),
        ("active", "restricted", None),
        ("active", "suspended", "suspended_at"),
        ("restricted", "retired", "retired_at"),
        ("suspended", "retired", "retired_at"),
    ],
)
def test_explicit_lifecycle_transitions_preserve_bounded_audit_lineage(
    db_session,
    source_status: str,
    target_status: str,
    timestamp_field: str | None,
) -> None:
    agent = _agent(status=source_status)
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    transitioned = transition_organization_agent(
        db_session,
        agent_id=agent.id,
        target_status=target_status,
        reason=f"Explicit {source_status} to {target_status} transition.",
        actor="lifecycle-admin",
    )
    db_session.commit()
    db_session.refresh(transitioned)

    assert transitioned.status == target_status
    assert transitioned.lifecycle_reason == f"Explicit {source_status} to {target_status} transition."
    if timestamp_field is not None:
        assert getattr(transitioned, timestamp_field) is not None

    audit = db_session.exec(select(AuditLog)).one()
    assert audit.action == AGENT_LIFECYCLE_AUDIT_ACTION
    assert audit.source == AGENT_LIFECYCLE_AUDIT_SOURCE
    assert audit.actor == "lifecycle-admin"
    assert audit.entity_type == "organization_agent"
    assert audit.entity_id == str(agent.id)

    before_state = json.loads(audit.before_state_json or "{}")
    after_state = json.loads(audit.after_state_json or "{}")
    assert before_state["status"] == source_status
    assert after_state["status"] == target_status
    assert after_state["lifecycle_reason"] == transitioned.lifecycle_reason
    for forbidden in (
        "authority_level",
        "permissions",
        "credentials",
        "autonomy_level",
        "tool_access",
        "work_assignment",
        "execution_enabled",
    ):
        assert forbidden not in before_state
        assert forbidden not in after_state


@pytest.mark.parametrize(
    ("source_status", "target_status"),
    [
        ("created", "active"),
        ("created", "created"),
        ("onboarding", "active"),
        ("inactive", "onboarding"),
        ("active", "retired"),
        ("restricted", "active"),
        ("suspended", "active"),
        ("retired", "active"),
        ("active", "executing"),
    ],
)
def test_invalid_lifecycle_transitions_fail_closed_without_evidence(
    db_session,
    source_status: str,
    target_status: str,
) -> None:
    agent = _agent(status=source_status)
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    with pytest.raises(InvalidTransition, match="is not allowed"):
        transition_organization_agent(
            db_session,
            agent_id=agent.id,
            target_status=target_status,
            reason="This transition must be rejected.",
            actor="lifecycle-admin",
        )

    db_session.refresh(agent)
    assert agent.status == source_status
    assert db_session.exec(select(AuditLog)).all() == []


def test_lifecycle_transition_and_audit_share_the_caller_transaction(db_session) -> None:
    agent = _agent()
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    transition_organization_agent(
        db_session,
        agent_id=agent.id,
        target_status="onboarding",
        reason="Stage then roll back the complete governed mutation.",
        actor="lifecycle-admin",
    )
    db_session.rollback()
    db_session.refresh(agent)

    assert agent.status == "created"
    assert agent.lifecycle_reason == "Governed lifecycle transition test."
    assert db_session.exec(select(AuditLog)).all() == []
