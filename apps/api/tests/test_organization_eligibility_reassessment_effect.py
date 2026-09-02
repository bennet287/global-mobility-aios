from __future__ import annotations

import json

import pytest
from sqlmodel import Session, select

from app.models.domain import EligibilityAssessment
from app.models.eligibility_revision import EligibilityAssessmentRevision
from app.services.organization_decision_readiness import (
    DecisionReadinessState,
    assess_eligibility_decision_readiness,
)
from app.services.organization_eligibility_effect import commit_governed_eligibility_effect
from app.services.organization_eligibility_transition_intent import (
    EligibilityIntentIntegrityError,
    governed_eligibility_transition_intent,
)
from app.services.organization_eligibility_verification_floor import (
    integrate_eligibility_verification_floor,
)
from app.services.organization_governance_kernel import GatewayOutcome
from app.services.organization_independent_eligibility_verification import (
    IndependentVerificationDisposition,
    verify_eligibility_proposal_independently,
)
from app.services.organization_transparency import transparency_activity_record
from tests.test_organization_eligibility_effect import _floor_ready
from tests.test_organization_eligibility_verification_floor import _authority_with
from tests.test_organization_independent_eligibility_verification import (
    FakeProvider,
    _proposer_output,
    _runtime,
    _verifier_output,
    _verifier_runtime,
)


def _initial_chain(session: Session):
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
    return (
        proposal,
        readiness,
        verification,
        floor,
        authority,
        effect,
        lead,
        profile,
        graph,
        proposal_work,
        verification_work,
    )


def _reassessment_chain(
    session: Session,
    *,
    graph,
    proposal_work,
    verification_work,
    expected_revision_version: int = 1,
    idempotency_key: str = "g5-reassessment-v2",
):
    producer = FakeProvider(
        name="deepseek",
        model="deepseek-reasoner",
        content=_proposer_output(graph, state="potentially_ineligible"),
    )
    proposal = governed_eligibility_transition_intent(
        session,
        tenant_key="tenant-a",
        position_key="austria_mobility_specialist",
        work_item_id=proposal_work.id,
        runtime_profile=_runtime(
            profile_key="g5-reassessment-producer",
            provider_key="deepseek",
            model_key="deepseek-reasoner",
            independence_group="proposer-group",
        ),
        authority=_authority_with(),
        provider=producer,
        idempotency_key=idempotency_key,
        expected_eligibility_revision_version=expected_revision_version,
    )
    readiness = assess_eligibility_decision_readiness(session, proposal=proposal)
    assert readiness.state is DecisionReadinessState.READY_FOR_INDEPENDENT_VERIFICATION

    verifier_provider = FakeProvider(
        name="openai",
        model="gpt-verifier",
        content=_verifier_output(
            graph,
            conclusion="supports_potential_ineligibility",
        ),
    )
    verification = verify_eligibility_proposal_independently(
        session,
        proposal=proposal,
        readiness=readiness,
        verification_work_item_id=verification_work.id,
        verifier_position_key="austria_independent_verifier",
        verifier_runtime_profile=_verifier_runtime(),
        provider=verifier_provider,
        idempotency_key=f"{idempotency_key}:independent-verification",
    )
    assert verification.disposition is IndependentVerificationDisposition.AGREES

    authority = _authority_with()
    floor = integrate_eligibility_verification_floor(
        session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        authority=authority,
    )
    assert floor.eligible_for_effect_integration is True
    return proposal, readiness, verification, floor, authority, producer, verifier_provider


def test_g5_commits_v2_and_supersedes_v1_atomically(db_session: Session) -> None:
    *_, v1, _lead, _profile, graph, proposal_work, verification_work = _initial_chain(db_session)
    proposal, readiness, verification, floor, authority, *_ = _reassessment_chain(
        db_session,
        graph=graph,
        proposal_work=proposal_work,
        verification_work=verification_work,
    )

    v2 = commit_governed_eligibility_effect(
        db_session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        floor=floor,
        authority=authority,
    )

    db_session.refresh(v1.revision)
    assert v1.revision.lifecycle_status == "superseded"
    assert v2.revision.version == 2
    assert v2.revision.lifecycle_status == "active"
    assert v2.revision.supersedes_revision_id == v1.revision.id
    assert v2.revision.aggregate_key == v1.revision.aggregate_key
    assert v2.assessment.status == "potentially_ineligible"
    assert v2.evaluation.outcome is GatewayOutcome.AUTO_EXECUTE
    assert v2.canonical_effect_committed is True
    assert v2.mutated is True
    assert v2.replayed is False

    revisions = list(
        db_session.exec(
            select(EligibilityAssessmentRevision).where(
                EligibilityAssessmentRevision.aggregate_key == v1.revision.aggregate_key
            )
        ).all()
    )
    assert sorted((row.version, row.lifecycle_status) for row in revisions) == [
        (1, "superseded"),
        (2, "active"),
    ]
    active = [row for row in revisions if row.lifecycle_status == "active"]
    assert [row.id for row in active] == [v2.revision.id]

    payload = json.loads(v2.assessment.assessment_json or "{}")
    assert payload["canonical_revision_version"] == 2
    assert payload["supersedes_revision_id"] == str(v1.revision.id)
    semantic = transparency_activity_record(v2.semantic_activity)
    assert semantic.payload["revision_version"] == 2
    assert semantic.payload["supersedes_revision_id"] == str(v1.revision.id)


