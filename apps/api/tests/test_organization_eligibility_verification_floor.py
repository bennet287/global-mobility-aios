from __future__ import annotations

import json
from dataclasses import replace
from datetime import timedelta
from uuid import uuid4

import pytest
from sqlmodel import Session, select

from app.core.organization_constitution import AutonomyLevel, MaterialActionType, RiskTier
from app.models.domain import EligibilityAssessment, OrganizationActivity, now_utc
from app.services.organization_eligibility_verification_floor import (
    ELIGIBILITY_VERIFICATION_FLOOR_SCHEMA_VERSION,
    EligibilityVerificationFloorIntegrityError,
    integrate_eligibility_verification_floor,
)
from app.services.organization_governance_kernel import (
    CapabilityAuthority,
    GatewayOutcome,
    GatewayReason,
)
from app.services.organization_independent_eligibility_verification import (
    IndependentVerificationDisposition,
    verify_eligibility_proposal_independently,
)
from app.services.organization_transparency import activities_for_trace, transparency_activity_record
from tests.test_organization_independent_eligibility_verification import (
    FakeProvider,
    _authority,
    _setup,
    _verifier_output,
    _verifier_runtime,
)


def _agreeing_verification(session: Session):
    proposal, readiness, lead, profile, graph, proposal_work, verification_work, _ = _setup(session)
    verification = verify_eligibility_proposal_independently(
        session,
        proposal=proposal,
        readiness=readiness,
        verification_work_item_id=verification_work.id,
        verifier_position_key="austria_independent_verifier",
        verifier_runtime_profile=_verifier_runtime(),
        provider=FakeProvider(
            name="openai",
            model="gpt-verifier",
            content=_verifier_output(graph),
        ),
        idempotency_key=f"g2-verification-{uuid4()}",
    )
    assert verification.disposition is IndependentVerificationDisposition.AGREES
    return proposal, readiness, verification, lead, profile, graph, proposal_work, verification_work


def _authority_with(
    *,
    autonomy: AutonomyLevel = AutonomyLevel.A5,
    actor_id: str = "austria_mobility_specialist",
    max_risk: RiskTier = RiskTier.R3,
    scopes: frozenset[str] = frozenset({"austria:visa"}),
) -> CapabilityAuthority:
    return CapabilityAuthority(
        tenant_key="tenant-a",
        actor_id=actor_id,
        capability="mobility.eligibility",
        allowed_action_types=frozenset({MaterialActionType.ELIGIBILITY_TRANSITION}),
        max_risk_tier=max_risk,
        autonomy_level=autonomy,
        allowed_scopes=scopes,
    )


def _original_idempotency_key(proposal) -> str:
    payload = json.loads(proposal.attempt_activity.payload_json)
    value = payload["idempotency_key"]
    assert isinstance(value, str)
    return value


def test_g2_agreement_satisfies_floor_and_allows_gateway_without_mutating(db_session: Session) -> None:
    proposal, readiness, verification, *_ = _agreeing_verification(db_session)
    before_assessments = len(list(db_session.exec(select(EligibilityAssessment)).all()))
    before_activities = len(list(db_session.exec(select(OrganizationActivity)).all()))

    result = integrate_eligibility_verification_floor(
        db_session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        authority=_authority(),
    )

    assert result.schema_version == ELIGIBILITY_VERIFICATION_FLOOR_SCHEMA_VERSION
    assert result.verification_floor_satisfied is True
    assert result.evaluation.outcome is GatewayOutcome.AUTO_EXECUTE
    assert result.evaluation.reason is GatewayReason.AUTHORIZED
    assert result.evaluation.action_fingerprint == proposal.evaluation.action_fingerprint
    assert result.gateway_authorized_for_execution is True
    assert result.eligible_for_effect_integration is True
    assert result.canonical_effect_committed is False
    assert result.mutated is False
    assert result.reevaluation_activity.causation_activity_id == verification.verification_activity.id
    assert len(list(db_session.exec(select(EligibilityAssessment)).all())) == before_assessments
    assert len(list(db_session.exec(select(OrganizationActivity)).all())) == before_activities + 1

    original_key = _original_idempotency_key(proposal)
    canonical = db_session.exec(
        select(OrganizationActivity).where(
            OrganizationActivity.tenant_key == "tenant-a",
            OrganizationActivity.activity_key == f"governance:{original_key}",
        )
    ).first()
    assert canonical is None


def test_g2_a0_remains_blocked_after_independent_agreement(db_session: Session) -> None:
    proposal, readiness, verification, *_ = _agreeing_verification(db_session)
    result = integrate_eligibility_verification_floor(
        db_session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        authority=_authority_with(autonomy=AutonomyLevel.A0),
    )
    assert result.verification_floor_satisfied is True
    assert result.evaluation.outcome is GatewayOutcome.BLOCK
    assert result.evaluation.reason is GatewayReason.AUTONOMY_PROHIBITED
    assert result.gateway_authorized_for_execution is False
    assert result.eligible_for_effect_integration is False


@pytest.mark.parametrize("autonomy", [AutonomyLevel.A1, AutonomyLevel.A2])
def test_g2_a1_a2_still_require_human_review(
    db_session: Session,
    autonomy: AutonomyLevel,
) -> None:
    proposal, readiness, verification, *_ = _agreeing_verification(db_session)
    result = integrate_eligibility_verification_floor(
        db_session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        authority=_authority_with(autonomy=autonomy),
    )
    assert result.verification_floor_satisfied is True
    assert result.evaluation.outcome is GatewayOutcome.REVIEW_REQUIRED
    assert result.evaluation.reason is GatewayReason.AUTONOMY_REVIEW_REQUIRED
    assert result.gateway_authorized_for_execution is False


