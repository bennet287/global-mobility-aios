from __future__ import annotations

import json
from dataclasses import replace
from datetime import timedelta
from typing import Any
from uuid import uuid4

import pytest
from sqlmodel import Session, select

from app.core.organization_constitution import AutonomyLevel, MaterialActionType, RiskTier
from app.models.domain import (
    CountryPolicy,
    EligibilityAssessment,
    Lead,
    LeadIntent,
    MobilityPathway,
    MobilityPathwayVersion,
    MobilityPathwayVersionEvidence,
    OfficialSource,
    OrganizationActivity,
    OrganizationPosition,
    OrganizationalWorkItem,
    Profile,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from app.services.llm_client import LLMProvider, LLMResponse
from app.services.organization_agent_runtime import AgentRuntimeProfile, RuntimeClass
from app.services.organization_command import canonical_json
from app.services.organization_decision_readiness import (
    DECISION_READINESS_SCHEMA_VERSION,
    DecisionReadinessGateCode,
    DecisionReadinessGateStatus,
    DecisionReadinessIntegrityError,
    DecisionReadinessState,
    assess_eligibility_decision_readiness,
)
from app.services.organization_eligibility_runtime_session import (
    execute_fenced_governed_eligibility_transition_intent,
)
from app.services.organization_eligibility_transition_intent import (
    GOVERNED_ELIGIBILITY_CAPABILITY,
    EligibilityProposedState,
    governed_eligibility_transition_intent,
)
from app.services.organization_governance_kernel import CapabilityAuthority, GatewayOutcome


class FakeProvider(LLMProvider):
    name = "deepseek"

    def __init__(self, content: str) -> None:
        self.content = content
        self.calls: list[dict[str, Any]] = []

    def complete(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        response_format: dict[str, Any] | None = None,
    ) -> LLMResponse:
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "messages": messages,
                "response_format": response_format,
            }
        )
        return LLMResponse(
            content=self.content,
            provider="deepseek",
            model="deepseek-reasoner",
            finish_reason="stop",
            total_tokens=123,
        )


