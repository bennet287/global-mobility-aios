from __future__ import annotations

import json
from dataclasses import replace
from uuid import uuid4

import pytest
from sqlmodel import Session, select

from app.core.organization_constitution import AutonomyLevel, OrganizationActivityClass as ConstitutionalActivityClass
from app.models.domain import EligibilityAssessment, MobilityPathwayVersion, OrganizationActivity
from app.models.eligibility_revision import EligibilityAssessmentRevision
from app.services.organization_eligibility_effect import (
    ELIGIBILITY_CANONICAL_EFFECT_ACTIVITY_TYPE,
    ELIGIBILITY_CANONICAL_EFFECT_SCHEMA_VERSION,
    EligibilityCanonicalEffectIntegrityError,
    EligibilityCanonicalEffectNotAuthorized,
    _aggregate_key,
    commit_governed_eligibility_effect,
)
from app.services.organization_eligibility_verification_floor import integrate_eligibility_verification_floor
from app.services.organization_governance_kernel import GatewayOutcome
from app.services.organization_transparency import activities_for_trace, transparency_activity_record
from tests.test_organization_eligibility_verification_floor import (
    _agreeing_verification,
    _authority_with,
    _original_idempotency_key,
)


def _floor_ready(session: Session, *, autonomy: AutonomyLevel = AutonomyLevel.A5):
    proposal, readiness, verification, lead, profile, graph, proposal_work, verification_work = (
        _agreeing_verification(session)
    )
    authority = _authority_with(autonomy=autonomy)
    floor = integrate_eligibility_verification_floor(
        session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        authority=authority,
    )
    return (
        proposal,
        readiness,
        verification,
        floor,
        authority,
        lead,
        profile,
        graph,
        proposal_work,
        verification_work,
    )


def _canonical_governance(session: Session, proposal):
    key = _original_idempotency_key(proposal)
    return session.exec(
        select(OrganizationActivity).where(
            OrganizationActivity.tenant_key == proposal.context.tenant_key,
            OrganizationActivity.activity_key == f"governance:{key}",
        )
    ).first()


def test_g3_commits_first_canonical_eligibility_effect_atomically(db_session: Session) -> None:
    proposal, readiness, verification, floor, authority, *_ = _floor_ready(db_session)
    before_assessments = len(list(db_session.exec(select(EligibilityAssessment)).all()))
    before_revisions = len(list(db_session.exec(select(EligibilityAssessmentRevision)).all()))

    result = commit_governed_eligibility_effect(
        db_session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        floor=floor,
        authority=authority,
    )

    assert result.schema_version == ELIGIBILITY_CANONICAL_EFFECT_SCHEMA_VERSION
    assert result.evaluation.outcome is GatewayOutcome.AUTO_EXECUTE
    assert result.canonical_effect_committed is True
    assert result.mutated is True
    assert result.replayed is False
    assert len(list(db_session.exec(select(EligibilityAssessment)).all())) == before_assessments + 1
    assert len(list(db_session.exec(select(EligibilityAssessmentRevision)).all())) == before_revisions + 1

    assert result.assessment.status == proposal.intent.proposed_state.value
    assert result.assessment.profile_id == proposal.intent.profile_id
    assert result.assessment.profile_version == proposal.intent.profile_version
    assert result.assessment.overall_score == 0.0
    assert result.assessment.confidence == proposal.intent.confidence
    payload = json.loads(result.assessment.assessment_json or "{}")
    assert payload["governed"] is True
    assert payload["intent_fingerprint"] == proposal.intent_fingerprint
    assert payload["readiness_fingerprint"] == readiness.readiness_fingerprint
    assert payload["verification_fingerprint"] == verification.verification_fingerprint
    assert payload["verification_floor_fingerprint"] == floor.verification_floor_fingerprint

    revision = result.revision
    assert revision.version == 1
    assert revision.lifecycle_status == "active"
    assert revision.supersedes_revision_id is None
    assert revision.assessment_id == result.assessment.id
    assert revision.governance_activity_id == result.governance_activity.id
    assert revision.verification_activity_id == verification.verification_activity.id
    assert revision.verification_floor_activity_id == floor.reevaluation_activity.id
    assert revision.semantic_activity_id == result.semantic_activity.id
    assert revision.original_action_fingerprint == proposal.evaluation.action_fingerprint


