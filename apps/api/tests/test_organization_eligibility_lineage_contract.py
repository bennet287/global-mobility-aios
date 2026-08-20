from __future__ import annotations

import json

import pytest
from sqlmodel import Session

from app.models.domain import OrganizationActivity
from app.services.organization_eligibility_effect import (
    EligibilityCanonicalEffectIntegrityError,
    commit_governed_eligibility_effect,
)
from app.services.organization_eligibility_lineage import (
    CanonicalEligibilityLineageError,
    validate_canonical_eligibility_lineage,
)
from tests.test_organization_eligibility_effect import _floor_ready


def test_g3_replay_rejects_semantic_activity_type_drift(db_session: Session) -> None:
    proposal, readiness, verification, floor, authority, *_ = _floor_ready(db_session)
    first = commit_governed_eligibility_effect(
        db_session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        floor=floor,
        authority=authority,
    )

    semantic = db_session.get(OrganizationActivity, first.semantic_activity.id)
    assert semantic is not None
    semantic.activity_type = "organization.unrelated.semantic.v1"
    db_session.add(semantic)
    db_session.commit()

    with pytest.raises(
        EligibilityCanonicalEffectIntegrityError,
        match="durable lineage validation",
    ):
        commit_governed_eligibility_effect(
            db_session,
            proposal=proposal,
            readiness=readiness,
            verification=verification,
            floor=floor,
            authority=authority,
        )


def test_shared_lineage_validator_rejects_wrong_governance_record_kind(
    db_session: Session,
) -> None:
    proposal, readiness, verification, floor, authority, *_ = _floor_ready(db_session)
    first = commit_governed_eligibility_effect(
        db_session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        floor=floor,
        authority=authority,
    )

    governance = db_session.get(OrganizationActivity, first.governance_activity.id)
    assert governance is not None
    payload = json.loads(governance.payload_json or "{}")
    payload["governance_record_kind"] = "unrelated_governance_record"
    governance.payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    db_session.add(governance)
    db_session.commit()

    with pytest.raises(CanonicalEligibilityLineageError) as exc_info:
        validate_canonical_eligibility_lineage(
            db_session,
            tenant_key=proposal.context.tenant_key,
            revision=first.revision,
        )

    assert exc_info.value.code == "governance_payload_mismatch"
