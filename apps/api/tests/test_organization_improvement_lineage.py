from __future__ import annotations

from uuid import uuid4

import pytest
from sqlmodel import Session, select

from app.models.agent_lifecycle import OrganizationAgent
from app.models.autonomy_profile import CapabilityAutonomyProfile
from app.models.domain import (
    OfficialSource,
    OrganizationActorType,
    OrganizationRecordReference,
    OrganizationReferenceRole,
    OrganizationReferenceTargetType,
    OrganizationalWorkItem,
)
from app.models.organization_improvement_lineage import (
    OrganizationImprovementCandidate,
    OrganizationImprovementProposal,
)
from app.models.runtime_economics import MonetaryAllocation
from app.services.organization_command import (
    InvalidReference,
    InvalidTransition,
    NotFound,
    OrganizationCommandContext,
)
from app.services.organization_improvement_lineage import (
    create_improvement_candidate,
    create_improvement_proposal,
    withdraw_improvement_candidate,
)


def _admin_context(*, tenant: str = "default") -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key=tenant,
        actor_id="pytest-admin",
        actor_type=OrganizationActorType.human,
        authenticated_user_id="pytest-admin",
        role="admin",
        department="executive",
        position_key="board",
        authority_level="L4",
    )


def _work(session: Session, *, tenant: str = "default", suffix: str | None = None) -> OrganizationalWorkItem:
    suffix = suffix or str(uuid4())
    row = OrganizationalWorkItem(
        idempotency_key=f"grsi-b-work-{suffix}",
        tenant_key=tenant,
        work_type="organizational",
        objective_key=f"grsi-b-objective-{suffix}",
        phase_key="GRSI.B",
        title="Investigate bounded AIOS capability improvement",
        objective="Produce authority-neutral proposal and candidate lineage only.",
        department="Technology",
        authority_level="L4",
        assigned_position_key="board",
        risk_level="high",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _evidence(session: Session, *, tenant: str = "default") -> OrganizationRecordReference:
    work = _work(session, tenant=tenant)
    source = OfficialSource(
        country="AT",
        domain="governance",
        name="GRSI bounded improvement evidence",
        url=f"https://example.invalid/{uuid4()}",
    )
    session.add(source)
    session.flush()
    row = OrganizationRecordReference(
        reference_key=f"grsi-b:evidence:{uuid4()}",
        record_fingerprint="e" * 64,
        tenant_key=tenant,
        work_item_id=work.id,
        reference_role=OrganizationReferenceRole.evidence,
        target_type=OrganizationReferenceTargetType.official_source,
        target_id=str(source.id),
        label="Concrete GRSI improvement evidence",
        created_by="pytest",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _proposal_kwargs(
    work: OrganizationalWorkItem,
    evidence: OrganizationRecordReference,
    *,
    key: str | None = None,
    target_reference: str = "controlled-agent:engineering:v1",
    supersedes_proposal_id=None,
) -> dict:
    return {
        "proposal_key": key or f"grsi-b:proposal:{uuid4()}",
        "work_item_id": work.id,
        "target_type": "organization_agent",
        "target_reference": target_reference,
        "baseline_version": "v1",
        "baseline_fingerprint": "a" * 64,
        "problem_statement": "Observed bounded quality weakness requires a candidate investigation.",
        "hypothesis": "A revised implementation can improve quality without expanding authority.",
        "expected_improvement": "Improve measured quality while preserving safety, cost and authority constraints.",
        "acceptance_constraints": {
            "minimum_quality_delta": 0.05,
            "authority_expansion_allowed": False,
        },
        "evidence_reference_ids": [evidence.id],
        "supersedes_proposal_id": supersedes_proposal_id,
    }


def _candidate_kwargs(*, key: str | None = None, fingerprint: str = "b" * 64, parent=None) -> dict:
    return {
        "candidate_key": key or f"grsi-b:candidate:{uuid4()}",
        "parent_candidate_id": parent,
        "candidate_version": "v2",
        "candidate_fingerprint": fingerprint,
        "artifact_reference": "git:commit:0123456789abcdef",
        "implementation_provenance": {
            "implemented_by": "software-engineering",
            "model_provider": "unasserted",
        },
        "candidate_hypothesis": "Candidate changes capability behavior only.",
        "expected_improvement": "Higher benchmark quality with no authority expansion.",
        "acceptance_constraints": {
            "authority_expansion_allowed": False,
            "independent_evaluation_required": True,
        },
    }


def _api_proposal_payload(work: OrganizationalWorkItem, evidence: OrganizationRecordReference) -> dict:
    payload = _proposal_kwargs(work, evidence, key="grsi-b:api-proposal")
    payload["work_item_id"] = str(work.id)
    payload["evidence_reference_ids"] = [str(evidence.id)]
    return payload


def _api_candidate_payload() -> dict:
    payload = _candidate_kwargs(key="grsi-b:api-candidate")
    payload["parent_candidate_id"] = None
    return payload


def test_improvement_lineage_api_is_admin_only_idempotent_and_non_authorizing(
    client,
    db_session: Session,
):
    work, evidence = _work(db_session), _evidence(db_session)
    proposal_payload = _api_proposal_payload(work, evidence)

    denied = client.post(
        "/api/v1/organization/improvements/proposals",
        json=proposal_payload,
        headers={"X-GMAI-Role": "operator", "X-GMAI-User": "operator"},
    )
    assert denied.status_code == 403

    created = client.post("/api/v1/organization/improvements/proposals", json=proposal_payload)
    assert created.status_code == 201, created.text
    proposal = created.json()
    assert proposal["authority_conclusion"] == "none_granted"
    assert proposal["active_version_changed"] is False
    assert proposal["autonomy_changed"] is False
    assert proposal["permission_or_tool_access_changed"] is False
    assert proposal["monetary_authority_changed"] is False
    assert proposal["deployment_authorized"] is False
    assert proposal["external_action_authorized"] is False
    assert proposal["evaluation_conclusion"] == "not_assessed"
    assert created.headers["cache-control"] == "no-store"

    replay = client.post("/api/v1/organization/improvements/proposals", json=proposal_payload)
    assert replay.status_code == 201
    assert replay.json()["id"] == proposal["id"]
    assert len(db_session.exec(select(OrganizationImprovementProposal)).all()) == 1

    candidate_payload = _api_candidate_payload()
    candidate_created = client.post(
        f"/api/v1/organization/improvements/proposals/{proposal['id']}/candidates",
        json=candidate_payload,
    )
    assert candidate_created.status_code == 201, candidate_created.text
    candidate = candidate_created.json()
    assert candidate["authority_conclusion"] == "none_granted"
    assert candidate["active_version_changed"] is False
    assert candidate["autonomy_changed"] is False
    assert candidate["permission_or_tool_access_changed"] is False
    assert candidate["monetary_authority_changed"] is False
    assert candidate["deployment_authorized"] is False
    assert candidate["external_action_authorized"] is False
    assert candidate["evaluation_conclusion"] == "not_assessed"
    assert candidate_created.headers["cache-control"] == "no-store"

    candidate_replay = client.post(
        f"/api/v1/organization/improvements/proposals/{proposal['id']}/candidates",
        json=candidate_payload,
    )
    assert candidate_replay.status_code == 201
    assert candidate_replay.json()["id"] == candidate["id"]
    assert len(db_session.exec(select(OrganizationImprovementCandidate)).all()) == 1


def test_proposal_requires_same_tenant_work_and_concrete_evidence(db_session: Session):
    context = _admin_context()
    work, evidence = _work(db_session), _evidence(db_session)
    evidence.reference_role = OrganizationReferenceRole.supports
    db_session.add(evidence)
    db_session.commit()

    with pytest.raises(InvalidReference, match="must use evidence"):
        create_improvement_proposal(db_session, context, **_proposal_kwargs(work, evidence))

    other_work = _work(db_session, tenant="other")
    other_evidence = _evidence(db_session, tenant="other")
    with pytest.raises(NotFound):
        create_improvement_proposal(
            db_session,
            context,
            **_proposal_kwargs(other_work, other_evidence),
        )


def test_candidate_lineage_is_pinned_and_parent_must_share_proposal(db_session: Session):
    context = _admin_context()
    work, evidence = _work(db_session), _evidence(db_session)
    proposal = create_improvement_proposal(db_session, context, **_proposal_kwargs(work, evidence))

    first = create_improvement_candidate(
        db_session,
        context,
        proposal_id=proposal.id,
        **_candidate_kwargs(key="grsi-b:parent", fingerprint="b" * 64),
    )
    child_kwargs = _candidate_kwargs(
        key="grsi-b:child",
        fingerprint="c" * 64,
        parent=first.id,
    )
    child = create_improvement_candidate(
        db_session,
        context,
        proposal_id=proposal.id,
        **child_kwargs,
    )
    assert child.parent_candidate_id == first.id
    assert child.target_type == proposal.target_type
    assert child.target_reference == proposal.target_reference
    assert child.baseline_version == first.candidate_version
    assert child.baseline_fingerprint == first.candidate_fingerprint

    with pytest.raises(InvalidReference, match="must differ from its effective baseline"):
        create_improvement_candidate(
            db_session,
            context,
            proposal_id=proposal.id,
            **_candidate_kwargs(key="grsi-b:no-op", fingerprint="a" * 64),
        )

    other_work, other_evidence = _work(db_session), _evidence(db_session)
    other_proposal = create_improvement_proposal(
        db_session,
        context,
        **_proposal_kwargs(
            other_work,
            other_evidence,
            key="grsi-b:other-proposal",
            target_reference="controlled-agent:security:v1",
        ),
    )
    with pytest.raises(InvalidReference, match="same improvement proposal"):
        create_improvement_candidate(
            db_session,
            context,
            proposal_id=other_proposal.id,
            **_candidate_kwargs(key="grsi-b:cross-parent", fingerprint="d" * 64, parent=first.id),
        )

    withdraw_improvement_candidate(
        db_session,
        context,
        candidate_id=first.id,
        reason="Parent candidate rejected before independent evaluation.",
    )
    replayed_child = create_improvement_candidate(
        db_session,
        context,
        proposal_id=proposal.id,
        **child_kwargs,
    )
    assert replayed_child.id == child.id

    with pytest.raises(InvalidTransition, match="withdrawn candidate"):
        create_improvement_candidate(
            db_session,
            context,
            proposal_id=proposal.id,
            **_candidate_kwargs(key="grsi-b:withdrawn-parent", fingerprint="e" * 64, parent=first.id),
        )


def test_proposal_supersession_closes_old_candidate_branch(db_session: Session):
    context = _admin_context()
    work, evidence = _work(db_session), _evidence(db_session)
    first = create_improvement_proposal(
        db_session,
        context,
        **_proposal_kwargs(work, evidence, key="grsi-b:proposal-v1"),
    )
    existing_candidate_kwargs = _candidate_kwargs(
        key="grsi-b:existing-candidate",
        fingerprint="b" * 64,
    )
    existing_candidate = create_improvement_candidate(
        db_session,
        context,
        proposal_id=first.id,
        **existing_candidate_kwargs,
    )
    successor_kwargs = _proposal_kwargs(
        work,
        evidence,
        key="grsi-b:proposal-v2",
        supersedes_proposal_id=first.id,
    )
    successor = create_improvement_proposal(
        db_session,
        context,
        **successor_kwargs,
    )
    assert successor.supersedes_proposal_id == first.id

    replayed_successor = create_improvement_proposal(
        db_session,
        context,
        **successor_kwargs,
    )
    assert replayed_successor.id == successor.id

    replayed_candidate = create_improvement_candidate(
        db_session,
        context,
        proposal_id=first.id,
        **existing_candidate_kwargs,
    )
    assert replayed_candidate.id == existing_candidate.id

    with pytest.raises(InvalidTransition, match="current open"):
        create_improvement_candidate(
            db_session,
            context,
            proposal_id=first.id,
            **_candidate_kwargs(key="grsi-b:stale-branch"),
        )

    with pytest.raises(InvalidReference, match="same target identity"):
        create_improvement_proposal(
            db_session,
            context,
            **_proposal_kwargs(
                work,
                evidence,
                key="grsi-b:invalid-supersession",
                target_reference="controlled-agent:different:v1",
                supersedes_proposal_id=successor.id,
            ),
        )


def test_improvement_lineage_has_zero_authority_resource_or_agent_side_effects(db_session: Session):
    context = _admin_context()
    assert db_session.exec(select(CapabilityAutonomyProfile)).all() == []
    assert db_session.exec(select(MonetaryAllocation)).all() == []
    assert db_session.exec(select(OrganizationAgent)).all() == []

    work, evidence = _work(db_session), _evidence(db_session)
    proposal = create_improvement_proposal(
        db_session,
        context,
        **_proposal_kwargs(work, evidence, key="grsi-b:no-authority"),
    )
    create_improvement_candidate(
        db_session,
        context,
        proposal_id=proposal.id,
        **_candidate_kwargs(key="grsi-b:no-authority-candidate"),
    )

    assert db_session.exec(select(CapabilityAutonomyProfile)).all() == []
    assert db_session.exec(select(MonetaryAllocation)).all() == []
    assert db_session.exec(select(OrganizationAgent)).all() == []
