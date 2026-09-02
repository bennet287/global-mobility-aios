from __future__ import annotations

import pytest
from sqlmodel import Session

from app.services.organization_eligibility_effect import commit_governed_eligibility_effect
from app.services.organization_eligibility_transition_intent import (
    EligibilityIntentIntegrityError,
    governed_eligibility_transition_intent,
)
from app.services.organization_eligibility_verification_floor import (
    EligibilityVerificationFloorIntegrityError,
    original_eligibility_attempt_payload,
    rebuild_eligibility_action,
)
from app.services.organization_transparency import transparency_activity_record
from tests.test_organization_eligibility_effect import _floor_ready
from tests.test_organization_eligibility_transition_intent import (
    FakeProvider,
    _authority,
    _runtime_profile,
    _safe_output,
    _setup,
)


def test_g5_initial_e2_binds_absent_revision_precondition_into_material_action(
    db_session: Session,
) -> None:
    _, _, graph, work = _setup(db_session)
    result = governed_eligibility_transition_intent(
        db_session,
        tenant_key="tenant-a",
        position_key="austria_mobility_specialist",
        work_item_id=work.id,
        runtime_profile=_runtime_profile(),
        authority=_authority(),
        provider=FakeProvider(_safe_output(graph)),
        idempotency_key="g5-e2-initial-precondition",
    )

    precondition = result.eligibility_revision_precondition
    assert precondition.expected_revision_version is None
    assert precondition.current_revision_id is None
    assert precondition.current_revision_version is None
    assert precondition.next_revision_version == 1
    assert precondition.supersedes_revision_id is None

    payload = transparency_activity_record(result.attempt_activity).payload
    assert payload["eligibility_aggregate_key"] == precondition.aggregate_key
    assert payload["expected_eligibility_revision_version"] is None
    assert payload["expected_eligibility_revision_id"] is None
    assert payload["next_eligibility_revision_version"] == 1

    action, _ = rebuild_eligibility_action(
        db_session,
        proposal=result,
        idempotency_key=str(payload["idempotency_key"]),
    )
    assert action.expected_version == result.intent.profile_version
    assert action.proposed_change["eligibility_aggregate_key"] == precondition.aggregate_key
    assert action.proposed_change["expected_eligibility_revision_version"] is None
    assert action.proposed_change["expected_eligibility_revision_id"] is None
    assert action.proposed_change["next_eligibility_revision_version"] == 1
    assert result.evaluation.action_fingerprint == original_eligibility_attempt_payload(
        db_session, result
    )["action_fingerprint"]


def _committed_v1(session: Session):
    proposal, readiness, verification, floor, authority, lead, profile, graph, proposal_work, verification_work = (
        _floor_ready(session)
    )
    effect = commit_governed_eligibility_effect(
        session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        floor=floor,
        authority=authority,
    )
    return effect, lead, profile, graph, proposal_work, verification_work


def test_g5_existing_revision_requires_explicit_expectation_before_runtime(
    db_session: Session,
) -> None:
    effect, _, _, graph, proposal_work, _ = _committed_v1(db_session)
    assert effect.revision.version == 1
    provider = FakeProvider(_safe_output(graph))

    with pytest.raises(EligibilityIntentIntegrityError, match="revision precondition"):
        governed_eligibility_transition_intent(
            db_session,
            tenant_key="tenant-a",
            position_key="austria_mobility_specialist",
            work_item_id=proposal_work.id,
            runtime_profile=_runtime_profile(),
            authority=_authority(),
            provider=provider,
            idempotency_key="g5-e2-missing-reassessment-precondition",
        )

    assert provider.calls == []


def test_g5_exact_active_revision_is_carried_and_reconstructed_exactly(
    db_session: Session,
) -> None:
    effect, _, _, graph, proposal_work, _ = _committed_v1(db_session)
    proposal = governed_eligibility_transition_intent(
        db_session,
        tenant_key="tenant-a",
        position_key="austria_mobility_specialist",
        work_item_id=proposal_work.id,
        runtime_profile=_runtime_profile(),
        authority=_authority(),
        provider=FakeProvider(_safe_output(graph)),
        idempotency_key="g5-e2-reassessment-v2",
        expected_eligibility_revision_version=1,
    )

    precondition = proposal.eligibility_revision_precondition
    assert precondition.expected_revision_version == 1
    assert precondition.current_revision_id == effect.revision.id
    assert precondition.current_revision_version == 1
    assert precondition.next_revision_version == 2
    assert precondition.supersedes_revision_id == effect.revision.id

    payload = original_eligibility_attempt_payload(db_session, proposal)
    action, _ = rebuild_eligibility_action(
        db_session,
        proposal=proposal,
        idempotency_key=str(payload["idempotency_key"]),
    )
    assert action.proposed_change["expected_eligibility_revision_version"] == 1
    assert action.proposed_change["expected_eligibility_revision_id"] == str(effect.revision.id)
    assert action.proposed_change["next_eligibility_revision_version"] == 2
    assert action.proposed_change["eligibility_aggregate_key"] == effect.revision.aggregate_key
    assert proposal.evaluation.action_fingerprint == transparency_activity_record(
        proposal.attempt_activity
    ).payload["action_fingerprint"]


def test_g5_g2_reconstruction_fails_if_revision_moves_after_e2(
    db_session: Session,
) -> None:
    effect, _, _, graph, proposal_work, _ = _committed_v1(db_session)
    proposal = governed_eligibility_transition_intent(
        db_session,
        tenant_key="tenant-a",
        position_key="austria_mobility_specialist",
        work_item_id=proposal_work.id,
        runtime_profile=_runtime_profile(),
        authority=_authority(),
        provider=FakeProvider(_safe_output(graph)),
        idempotency_key="g5-e2-stale-before-g2",
        expected_eligibility_revision_version=1,
    )

    effect.revision.lifecycle_status = "superseded"
    db_session.add(effect.revision)
    db_session.commit()

    with pytest.raises(EligibilityVerificationFloorIntegrityError, match="revision precondition"):
        rebuild_eligibility_action(
            db_session,
            proposal=proposal,
            idempotency_key="g5-e2-stale-before-g2",
        )