def test_g5_historical_v1_replay_survives_v2_supersession(db_session: Session) -> None:
    (
        v1_proposal,
        v1_readiness,
        v1_verification,
        v1_floor,
        v1_authority,
        v1,
        _lead,
        _profile,
        graph,
        proposal_work,
        verification_work,
    ) = _initial_chain(db_session)
    proposal, readiness, verification, floor, authority, *_ = _reassessment_chain(
        db_session,
        graph=graph,
        proposal_work=proposal_work,
        verification_work=verification_work,
        idempotency_key="g5-reassessment-for-history",
    )
    v2 = commit_governed_eligibility_effect(
        db_session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        floor=floor,
        authority=authority,
    )
    assert v2.revision.version == 2

    replay = commit_governed_eligibility_effect(
        db_session,
        proposal=v1_proposal,
        readiness=v1_readiness,
        verification=v1_verification,
        floor=v1_floor,
        authority=v1_authority,
    )

    assert replay.evaluation.outcome is GatewayOutcome.IDEMPOTENT_REPLAY
    assert replay.replayed is True
    assert replay.mutated is False
    assert replay.revision.id == v1.revision.id
    assert replay.revision.version == 1
    assert replay.revision.lifecycle_status == "superseded"
    assert replay.assessment.id == v1.assessment.id


def test_g5_stale_expected_revision_fails_before_runtime(db_session: Session) -> None:
    *_, v1, _lead, _profile, graph, proposal_work, _verification_work = _initial_chain(db_session)
    assert v1.revision.version == 1
    provider = FakeProvider(
        name="deepseek",
        model="deepseek-reasoner",
        content=_proposer_output(graph, state="potentially_ineligible"),
    )

    with pytest.raises(EligibilityIntentIntegrityError, match="revision precondition"):
        governed_eligibility_transition_intent(
            db_session,
            tenant_key="tenant-a",
            position_key="austria_mobility_specialist",
            work_item_id=proposal_work.id,
            runtime_profile=_runtime(
                profile_key="g5-stale-producer",
                provider_key="deepseek",
                model_key="deepseek-reasoner",
                independence_group="proposer-group",
            ),
            authority=_authority_with(),
            provider=provider,
            idempotency_key="g5-stale-revision",
            expected_eligibility_revision_version=2,
        )

    assert provider.calls == []


def test_g5_reassessment_rollback_restores_v1_active(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    *_, v1, _lead, _profile, graph, proposal_work, verification_work = _initial_chain(db_session)
    proposal, readiness, verification, floor, authority, *_ = _reassessment_chain(
        db_session,
        graph=graph,
        proposal_work=proposal_work,
        verification_work=verification_work,
        idempotency_key="g5-reassessment-rollback",
    )
    before_assessments = len(list(db_session.exec(select(EligibilityAssessment)).all()))
    before_revisions = len(list(db_session.exec(select(EligibilityAssessmentRevision)).all()))

    def fail_semantic(*args, **kwargs):
        raise RuntimeError("synthetic g5 semantic failure")

    monkeypatch.setattr(
        "app.services.organization_eligibility_effect._stage_semantic_effect",
        fail_semantic,
    )
    with pytest.raises(RuntimeError, match="synthetic g5 semantic failure"):
        commit_governed_eligibility_effect(
            db_session,
            proposal=proposal,
            readiness=readiness,
            verification=verification,
            floor=floor,
            authority=authority,
        )

    db_session.expire_all()
    prior = db_session.get(EligibilityAssessmentRevision, v1.revision.id)
    assert prior is not None
    assert prior.lifecycle_status == "active"
    assert len(list(db_session.exec(select(EligibilityAssessment)).all())) == before_assessments
    assert len(list(db_session.exec(select(EligibilityAssessmentRevision)).all())) == before_revisions
