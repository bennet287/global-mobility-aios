from __future__ import annotations

import json

import pytest
from sqlalchemy import text
from sqlmodel import Session, select

from app.models.domain import OrganizationPosition
from app.services.organization_capability_architecture import (
    MOBILITY_OPERATIONS_INTELLIGENCE_LEGAL_FOUNDATION_TRANCHE_KEYS,
    TECHNOLOGY_SECURITY_FOUNDATION_TRANCHE_KEYS,
)
from app.services.organization_governance import (
    APPLICATION_READINESS_DELEGATION,
    CAPABILITY_ONLY_POSITION_KEYS,
    LEGAL_REQUIRED_DELEGATES,
    OPERATIONS_DELEGATION_SPECS,
    POSITION_SPECS,
    SECURITY_REQUIRED_DELEGATES,
    TECHNOLOGY_REQUIRED_DELEGATES,
    active_organization_position_identity_duplicates,
    ensure_foundation_positions,
)


def test_technology_security_foundation_tranche_is_additive_and_non_executable(
    db_session: Session,
) -> None:
    positions = ensure_foundation_positions(db_session, actor="phase-13.16.3a2-test")
    db_session.commit()

    assert len(POSITION_SPECS) == 61
    assert len(positions) == 61
    assert CAPABILITY_ONLY_POSITION_KEYS == (
        TECHNOLOGY_SECURITY_FOUNDATION_TRANCHE_KEYS
        | MOBILITY_OPERATIONS_INTELLIGENCE_LEGAL_FOUNDATION_TRANCHE_KEYS
    )

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


def test_mobility_operations_intelligence_legal_tranche_is_non_executable(
    db_session: Session,
) -> None:
    ensure_foundation_positions(db_session, actor="phase-13.16.3a3-test")
    db_session.commit()

    live = {
        position.position_key: position
        for position in db_session.exec(
            select(OrganizationPosition).where(
                OrganizationPosition.version == 1,
                OrganizationPosition.status == "active",
            )
        ).all()
    }

    for position_key in MOBILITY_OPERATIONS_INTELLIGENCE_LEGAL_FOUNDATION_TRANCHE_KEYS:
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
        assert contract["capability_owner"] in {"coo", "clo"}
        assert contract["capability_domain"]
        assert "authority.submit" in contract["prohibited_direct_actions"]
        assert "policy.publish" in contract["prohibited_direct_actions"]
        assert "legal.opinion.final" in contract["prohibited_direct_actions"]
        assert "compliance.certify" in contract["prohibited_direct_actions"]


def test_tranche_does_not_expand_existing_executable_delegation_sets() -> None:
    operations_delegates = {key for key, _task in OPERATIONS_DELEGATION_SPECS}
    operations_delegates.add(APPLICATION_READINESS_DELEGATION[0])

    assert TECHNOLOGY_REQUIRED_DELEGATES == {"vp_engineering", "lead_architect"}
    assert SECURITY_REQUIRED_DELEGATES == {"security_lead", "threat_analyst"}
    assert TECHNOLOGY_SECURITY_FOUNDATION_TRANCHE_KEYS.isdisjoint(TECHNOLOGY_REQUIRED_DELEGATES)
    assert TECHNOLOGY_SECURITY_FOUNDATION_TRANCHE_KEYS.isdisjoint(SECURITY_REQUIRED_DELEGATES)
    assert MOBILITY_OPERATIONS_INTELLIGENCE_LEGAL_FOUNDATION_TRANCHE_KEYS.isdisjoint(
        operations_delegates
    )
    assert MOBILITY_OPERATIONS_INTELLIGENCE_LEGAL_FOUNDATION_TRANCHE_KEYS.isdisjoint(
        LEGAL_REQUIRED_DELEGATES
    )


def test_foundation_bootstrap_fails_closed_on_duplicate_active_position_identity(
    db_session: Session,
) -> None:
    ensure_foundation_positions(db_session, actor="position-identity-integrity-test")
    db_session.commit()

    db_session.exec(text("DROP INDEX ux_organization_positions_active_position_key"))
    board = db_session.exec(
        select(OrganizationPosition).where(
            OrganizationPosition.position_key == "board",
            OrganizationPosition.status == "active",
        )
    ).first()
    assert board is not None
    duplicate = OrganizationPosition(
        position_key=board.position_key,
        title=board.title,
        department=board.department,
        reports_to_position_key=board.reports_to_position_key,
        role_card_name=board.role_card_name,
        authority_level=board.authority_level,
        contract_json=board.contract_json,
        status=board.status,
        # The original 0056 position/version uniqueness remains authoritative.
        # Use a second active version to isolate the stronger 0076 active-key guard.
        version=board.version + 1,
        created_by=board.created_by,
    )
    db_session.add(duplicate)
    db_session.commit()

    duplicates = active_organization_position_identity_duplicates(db_session)
    assert list(duplicates) == ["board"]
    assert len(duplicates["board"]) == 2

    with pytest.raises(RuntimeError, match="Duplicate active OrganizationPosition identities"):
        ensure_foundation_positions(db_session, actor="position-identity-integrity-test")
