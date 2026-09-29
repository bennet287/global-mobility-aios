from __future__ import annotations

from sqlmodel import Session, select

from app.models.autonomy_profile import CapabilityAutonomyProfile
from app.models.domain import OrganizationActivity
from app.services.organization_grc_capability_review import project_grc_capability_authorization_review
from tests.test_organization_autonomy_promotion_policy import (
    CAPABILITY_KEY,
    CONTEXT_SCOPE,
    POSITION_KEY,
    _board_context,
    _position,
    _profile,
)


def test_capability_authorization_review_reuses_canonical_profile_and_is_read_only(
    client, db_session: Session,
) -> None:
    board = _board_context()
    _position(db_session)
    profile = _profile(db_session, board, key="18e")
    before_profiles = len(db_session.exec(select(CapabilityAutonomyProfile)).all())
    before_activities = len(db_session.exec(select(OrganizationActivity)).all())

    route = (
        "/api/v1/organization/grc/capabilities/authorization-review"
        f"?position_key={POSITION_KEY}&capability_key={CAPABILITY_KEY}"
        f"&context_scope={CONTEXT_SCOPE}"
    )
    denied = client.get(
        route,
        headers={"X-GMAI-Role": "operator", "X-GMAI-User": "operator"},
    )
    assert denied.status_code == 403

    response = client.get(route)
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body["schema_version"] == "grc-capability-authorization-review-v1"
    assert body["current_profile_id"] == str(profile.id)
    assert body["position_key"] == POSITION_KEY
    assert body["capability_key"] == CAPABILITY_KEY
    assert body["context_scope"] == CONTEXT_SCOPE
    assert body["current_autonomy_level"] == "A2"
    assert body["board_ceiling"] == "A3"
    assert body["authority_requirement"] == "L2"
    assert body["risk_ceiling"] == "R3"
    assert body["current_profile"]["profile_id"] == str(profile.id)
    assert body["evidence_profile"]["metrics"]["qualifying_execution_volume"] == 0
    assert body["promotion_eligibility"] is None
    assert body["authorization_conclusion"] == "not_assessed"
    assert any("not executable permission" in item for item in body["limitations"])
    assert any("agent-to-tool execution boundary" in item for item in body["limitations"])

    assert before_profiles == len(db_session.exec(select(CapabilityAutonomyProfile)).all())
    assert before_activities == len(db_session.exec(select(OrganizationActivity)).all())

    projection = project_grc_capability_authorization_review(
        db_session,
        board,
        position_key=POSITION_KEY,
        capability_key=CAPABILITY_KEY,
        context_scope=CONTEXT_SCOPE,
    )
    assert projection.current_profile_id == profile.id


def test_capability_authorization_review_is_tenant_scoped(client, db_session: Session) -> None:
    board = _board_context("other")
    _position(db_session)
    _profile(db_session, board, key="18e-other")
    route = (
        "/api/v1/organization/grc/capabilities/authorization-review"
        f"?position_key={POSITION_KEY}&capability_key={CAPABILITY_KEY}"
        f"&context_scope={CONTEXT_SCOPE}"
    )
    assert client.get(route).status_code == 404