def _position(session: Session) -> OrganizationPosition:
    row = OrganizationPosition(
        position_key="austria_mobility_specialist",
        title="Austria Immigration Specialist",
        department="Mobility",
        reports_to_position_key="mobility_operations_lead",
        role_card_name="austria_mobility_specialist",
        authority_level="L2",
        contract_json=canonical_json(
            {
                "jurisdiction": "AT",
                "context_authority": {
                    "allowed_tools": ["official_source.search", "document.read"],
                },
            }
        ),
        status="active",
        version=8,
        created_by="pytest",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _case(
    session: Session,
    *,
    nationality: str | None = "india",
    job_offer_status: str | None = "confirmed",
    completeness_score: float = 90.0,
    readiness_stage: str = "evidence_ready",
) -> tuple[Lead, Profile]:
    lead = Lead(
        full_name="Readiness Subject",
        email="readiness@example.test",
        phone="+4300000000",
        intent=LeadIntent.visa,
        target_country="austria",
        nationality=nationality,
        current_country="austria",
        occupation_title="Software Engineer",
        years_experience=5.0,
        job_offer_status=job_offer_status,
        qualification_recognition="recognized",
        german_level="B1",
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)

    profile = Profile(
        lead_id=lead.id,
        profile_type="universal_mobility",
        profile_version=4,
        lifecycle_status="active",
        current_country="austria",
        target_country="austria",
        desired_role="Software Engineer",
        highest_qualification="Bachelor degree",
        field_of_study="Computer Science",
        years_experience=5.0,
        goals_json='[{"domain":"visa","target_country":"austria","desired_role_or_program":"Software Engineer"}]',
        employment_json='[{"role":"Software Engineer","country":"austria","years":5,"current":true}]',
        education_json='[{"qualification":"Bachelor degree","field_of_study":"Computer Science"}]',
        consent_json='{"status":"granted"}',
        completeness_score=completeness_score,
        readiness_stage=readiness_stage,
        consent_status="granted",
        activated_at=now_utc(),
        updated_by="pytest",
    )
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return lead, profile


def _authority_graph(
    session: Session,
    *,
    evidence_role: str = "core_route",
    eligibility_criteria: dict[str, Any] | None = None,
) -> dict[str, object]:
    source = OfficialSource(
        country="austria",
        domain="visa",
        name="Austrian official readiness source",
        url=f"https://example.gv.at/{uuid4()}",
        source_type="government",
        authority="Austrian authority",
        active=True,
    )
    session.add(source)
    session.commit()
    session.refresh(source)

    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="f1-snapshot-v1",
        content_text="Official governed Austrian readiness source.",
        http_status=200,
        retrieval_method="http",
        parser_version="pytest-v1",
        status="captured",
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)

    rule = VerifiedRule(
        country="austria",
        domain="visa",
        rule_key=f"at-f1-rule-{uuid4()}",
        statement="The governed pathway criterion must be independently verified before commitment.",
        official_source_id=source.id,
        source_snapshot_id=snapshot.id,
        confidence=0.99,
        active=True,
        effective_from=now_utc() - timedelta(days=30),
        approved_by="pytest-reviewer",
        published_at=now_utc() - timedelta(days=1),
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)

    pathway = MobilityPathway(
        pathway_key=f"at-f1-path-{uuid4()}",
        name="Austria Decision Readiness Pathway",
        country="austria",
        domain="visa",
        catalogue_status="published",
        created_by="pytest",
    )
    session.add(pathway)
    session.commit()
    session.refresh(pathway)

    version = MobilityPathwayVersion(
        pathway_id=pathway.id,
        version_number=6,
        lifecycle_status="published",
        official_source_id=source.id,
        source_snapshot_id=snapshot.id,
        verified_rule_ids_json=json.dumps([str(rule.id)]),
        eligibility_criteria_json=json.dumps(eligibility_criteria or {}),
        required_documents_json='["Valid passport"]',
        metadata_json='{"scope":"f1-test"}',
        effective_from=now_utc() - timedelta(days=10),
        human_review_required=True,
        approved_by="pytest-reviewer",
        published_at=now_utc() - timedelta(days=1),
        created_by="pytest",
    )
    session.add(version)
    session.commit()
    session.refresh(version)

    evidence = MobilityPathwayVersionEvidence(
        pathway_version_id=version.id,
        evidence_role=evidence_role,
        official_source_id=source.id,
        source_snapshot_id=snapshot.id,
        required_for_publication=True,
        metadata_json='{"purpose":"f1 pathway authority"}',
    )
    session.add(evidence)
    session.commit()
    session.refresh(evidence)

    policy = CountryPolicy(
        country="austria",
        domain="visa",
        policy_json='{"human_review_required":true,"verification_required":true}',
        status="active",
        last_reviewed_at=now_utc() - timedelta(days=2),
    )
    session.add(policy)
    session.commit()
    session.refresh(policy)

    return {
        "source": source,
        "snapshot": snapshot,
        "rule": rule,
        "pathway": pathway,
        "version": version,
        "evidence": evidence,
        "policy": policy,
    }


