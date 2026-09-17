from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.models.agent_lifecycle import OrganizationAgent


def _agent(*, key: str = "security_lead_primary", status: str = "created") -> OrganizationAgent:
    return OrganizationAgent(
        agent_key=key,
        registry_key="security_lead_agent",
        registry_version="v13.8",
        display_name="Security Lead",
        department="security",
        status=status,
        lifecycle_reason="Governed lifecycle foundation test.",
        created_by="pytest-admin",
    )


def test_agent_lifecycle_identity_is_durable_and_separate_from_execution(db_session) -> None:
    agent = _agent()
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    stored = db_session.exec(select(OrganizationAgent).where(OrganizationAgent.id == agent.id)).one()
    assert stored.agent_key == "security_lead_primary"
    assert stored.registry_key == "security_lead_agent"
    assert stored.status == "created"
    assert stored.position_key is None
    assert stored.activated_at is None
    assert stored.suspended_at is None
    assert stored.retired_at is None


def test_agent_key_is_unique_canonical_identity(db_session) -> None:
    db_session.add(_agent())
    db_session.commit()
    db_session.add(_agent())

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_invalid_lifecycle_status_fails_closed(db_session) -> None:
    db_session.add(_agent(status="executing"))

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_lifecycle_record_does_not_embed_authority_permission_or_credentials() -> None:
    fields = set(OrganizationAgent.model_fields)
    forbidden = {
        "authority_level",
        "permissions",
        "permissions_json",
        "credentials",
        "credentials_json",
        "autonomy_level",
        "tool_credentials",
        "execution_enabled",
    }
    assert fields.isdisjoint(forbidden)
