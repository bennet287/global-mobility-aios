from __future__ import annotations

import json
from datetime import timedelta
from typing import Any
from uuid import uuid4

import pytest
from sqlmodel import Session, select

from app.models.domain import (
    AgentRun,
    CountryPolicy,
    MobilityPathway,
    MobilityPathwayVersion,
    MobilityPathwayVersionEvidence,
    OfficialSource,
    OrganizationActivity,
    OrganizationPosition,
    OrganizationalWorkItem,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from app.services.llm_client import LLMProvider, LLMResponse
from app.services.organization_agent_runtime import AgentRuntimeProfile, RuntimeClass
from app.services.organization_command import canonical_json
from app.services.organization_mobility_pathway_brief import (
    MobilityPathwayBriefOutputError,
    MobilityPathwayBriefRuntimeError,
    prepare_governed_mobility_pathway_brief,
)


class FakeProvider(LLMProvider):
    name = "deepseek"

    def __init__(self, content: str, *, response_provider: str = "deepseek") -> None:
        self.content = content
        self.response_provider = response_provider
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
            provider=self.response_provider,
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
        version=6,
        created_by="pytest",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _authority_graph(session: Session, *, with_evidence: bool = True) -> dict[str, object]:
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
        content_hash="e1-snapshot-v1",
        content_text="Official Austrian pathway evidence for the governed E.1 brief.",
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
        rule_key=f"at-e1-rule-{uuid4()}",
        statement="Applicants must satisfy the governed pathway criterion in this test.",
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
        pathway_key=f"at-e1-path-{uuid4()}",
        name="Austria Governed Mobility Pathway",
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
        version_number=4,
        lifecycle_status="published",
        official_source_id=source.id,
        source_snapshot_id=snapshot.id,
        verified_rule_ids_json=json.dumps([str(rule.id)]),
        eligibility_criteria_json='{"criterion":"governed criterion"}',
        required_documents_json='["Valid passport"]',
        costs_json='{"currency":"EUR","amount":100}',
        processing_time_json='{"note":"Use only official published estimate when present"}',
        benefits_json='["Governed internal test benefit"]',
        risks_json='["Human verification remains required"]',
        metadata_json='{"scope":"e1-test"}',
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
            metadata_json='{"purpose":"e1 primary authority"}',
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
    version: MobilityPathwayVersion,
    *,
    context_json: str = "{}",
) -> OrganizationalWorkItem:
    row = OrganizationalWorkItem(
        idempotency_key=f"e1-pathway-brief-{uuid4()}",
        tenant_key="tenant-a",
        title="Prepare governed Austria pathway brief",
        objective="Prepare an internal evidence-grounded pathway brief for human review.",
        department="Mobility",
        authority_level="L2",
        assigned_position_key="austria_mobility_specialist",
        risk_level="routine",
        context_json=context_json,
        source_object_type="mobility_pathway_version",
        source_object_id=str(version.id),
        source_object_version="untrusted-caller-version",
        created_by="pytest",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _runtime_profile(*, runtime_class: RuntimeClass = RuntimeClass.HOSTED_API) -> AgentRuntimeProfile:
    return AgentRuntimeProfile(
        profile_key="e1-hosted-reasoning",
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


def _safe_output(graph: dict[str, object]) -> str:
    evidence = graph["evidence"]
    rule = graph["rule"]
    snapshot = graph["snapshot"]
    version = graph["version"]
    policy = graph["policy"]
    citations = [
        f"mobility_pathway_version:{version.id}",
        f"verified_rule:{rule.id}",
        f"source_snapshot:{snapshot.id}",
        f"country_policy:{policy.id}",
    ]
    if evidence is not None:
        citations.append(f"evidence:{evidence.id}")
    return json.dumps(
        {
            "summary": "Internal governed pathway brief prepared from the supplied authority set.",
            "key_requirements": ["Use the governed pathway criterion only."],
            "material_risks": ["Human verification remains required."],
            "evidence_gaps": [],
            "operator_questions": ["Is any additional case-specific Evidence required before assessment?"],
            "evidence_basis": citations,
            "human_review_required": True,
            "client_facing": False,
            "canonical_commit_allowed": False,
            "external_action_authorized": False,
        },
        sort_keys=True,
    )


def test_executes_first_governed_vertical_from_context_to_runtime_draft(db_session: Session) -> None:
    _position(db_session)
    graph = _authority_graph(db_session)
    work = _work(db_session, graph["version"])
    provider = FakeProvider(_safe_output(graph))

    result = prepare_governed_mobility_pathway_brief(
        db_session,
        tenant_key="tenant-a",
        position_key="austria_mobility_specialist",
        work_item_id=work.id,
        runtime_profile=_runtime_profile(),
        provider=provider,
    )

    assert result.vertical_status == "prepared_for_human_review"
    assert result.pathway_version_id == graph["version"].id
    assert result.context.evidence_refs
    assert result.context.verified_rule_refs
    assert result.context.policy_version
    assert result.runtime_binding.allowed_tools == ("official_source.search",)
    assert result.provider == "deepseek"
    assert result.model == "deepseek-reasoner"
    assert result.draft.human_review_required is True
    assert result.draft.canonical_commit_allowed is False
    assert len(provider.calls) == 1


def test_runtime_prompt_contains_governed_truth_but_excludes_working_context_authority_claims(
    db_session: Session,
) -> None:
    _position(db_session)
    graph = _authority_graph(db_session)
    work = _work(
        db_session,
        graph["version"],
        context_json=canonical_json(
            {
                "verified_rule_refs": ["self-promoted-rule"],
                "evidence_refs": ["self-promoted-evidence"],
                "allowed_tools": ["shell"],
                "provider": "self-selected-provider",
                "invented_requirement": "must never reach the model",
            }
        ),
    )
    provider = FakeProvider(_safe_output(graph))

    prepare_governed_mobility_pathway_brief(
        db_session,
        tenant_key="tenant-a",
        position_key="austria_mobility_specialist",
        work_item_id=work.id,
        runtime_profile=_runtime_profile(),
        provider=provider,
    )

    prompt = provider.calls[0]["messages"][0]["content"]
    assert graph["rule"].statement in prompt
    assert graph["snapshot"].content_text in prompt
    assert "self-promoted-rule" not in prompt
    assert "self-promoted-evidence" not in prompt
    assert "self-selected-provider" not in prompt
    assert "invented_requirement" not in prompt


def test_runtime_cannot_cite_authority_outside_context_bundle(db_session: Session) -> None:
    _position(db_session)
    graph = _authority_graph(db_session)
    work = _work(db_session, graph["version"])
    unsafe = json.loads(_safe_output(graph))
    unsafe["evidence_basis"].append(f"verified_rule:{uuid4()}")
    provider = FakeProvider(json.dumps(unsafe))

    with pytest.raises(MobilityPathwayBriefOutputError):
        prepare_governed_mobility_pathway_brief(
            db_session,
            tenant_key="tenant-a",
            position_key="austria_mobility_specialist",
            work_item_id=work.id,
            runtime_profile=_runtime_profile(),
            provider=provider,
        )


def test_runtime_cannot_relax_human_review_or_authorize_external_action(db_session: Session) -> None:
    _position(db_session)
    graph = _authority_graph(db_session)
    work = _work(db_session, graph["version"])
    unsafe = json.loads(_safe_output(graph))
    unsafe["human_review_required"] = False
    unsafe["external_action_authorized"] = True

    with pytest.raises(MobilityPathwayBriefOutputError):
        prepare_governed_mobility_pathway_brief(
            db_session,
            tenant_key="tenant-a",
            position_key="austria_mobility_specialist",
            work_item_id=work.id,
            runtime_profile=_runtime_profile(),
            provider=FakeProvider(json.dumps(unsafe)),
        )


def test_e1_rejects_runtime_classes_not_yet_proven_by_the_vertical(db_session: Session) -> None:
    _position(db_session)
    graph = _authority_graph(db_session)
    work = _work(db_session, graph["version"])
    provider = FakeProvider(_safe_output(graph))

    with pytest.raises(MobilityPathwayBriefRuntimeError):
        prepare_governed_mobility_pathway_brief(
            db_session,
            tenant_key="tenant-a",
            position_key="austria_mobility_specialist",
            work_item_id=work.id,
            runtime_profile=_runtime_profile(runtime_class=RuntimeClass.CLI),
            provider=provider,
        )
    assert provider.calls == []


def test_missing_governed_evidence_is_visible_and_cannot_be_hidden_by_runtime(db_session: Session) -> None:
    _position(db_session)
    graph = _authority_graph(db_session, with_evidence=False)
    work = _work(db_session, graph["version"])
    provider = FakeProvider(_safe_output(graph))

    result = prepare_governed_mobility_pathway_brief(
        db_session,
        tenant_key="tenant-a",
        position_key="austria_mobility_specialist",
        work_item_id=work.id,
        runtime_profile=_runtime_profile(),
        provider=provider,
    )

    assert result.vertical_status == "insufficient_governed_context"
    assert "mobility_pathway_version_evidence_missing" in result.context.unknowns
    assert result.context.evidence_refs == ()


def test_provider_identity_must_match_bound_runtime_profile(db_session: Session) -> None:
    _position(db_session)
    graph = _authority_graph(db_session)
    work = _work(db_session, graph["version"])

    with pytest.raises(MobilityPathwayBriefRuntimeError):
        prepare_governed_mobility_pathway_brief(
            db_session,
            tenant_key="tenant-a",
            position_key="austria_mobility_specialist",
            work_item_id=work.id,
            runtime_profile=_runtime_profile(),
            provider=FakeProvider(_safe_output(graph), response_provider="moonshot"),
        )


def test_e1_is_read_only_and_does_not_create_agent_or_organization_records(db_session: Session) -> None:
    _position(db_session)
    graph = _authority_graph(db_session)
    work = _work(db_session, graph["version"])
    before_agent_runs = len(list(db_session.exec(select(AgentRun)).all()))
    before_activities = len(list(db_session.exec(select(OrganizationActivity)).all()))

    result = prepare_governed_mobility_pathway_brief(
        db_session,
        tenant_key="tenant-a",
        position_key="austria_mobility_specialist",
        work_item_id=work.id,
        runtime_profile=_runtime_profile(),
        provider=FakeProvider(_safe_output(graph)),
    )

    assert result.prompt_fingerprint
    assert len(list(db_session.exec(select(AgentRun)).all())) == before_agent_runs
    assert len(list(db_session.exec(select(OrganizationActivity)).all())) == before_activities