def _work(
    session: Session,
    *,
    lead: Lead,
    profile: Profile,
    version: MobilityPathwayVersion,
) -> OrganizationalWorkItem:
    row = OrganizationalWorkItem(
        idempotency_key=f"f1-decision-readiness-{uuid4()}",
        tenant_key="tenant-a",
        title="Assess eligibility decision readiness",
        objective="Determine whether the governed E.2 eligibility proposal is ready for independent verification.",
        department="Mobility",
        authority_level="L2",
        assigned_position_key="austria_mobility_specialist",
        risk_level="material",
        lead_id=lead.id,
        profile_id=profile.id,
        context_json="{}",
        source_object_type="mobility_pathway_version",
        source_object_id=str(version.id),
        source_object_version="caller-hint-is-not-authority",
        created_by="pytest",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _runtime_profile() -> AgentRuntimeProfile:
    return AgentRuntimeProfile(
        profile_key="f1-e2-hosted-reasoning",
        runtime_class=RuntimeClass.HOSTED_API,
        adapter_key="deepseek-adapter",
        provider_key="deepseek",
        model_key="deepseek-reasoner",
        technical_capabilities=("reasoning", "structured_output"),
        available_tools=("official_source.search", "shell"),
        independence_group="deepseek",
        profile_version=1,
        enabled=True,
    )


def _authority(*, autonomy: AutonomyLevel = AutonomyLevel.A5) -> CapabilityAuthority:
    return CapabilityAuthority(
        tenant_key="tenant-a",
        actor_id="austria_mobility_specialist",
        capability=GOVERNED_ELIGIBILITY_CAPABILITY,
        allowed_action_types=frozenset({MaterialActionType.ELIGIBILITY_TRANSITION}),
        max_risk_tier=RiskTier.R3,
        autonomy_level=autonomy,
        allowed_scopes=frozenset({"austria:visa"}),
    )


def _safe_output(
    graph: dict[str, object],
    *,
    proposed_state: str = "potentially_eligible",
    confidence: float = 0.83,
) -> str:
    return json.dumps(
        {
            "proposed_state": proposed_state,
            "evidence_basis": [f"evidence:{graph['evidence'].id}"],
            "rule_basis": [f"verified_rule:{graph['rule'].id}"],
            "rationale": "The governed case facts support a bounded proposal that must still be independently verified.",
            "confidence": confidence,
        },
        sort_keys=True,
    )


def _proposal(
    session: Session,
    *,
    nationality: str | None = "india",
    job_offer_status: str | None = "confirmed",
    completeness_score: float = 90.0,
    readiness_stage: str = "evidence_ready",
    evidence_role: str = "core_route",
    eligibility_criteria: dict[str, Any] | None = None,
    proposed_state: str = "potentially_eligible",
    confidence: float = 0.83,
    autonomy: AutonomyLevel = AutonomyLevel.A5,
):
    _position(session)
    lead, profile = _case(
        session,
        nationality=nationality,
        job_offer_status=job_offer_status,
        completeness_score=completeness_score,
        readiness_stage=readiness_stage,
    )
    graph = _authority_graph(
        session,
        evidence_role=evidence_role,
        eligibility_criteria=eligibility_criteria,
    )
    work = _work(session, lead=lead, profile=profile, version=graph["version"])
    provider = FakeProvider(
        _safe_output(graph, proposed_state=proposed_state, confidence=confidence)
    )
    result = governed_eligibility_transition_intent(
        session,
        tenant_key="tenant-a",
        position_key="austria_mobility_specialist",
        work_item_id=work.id,
        runtime_profile=_runtime_profile(),
        authority=_authority(autonomy=autonomy),
        provider=provider,
        idempotency_key=f"f1-source-proposal-{uuid4()}",
    )
    return result, lead, profile, graph, work, provider


def _gate(result, code: DecisionReadinessGateCode):
    return next(gate for gate in result.gates if gate.code is code)


def test_f1_ready_proposal_advances_only_to_independent_verification_and_is_read_only(
    db_session: Session,
) -> None:
    proposal, _, profile, graph, _, provider = _proposal(db_session, confidence=0.01)
    before_activities = len(list(db_session.exec(select(OrganizationActivity)).all()))
    before_assessments = len(list(db_session.exec(select(EligibilityAssessment)).all()))

    first = assess_eligibility_decision_readiness(db_session, proposal=proposal)
    second = assess_eligibility_decision_readiness(db_session, proposal=proposal)

    assert first.schema_version == DECISION_READINESS_SCHEMA_VERSION
    assert first.state is DecisionReadinessState.READY_FOR_INDEPENDENT_VERIFICATION
    assert first.ready_for_independent_verification is True
    assert first.independent_verification_required is True
    assert first.authorization_effect is False
    assert first.canonical_commit_allowed is False
    assert first.readiness_score == 1.0
    assert all(gate.status is DecisionReadinessGateStatus.PASS for gate in first.gates)
    assert first.profile_id == profile.id
    assert first.pathway_version_id == graph["version"].id
    assert len(first.readiness_fingerprint) == 64
    assert first.readiness_fingerprint == second.readiness_fingerprint
    assert len(provider.calls) == 1
    assert len(list(db_session.exec(select(OrganizationActivity)).all())) == before_activities
    assert len(list(db_session.exec(select(EligibilityAssessment)).all())) == before_assessments


def test_f1_does_not_confuse_profile_completeness_with_material_decision_readiness(
    db_session: Session,
) -> None:
    proposal, _, profile, _, _, _ = _proposal(
        db_session,
        completeness_score=45.0,
        readiness_stage="developing",
    )

    result = assess_eligibility_decision_readiness(db_session, proposal=proposal)

    assert profile.completeness_score == 45.0
    assert profile.readiness_stage == "developing"
    assert result.state is DecisionReadinessState.READY_FOR_INDEPENDENT_VERIFICATION
    assert result.readiness_score == 1.0


@pytest.mark.parametrize("proposed_state", ["needs_documents", "insufficient_information"])
def test_f1_non_actionable_e2_proposal_is_not_ready(
    db_session: Session,
    proposed_state: str,
) -> None:
    proposal, *_ = _proposal(db_session, proposed_state=proposed_state)

    result = assess_eligibility_decision_readiness(db_session, proposal=proposal)

    assert result.state is DecisionReadinessState.NOT_READY
    assert result.ready_for_independent_verification is False
    assert _gate(result, DecisionReadinessGateCode.PROPOSAL_STATE_ACTIONABLE).status is DecisionReadinessGateStatus.FAIL


def test_f1_missing_nationality_routes_to_human_input_without_model_or_authorization_override(
    db_session: Session,
) -> None:
    proposal, *_ = _proposal(db_session, nationality=None, confidence=1.0)

    result = assess_eligibility_decision_readiness(db_session, proposal=proposal)

    assert proposal.intent.confidence == 1.0
    assert result.state is DecisionReadinessState.HUMAN_INPUT_REQUIRED
    assert result.authorization_effect is False
    gate = _gate(result, DecisionReadinessGateCode.REQUIRED_CASE_FACTS_PRESENT)
    assert gate.status is DecisionReadinessGateStatus.HUMAN_REQUIRED
    assert "nationality" in gate.detail


def test_f1_known_missing_material_job_offer_precondition_is_not_ready(db_session: Session) -> None:
    proposal, *_ = _proposal(
        db_session,
        job_offer_status="none",
        eligibility_criteria={"binding_job_offer_in_austria_required": True},
    )

    result = assess_eligibility_decision_readiness(db_session, proposal=proposal)

    assert result.state is DecisionReadinessState.NOT_READY
    gate = _gate(result, DecisionReadinessGateCode.MATERIAL_FACT_PRECONDITIONS)
    assert gate.status is DecisionReadinessGateStatus.FAIL
    assert "requires a binding Austrian job offer" in gate.detail


def test_f1_unresolved_material_job_offer_precondition_requires_human_input(db_session: Session) -> None:
    proposal, *_ = _proposal(
        db_session,
        job_offer_status=None,
        eligibility_criteria={"binding_job_offer_in_austria_required": True},
    )

    result = assess_eligibility_decision_readiness(db_session, proposal=proposal)

    assert result.state is DecisionReadinessState.HUMAN_INPUT_REQUIRED
    assert _gate(result, DecisionReadinessGateCode.MATERIAL_FACT_PRECONDITIONS).status is DecisionReadinessGateStatus.HUMAN_REQUIRED


def test_f1_reuses_pathway_publication_integrity_and_blocks_degraded_noncore_evidence(
    db_session: Session,
) -> None:
    proposal, *_ = _proposal(db_session, evidence_role="supporting")

    result = assess_eligibility_decision_readiness(db_session, proposal=proposal)

    assert result.state is DecisionReadinessState.NOT_READY
    gate = _gate(result, DecisionReadinessGateCode.PATHWAY_PUBLICATION_INTEGRITY)
    assert gate.status is DecisionReadinessGateStatus.FAIL
    assert "approved source certification" in gate.detail


def test_f1_rejects_blocked_e2_attempt_instead_of_reclassifying_authority(db_session: Session) -> None:
    proposal, *_ = _proposal(db_session, autonomy=AutonomyLevel.A0)
    assert proposal.evaluation.outcome is GatewayOutcome.BLOCK

    with pytest.raises(DecisionReadinessIntegrityError, match="REVIEW_REQUIRED"):
        assess_eligibility_decision_readiness(db_session, proposal=proposal)


def test_f1_accepts_only_proven_fenced_e2_runtime_terminal_drift(
    db_session: Session,
) -> None:
    _position(db_session)
    lead, profile = _case(db_session)
    graph = _authority_graph(db_session)
    work = _work(db_session, lead=lead, profile=profile, version=graph["version"])
    provider = FakeProvider(_safe_output(graph))

    wrapped = execute_fenced_governed_eligibility_transition_intent(
        db_session,
        tenant_key="tenant-a",
        position_key="austria_mobility_specialist",
        work_item_id=work.id,
        runtime_profile=_runtime_profile(),
        authority=_authority(),
        provider=provider,
        idempotency_key=f"f1-fenced-source-{uuid4()}",
    )

    persisted_work = db_session.get(OrganizationalWorkItem, work.id)
    assert persisted_work is not None
    assert persisted_work.status == "completed"
    readiness = assess_eligibility_decision_readiness(
        db_session,
        proposal=wrapped.result,
    )
    assert readiness.state is DecisionReadinessState.READY_FOR_INDEPENDENT_VERIFICATION
    assert readiness.context_hash != wrapped.result.context.context_hash


def test_f1_rejects_unfenced_work_completion_as_context_drift(
    db_session: Session,
) -> None:
    proposal, _, _, _, work, _ = _proposal(db_session)
    work.status = "completed"
    work.completed_at = now_utc()
    work.updated_at = now_utc() + timedelta(seconds=1)
    db_session.add(work)
    db_session.commit()

    with pytest.raises(DecisionReadinessIntegrityError, match="ContextBundle changed"):
        assess_eligibility_decision_readiness(db_session, proposal=proposal)


def test_f1_rejects_case_change_after_e2_acceptance(db_session: Session) -> None:
    proposal, lead, *_ = _proposal(db_session)
    lead.job_offer_status = "none"
    lead.updated_at = now_utc() + timedelta(seconds=1)
    db_session.add(lead)
    db_session.commit()

    with pytest.raises(DecisionReadinessIntegrityError, match="ContextBundle changed"):
        assess_eligibility_decision_readiness(db_session, proposal=proposal)


def test_f1_rejects_forged_in_memory_intent_even_with_real_durable_attempt(db_session: Session) -> None:
    proposal, *_ = _proposal(db_session)
    forged_intent = replace(
        proposal.intent,
        proposed_state=EligibilityProposedState.POTENTIALLY_INELIGIBLE,
    )
    forged = replace(proposal, intent=forged_intent)

    with pytest.raises(DecisionReadinessIntegrityError, match="fingerprint"):
        assess_eligibility_decision_readiness(db_session, proposal=forged)


def test_f1_rejects_malformed_supported_material_criterion(db_session: Session) -> None:
    proposal, *_ = _proposal(
        db_session,
        eligibility_criteria={"binding_job_offer_in_austria_required": "yes"},
    )

    with pytest.raises(DecisionReadinessIntegrityError, match="must be a boolean"):
        assess_eligibility_decision_readiness(db_session, proposal=proposal)
