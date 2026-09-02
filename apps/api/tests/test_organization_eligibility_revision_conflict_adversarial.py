from __future__ import annotations

import pytest
from sqlmodel import Session, select

from app.models.domain import OrganizationActivity
from app.services.organization_eligibility_immune_system import (
    ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE,
    EligibilityCircuitState,
    EligibilityImmuneIncidentKind,
    eligibility_circuit_status,
    record_eligibility_immune_incident,
)
from app.services.organization_eligibility_orchestration import (
    GovernedEligibilityOrchestrationIntegrityError,
    orchestrate_governed_eligibility,
)
from app.services.organization_eligibility_revision_conflict import (
    ELIGIBILITY_REVISION_CONFLICT_ATTRIBUTION_ACTIVITY_TYPE,
    EligibilityRevisionConflictAttributionError,
    record_attributed_eligibility_revision_conflict,
)
from app.services.organization_eligibility_revision_precondition import eligibility_aggregate_key
from app.services.organization_transparency import transparency_activity_record
from tests.test_organization_eligibility_orchestration import _fixture, _plan
from tests.test_organization_eligibility_revision_conflict import (
    _commit_v1_v2,
    _stale_conflict,
)


def _immune_activities(session: Session, *, aggregate_key: str) -> list[OrganizationActivity]:
    return list(
        session.exec(
            select(OrganizationActivity)
            .where(
                OrganizationActivity.tenant_key == "tenant-a",
                OrganizationActivity.source_object_type == "eligibility_aggregate",
                OrganizationActivity.source_object_id == aggregate_key,
            )
            .order_by(OrganizationActivity.stream_sequence)
        ).all()
    )


def test_h2_3_expected_revision_without_canonical_revision_is_not_attributed(
    db_session: Session,
) -> None:
    lead, _, graph, proposal_work, verification_work = _fixture(db_session)
    aggregate = eligibility_aggregate_key(
        tenant_key="tenant-a",
        lead_id=lead.id,
        pathway_id=graph["pathway"].id,
    )
    plan, producer, verifier = _plan(graph)

    with pytest.raises(GovernedEligibilityOrchestrationIntegrityError):
        orchestrate_governed_eligibility(
            db_session,
            tenant_key="tenant-a",
            proposal_work_item_id=proposal_work.id,
            verification_work_item_id=verification_work.id,
            idempotency_key="h2-3-no-current-revision",
            execution_plan=plan,
            expected_eligibility_revision_version=1,
        )

    assert producer.calls == []
    assert verifier.calls == []
    conflicts = [
        row
        for row in _immune_activities(db_session, aggregate_key=aggregate)
        if row.activity_type == ELIGIBILITY_REVISION_CONFLICT_ATTRIBUTION_ACTIVITY_TYPE
        or (
            row.activity_type == ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE
            and transparency_activity_record(row).payload.get("incident_kind")
            == EligibilityImmuneIncidentKind.REVISION_CONFLICT.value
        )
    ]
    assert conflicts == []
    assert eligibility_circuit_status(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
    ).state is EligibilityCircuitState.CLOSED


def test_h2_3_incident_only_torn_pair_fails_closed(db_session: Session) -> None:
    lead, graph, _, _, _, aggregate = _commit_v1_v2(db_session)
    conflict = _stale_conflict(
        db_session,
        lead_id=lead.id,
        pathway_id=graph["pathway"].id,
    )
    incident_key = "h2-3-torn-pair"
    summary = "Synthetic stale reassessment warning without H.2.3 attribution."

    incident = record_eligibility_immune_incident(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
        incident_key=incident_key,
        kind=EligibilityImmuneIncidentKind.REVISION_CONFLICT,
        summary=summary,
    )
    assert incident.circuit_status.state is EligibilityCircuitState.CLOSED

    with pytest.raises(
        EligibilityRevisionConflictAttributionError,
        match="must exist as one atomic pair",
    ):
        record_attributed_eligibility_revision_conflict(
            db_session,
            tenant_key="tenant-a",
            aggregate_key=aggregate,
            incident_key=incident_key,
            conflict=conflict,
            summary=summary,
        )

    rows = _immune_activities(db_session, aggregate_key=aggregate)
    torn_rows = [row for row in rows if row.activity_key.endswith(f":{incident_key}")]
    assert len(torn_rows) == 1
    assert torn_rows[0].activity_type == ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE
