from __future__ import annotations

import json

import pytest
from sqlmodel import Session

from app.models.domain import OrganizationActivity
from app.services.organization_eligibility_effect import (
    EligibilityCanonicalEffectIntegrityError,
    commit_governed_eligibility_effect,
)
from app.services.organization_eligibility_immune_system import (
    EligibilityCircuitState,
    eligibility_circuit_status,
)
from app.services.organization_eligibility_lineage import (
    CanonicalEligibilityLineageError,
    validate_canonical_eligibility_lineage,
)
from app.services.organization_eligibility_orchestration import (
    GovernedEligibilityOrchestrationIntegrityError,
    orchestrate_governed_eligibility,
)
from tests.test_organization_eligibility_effect import _floor_ready
from tests.test_organization_eligibility_immune_lineage import (
    _committed_v1,
    _critical_durable_incidents,
)


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


def test_h1_governance_activity_type_drift_opens_before_provider_egress(
    db_session: Session,
) -> None:
    (
        _,
        revision,
        _,
        proposal_work,
        verification_work,
        plan,
        producer,
        verifier,
    ) = _committed_v1(db_session, idempotency_key="h1-governance-type-base")
    aggregate = revision.aggregate_key
    governance = db_session.get(OrganizationActivity, revision.governance_activity_id)
    assert governance is not None
    governance.activity_type = "governance.unrelated.auto_execute"
    db_session.add(governance)
    db_session.commit()
    producer.calls.clear()
    verifier.calls.clear()

    with pytest.raises(GovernedEligibilityOrchestrationIntegrityError, match="circuit is open"):
        orchestrate_governed_eligibility(
            db_session,
            tenant_key="tenant-a",
            proposal_work_item_id=proposal_work.id,
            verification_work_item_id=verification_work.id,
            idempotency_key="h1-governance-type-fresh",
            execution_plan=plan,
            expected_eligibility_revision_version=1,
        )

    assert producer.calls == []
    assert verifier.calls == []
    assert eligibility_circuit_status(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
    ).state is EligibilityCircuitState.OPEN
    assert len(_critical_durable_incidents(db_session, aggregate_key=aggregate)) == 1
