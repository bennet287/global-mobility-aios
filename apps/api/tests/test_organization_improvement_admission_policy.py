from __future__ import annotations

import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, func, select

from app.models.autonomy_profile import CapabilityAutonomyProfile
from app.models.domain import (
    ExecutiveDecision,
    OrganizationActivity,
    OrganizationActorType,
)
from app.models.organization_improvement_admission_policy import (
    OrganizationImprovementAdmissionDependencyPolicy,
)
from app.models.runtime_economics import MonetaryAllocation
from app.services.organization_command import (
    AuthorityDenied,
    IdempotencyConflict,
    InvalidReference,
    InvalidTransition,
    OrganizationCommandContext,
)
from app.services.organization_improvement_admission_policy import (
    POLICY_ACTIVITY_TYPE,
    POLICY_SOURCE_TYPE,
    ImprovementAdmissionPolicyIntegrityError,
    current_improvement_admission_dependency_policy,
    establish_improvement_admission_dependency_policy,
    project_improvement_admission_dependency_policy,
)


BASE = "/api/v1/organization/improvements/admission-policies"
PHASE16_CEILING = "phase16.runtime_economics.hard_monetary_ceiling.v1"
PHASE17_CODEQL = "phase17.repository.codeql_exact_head.v1"


def _board_context() -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key="default",
        actor_id="board-human",
        actor_type=OrganizationActorType.human,
        authenticated_user_id="board-human",
        role="admin",
        department="executive",
        position_key="board",
        authority_level="L4",
    )


def _non_board_admin() -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key="default",
        actor_id="ceo-human",
        actor_type=OrganizationActorType.human,
        authenticated_user_id="ceo-human",
        role="admin",
        department="executive",
        position_key="ceo",
        authority_level="L3",
    )


def _requirements(
    *,
    phase16_disposition: str = "required",
    phase16_keys: list[str] | None = None,
    phase17_disposition: str = "required",
    phase17_keys: list[str] | None = None,
    phase19_disposition: str = "not_required",
    phase20_disposition: str = "not_required",
) -> list[dict]:
    return [
        {
            "phase_key": "phase16",
            "disposition": phase16_disposition,
            "dependency_contract_keys": (
                [PHASE16_CEILING] if phase16_keys is None and phase16_disposition == "required"
                else (phase16_keys or [])
            ),
            "rationale": "Board requires enforceable monetary evidence when Phase 16 applies.",
        },
        {
            "phase_key": "phase17",
            "disposition": phase17_disposition,
            "dependency_contract_keys": (
                [PHASE17_CODEQL] if phase17_keys is None and phase17_disposition == "required"
                else (phase17_keys or [])
            ),
            "rationale": "Board requires exact-head repository security analysis when Phase 17 applies.",
        },
        {
            "phase_key": "phase19",
            "disposition": phase19_disposition,
            "dependency_contract_keys": [],
            "rationale": "No code-configuration shadow Phase 19 resolver is currently required by this policy.",
        },
        {
            "phase_key": "phase20",
            "disposition": phase20_disposition,
            "dependency_contract_keys": [],
            "rationale": "No autonomy or resource expansion is requested by this shadow policy.",
        },
    ]


def _policy(
    session: Session,
    *,
    key: str,
    requirements: list[dict] | None = None,
    expected_policy_version: int | None = None,
    reason: str | None = None,
):
    return establish_improvement_admission_dependency_policy(
        session,
        _board_context(),
        target_type="code_configuration",
        execution_mode="shadow",
        candidate_risk_class="high",
        phase_requirements=requirements or _requirements(),
        policy_reason=reason or f"Board GRSI.E admission policy {key}",
        idempotency_key=f"grsi-admission-policy-{key}",
        expected_policy_version=expected_policy_version,
    )


def _count(session: Session, model) -> int:
    return session.exec(select(func.count()).select_from(model)).one()