@pytest.mark.parametrize("autonomy", [AutonomyLevel.A3, AutonomyLevel.A4, AutonomyLevel.A5])
def test_g2_a3_plus_can_be_gateway_authorized_but_g2_never_commits_effect(
    db_session: Session,
    autonomy: AutonomyLevel,
) -> None:
    proposal, readiness, verification, *_ = _agreeing_verification(db_session)
    before = len(list(db_session.exec(select(EligibilityAssessment)).all()))
    result = integrate_eligibility_verification_floor(
        db_session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        authority=_authority_with(autonomy=autonomy),
    )
    assert result.evaluation.outcome is GatewayOutcome.AUTO_EXECUTE
    assert result.evaluation.reason is GatewayReason.AUTHORIZED
    assert result.evaluation.post_review_required is (autonomy is AutonomyLevel.A3)
    assert result.gateway_authorized_for_execution is True
    assert result.canonical_effect_committed is False
    assert result.mutated is False
    assert len(list(db_session.exec(select(EligibilityAssessment)).all())) == before


def test_g2_rejects_forged_or_nonagreeing_verification(db_session: Session) -> None:
    proposal, readiness, verification, *_ = _agreeing_verification(db_session)

    with pytest.raises(EligibilityVerificationFloorIntegrityError):
        integrate_eligibility_verification_floor(
            db_session,
            proposal=proposal,
            readiness=readiness,
            verification=replace(
                verification,
                disposition=IndependentVerificationDisposition.DISAGREES,
                eligible_for_verification_floor_integration=False,
            ),
            authority=_authority(),
        )

    with pytest.raises(EligibilityVerificationFloorIntegrityError):
        integrate_eligibility_verification_floor(
            db_session,
            proposal=proposal,
            readiness=readiness,
            verification=replace(verification, verification_fingerprint="0" * 64),
            authority=_authority(),
        )


def test_g2_stale_case_after_g1_fails_before_floor_activity(db_session: Session) -> None:
    proposal, readiness, verification, lead, *_ = _agreeing_verification(db_session)
    before = len(list(db_session.exec(select(OrganizationActivity)).all()))
    lead.job_offer_status = "none"
    lead.updated_at = now_utc() + timedelta(seconds=1)
    db_session.add(lead)
    db_session.commit()

    with pytest.raises(EligibilityVerificationFloorIntegrityError):
        integrate_eligibility_verification_floor(
            db_session,
            proposal=proposal,
            readiness=readiness,
            verification=verification,
            authority=_authority(),
        )
    assert len(list(db_session.exec(select(OrganizationActivity)).all())) == before


@pytest.mark.parametrize(
    "authority,reason",
    [
        (_authority_with(actor_id="other-employee"), GatewayReason.OUTSIDE_AUTHORITY),
        (_authority_with(scopes=frozenset({"germany:visa"})), GatewayReason.SCOPE_DENIED),
        (_authority_with(max_risk=RiskTier.R2), GatewayReason.RISK_EXCEEDS_AUTHORITY),
    ],
)
def test_g2_gateway_still_owns_authority_scope_and_risk(
    db_session: Session,
    authority: CapabilityAuthority,
    reason: GatewayReason,
) -> None:
    proposal, readiness, verification, *_ = _agreeing_verification(db_session)
    result = integrate_eligibility_verification_floor(
        db_session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        authority=authority,
    )
    assert result.verification_floor_satisfied is True
    assert result.evaluation.outcome is GatewayOutcome.BLOCK
    assert result.evaluation.reason is reason
    assert result.gateway_authorized_for_execution is False


def test_g2_exact_rerun_reuses_floor_activity_without_consuming_canonical_slot(
    db_session: Session,
) -> None:
    proposal, readiness, verification, *_ = _agreeing_verification(db_session)
    first = integrate_eligibility_verification_floor(
        db_session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        authority=_authority(),
    )
    count_after_first = len(list(db_session.exec(select(OrganizationActivity)).all()))
    second = integrate_eligibility_verification_floor(
        db_session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        authority=_authority(),
    )
    assert second.verification_floor_fingerprint == first.verification_floor_fingerprint
    assert second.reevaluation_activity.id == first.reevaluation_activity.id
    assert len(list(db_session.exec(select(OrganizationActivity)).all())) == count_after_first

    original_key = _original_idempotency_key(proposal)
    canonical = db_session.exec(
        select(OrganizationActivity).where(
            OrganizationActivity.tenant_key == "tenant-a",
            OrganizationActivity.activity_key == f"governance:{original_key}",
        )
    ).first()
    assert canonical is None


def test_g2_trace_lineage_is_e2_to_g1_to_g2_and_material(db_session: Session) -> None:
    proposal, readiness, verification, *_ = _agreeing_verification(db_session)
    result = integrate_eligibility_verification_floor(
        db_session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        authority=_authority(),
    )

    record = transparency_activity_record(result.reevaluation_activity)
    assert record.causation_activity_id == verification.verification_activity.id
    assert record.trace_id == str(proposal.evaluation.trace_id)
    assert record.constitutional_activity_class.value == "MATERIAL"
    assert record.payload["verification_floor_satisfied"] is True
    assert record.payload["gateway_authorized_for_execution"] is True
    assert record.payload["canonical_effect_committed"] is False

    trace = activities_for_trace(
        db_session,
        tenant_key="tenant-a",
        trace_id=proposal.evaluation.trace_id,
    )
    ids = [item.activity_id for item in trace]
    assert proposal.attempt_activity.id in ids
    assert verification.verification_activity.id in ids
    assert result.reevaluation_activity.id in ids
    assert verification.verification_activity.causation_activity_id == proposal.attempt_activity.id
    assert result.reevaluation_activity.causation_activity_id == verification.verification_activity.id
