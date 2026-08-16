from __future__ import annotations

import json

from sqlmodel import Session, select

from app.models.domain import OrganizationPosition
from app.services.organization_capability_architecture import (
    TECHNOLOGY_SECURITY_FOUNDATION_TRANCHE_KEYS,
)
from app.services.organization_governance import (
    CAPABILITY_ONLY_POSITION_KEYS,
    POSITION_SPECS,
    SECURITY_REQUIRED_DELEGATES,
    TECHNOLOGY_REQUIRED_DELEGATES,
    ensure_foundation_positions,
)


def test_technology_security_foundation_tranche_is_additive_and_non_executable(
    db_session: Session,
) -> None:
    positions = ensure_foundation_positions(db_session, actor="phase-13.16.3a2-test")
    db_session.commit()

    assert len(POSITION_SPECS) == 47
    assert len(positions) == 47
    assert CAPABILITY_ONLY_POSITION_KEYS == TECHNOLOGY_SECURITY_FOUNDATION_TRANCHE_KEYS

    live = {
        position.position_key: position
        for position in db_session.exec(
            select(OrganizationPosition).where(
                OrganizationPosition.version == 1,
                OrganizationPosition.status == "active",
            )
        ).all()
    }
    assert set(live) == {item[0] for item in POSITION_SPECS}

    for position_key in TECHNOLOGY_SECURITY_FOUNDATION_TRANCHE_KEYS:
        position = live[position_key]
        contract = json.loads(position.contract_json)
        assert position.authority_level in {"L1", "L2"}
        assert position.role_card_name is None
        assert contract["execution_enabled"] is False
        assert contract["execution_posture"] == "organization_capability_only"
        assert contract["delegated_action_authority"] == []
        assert contract["direct_action_authority"] == []
        assert contract["external_action_authorized"] is False
        assert contract["self_approval_allowed"] is False
        assert contract["capability_owner"] in {"cto", "ciso"}
        assert contract["capability_domain"]
        assert "executive.authority.change" in contract["prohibited_direct_actions"]
        assert "secrets.access" in contract["prohibited_direct_actions"]


def test_tranche_does_not_expand_existing_executable_delegation_sets() -> None:
    assert TECHNOLOGY_REQUIRED_DELEGATES == {"vp_engineering", "lead_architect"}
    assert SECURITY_REQUIRED_DELEGATES == {"security_lead", "threat_analyst"}
    assert TECHNOLOGY_SECURITY_FOUNDATION_TRANCHE_KEYS.isdisjoint(TECHNOLOGY_REQUIRED_DELEGATES)
    assert TECHNOLOGY_SECURITY_FOUNDATION_TRANCHE_KEYS.isdisjoint(SECURITY_REQUIRED_DELEGATES)