def test_g3_lineage_is_e2_g1_g2_governance_then_semantic_effect(db_session: Session) -> None:
    proposal, readiness, verification, floor, authority, *_ = _floor_ready(db_session)
    result = commit_governed_eligibility_effect(
        db_session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        floor=floor,
        authority=authority,
    )

    governance = transparency_activity_record(result.governance_activity)
    semantic = transparency_activity_record(result.semantic_activity)
    assert governance.causation_activity_id == floor.reevaluation_activity.id
    assert governance.payload["governance_record_kind"] == "eligibility_canonical_effect_authorization"
    assert governance.payload["verification_floor_fingerprint"] == floor.verification_floor_fingerprint
    assert governance.constitutional_activity_class is ConstitutionalActivityClass.MATERIAL

    assert semantic.activity_type == ELIGIBILITY_CANONICAL_EFFECT_ACTIVITY_TYPE
    assert semantic.causation_activity_id == result.governance_activity.id
    assert semantic.constitutional_activity_class is ConstitutionalActivityClass.MATERIAL
    assert semantic.payload["client_facing"] is False
    assert semantic.payload["external_action_authorized"] is False

    trace = activities_for_trace(
        db_session,
        tenant_key=proposal.context.tenant_key,
        trace_id=proposal.evaluation.trace_id,
    )
    ids = [item.activity_id for item in trace]
    assert proposal.attempt_activity.id in ids
    assert verification.verification_activity.id in ids
    assert floor.reevaluation_activity.id in ids
    assert result.governance_activity.id in ids
    assert result.semantic_activity.id in ids


def test_g3_exact_retry_returns_durable_effect_without_duplicates(db_session: Session) -> None:
    proposal, readiness, verification, floor, authority, *_ = _floor_ready(db_session)
    first = commit_governed_eligibility_effect(
        db_session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        floor=floor,
        authority=authority,
    )
    assessment_count = len(list(db_session.exec(select(EligibilityAssessment)).all()))
    revision_count = len(list(db_session.exec(select(EligibilityAssessmentRevision)).all()))
    activity_count = len(list(db_session.exec(select(OrganizationActivity)).all()))

    second = commit_governed_eligibility_effect(
        db_session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        floor=floor,
        authority=authority,
    )

    assert second.evaluation.outcome is GatewayOutcome.IDEMPOTENT_REPLAY
    assert second.replayed is True
    assert second.mutated is False
    assert second.canonical_effect_committed is True
    assert second.assessment.id == first.assessment.id
    assert second.revision.id == first.revision.id
    assert second.governance_activity.id == first.governance_activity.id
    assert second.semantic_activity.id == first.semantic_activity.id
    assert len(list(db_session.exec(select(EligibilityAssessment)).all())) == assessment_count
    assert len(list(db_session.exec(select(EligibilityAssessmentRevision)).all())) == revision_count
    assert len(list(db_session.exec(select(OrganizationActivity)).all())) == activity_count


def test_g3_retry_prioritizes_durable_idempotency_after_later_case_change(db_session: Session) -> None:
    proposal, readiness, verification, floor, authority, lead, *_ = _floor_ready(db_session)
    first = commit_governed_eligibility_effect(
        db_session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        floor=floor,
        authority=authority,
    )

    lead.job_offer_status = "none"
    db_session.add(lead)
    db_session.commit()

    replay = commit_governed_eligibility_effect(
        db_session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        floor=floor,
        authority=authority,
    )
    assert replay.evaluation.outcome is GatewayOutcome.IDEMPOTENT_REPLAY
    assert replay.assessment.id == first.assessment.id
    assert replay.revision.id == first.revision.id


