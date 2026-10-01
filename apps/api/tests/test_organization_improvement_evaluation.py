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
from app.models.organization_improvement_evaluation import (
    OrganizationImprovementEvaluationCampaign,
    OrganizationImprovementEvaluationReport,
)
from app.models.runtime_economics import MonetaryAllocation
from app.schemas_organization_improvement_evaluation import ImprovementEvaluationConstraint
from app.services.organization_command import InvalidReference, InvalidTransition, NotFound, OrganizationCommandContext
from app.services.organization_improvement_evaluation import (
    close_evaluation_campaign,
    create_evaluation_campaign,
    record_evaluation_report,
)
from app.services.organization_improvement_lineage import (
    create_improvement_candidate,
    create_improvement_proposal,
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


def _work(session: Session, *, tenant: str = "default") -> OrganizationalWorkItem:
    suffix = str(uuid4())
    row = OrganizationalWorkItem(
        idempotency_key=f"grsi-c-work-{suffix}",
        tenant_key=tenant,
        work_type="organizational",
        objective_key=f"grsi-c-objective-{suffix}",
        phase_key="GRSI.C",
        title="Evaluate one bounded improvement candidate",
        objective="Compare current baseline and candidate without promotion or authority effects.",
        department="Technology",
        authority_level="L4",
        assigned_position_key="board",
        risk_level="high",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _evidence(session: Session, work: OrganizationalWorkItem, *, tenant: str = "default") -> OrganizationRecordReference:
    source = OfficialSource(
        country="AT",
        domain="governance",
        name=f"GRSI C evidence {uuid4()}",
        url=f"https://example.invalid/{uuid4()}",
    )
    session.add(source)
    session.flush()
    row = OrganizationRecordReference(
        reference_key=f"grsi-c:evidence:{uuid4()}",
        record_fingerprint="e" * 64,
        tenant_key=tenant,
        work_item_id=work.id,
        reference_role=OrganizationReferenceRole.evidence,
        target_type=OrganizationReferenceTargetType.official_source,
        target_id=str(source.id),
        label="Concrete GRSI.C evidence",
        created_by="pytest",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _candidate(session: Session, context: OrganizationCommandContext):
    work = _work(session, tenant=context.tenant_key)
    proposal_evidence = _evidence(session, work, tenant=context.tenant_key)
    proposal = create_improvement_proposal(
        session,
        context,
        proposal_key=f"grsi-c:proposal:{uuid4()}",
        work_item_id=work.id,
        target_type="organization_agent",
        target_reference="controlled-agent:engineering:v1",
        baseline_version="v1",
        baseline_fingerprint="a" * 64,
        problem_statement="A measured engineering-agent weakness requires independent comparison.",
        hypothesis="A bounded candidate can improve quality without authority expansion.",
        expected_improvement="Higher benchmark quality at equal or lower latency.",
        acceptance_constraints={"independent_evaluation_required": True},
        evidence_reference_ids=[proposal_evidence.id],
    )
    candidate = create_improvement_candidate(
        session,
        context,
        proposal_id=proposal.id,
        candidate_key=f"grsi-c:candidate:{uuid4()}",
        parent_candidate_id=None,
        candidate_version="v2",
        candidate_fingerprint="b" * 64,
        artifact_reference="git:commit:candidate-v2",
        implementation_provenance={"implemented_by": "builder-agent:v1", "model_provider": "unasserted"},
        candidate_hypothesis="Candidate changes capability behavior only.",
        expected_improvement="Higher benchmark quality at equal or lower latency.",
        acceptance_constraints={"authority_expansion_allowed": False},
    )
    return work, proposal, candidate


def _campaign(session: Session, context: OrganizationCommandContext):
    work, proposal, candidate = _candidate(session, context)
    author_evidence = _evidence(session, work, tenant=context.tenant_key)
    set_evidence = _evidence(session, work, tenant=context.tenant_key)
    campaign = create_evaluation_campaign(
        session,
        context,
        campaign_key=f"grsi-c:campaign:{uuid4()}",
        campaign_version=1,
        candidate_id=candidate.id,
        candidate_author_identities=["builder-agent:v1"],
        candidate_author_evidence_reference_ids=[author_evidence.id],
        evaluation_set_key="engineering-regression-suite",
        evaluation_set_version="2026.10.1",
        evaluation_set_fingerprint="c" * 64,
        evaluation_set_reference_ids=[set_evidence.id],
        regression_constraints=[
            ImprovementEvaluationConstraint(
                metric_key="quality",
                operator="candidate_gte_baseline_plus",
                value=0.05,
            ),
            ImprovementEvaluationConstraint(
                metric_key="latency_ms",
                operator="candidate_lte_baseline_plus",
                value=0.0,
            ),
        ],
        required_structurally_separate_evaluators=1,
    )
    return work, proposal, candidate, campaign


def _report_evidence(session: Session, work: OrganizationalWorkItem, tenant: str):
    return (
        _evidence(session, work, tenant=tenant),
        _evidence(session, work, tenant=tenant),
        _evidence(session, work, tenant=tenant),
    )


def _record_report(
    session: Session,
    context: OrganizationCommandContext,
    work: OrganizationalWorkItem,
    campaign: OrganizationImprovementEvaluationCampaign,
    *,
    evaluator: str,
    quality: float = 0.86,
):
    independence, evaluation, reproducibility = _report_evidence(session, work, context.tenant_key)
    return record_evaluation_report(
        session,
        context,
        campaign_id=campaign.id,
        report_key=f"grsi-c:report:{uuid4()}",
        evaluator_actor_type="agent",
        evaluator_identity=evaluator,
        evaluator_independence_group=f"group:{evaluator}",
        independence_evidence_reference_ids=[independence.id],
        baseline_measurements={"quality": 0.80, "latency_ms": 100.0},
        candidate_measurements={"quality": quality, "latency_ms": 95.0},
        evaluation_evidence_reference_ids=[evaluation.id],
        reproducibility_reference_ids=[reproducibility.id],
    )


def test_campaign_pins_candidate_and_has_zero_authority_side_effects(db_session: Session):
    context = _admin_context()
    assert db_session.exec(select(CapabilityAutonomyProfile)).all() == []
    assert db_session.exec(select(MonetaryAllocation)).all() == []
    assert db_session.exec(select(OrganizationAgent)).all() == []

    _, _, candidate, campaign = _campaign(db_session, context)
    assert campaign.baseline_version == candidate.baseline_version
    assert campaign.baseline_fingerprint == candidate.baseline_fingerprint
    assert campaign.candidate_version == candidate.candidate_version
    assert campaign.candidate_fingerprint == candidate.candidate_fingerprint
    assert campaign.status == "open"
    assert campaign.comparison_conclusion == "not_assessed"

    assert db_session.exec(select(CapabilityAutonomyProfile)).all() == []
    assert db_session.exec(select(MonetaryAllocation)).all() == []
    assert db_session.exec(select(OrganizationAgent)).all() == []


def test_author_cannot_be_sole_evaluator_and_independent_report_closes_campaign(db_session: Session):
    context = _admin_context()
    work, _, candidate, campaign = _campaign(db_session, context)
    author_report = _record_report(
        db_session,
        context,
        work,
        campaign,
        evaluator="builder-agent:v1",
    )
    assert author_report.constraints_satisfied is True
    with pytest.raises(InvalidTransition, match="structurally separate non-author"):
        close_evaluation_campaign(db_session, context, campaign_id=campaign.id)

    independent = _record_report(
        db_session,
        context,
        work,
        campaign,
        evaluator="qa-agent:v1",
    )
    assert independent.constraints_satisfied is True
    closed = close_evaluation_campaign(db_session, context, campaign_id=campaign.id)
    assert closed.status == "closed"
    assert closed.comparison_conclusion == "constraints_met"
    db_session.refresh(candidate)
    assert candidate.status == "prepared"


def test_failed_declared_constraint_is_recorded_without_promotion(db_session: Session):
    context = _admin_context()
    work, _, candidate, campaign = _campaign(db_session, context)
    report = _record_report(
        db_session,
        context,
        work,
        campaign,
        evaluator="qa-agent:v2",
        quality=0.81,
    )
    assert report.constraints_satisfied is False
    closed = close_evaluation_campaign(db_session, context, campaign_id=campaign.id)
    assert closed.comparison_conclusion == "constraints_not_met"
    db_session.refresh(candidate)
    assert candidate.status == "prepared"
    assert db_session.exec(select(CapabilityAutonomyProfile)).all() == []
    assert db_session.exec(select(MonetaryAllocation)).all() == []


def test_report_requires_constrained_metrics_and_concrete_same_tenant_evidence(db_session: Session):
    context = _admin_context()
    work, _, _, campaign = _campaign(db_session, context)
    independence, evaluation, reproducibility = _report_evidence(db_session, work, context.tenant_key)
    with pytest.raises(InvalidReference, match="missing constrained metric"):
        record_evaluation_report(
            db_session,
            context,
            campaign_id=campaign.id,
            report_key="grsi-c:missing-metric",
            evaluator_actor_type="agent",
            evaluator_identity="qa-agent:v3",
            evaluator_independence_group="qa",
            independence_evidence_reference_ids=[independence.id],
            baseline_measurements={"quality": 0.80, "latency_ms": 100.0},
            candidate_measurements={"latency_ms": 95.0},
            evaluation_evidence_reference_ids=[evaluation.id],
            reproducibility_reference_ids=[reproducibility.id],
        )

    other_work = _work(db_session, tenant="other")
    foreign_evidence = _evidence(db_session, other_work, tenant="other")
    with pytest.raises(NotFound):
        record_evaluation_report(
            db_session,
            context,
            campaign_id=campaign.id,
            report_key="grsi-c:foreign-evidence",
            evaluator_actor_type="agent",
            evaluator_identity="qa-agent:v4",
            evaluator_independence_group="qa",
            independence_evidence_reference_ids=[foreign_evidence.id],
            baseline_measurements={"quality": 0.80, "latency_ms": 100.0},
            candidate_measurements={"quality": 0.86, "latency_ms": 95.0},
            evaluation_evidence_reference_ids=[evaluation.id],
            reproducibility_reference_ids=[reproducibility.id],
        )


def test_evaluation_api_is_admin_only_and_non_authorizing(client, db_session: Session):
    context = _admin_context()
    work, _, candidate = _candidate(db_session, context)
    author_evidence = _evidence(db_session, work)
    set_evidence = _evidence(db_session, work)
    payload = {
        "campaign_key": "grsi-c:api-campaign",
        "campaign_version": 1,
        "candidate_id": str(candidate.id),
        "candidate_author_identities": ["builder-agent:v1"],
        "candidate_author_evidence_reference_ids": [str(author_evidence.id)],
        "evaluation_set_key": "engineering-regression-suite",
        "evaluation_set_version": "2026.10.1",
        "evaluation_set_fingerprint": "c" * 64,
        "evaluation_set_reference_ids": [str(set_evidence.id)],
        "regression_constraints": [
            {"metric_key": "quality", "operator": "candidate_gte_baseline_plus", "value": 0.05}
        ],
        "required_structurally_separate_evaluators": 1,
    }
    denied = client.post(
        "/api/v1/organization/improvements/evaluations/campaigns",
        json=payload,
        headers={"X-GMAI-Role": "operator", "X-GMAI-User": "operator"},
    )
    assert denied.status_code == 403

    created = client.post("/api/v1/organization/improvements/evaluations/campaigns", json=payload)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["authority_conclusion"] == "none_granted"
    assert body["promotion_conclusion"] == "not_assessed"
    assert body["active_version_changed"] is False
    assert body["evaluator_independence_conclusion"].endswith("not_independently_verified")
    assert created.headers["cache-control"] == "no-store"

    assert len(db_session.exec(select(OrganizationImprovementEvaluationCampaign)).all()) == 1
    assert db_session.exec(select(OrganizationImprovementEvaluationReport)).all() == []