def test_grsi_admission_policy_is_board_only_explicit_and_authority_neutral(
    db_session: Session,
) -> None:
    with pytest.raises(AuthorityDenied):
        establish_improvement_admission_dependency_policy(
            db_session,
            _non_board_admin(),
            target_type="code_configuration",
            execution_mode="shadow",
            candidate_risk_class="high",
            phase_requirements=_requirements(),
            policy_reason="CEO must not establish Board policy.",
            idempotency_key="grsi-admission-policy-ceo",
        )

    missing_phase = _requirements()[:-1]
    with pytest.raises(InvalidReference, match="exactly once"):
        establish_improvement_admission_dependency_policy(
            db_session,
            _board_context(),
            target_type="code_configuration",
            execution_mode="shadow",
            candidate_risk_class="high",
            phase_requirements=missing_phase,
            policy_reason="Incomplete phase policy.",
            idempotency_key="grsi-admission-policy-missing-phase",
        )

    unsupported = _requirements()
    unsupported[2] = {
        "phase_key": "phase19",
        "disposition": "required",
        "dependency_contract_keys": ["phase19.fake_complete.v1"],
        "rationale": "Unsupported keys must fail closed.",
    }
    with pytest.raises(InvalidReference, match="unsupported dependency contract key"):
        establish_improvement_admission_dependency_policy(
            db_session,
            _board_context(),
            target_type="code_configuration",
            execution_mode="shadow",
            candidate_risk_class="high",
            phase_requirements=unsupported,
            policy_reason="Unsupported key.",
            idempotency_key="grsi-admission-policy-unsupported",
        )

    wrong_phase = _requirements(phase16_keys=[PHASE17_CODEQL])
    with pytest.raises(InvalidReference, match="belongs to phase17"):
        establish_improvement_admission_dependency_policy(
            db_session,
            _board_context(),
            target_type="code_configuration",
            execution_mode="shadow",
            candidate_risk_class="high",
            phase_requirements=wrong_phase,
            policy_reason="Wrong phase.",
            idempotency_key="grsi-admission-policy-wrong-phase",
        )

    before = {
        "autonomy": _count(db_session, CapabilityAutonomyProfile),
        "money": _count(db_session, MonetaryAllocation),
        "decisions": _count(db_session, ExecutiveDecision),
    }
    row = _policy(db_session, key="v1")
    projected = project_improvement_admission_dependency_policy(
        db_session,
        _board_context(),
        row,
    )

    assert row.policy_version == 1
    assert projected.lifecycle_status == "CURRENT"
    assert [item.phase_key for item in projected.phase_requirements] == [
        "phase16",
        "phase17",
        "phase19",
        "phase20",
    ]
    assert projected.authority_conclusion == "none_granted"
    assert projected.qualification_conclusion == "not_evaluated"
    assert projected.autonomy_changed is False
    assert projected.monetary_authority_changed is False
    assert projected.deployment_authorized is False
    assert projected.external_action_authorized is False
    assert {
        "autonomy": _count(db_session, CapabilityAutonomyProfile),
        "money": _count(db_session, MonetaryAllocation),
        "decisions": _count(db_session, ExecutiveDecision),
    } == before

    activity = db_session.get(OrganizationActivity, row.decision_activity_id)
    assert activity is not None
    assert getattr(activity.activity_class, "value", activity.activity_class) == "decision"
    assert getattr(activity.actor_type, "value", activity.actor_type) == "human"
    assert activity.position_key == "board"
    assert activity.authority_level == "L4"
    assert activity.activity_type == POLICY_ACTIVITY_TYPE
    assert activity.source_object_type == POLICY_SOURCE_TYPE
    assert activity.source_object_id == str(row.id)
    payload = json.loads(activity.payload_json)
    assert payload["constitutional_activity_class"] == "AUTHORITY"
    assert payload["candidate_qualified"] is False
    assert payload["authority_mutated"] is False
    assert payload["autonomy_mutated"] is False
    assert payload["deployment_authorized"] is False