@pytest.mark.parametrize("autonomy", [AutonomyLevel.A0, AutonomyLevel.A1, AutonomyLevel.A2])
def test_g3_never_commits_when_fresh_gateway_is_not_auto_execute(
    db_session: Session,
    autonomy: AutonomyLevel,
) -> None:
    proposal, readiness, verification, floor, authority, *_ = _floor_ready(
        db_session,
        autonomy=autonomy,
    )
    before_assessments = len(list(db_session.exec(select(EligibilityAssessment)).all()))
    before_revisions = len(list(db_session.exec(select(EligibilityAssessmentRevision)).all()))

    with pytest.raises(EligibilityCanonicalEffectNotAuthorized):
        commit_governed_eligibility_effect(
            db_session,
            proposal=proposal,
            readiness=readiness,
            verification=verification,
            floor=floor,
            authority=authority,
        )

    assert len(list(db_session.exec(select(EligibilityAssessment)).all())) == before_assessments
    assert len(list(db_session.exec(select(EligibilityAssessmentRevision)).all())) == before_revisions
    assert _canonical_governance(db_session, proposal) is None


def test_g3_a3_commits_with_mandatory_post_review_flag(db_session: Session) -> None:
    proposal, readiness, verification, floor, authority, *_ = _floor_ready(
        db_session,
        autonomy=AutonomyLevel.A3,
    )
    result = commit_governed_eligibility_effect(
        db_session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        floor=floor,
        authority=authority,
    )
    assert result.evaluation.outcome is GatewayOutcome.AUTO_EXECUTE
    assert result.evaluation.post_review_required is True
    assert result.revision.post_review_required is True
    assert transparency_activity_record(result.semantic_activity).payload["post_review_required"] is True


def test_g3_rejects_forged_floor_identity_before_effect(db_session: Session) -> None:
    proposal, readiness, verification, floor, authority, *_ = _floor_ready(db_session)
    before = len(list(db_session.exec(select(EligibilityAssessment)).all()))

    with pytest.raises(EligibilityCanonicalEffectIntegrityError):
        commit_governed_eligibility_effect(
            db_session,
            proposal=proposal,
            readiness=readiness,
            verification=verification,
            floor=replace(floor, verification_floor_fingerprint="0" * 64),
            authority=authority,
        )

    assert len(list(db_session.exec(select(EligibilityAssessment)).all())) == before
    assert _canonical_governance(db_session, proposal) is None


def test_g3_stale_case_before_first_effect_fails_closed(db_session: Session) -> None:
    proposal, readiness, verification, floor, authority, lead, *_ = _floor_ready(db_session)
    before = len(list(db_session.exec(select(EligibilityAssessment)).all()))
    lead.job_offer_status = "none"
    db_session.add(lead)
    db_session.commit()

    with pytest.raises(EligibilityCanonicalEffectIntegrityError):
        commit_governed_eligibility_effect(
            db_session,
            proposal=proposal,
            readiness=readiness,
            verification=verification,
            floor=floor,
            authority=authority,
        )
    assert len(list(db_session.exec(select(EligibilityAssessment)).all())) == before
    assert _canonical_governance(db_session, proposal) is None


def test_g3_legacy_assessment_does_not_self_promote_to_canonical_revision(db_session: Session) -> None:
    proposal, readiness, verification, floor, authority, *_ = _floor_ready(db_session)
    legacy = EligibilityAssessment(
        lead_id=proposal.intent.lead_id,
        profile_id=proposal.intent.profile_id,
        profile_version=proposal.intent.profile_version,
        target_country="Austria",
        domain="visa",
        status="legacy_preview",
    )
    db_session.add(legacy)
    db_session.commit()

    result = commit_governed_eligibility_effect(
        db_session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        floor=floor,
        authority=authority,
    )
    assert result.assessment.id != legacy.id
    assert result.revision.assessment_id == result.assessment.id
    assert len(list(db_session.exec(select(EligibilityAssessmentRevision)).all())) == 1


