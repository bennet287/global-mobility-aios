from __future__ import annotations

import pytest
from sqlmodel import Session

from app.models.domain import MobilityPathwayVersion
from app.services.organization_eligibility_effect import commit_governed_eligibility_effect
from app.services.organization_eligibility_revision_precondition import (
    EligibilityRevisionPreconditionRequired,
    EligibilityRevisionPreconditionStale,
    eligibility_aggregate_key,
    require_eligibility_revision_precondition_current,
    resolve_eligibility_revision_precondition,
)
from tests.test_organization_eligibility_effect import _floor_ready


def _pathway_id(session: Session, proposal):
    pathway_version = session.get(MobilityPathwayVersion, proposal.intent.pathway_version_id)
    assert pathway_version is not None
    return pathway_version.pathway_id


def _commit_v1(session: Session):
    proposal, readiness, verification, floor, authority, *_ = _floor_ready(session)
    result = commit_governed_eligibility_effect(
        session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        floor=floor,
        authority=authority,
    )
    return proposal, result


def test_g5_initial_effect_requires_absence_of_active_revision(db_session: Session) -> None:
    proposal, _, _, _, _, *_ = _floor_ready(db_session)
    pathway_id = _pathway_id(db_session, proposal)

    precondition = resolve_eligibility_revision_precondition(
        db_session,
        tenant_key=proposal.context.tenant_key,
        lead_id=proposal.intent.lead_id,
        pathway_id=pathway_id,
        expected_revision_version=None,
    )

    assert precondition.aggregate_key == eligibility_aggregate_key(
        tenant_key=proposal.context.tenant_key,
        lead_id=proposal.intent.lead_id,
        pathway_id=pathway_id,
    )
    assert precondition.expected_revision_version is None
    assert precondition.current_revision_id is None
    assert precondition.current_revision_version is None
    assert precondition.next_revision_version == 1
    assert precondition.supersedes_revision_id is None
    assert precondition.is_reassessment is False


def test_g5_existing_active_revision_requires_explicit_expectation(db_session: Session) -> None:
    proposal, result = _commit_v1(db_session)
    pathway_id = _pathway_id(db_session, proposal)

    with pytest.raises(EligibilityRevisionPreconditionRequired, match="expected revision"):
        resolve_eligibility_revision_precondition(
            db_session,
            tenant_key=proposal.context.tenant_key,
            lead_id=proposal.intent.lead_id,
            pathway_id=pathway_id,
            expected_revision_version=None,
        )

    assert result.revision.version == 1
    assert result.revision.lifecycle_status == "active"


def test_g5_exact_active_revision_resolves_next_version_and_supersedes_target(
    db_session: Session,
) -> None:
    proposal, result = _commit_v1(db_session)
    pathway_id = _pathway_id(db_session, proposal)

    precondition = resolve_eligibility_revision_precondition(
        db_session,
        tenant_key=proposal.context.tenant_key,
        lead_id=proposal.intent.lead_id,
        pathway_id=pathway_id,
        expected_revision_version=1,
    )

    assert precondition.expected_revision_version == 1
    assert precondition.current_revision_id == result.revision.id
    assert precondition.current_revision_version == 1
    assert precondition.next_revision_version == 2
    assert precondition.supersedes_revision_id == result.revision.id
    assert precondition.is_reassessment is True


def test_g5_stale_revision_expectation_fails_closed(db_session: Session) -> None:
    proposal, _ = _commit_v1(db_session)
    pathway_id = _pathway_id(db_session, proposal)

    with pytest.raises(EligibilityRevisionPreconditionStale, match="stale"):
        resolve_eligibility_revision_precondition(
            db_session,
            tenant_key=proposal.context.tenant_key,
            lead_id=proposal.intent.lead_id,
            pathway_id=pathway_id,
            expected_revision_version=2,
        )

    with pytest.raises(EligibilityRevisionPreconditionStale, match="at least 1"):
        resolve_eligibility_revision_precondition(
            db_session,
            tenant_key=proposal.context.tenant_key,
            lead_id=proposal.intent.lead_id,
            pathway_id=pathway_id,
            expected_revision_version=0,
        )


def test_g5_precondition_revalidation_detects_intervening_canonical_commit(
    db_session: Session,
) -> None:
    proposal, readiness, verification, floor, authority, *_ = _floor_ready(db_session)
    pathway_id = _pathway_id(db_session, proposal)
    initial = resolve_eligibility_revision_precondition(
        db_session,
        tenant_key=proposal.context.tenant_key,
        lead_id=proposal.intent.lead_id,
        pathway_id=pathway_id,
        expected_revision_version=None,
    )

    commit_governed_eligibility_effect(
        db_session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        floor=floor,
        authority=authority,
    )

    with pytest.raises(EligibilityRevisionPreconditionStale, match="changed"):
        require_eligibility_revision_precondition_current(
            db_session,
            precondition=initial,
            lead_id=proposal.intent.lead_id,
            pathway_id=pathway_id,
        )
