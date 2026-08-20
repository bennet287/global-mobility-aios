from __future__ import annotations

import json
from dataclasses import replace
from datetime import timedelta
from typing import Any, Callable
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
    DecisionReadinessState,
    assess_eligibility_decision_readiness,
)
from app.services.organization_eligibility_transition_intent import (
    GOVERNED_ELIGIBILITY_CAPABILITY,
    governed_eligibility_transition_intent,
)
from app.services.organization_governance_kernel import CapabilityAuthority
from app.services.organization_independent_eligibility_verification import (
    INDEPENDENT_ELIGIBILITY_VERIFICATION_SCHEMA_VERSION,
    IndependentEligibilityVerificationIntegrityError,
    IndependentEligibilityVerificationOutputError,
    IndependentEligibilityVerificationRuntimeError,
    IndependentEligibilityConclusion,
    IndependentVerificationDisposition,
    verify_eligibility_proposal_independently,
)
from app.services.organization_transparency import activities_for_work_item


class FakeProvider(LLMProvider):
    def __init__(
        self,
        *,
        name: str,
        model: str,
        content: str,
        response_provider: str | None = None,
        response_model: str | None = None,
        on_complete: Callable[[], None] | None = None,
    ) -> None:
        self.name = name
        self.model = model
        self.content = content
        self.response_provider = response_provider or name
        self.response_model = response_model or model
        self.on_complete = on_complete
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
        if self.on_complete is not None:
            self.on_complete()
        return LLMResponse(
            content=self.content,
            provider=self.response_provider,
            model=self.response_model,
            finish_reason="stop",
            total_tokens=144,
        )