def test_grsi_admission_policy_is_idempotent_and_supersession_is_append_only(
    db_session: Session,
) -> None:
    first = _policy(db_session, key="v1")
    replay = _policy(db_session, key="v1")
    assert replay.id == first.id

    with pytest.raises(IdempotencyConflict):
        _policy(
            db_session,
            key="v1",
            reason="Changed meaning under the same idempotency key.",
        )

    with pytest.raises(InvalidTransition, match="expected_policy_version"):
        _policy(db_session, key="missing-sequence")

    with pytest.raises(InvalidTransition, match="stale"):
        _policy(db_session, key="stale", expected_policy_version=2)

    second_requirements = _requirements(
        phase16_disposition="not_required",
        phase16_keys=[],
    )
    second = _policy(
        db_session,
        key="v2",
        requirements=second_requirements,
        expected_policy_version=1,
    )
    assert second.policy_version == 2
    assert second.supersedes_policy_id == first.id

    first_read = project_improvement_admission_dependency_policy(
        db_session,
        _board_context(),
        first,
    )
    current = current_improvement_admission_dependency_policy(
        db_session,
        _board_context(),
        target_type="code_configuration",
        execution_mode="shadow",
        candidate_risk_class="high",
    )
    assert first_read.lifecycle_status == "HISTORICAL"
    assert current.id == second.id
    assert current.policy_version == 2
    phase16 = next(item for item in current.phase_requirements if item.phase_key == "phase16")
    assert phase16.disposition == "not_required"
    assert phase16.dependency_contract_keys == ()

    first_activity = db_session.get(OrganizationActivity, first.decision_activity_id)
    second_activity = db_session.get(OrganizationActivity, second.decision_activity_id)
    assert first_activity is not None and second_activity is not None
    assert second_activity.supersedes_activity_id == first_activity.id


def test_grsi_admission_policy_integrity_drift_fails_closed(db_session: Session) -> None:
    row = _policy(db_session, key="drift")
    row.phase_requirements_json = "[]"
    db_session.add(row)
    db_session.commit()

    with pytest.raises(ImprovementAdmissionPolicyIntegrityError):
        current_improvement_admission_dependency_policy(
            db_session,
            _board_context(),
            target_type="code_configuration",
            execution_mode="shadow",
            candidate_risk_class="high",
        )


def test_grsi_admission_policy_activity_drift_fails_closed(db_session: Session) -> None:
    row = _policy(db_session, key="activity-drift")
    activity = db_session.get(OrganizationActivity, row.decision_activity_id)
    assert activity is not None
    activity.record_fingerprint = "0" * 64
    db_session.add(activity)
    db_session.commit()

    with pytest.raises(ImprovementAdmissionPolicyIntegrityError, match="Activity fingerprint"):
        current_improvement_admission_dependency_policy(
            db_session,
            _board_context(),
            target_type="code_configuration",
            execution_mode="shadow",
            candidate_risk_class="high",
        )


def test_grsi_admission_policy_api_is_board_admin_no_store_and_does_not_qualify(
    client: TestClient,
    raw_client: TestClient,
) -> None:
    payload = {
        "target_type": "code_configuration",
        "execution_mode": "shadow",
        "candidate_risk_class": "high",
        "phase_requirements": _requirements(),
        "policy_reason": "Board-authored test policy.",
        "idempotency_key": f"grsi-admission-policy-api-{uuid4()}",
        "expected_policy_version": None,
    }
    response = client.post(BASE, json=payload)
    assert response.status_code == 201, response.text
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body["policy_version"] == 1
    assert body["qualification_conclusion"] == "not_evaluated"
    assert body["authority_conclusion"] == "none_granted"

    current = client.get(
        f"{BASE}/current",
        params={
            "target_type": "code_configuration",
            "execution_mode": "shadow",
            "candidate_risk_class": "high",
        },
    )
    assert current.status_code == 200, current.text
    assert current.headers["cache-control"] == "no-store"
    assert current.json()["id"] == body["id"]

    denied = raw_client.post(
        BASE,
        headers={"X-GMAI-Role": "operator", "X-GMAI-User": "operator-user"},
        json=payload,
    )
    assert denied.status_code == 403