def test_g3_refuses_implicit_second_revision_until_supersession_contract_exists(db_session: Session) -> None:
    proposal, readiness, verification, floor, authority, *_ = _floor_ready(db_session)
    pathway_version = db_session.get(MobilityPathwayVersion, proposal.intent.pathway_version_id)
    assert pathway_version is not None
    aggregate_key = _aggregate_key(
        tenant_key=proposal.context.tenant_key,
        lead_id=proposal.intent.lead_id,
        pathway_id=pathway_version.pathway_id,
    )
    legacy = EligibilityAssessment(
        lead_id=proposal.intent.lead_id,
        profile_id=proposal.intent.profile_id,
        profile_version=proposal.intent.profile_version,
        target_country="Austria",
        domain="visa",
        status="potentially_eligible",
    )
    db_session.add(legacy)
    db_session.flush()
    existing = EligibilityAssessmentRevision(
        assessment_id=legacy.id,
        tenant_key=proposal.context.tenant_key,
        aggregate_key=aggregate_key,
        version=1,
        lifecycle_status="active",
        supersedes_revision_id=None,
        lead_id=proposal.intent.lead_id,
        profile_id=proposal.intent.profile_id,
        profile_version=proposal.intent.profile_version,
        pathway_version_id=proposal.intent.pathway_version_id,
        governance_activity_id=proposal.attempt_activity.id,
        verification_activity_id=verification.verification_activity.id,
        verification_floor_activity_id=floor.reevaluation_activity.id,
        semantic_activity_id=verification.verification_activity.id,
        original_action_fingerprint=proposal.evaluation.action_fingerprint,
        intent_fingerprint=proposal.intent_fingerprint,
        readiness_fingerprint=readiness.readiness_fingerprint,
        verification_fingerprint=verification.verification_fingerprint,
        verification_floor_fingerprint=floor.verification_floor_fingerprint,
        effect_fingerprint="f" * 64,
        post_review_required=False,
    )
    db_session.add(existing)
    db_session.commit()

    with pytest.raises(EligibilityCanonicalEffectIntegrityError, match="reassessment/supersession"):
        commit_governed_eligibility_effect(
            db_session,
            proposal=proposal,
            readiness=readiness,
            verification=verification,
            floor=floor,
            authority=authority,
        )
    assert _canonical_governance(db_session, proposal) is None


def test_g3_atomic_rollback_removes_governance_assessment_and_revision(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    proposal, readiness, verification, floor, authority, *_ = _floor_ready(db_session)
    before_assessments = len(list(db_session.exec(select(EligibilityAssessment)).all()))
    before_revisions = len(list(db_session.exec(select(EligibilityAssessmentRevision)).all()))

    def fail_semantic(*args, **kwargs):
        raise RuntimeError("synthetic semantic Activity failure")

    monkeypatch.setattr(
        "app.services.organization_eligibility_effect._stage_semantic_effect",
        fail_semantic,
    )
    with pytest.raises(RuntimeError, match="synthetic semantic Activity failure"):
        commit_governed_eligibility_effect(
            db_session,
            proposal=proposal,
            readiness=readiness,
            verification=verification,
            floor=floor,
            authority=authority,
        )

    assert len(list(db_session.exec(select(EligibilityAssessment)).all())) == before_assessments
    assert len(list(db_session.exec(select(EligibilityAssessmentRevision)).all())) == before_revisions
    assert _canonical_governance(db_session, proposal) is None


def test_g3_torn_persisted_governance_effect_fails_closed_on_replay(db_session: Session) -> None:
    proposal, readiness, verification, floor, authority, *_ = _floor_ready(db_session)
    first = commit_governed_eligibility_effect(
        db_session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        floor=floor,
        authority=authority,
    )
    db_session.delete(first.revision)
    db_session.commit()

    with pytest.raises(EligibilityCanonicalEffectIntegrityError, match="exactly one"):
        commit_governed_eligibility_effect(
            db_session,
            proposal=proposal,
            readiness=readiness,
            verification=verification,
            floor=floor,
            authority=authority,
        )


def test_g3_effect_does_not_mutate_lead_or_authorize_external_action(db_session: Session) -> None:
    proposal, readiness, verification, floor, authority, lead, *_ = _floor_ready(db_session)
    original_status = lead.status
    result = commit_governed_eligibility_effect(
        db_session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        floor=floor,
        authority=authority,
    )
    db_session.refresh(lead)
    assert lead.status == original_status
    semantic = transparency_activity_record(result.semantic_activity)
    assert semantic.payload["client_facing"] is False
    assert semantic.payload["external_action_authorized"] is False