def _position(
    session: Session,
    *,
    position_key: str,
    title: str,
    version: int,
) -> OrganizationPosition:
    row = OrganizationPosition(
        position_key=position_key,
        title=title,
        department="Mobility",
        reports_to_position_key="mobility_operations_lead",
        role_card_name=position_key,
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
        version=version,
        created_by="pytest",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _case(session: Session) -> tuple[Lead, Profile]:
    lead = Lead(
        full_name="Independent Verification Subject",
        email="verification@example.test",
        phone="+4300000000",
        intent=LeadIntent.visa,
        target_country="austria",
        nationality="india",
        current_country="austria",
        occupation_title="Software Engineer",
        years_experience=5.0,
        job_offer_status="confirmed",
        qualification_recognition="recognized",
        german_level="B1",
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)

    profile = Profile(
        lead_id=lead.id,
        profile_type="universal_mobility",
        profile_version=5,
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
        completeness_score=90.0,
        readiness_stage="evidence_ready",
        consent_status="granted",
        activated_at=now_utc(),
        updated_by="pytest",
    )
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return lead, profile


def _authority_graph(session: Session) -> dict[str, object]:
    source = OfficialSource(
        country="austria",
        domain="visa",
        name="Austrian independent verification source",
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
        content_hash="g1-snapshot-v1",
        content_text=(
            "Official governed Austrian eligibility source. The route must be assessed "
            "against the published criteria and verified rules."
        ),
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
        rule_key=f"at-g1-rule-{uuid4()}",
        statement="The governed case must independently satisfy the published pathway criterion.",
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
        pathway_key=f"at-g1-path-{uuid4()}",
        name="Austria Independent Verification Pathway",
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
        version_number=7,
        lifecycle_status="published",
        official_source_id=source.id,
        source_snapshot_id=snapshot.id,
        verified_rule_ids_json=json.dumps([str(rule.id)]),
        eligibility_criteria_json="{}",
        required_documents_json='["Valid passport"]',
        metadata_json='{"scope":"g1-test"}',
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
        evidence_role="core_route",
        official_source_id=source.id,
        source_snapshot_id=snapshot.id,
        required_for_publication=True,
        metadata_json='{"purpose":"g1 core authority"}',
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
    position_key: str,
    lead: Lead,
    profile: Profile,
    version: MobilityPathwayVersion,
    title: str,
) -> OrganizationalWorkItem:
    row = OrganizationalWorkItem(
        idempotency_key=f"g1-work-{uuid4()}",
        tenant_key="tenant-a",
        title=title,
        objective="Use governed case facts, Evidence and rules for bounded eligibility work.",
        department="Mobility",
        authority_level="L2",
        assigned_position_key=position_key,
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


def _runtime(
    *,
    profile_key: str,
    provider_key: str,
    model_key: str,
    independence_group: str,
) -> AgentRuntimeProfile:
    return AgentRuntimeProfile(
        profile_key=profile_key,
        runtime_class=RuntimeClass.HOSTED_API,
        adapter_key=f"{provider_key}-adapter",
        provider_key=provider_key,
        model_key=model_key,
        technical_capabilities=("reasoning", "structured_output"),
        available_tools=("official_source.search", "document.read"),
        independence_group=independence_group,
        profile_version=1,
        enabled=True,
    )


def _authority() -> CapabilityAuthority:
    return CapabilityAuthority(
        tenant_key="tenant-a",
        actor_id="austria_mobility_specialist",
        capability=GOVERNED_ELIGIBILITY_CAPABILITY,
        allowed_action_types=frozenset({MaterialActionType.ELIGIBILITY_TRANSITION}),
        max_risk_tier=RiskTier.R3,
        autonomy_level=AutonomyLevel.A5,
        allowed_scopes=frozenset({"austria:visa"}),
    )


def _proposer_output(graph: dict[str, object], *, state: str = "potentially_eligible") -> str:
    return json.dumps(
        {
            "proposed_state": state,
            "evidence_basis": [f"evidence:{graph['evidence'].id}"],
            "rule_basis": [f"verified_rule:{graph['rule'].id}"],
            "rationale": "PROPOSER_SECRET_RATIONALE_7f4c8d independently verify this proposal.",
            "confidence": 0.731,
        },
        sort_keys=True,
    )


def _verifier_output(
    graph: dict[str, object],
    *,
    conclusion: str = "supports_potential_eligibility",
) -> str:
    return json.dumps(
        {
            "conclusion": conclusion,
            "evidence_basis": [f"evidence:{graph['evidence'].id}"],
            "rule_basis": [f"verified_rule:{graph['rule'].id}"],
            "findings": ["The independently reviewed governed Evidence and rule support this bounded conclusion."],
            "unresolved_questions": [],
        },
        sort_keys=True,
    )


def _setup(session: Session, *, proposer_state: str = "potentially_eligible"):
    _position(
        session,
        position_key="austria_mobility_specialist",
        title="Austria Mobility Specialist",
        version=10,
    )
    _position(
        session,
        position_key="austria_independent_verifier",
        title="Austria Independent Verifier",
        version=4,
    )
    lead, profile = _case(session)
    graph = _authority_graph(session)
    proposal_work = _work(
        session,
        position_key="austria_mobility_specialist",
        lead=lead,
        profile=profile,
        version=graph["version"],
        title="Propose governed eligibility transition",
    )
    verification_work = _work(
        session,
        position_key="austria_independent_verifier",
        lead=lead,
        profile=profile,
        version=graph["version"],
        title="Independently verify governed eligibility proposal",
    )
    proposer_provider = FakeProvider(
        name="deepseek",
        model="deepseek-reasoner",
        content=_proposer_output(graph, state=proposer_state),
    )
    proposal = governed_eligibility_transition_intent(
        session,
        tenant_key="tenant-a",
        position_key="austria_mobility_specialist",
        work_item_id=proposal_work.id,
        runtime_profile=_runtime(
            profile_key="proposer-runtime",
            provider_key="deepseek",
            model_key="deepseek-reasoner",
            independence_group="proposer-group",
        ),
        authority=_authority(),
        provider=proposer_provider,
        idempotency_key=f"g1-proposal-{uuid4()}",
    )
    readiness = assess_eligibility_decision_readiness(session, proposal=proposal)
    assert readiness.state is DecisionReadinessState.READY_FOR_INDEPENDENT_VERIFICATION
    return proposal, readiness, lead, profile, graph, proposal_work, verification_work, proposer_provider


def _verifier_runtime(
    *,
    provider_key: str = "openai",
    model_key: str = "gpt-verifier",
    independence_group: str = "independent-verifier-group",
) -> AgentRuntimeProfile:
    return _runtime(
        profile_key="independent-verifier-runtime",
        provider_key=provider_key,
        model_key=model_key,
        independence_group=independence_group,
    )


def test_g1_blind_agreement_is_durable_independent_but_has_no_authorization_effect(
    db_session: Session,
) -> None:
    proposal, readiness, _, _, graph, _, verification_work, _ = _setup(db_session)
    before_assessments = len(list(db_session.exec(select(EligibilityAssessment)).all()))
    before_activities = len(list(db_session.exec(select(OrganizationActivity)).all()))
    verifier = FakeProvider(
        name="openai",
        model="gpt-verifier",
        content=_verifier_output(graph),
    )

    result = verify_eligibility_proposal_independently(
        db_session,
        proposal=proposal,
        readiness=readiness,
        verification_work_item_id=verification_work.id,
        verifier_position_key="austria_independent_verifier",
        verifier_runtime_profile=_verifier_runtime(),
        provider=verifier,
        idempotency_key="g1-agreement",
    )

    assert result.schema_version == INDEPENDENT_ELIGIBILITY_VERIFICATION_SCHEMA_VERSION
    assert result.disposition is IndependentVerificationDisposition.AGREES
    assert result.draft.conclusion is IndependentEligibilityConclusion.SUPPORTS_POTENTIAL_ELIGIBILITY
    assert result.blind_review is True
    assert result.proposer_conclusion_exposed is False
    assert result.independent_verification_completed is True
    assert result.eligible_for_verification_floor_integration is True
    assert result.command_gateway_floor_satisfied is False
    assert result.authorization_effect is False
    assert result.canonical_commit_allowed is False
    assert result.verifier_context.position.position_key == "austria_independent_verifier"
    assert result.verifier_runtime_binding.independence_group == "independent-verifier-group"
    assert result.verifier_runtime_binding.independence_group != proposal.runtime_binding.independence_group
    assert len(result.verification_fingerprint) == 64
    assert result.verification_activity.causation_activity_id == proposal.attempt_activity.id
    assert result.verification_activity.activity_class.value == "material"
    assert len(list(db_session.exec(select(OrganizationActivity)).all())) == before_activities + 1
    assert len(list(db_session.exec(select(EligibilityAssessment)).all())) == before_assessments

    prompt = verifier.calls[0]["messages"][0]["content"]
    assert proposal.intent.proposed_state.value not in prompt
    assert proposal.intent.rationale not in prompt
    assert "PROPOSER_SECRET_RATIONALE_7f4c8d" not in prompt
    assert '"confidence":0.731' not in prompt
    assert "Independent Verification Subject" not in prompt
    assert "verification@example.test" not in prompt
    assert "+4300000000" not in prompt


def test_g1_disagreement_and_insufficient_basis_remain_non_authorizing(db_session: Session) -> None:
    for conclusion, expected in (
        ("supports_potential_ineligibility", IndependentVerificationDisposition.DISAGREES),
        ("insufficient_basis", IndependentVerificationDisposition.INSUFFICIENT_BASIS),
    ):
        proposal, readiness, _, _, graph, _, verification_work, _ = _setup(db_session)
        result = verify_eligibility_proposal_independently(
            db_session,
            proposal=proposal,
            readiness=readiness,
            verification_work_item_id=verification_work.id,
            verifier_position_key="austria_independent_verifier",
            verifier_runtime_profile=_verifier_runtime(),
            provider=FakeProvider(
                name="openai",
                model="gpt-verifier",
                content=_verifier_output(graph, conclusion=conclusion),
            ),
            idempotency_key=f"g1-{conclusion}-{uuid4()}",
        )
        assert result.disposition is expected
        assert result.eligible_for_verification_floor_integration is False
        assert result.command_gateway_floor_satisfied is False
        assert result.authorization_effect is False


def test_g1_requires_separate_verifier_employee_and_work_item(db_session: Session) -> None:
    proposal, readiness, _, _, graph, proposal_work, _, _ = _setup(db_session)
    provider = FakeProvider(name="openai", model="gpt-verifier", content=_verifier_output(graph))

    with pytest.raises(IndependentEligibilityVerificationIntegrityError):
        verify_eligibility_proposal_independently(
            db_session,
            proposal=proposal,
            readiness=readiness,
            verification_work_item_id=proposal_work.id,
            verifier_position_key="austria_mobility_specialist",
            verifier_runtime_profile=_verifier_runtime(),
            provider=provider,
            idempotency_key="g1-same-work",
        )
    assert provider.calls == []


@pytest.mark.parametrize(
    "provider_key,model_key,independence_group",
    [
        ("openai", "gpt-verifier", "proposer-group"),
        ("deepseek", "deepseek-reasoner", "different-metadata-group"),
    ],
)
def test_g1_rejects_runtime_that_is_not_meaningfully_independent(
    db_session: Session,
    provider_key: str,
    model_key: str,
    independence_group: str,
) -> None:
    proposal, readiness, _, _, graph, _, verification_work, _ = _setup(db_session)
    provider = FakeProvider(name=provider_key, model=model_key, content=_verifier_output(graph))

    with pytest.raises(IndependentEligibilityVerificationIntegrityError):
        verify_eligibility_proposal_independently(
            db_session,
            proposal=proposal,
            readiness=readiness,
            verification_work_item_id=verification_work.id,
            verifier_position_key="austria_independent_verifier",
            verifier_runtime_profile=_verifier_runtime(
                provider_key=provider_key,
                model_key=model_key,
                independence_group=independence_group,
            ),
            provider=provider,
            idempotency_key=f"g1-not-independent-{uuid4()}",
        )
    assert provider.calls == []


def test_g1_rejects_verification_work_item_bound_to_different_case(db_session: Session) -> None:
    proposal, readiness, _, profile, graph, _, _, _ = _setup(db_session)
    other_lead = Lead(
        full_name="Other Case",
        intent=LeadIntent.visa,
        target_country="austria",
    )
    db_session.add(other_lead)
    db_session.commit()
    db_session.refresh(other_lead)
    bad_work = _work(
        db_session,
        position_key="austria_independent_verifier",
        lead=other_lead,
        profile=profile,
        version=graph["version"],
        title="Wrong case verification",
    )
    provider = FakeProvider(name="openai", model="gpt-verifier", content=_verifier_output(graph))

    with pytest.raises(IndependentEligibilityVerificationIntegrityError):
        verify_eligibility_proposal_independently(
            db_session,
            proposal=proposal,
            readiness=readiness,
            verification_work_item_id=bad_work.id,
            verifier_position_key="austria_independent_verifier",
            verifier_runtime_profile=_verifier_runtime(),
            provider=provider,
            idempotency_key="g1-wrong-case",
        )
    assert provider.calls == []


def test_g1_rejects_forged_or_nonready_readiness(db_session: Session) -> None:
    proposal, readiness, _, _, graph, _, verification_work, _ = _setup(db_session)
    provider = FakeProvider(name="openai", model="gpt-verifier", content=_verifier_output(graph))
    forged = replace(readiness, readiness_fingerprint="0" * 64)

    with pytest.raises(IndependentEligibilityVerificationIntegrityError, match="Decision Readiness changed"):
        verify_eligibility_proposal_independently(
            db_session,
            proposal=proposal,
            readiness=forged,
            verification_work_item_id=verification_work.id,
            verifier_position_key="austria_independent_verifier",
            verifier_runtime_profile=_verifier_runtime(),
            provider=provider,
            idempotency_key="g1-forged-readiness",
        )
    assert provider.calls == []


def test_g1_forged_verifier_authority_citation_fails_without_verification_activity(
    db_session: Session,
) -> None:
    proposal, readiness, _, _, graph, _, verification_work, _ = _setup(db_session)
    payload = json.loads(_verifier_output(graph))
    payload["rule_basis"].append(f"verified_rule:{uuid4()}")
    provider = FakeProvider(name="openai", model="gpt-verifier", content=json.dumps(payload))
    before = len(list(db_session.exec(select(OrganizationActivity)).all()))

    with pytest.raises(IndependentEligibilityVerificationOutputError):
        verify_eligibility_proposal_independently(
            db_session,
            proposal=proposal,
            readiness=readiness,
            verification_work_item_id=verification_work.id,
            verifier_position_key="austria_independent_verifier",
            verifier_runtime_profile=_verifier_runtime(),
            provider=provider,
            idempotency_key="g1-forged-rule",
        )
    assert len(list(db_session.exec(select(OrganizationActivity)).all())) == before


def test_g1_case_change_during_verifier_runtime_fails_before_verification_activity(
    db_session: Session,
) -> None:
    proposal, readiness, lead, _, graph, _, verification_work, _ = _setup(db_session)
    before = len(list(db_session.exec(select(OrganizationActivity)).all()))

    def mutate_case() -> None:
        lead.job_offer_status = "none"
        lead.updated_at = now_utc() + timedelta(seconds=1)
        db_session.add(lead)
        db_session.commit()

    provider = FakeProvider(
        name="openai",
        model="gpt-verifier",
        content=_verifier_output(graph),
        on_complete=mutate_case,
    )
    with pytest.raises(IndependentEligibilityVerificationIntegrityError):
        verify_eligibility_proposal_independently(
            db_session,
            proposal=proposal,
            readiness=readiness,
            verification_work_item_id=verification_work.id,
            verifier_position_key="austria_independent_verifier",
            verifier_runtime_profile=_verifier_runtime(),
            provider=provider,
            idempotency_key="g1-stale-during-runtime",
        )
    assert len(list(db_session.exec(select(OrganizationActivity)).all())) == before


def test_g1_rejects_verifier_provider_or_model_identity_drift(db_session: Session) -> None:
    proposal, readiness, _, _, graph, _, verification_work, _ = _setup(db_session)

    for provider in (
        FakeProvider(
            name="openai",
            model="gpt-verifier",
            response_provider="other-provider",
            content=_verifier_output(graph),
        ),
        FakeProvider(
            name="openai",
            model="gpt-verifier",
            response_model="other-model",
            content=_verifier_output(graph),
        ),
    ):
        with pytest.raises(IndependentEligibilityVerificationRuntimeError):
            verify_eligibility_proposal_independently(
                db_session,
                proposal=proposal,
                readiness=readiness,
                verification_work_item_id=verification_work.id,
                verifier_position_key="austria_independent_verifier",
                verifier_runtime_profile=_verifier_runtime(),
                provider=provider,
                idempotency_key=f"g1-runtime-drift-{uuid4()}",
            )


def test_g1_verification_is_visible_in_verifier_work_item_transparency_and_linked_to_proposer(
    db_session: Session,
) -> None:
    proposal, readiness, _, _, graph, _, verification_work, _ = _setup(db_session)
    result = verify_eligibility_proposal_independently(
        db_session,
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
        idempotency_key="g1-transparency",
    )

    history = activities_for_work_item(
        db_session,
        tenant_key="tenant-a",
        work_item_id=verification_work.id,
    )
    record = next(item for item in history if item.activity_id == result.verification_activity.id)
    assert record.actor_id == "austria_independent_verifier"
    assert record.causation_activity_id == proposal.attempt_activity.id
    assert record.payload["proposer_trace_id"] == str(proposal.evaluation.trace_id)
    assert record.payload["blind_review"] is True
    assert record.payload["command_gateway_floor_satisfied"] is False
    assert record.payload["authorization_effect"] is False
