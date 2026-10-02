from __future__ import annotations

from uuid import uuid4

import pytest
from sqlmodel import Session, func, select

from app.models.agent_lifecycle import OrganizationAgent
from app.models.autonomy_profile import CapabilityAutonomyProfile
from app.models.domain import (
    ExecutiveDecision,
    OfficialSource,
    OrganizationActorType,
    OrganizationDecisionType,
    OrganizationHumanAction,
    OrganizationHumanActionType,
    OrganizationRecordReference,
    OrganizationReferenceRole,
    OrganizationReferenceTargetType,
    OrganizationalWorkItem,
    now_utc,
)
from app.models.organization_improvement_review import OrganizationImprovementReviewPackage
from app.models.runtime_economics import MonetaryAllocation
from app.schemas_organization_improvement_evaluation import ImprovementEvaluationConstraint
from app.schemas_organization_improvement_review import ImprovementReviewBindingCreate
from app.services.organization_command import InvalidReference, NotFound, OrganizationCommandContext
from app.services.organization_improvement_evaluation import (
    close_evaluation_campaign,
    create_evaluation_campaign,
    record_evaluation_report,
)
from app.services.organization_improvement_lineage import (
    create_improvement_candidate,
    create_improvement_proposal,
)
from app.services.organization_improvement_review import (
    REVIEW_POLICY_FINGERPRINT,
    create_review_package,
    get_review_package,
    project_review_package,
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


def _work(
    session: Session,
    *,
    tenant: str = "default",
    phase: str = "GRSI.D",
    title: str = "Governed GRSI work",
    position: str = "board",
    department: str = "Technology",
    candidate_id: str | None = None,
    candidate_fingerprint: str | None = None,
) -> OrganizationalWorkItem:
    suffix = str(uuid4())
    row = OrganizationalWorkItem(
        idempotency_key=f"grsi-d-work-{suffix}",
        tenant_key=tenant,
        work_type="organizational",
        objective_key=f"grsi-d-objective-{suffix}",
        phase_key=phase,
        title=title,
        objective="Produce bounded review evidence without granting candidate authority.",
        department=department,
        authority_level="L4",
        assigned_position_key=position,
        risk_level="high",
        source_object_type="organization_improvement_candidate" if candidate_id else None,
        source_object_id=candidate_id,
        source_object_version=candidate_fingerprint,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _evidence(
    session: Session,
    work: OrganizationalWorkItem,
    *,
    tenant: str = "default",
) -> OrganizationRecordReference:
    suffix = str(uuid4())
    source = OfficialSource(
        country="AT",
        domain="governance",
        name=f"GRSI D evidence {suffix}",
        url=f"https://example.test/grsi-d/{suffix}",
        source_type="official",
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    row = OrganizationRecordReference(
        reference_key=f"grsi-d-evidence-{suffix}",
        record_fingerprint="e" * 64,
        tenant_key=tenant,
        work_item_id=work.id,
        reference_role=OrganizationReferenceRole.evidence,
        target_type=OrganizationReferenceTargetType.official_source,
        target_id=str(source.id),
        target_version="v1",
        target_state="current",
        content_hash="f" * 64,
        label="GRSI D evidence",
        created_by="pytest",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _candidate_and_campaign(session: Session):
    context = _admin_context()
    work = _work(session, phase="GRSI.B")
    evidence = _evidence(session, work)
    proposal = create_improvement_proposal(
        session,
        context,
        proposal_key=f"grsi-d-proposal-{uuid4()}",
        work_item_id=work.id,
        target_type="workflow",
        target_reference="git:workflow/grsi-d",
        baseline_version="v1",
        baseline_fingerprint="1" * 64,
        problem_statement="Current workflow needs bounded improvement.",
        hypothesis="The candidate improves quality without expanding authority.",
        expected_improvement="Higher measured quality.",
        acceptance_constraints={"quality": {"minimum": 2}},
        evidence_reference_ids=[evidence.id],
    )
    candidate = create_improvement_candidate(
        session,
        context,
        proposal_id=proposal.id,
        candidate_key=f"grsi-d-candidate-{uuid4()}",
        parent_candidate_id=None,
        candidate_version="v2",
        candidate_fingerprint="2" * 64,
        artifact_reference="git:commit:grsi-d-candidate",
        implementation_provenance={"authors": ["candidate-author"]},
        candidate_hypothesis="Improve quality.",
        expected_improvement="Higher measured quality.",
        acceptance_constraints={"quality": {"minimum": 2}},
    )
    campaign = create_evaluation_campaign(
        session,
        context,
        campaign_key=f"grsi-d-campaign-{uuid4()}",
        campaign_version=1,
        candidate_id=candidate.id,
        candidate_author_identities=["candidate-author"],
        candidate_author_evidence_reference_ids=[evidence.id],
        evaluation_set_key="grsi-d-evaluation-set",
        evaluation_set_version="v1",
        evaluation_set_fingerprint="3" * 64,
        evaluation_set_reference_ids=[evidence.id],
        regression_constraints=[
            ImprovementEvaluationConstraint(
                metric_key="quality",
                operator="candidate_gte_baseline_plus",
                value=0.5,
            )
        ],
        required_structurally_separate_evaluators=1,
    )
    record_evaluation_report(
        session,
        context,
        campaign_id=campaign.id,
        report_key=f"grsi-d-report-{uuid4()}",
        evaluator_actor_type="human",
        evaluator_identity="independent-evaluator",
        evaluator_independence_group="independent-group",
        independence_evidence_reference_ids=[evidence.id],
        baseline_measurements={"quality": 1.0},
        candidate_measurements={"quality": 2.0},
        evaluation_evidence_reference_ids=[evidence.id],
        reproducibility_reference_ids=[evidence.id],
    )
    campaign = close_evaluation_campaign(session, context, campaign_id=campaign.id)
    assert campaign.comparison_conclusion == "constraints_met"
    return context, candidate, campaign, evidence


def _approved_human_review(
    session: Session,
    candidate,
    *,
    position: str,
    department: str,
    action_type: OrganizationHumanActionType = OrganizationHumanActionType.approved,
) -> OrganizationHumanAction:
    work = _work(
        session,
        title=f"{position} review",
        position=position,
        department=department,
        candidate_id=str(candidate.id),
        candidate_fingerprint=candidate.candidate_fingerprint,
    )
    row = OrganizationHumanAction(
        action_key=f"grsi-d-action-{uuid4()}",
        record_fingerprint="a" * 64,
        tenant_key=candidate.tenant_key,
        action_type=action_type,
        actor_type=OrganizationActorType.human,
        human_actor_id=f"{position}-human",
        actor_role="admin",
        actor_position_key=position,
        actor_department=department,
        authority_level="L2",
        work_item_id=work.id,
        source_object_type="organization_improvement_candidate",
        source_object_id=str(candidate.id),
        source_object_version=candidate.candidate_fingerprint,
        outcome="Review approved from supplied evidence.",
        occurred_at=now_utc(),
        created_by="pytest",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _approved_governance_decision(session: Session, candidate) -> ExecutiveDecision:
    work = _work(
        session,
        title="Governance review",
        position="board",
        department="Executive",
        candidate_id=str(candidate.id),
        candidate_fingerprint=candidate.candidate_fingerprint,
    )
    row = ExecutiveDecision(
        decision_key=f"grsi-d-decision-{uuid4()}",
        tenant_key=candidate.tenant_key,
        decision_type=OrganizationDecisionType.risk,
        work_item_id=work.id,
        source_object_type="organization_improvement_candidate",
        source_object_id=str(candidate.id),
        source_object_version=candidate.candidate_fingerprint,
        authority_level="L4",
        requested_by_position="security_grc_lead",
        decision_owner_position="board",
        title="Governance review of GRSI candidate",
        question="Is the review evidence acceptable for later governed consideration?",
        recommendation="Record review disposition only; do not promote from this decision record.",
        status="approved",
        decided_by="board-human",
        decision_reason="Review evidence accepted.",
        decided_at=now_utc(),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _count(session: Session, model) -> int:
    return session.exec(select(func.count()).select_from(model)).one()


def test_high_risk_review_package_projects_canonical_reviews_without_authority_side_effects(
    db_session: Session,
) -> None:
    session = db_session
    context, candidate, campaign, risk_evidence = _candidate_and_campaign(session)
    security = _approved_human_review(
        session, candidate, position="security_lead", department="Security"
    )
    qa = _approved_human_review(
        session, candidate, position="qa_automation_engineer", department="Technology"
    )
    domain = _approved_human_review(
        session,
        candidate,
        position="product_manager",
        department="Product",
        action_type=OrganizationHumanActionType.reviewed,
    )
    platform = _approved_human_review(
        session, candidate, position="platform_engineer", department="Technology"
    )
    governance = _approved_governance_decision(session, candidate)

    before = {
        "agents": _count(session, OrganizationAgent),
        "autonomy": _count(session, CapabilityAutonomyProfile),
        "money": _count(session, MonetaryAllocation),
        "actions": _count(session, OrganizationHumanAction),
        "decisions": _count(session, ExecutiveDecision),
    }

    package = create_review_package(
        session,
        context,
        package_key=f"grsi-d-package-{uuid4()}",
        package_version=1,
        candidate_id=candidate.id,
        evaluation_campaign_id=campaign.id,
        risk_class="high",
        risk_basis_reference_ids=[risk_evidence.id],
        review_bindings=[
            ImprovementReviewBindingCreate(
                review_kind="security_red_team",
                artifact_type="human_action",
                artifact_id=security.id,
                reviewer_position_key="security_lead",
            ),
            ImprovementReviewBindingCreate(
                review_kind="qa",
                artifact_type="human_action",
                artifact_id=qa.id,
                reviewer_position_key="qa_automation_engineer",
            ),
            ImprovementReviewBindingCreate(
                review_kind="domain",
                artifact_type="human_action",
                artifact_id=domain.id,
                reviewer_position_key="product_manager",
            ),
            ImprovementReviewBindingCreate(
                review_kind="platform_sre",
                artifact_type="human_action",
                artifact_id=platform.id,
                reviewer_position_key="platform_engineer",
            ),
            ImprovementReviewBindingCreate(
                review_kind="governance",
                artifact_type="decision",
                artifact_id=governance.id,
                reviewer_position_key="board",
            ),
        ],
    )
    projected = project_review_package(session, context, package)

    assert projected.review_policy_fingerprint == REVIEW_POLICY_FINGERPRINT
    assert projected.required_review_kinds == (
        "security_red_team",
        "qa",
        "domain",
        "platform_sre",
        "governance",
    )
    assert projected.evaluation_status == "satisfied"
    assert {item.review_kind: item.status for item in projected.review_requirements} == {
        "security_red_team": "satisfied",
        "qa": "satisfied",
        "domain": "satisfied",
        "platform_sre": "satisfied",
        "governance": "satisfied",
    }
    assert projected.promotion_evidence_complete_for_decision is True
    assert projected.authority_conclusion == "none_granted"
    assert projected.promotion_conclusion == "not_authorized"
    assert projected.deployment_authorized is False
    assert projected.external_action_authorized is False

    after = {
        "agents": _count(session, OrganizationAgent),
        "autonomy": _count(session, CapabilityAutonomyProfile),
        "money": _count(session, MonetaryAllocation),
        "actions": _count(session, OrganizationHumanAction),
        "decisions": _count(session, ExecutiveDecision),
    }
    assert after == before
    assert _count(session, OrganizationImprovementReviewPackage) == 1


def test_medium_risk_package_reports_missing_reviews_without_fabricating_completion(
    db_session: Session,
) -> None:
    session = db_session
    context, candidate, campaign, risk_evidence = _candidate_and_campaign(session)
    qa = _approved_human_review(
        session, candidate, position="qa_automation_engineer", department="Technology"
    )
    package = create_review_package(
        session,
        context,
        package_key=f"grsi-d-package-{uuid4()}",
        package_version=1,
        candidate_id=candidate.id,
        evaluation_campaign_id=campaign.id,
        risk_class="medium",
        risk_basis_reference_ids=[risk_evidence.id],
        review_bindings=[
            ImprovementReviewBindingCreate(
                review_kind="qa",
                artifact_type="human_action",
                artifact_id=qa.id,
                reviewer_position_key="qa_automation_engineer",
            )
        ],
    )
    projected = project_review_package(session, context, package)

    assert projected.required_review_kinds == ("qa", "domain", "platform_sre", "governance")
    assert {item.review_kind: item.status for item in projected.review_requirements} == {
        "qa": "satisfied",
        "domain": "absent",
        "platform_sre": "absent",
        "governance": "absent",
    }
    assert projected.evaluation_status == "satisfied"
    assert projected.promotion_evidence_complete_for_decision is False


def test_review_binding_requires_exact_candidate_source_and_canonical_reviewer_position(
    db_session: Session,
) -> None:
    session = db_session
    context, candidate, campaign, risk_evidence = _candidate_and_campaign(session)
    wrong_reviewer = _approved_human_review(
        session, candidate, position="security_lead", department="Security"
    )

    with pytest.raises(InvalidReference):
        create_review_package(
            session,
            context,
            package_key=f"grsi-d-package-{uuid4()}",
            package_version=1,
            candidate_id=candidate.id,
            evaluation_campaign_id=campaign.id,
            risk_class="medium",
            risk_basis_reference_ids=[risk_evidence.id],
            review_bindings=[
                ImprovementReviewBindingCreate(
                    review_kind="qa",
                    artifact_type="human_action",
                    artifact_id=wrong_reviewer.id,
                    reviewer_position_key="security_lead",
                )
            ],
        )


def test_review_package_is_tenant_isolated(db_session: Session) -> None:
    session = db_session
    context, candidate, campaign, risk_evidence = _candidate_and_campaign(session)
    package = create_review_package(
        session,
        context,
        package_key=f"grsi-d-package-{uuid4()}",
        package_version=1,
        candidate_id=candidate.id,
        evaluation_campaign_id=campaign.id,
        risk_class="low",
        risk_basis_reference_ids=[risk_evidence.id],
        review_bindings=[],
    )
    other = _admin_context(tenant="other")
    with pytest.raises(NotFound):
        get_review_package(session, other, package_id=package.id)
