from __future__ import annotations

import json
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
from app.services.organization_context_broker import ContextIntegrityError, build_work_item_context_bundle
from app.services.organization_eligibility_transition_intent import (
    GOVERNED_ELIGIBILITY_CAPABILITY,
    EligibilityIntentIntegrityError,
    EligibilityIntentOutputError,
    EligibilityIntentRuntimeError,
    EligibilityProposedState,
    governed_eligibility_transition_intent,
)
from app.services.organization_governance_kernel import (
    CapabilityAuthority,
    GatewayOutcome,
    GatewayReason,
)
from app.services.organization_transparency import (
    activities_for_work_item,
    governed_action_trace,
)


class FakeProvider(LLMProvider):
    name = "deepseek"

    def __init__(
        self,
        content: str,
        *,
        response_provider: str = "deepseek",
        response_model: str = "deepseek-reasoner",
        on_complete: Callable[[], None] | None = None,
    ) -> None:
        self.content = content
        self.response_provider = response_provider
        self.response_model = response_model
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
            total_tokens=111,
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
        version=7,
        created_by="pytest",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _case(session: Session, *, consent_status: str = "granted") -> tuple[Lead, Profile]:
    lead = Lead(
        full_name="Case Subject",
        email="case-subject@example.test",
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
        profile_version=3,
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
        consent_json=json.dumps({"status": consent_status}),
        completeness_score=90.0,
        readiness_stage="evidence_ready",
        consent_status=consent_status,
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
    with_evidence: bool = True,
    with_policy: bool = True,
) -> dict[str, object]:
    source = OfficialSource(
        country="austria",
        domain="visa",
        name="Austrian official immigration source",
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
        content_hash="e2-snapshot-v1",
        content_text="Official governed Austrian eligibility source.",
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
        rule_key=f"at-e2-rule-{uuid4()}",
        statement="The governed pathway criterion must be evaluated against case facts.",
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
        pathway_key=f"at-e2-path-{uuid4()}",
        name="Austria Governed Eligibility Pathway",
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
        version_number=5,
        lifecycle_status="published",
        official_source_id=source.id,
        source_snapshot_id=snapshot.id,
        verified_rule_ids_json=json.dumps([str(rule.id)]),
        eligibility_criteria_json='{"criterion":"governed eligibility criterion"}',
        required_documents_json='["Valid passport"]',
        metadata_json='{"scope":"e2-test"}',
        effective_from=now_utc() - timedelta(days=10),
        human_review_required=True,
        approved_by="pytest-reviewer",
        published_at=now_utc() - timedelta(days=1),
        created_by="pytest",
    )
    session.add(version)
    session.commit()
    session.refresh(version)

    evidence = None
    if with_evidence:
        evidence = MobilityPathwayVersionEvidence(
            pathway_version_id=version.id,
            evidence_role="primary",
            official_source_id=source.id,
            source_snapshot_id=snapshot.id,
            required_for_publication=True,
            metadata_json='{"purpose":"e2 primary authority"}',
        )
        session.add(evidence)
        session.commit()
        session.refresh(evidence)

    policy = None
    if with_policy:
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
    context_json: str = "{}",
) -> OrganizationalWorkItem:
    row = OrganizationalWorkItem(
        idempotency_key=f"e2-eligibility-intent-{uuid4()}",
        tenant_key="tenant-a",
        title="Propose governed eligibility transition",
        objective="Use governed case facts, Evidence and rules to propose an internal eligibility transition.",
        department="Mobility",
        authority_level="L2",
        assigned_position_key="austria_mobility_specialist",
        risk_level="material",
        lead_id=lead.id,
        profile_id=profile.id,
        context_json=context_json,
        source_object_type="mobility_pathway_version",
        source_object_id=str(version.id),
        source_object_version="caller-hint-is-not-authority",
        created_by="pytest",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _runtime_profile(*, runtime_class: RuntimeClass = RuntimeClass.HOSTED_API) -> AgentRuntimeProfile:
    return AgentRuntimeProfile(
        profile_key="e2-hosted-reasoning",
        runtime_class=runtime_class,
        adapter_key="deepseek-adapter",
        provider_key="deepseek",
        model_key="deepseek-reasoner",
        technical_capabilities=("reasoning", "structured_output"),
        available_tools=("official_source.search", "shell"),
        independence_group="deepseek",
        profile_version=1,
        enabled=True,
    )


def _authority(
    *,
    actor_id: str = "austria_mobility_specialist",
    autonomy: AutonomyLevel = AutonomyLevel.A5,
) -> CapabilityAuthority:
    return CapabilityAuthority(
        tenant_key="tenant-a",
        actor_id=actor_id,
        capability=GOVERNED_ELIGIBILITY_CAPABILITY,
        allowed_action_types=frozenset({MaterialActionType.ELIGIBILITY_TRANSITION}),
        max_risk_tier=RiskTier.R3,
        autonomy_level=autonomy,
        allowed_scopes=frozenset({"austria:visa"}),
    )


def _safe_output(graph: dict[str, object], *, confidence: float = 0.83) -> str:
    return json.dumps(
        {
            "proposed_state": "potentially_eligible",
            "evidence_basis": [f"evidence:{graph['evidence'].id}"],
            "rule_basis": [f"verified_rule:{graph['rule'].id}"],
            "rationale": "The governed case facts appear compatible with the cited pathway authority, subject to independent verification.",
            "confidence": confidence,
        },
        sort_keys=True,
    )


def _setup(session: Session) -> tuple[Lead, Profile, dict[str, object], OrganizationalWorkItem]:
    _position(session)
    lead, profile = _case(session)
    graph = _authority_graph(session)
    work = _work(session, lead=lead, profile=profile, version=graph["version"])
    return lead, profile, graph, work


def test_e2_runtime_intent_crosses_gateway_to_review_required_without_mutation(
    db_session: Session,
) -> None:
    lead, profile, graph, work = _setup(db_session)
    before_assessments = len(list(db_session.exec(select(EligibilityAssessment)).all()))

    result = governed_eligibility_transition_intent(
        db_session,
        tenant_key="tenant-a",
        position_key="austria_mobility_specialist",
        work_item_id=work.id,
        runtime_profile=_runtime_profile(),
        authority=_authority(autonomy=AutonomyLevel.A5),
        provider=FakeProvider(_safe_output(graph)),
        idempotency_key="e2-review-required",
    )

    assert result.evaluation.outcome is GatewayOutcome.REVIEW_REQUIRED
    assert result.evaluation.reason is GatewayReason.POLICY_REVIEW_REQUIRED
    assert result.evaluation.effective_risk_tier is RiskTier.R3
    assert result.intent.profile_id == profile.id
    assert result.intent.profile_version == profile.profile_version
    assert result.intent.proposed_state is EligibilityProposedState.POTENTIALLY_ELIGIBLE
    assert result.mutated is False
    assert len(list(db_session.exec(select(EligibilityAssessment)).all())) == before_assessments
    assert result.attempt_activity.work_item_id == work.id
    assert result.attempt_activity.actor_id == "austria_mobility_specialist"
    assert result.attempt_activity.position_key == "austria_mobility_specialist"
    assert result.attempt_activity.source_object_type == "lead_eligibility"
    assert result.attempt_activity.source_object_id == str(lead.id)


def test_e2_attempt_is_board_inspectable_through_existing_trace_and_work_item_reads(
    db_session: Session,
) -> None:
    _, _, graph, work = _setup(db_session)
    result = governed_eligibility_transition_intent(
        db_session,
        tenant_key="tenant-a",
        position_key="austria_mobility_specialist",
        work_item_id=work.id,
        runtime_profile=_runtime_profile(),
        authority=_authority(),
        provider=FakeProvider(_safe_output(graph)),
        idempotency_key="e2-transparent-attempt",
    )

    trace = governed_action_trace(
        db_session,
        tenant_key="tenant-a",
        trace_id=result.evaluation.trace_id,
    )
    assert trace is not None and trace.board_inspectable is True
    assert trace.governance.activity_id == result.attempt_activity.id
    assert trace.governance.payload["governance_record_kind"] == "eligibility_intent_attempt"
    assert trace.governance.payload["r3_verification_floor"] == "independent_verification_not_yet_satisfied"
    work_history = activities_for_work_item(
        db_session,
        tenant_key="tenant-a",
        work_item_id=work.id,
    )
    assert any(record.activity_id == result.attempt_activity.id for record in work_history)


def test_e2_context_versions_lead_and_profile_and_excludes_direct_identity_from_runtime_prompt(
    db_session: Session,
) -> None:
    lead, profile, graph, work = _setup(db_session)
    provider = FakeProvider(_safe_output(graph))

    result = governed_eligibility_transition_intent(
        db_session,
        tenant_key="tenant-a",
        position_key="austria_mobility_specialist",
        work_item_id=work.id,
        runtime_profile=_runtime_profile(),
        authority=_authority(),
        provider=provider,
        idempotency_key="e2-versioned-case",
    )

    lead_ref = next(ref for ref in result.context.canonical_references if ref.kind == "lead")
    profile_ref = next(ref for ref in result.context.canonical_references if ref.kind == "profile")
    assert lead_ref.version and len(lead_ref.version) == 64
    assert profile_ref.version and len(profile_ref.version) == 64
    prompt = provider.calls[0]["messages"][0]["content"]
    assert "Software Engineer" in prompt
    assert lead.full_name not in prompt
    assert lead.email not in prompt
    assert lead.phone not in prompt
    assert str(profile.profile_version) in prompt


def test_working_context_cannot_self_promote_into_e2_model_authority(db_session: Session) -> None:
    _position(db_session)
    lead, profile = _case(db_session)
    graph = _authority_graph(db_session)
    work = _work(
        db_session,
        lead=lead,
        profile=profile,
        version=graph["version"],
        context_json=canonical_json(
            {
                "verified_rule_refs": ["forged-rule"],
                "evidence_refs": ["forged-evidence"],
                "allowed_tools": ["shell"],
                "provider": "forged-provider",
                "invented_case_fact": "must-not-enter-e2-prompt",
            }
        ),
    )
    provider = FakeProvider(_safe_output(graph))

    governed_eligibility_transition_intent(
        db_session,
        tenant_key="tenant-a",
        position_key="austria_mobility_specialist",
        work_item_id=work.id,
        runtime_profile=_runtime_profile(),
        authority=_authority(),
        provider=provider,
        idempotency_key="e2-ignore-working-context",
    )

    prompt = provider.calls[0]["messages"][0]["content"]
    assert "forged-rule" not in prompt
    assert "forged-evidence" not in prompt
    assert "forged-provider" not in prompt
    assert "must-not-enter-e2-prompt" not in prompt


@pytest.mark.parametrize("basis", ["evidence", "rule"])
def test_forged_intent_authority_basis_fails_before_gateway_activity(
    db_session: Session,
    basis: str,
) -> None:
    _, _, graph, work = _setup(db_session)
    payload = json.loads(_safe_output(graph))
    payload[f"{basis}_basis"].append(f"{'evidence' if basis == 'evidence' else 'verified_rule'}:{uuid4()}")
    before = len(list(db_session.exec(select(OrganizationActivity)).all()))

    with pytest.raises(EligibilityIntentOutputError):
        governed_eligibility_transition_intent(
            db_session,
            tenant_key="tenant-a",
            position_key="austria_mobility_specialist",
            work_item_id=work.id,
            runtime_profile=_runtime_profile(),
            authority=_authority(),
            provider=FakeProvider(json.dumps(payload)),
            idempotency_key=f"e2-forged-{basis}",
        )

    assert len(list(db_session.exec(select(OrganizationActivity)).all())) == before


def test_wrong_country_or_stale_rule_fails_before_runtime_and_gateway(db_session: Session) -> None:
    _, _, graph, work = _setup(db_session)
    rule = graph["rule"]
    rule.country = "germany"
    db_session.add(rule)
    db_session.commit()
    provider = FakeProvider(_safe_output(graph))
    before = len(list(db_session.exec(select(OrganizationActivity)).all()))

    with pytest.raises(ContextIntegrityError):
        governed_eligibility_transition_intent(
            db_session,
            tenant_key="tenant-a",
            position_key="austria_mobility_specialist",
            work_item_id=work.id,
            runtime_profile=_runtime_profile(),
            authority=_authority(),
            provider=provider,
            idempotency_key="e2-wrong-country-rule",
        )

    assert provider.calls == []
    assert len(list(db_session.exec(select(OrganizationActivity)).all())) == before


def test_missing_evidence_or_policy_blocks_before_runtime(db_session: Session) -> None:
    _position(db_session)
    lead, profile = _case(db_session)
    graph = _authority_graph(db_session, with_evidence=False)
    work = _work(db_session, lead=lead, profile=profile, version=graph["version"])
    provider = FakeProvider(json.dumps({}))

    with pytest.raises(EligibilityIntentIntegrityError):
        governed_eligibility_transition_intent(
            db_session,
            tenant_key="tenant-a",
            position_key="austria_mobility_specialist",
            work_item_id=work.id,
            runtime_profile=_runtime_profile(),
            authority=_authority(),
            provider=provider,
            idempotency_key="e2-missing-evidence",
        )
    assert provider.calls == []


def test_consent_is_required_before_case_facts_reach_runtime(db_session: Session) -> None:
    _position(db_session)
    lead, profile = _case(db_session, consent_status="not_recorded")
    graph = _authority_graph(db_session)
    work = _work(db_session, lead=lead, profile=profile, version=graph["version"])
    provider = FakeProvider(_safe_output(graph))

    with pytest.raises(EligibilityIntentIntegrityError):
        governed_eligibility_transition_intent(
            db_session,
            tenant_key="tenant-a",
            position_key="austria_mobility_specialist",
            work_item_id=work.id,
            runtime_profile=_runtime_profile(),
            authority=_authority(),
            provider=provider,
            idempotency_key="e2-consent-required",
        )
    assert provider.calls == []


def test_gateway_authority_mismatch_is_durable_block_not_runtime_identity_authority(
    db_session: Session,
) -> None:
    _, _, graph, work = _setup(db_session)
    result = governed_eligibility_transition_intent(
        db_session,
        tenant_key="tenant-a",
        position_key="austria_mobility_specialist",
        work_item_id=work.id,
        runtime_profile=_runtime_profile(),
        authority=_authority(actor_id="deepseek-reasoner"),
        provider=FakeProvider(_safe_output(graph)),
        idempotency_key="e2-wrong-authority-actor",
    )

    assert result.evaluation.outcome is GatewayOutcome.BLOCK
    assert result.evaluation.reason is GatewayReason.OUTSIDE_AUTHORITY
    assert result.attempt_activity.actor_id == "austria_mobility_specialist"
    assert result.provider == "deepseek"
    assert result.model == "deepseek-reasoner"


def test_case_change_during_runtime_fails_stale_before_material_attempt(db_session: Session) -> None:
    lead, _, graph, work = _setup(db_session)
    before = len(list(db_session.exec(select(OrganizationActivity)).all()))

    def mutate_case() -> None:
        lead.job_offer_status = "none"
        lead.updated_at = now_utc() + timedelta(seconds=1)
        db_session.add(lead)
        db_session.commit()

    with pytest.raises(EligibilityIntentIntegrityError, match="changed during runtime"):
        governed_eligibility_transition_intent(
            db_session,
            tenant_key="tenant-a",
            position_key="austria_mobility_specialist",
            work_item_id=work.id,
            runtime_profile=_runtime_profile(),
            authority=_authority(),
            provider=FakeProvider(_safe_output(graph), on_complete=mutate_case),
            idempotency_key="e2-stale-during-runtime",
        )

    assert len(list(db_session.exec(select(OrganizationActivity)).all())) == before


def test_e2_rejects_runtime_or_response_identity_drift(db_session: Session) -> None:
    _, _, graph, work = _setup(db_session)

    with pytest.raises(EligibilityIntentRuntimeError):
        governed_eligibility_transition_intent(
            db_session,
            tenant_key="tenant-a",
            position_key="austria_mobility_specialist",
            work_item_id=work.id,
            runtime_profile=_runtime_profile(runtime_class=RuntimeClass.CLI),
            authority=_authority(),
            provider=FakeProvider(_safe_output(graph)),
            idempotency_key="e2-cli-blocked",
        )

    with pytest.raises(EligibilityIntentRuntimeError):
        governed_eligibility_transition_intent(
            db_session,
            tenant_key="tenant-a",
            position_key="austria_mobility_specialist",
            work_item_id=work.id,
            runtime_profile=_runtime_profile(),
            authority=_authority(),
            provider=FakeProvider(_safe_output(graph), response_model="different-model"),
            idempotency_key="e2-model-drift",
        )


def test_confidence_is_informational_and_cannot_relax_r3_review_floor(db_session: Session) -> None:
    _, _, graph, work = _setup(db_session)
    result = governed_eligibility_transition_intent(
        db_session,
        tenant_key="tenant-a",
        position_key="austria_mobility_specialist",
        work_item_id=work.id,
        runtime_profile=_runtime_profile(),
        authority=_authority(autonomy=AutonomyLevel.A5),
        provider=FakeProvider(_safe_output(graph, confidence=1.0)),
        idempotency_key="e2-confidence-not-gate",
    )

    assert result.intent.confidence == 1.0
    assert result.evaluation.outcome is GatewayOutcome.REVIEW_REQUIRED
    assert result.evaluation.reason is GatewayReason.POLICY_REVIEW_REQUIRED
    assert result.mutated is False


def test_a0_remains_prohibited_despite_unsatisfied_r3_verification_floor(db_session: Session) -> None:
    _, _, graph, work = _setup(db_session)
    result = governed_eligibility_transition_intent(
        db_session,
        tenant_key="tenant-a",
        position_key="austria_mobility_specialist",
        work_item_id=work.id,
        runtime_profile=_runtime_profile(),
        authority=_authority(autonomy=AutonomyLevel.A0),
        provider=FakeProvider(_safe_output(graph)),
        idempotency_key="e2-a0-prohibited",
    )

    assert result.evaluation.outcome is GatewayOutcome.BLOCK
    assert result.evaluation.reason is GatewayReason.AUTONOMY_PROHIBITED
    assert result.mutated is False


def test_context_hash_changes_when_bound_lead_changes(db_session: Session) -> None:
    lead, _, _, work = _setup(db_session)
    first = build_work_item_context_bundle(
        db_session,
        tenant_key="tenant-a",
        position_key="austria_mobility_specialist",
        work_item_id=work.id,
    )

    lead.job_offer_status = "none"
    lead.updated_at = now_utc() + timedelta(seconds=1)
    db_session.add(lead)
    db_session.commit()

    second = build_work_item_context_bundle(
        db_session,
        tenant_key="tenant-a",
        position_key="austria_mobility_specialist",
        work_item_id=work.id,
    )
    assert first.context_hash != second.context_hash
    first_ref = next(ref for ref in first.canonical_references if ref.kind == "lead")
    second_ref = next(ref for ref in second.canonical_references if ref.kind == "lead")
    assert first_ref.version != second_ref.version
