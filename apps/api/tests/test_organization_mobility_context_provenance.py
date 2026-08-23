from __future__ import annotations

import json
from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from sqlmodel import Session, select

from app.models.domain import (
    AgentRun,
    CountryPolicy,
    MobilityPathway,
    MobilityPathwayVersion,
    MobilityPathwayVersionEvidence,
    OfficialSource,
    OrganizationActorType,
    OrganizationalActionOutput,
    OrganizationalWorkItem,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from app.services.organization_agent_runtime import AgentRuntimeProfile, RuntimeClass
from app.services.organization_command import (
    DependencyConflict,
    OrganizationCommandContext,
    canonical_fingerprint,
)
from app.services.organization_governance import ensure_foundation_positions
from app.services.organization_mobility_live_organization import austria_live_organization_snapshot
from app.services.organization_mobility_objective_execution import execute_austria_specialists
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_OBJECTIVE_ROUTE,
    AUSTRIA_MOBILITY_PATHWAY_POSITION,
    AUSTRIA_MOBILITY_REGULATORY_POSITION,
    AUSTRIA_MOBILITY_SPECIALIST_POSITIONS,
    austria_objective_readiness,
    create_austria_mobility_objective,
)


SOURCE_REPLAY_CONFLICT = "canonical Austria objective already bound to a different pathway version"


def _human_context() -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key="default",
        actor_id="human-owner",
        actor_type=OrganizationActorType.human,
        authenticated_user_id="human-owner",
        role="admin",
        department="Global Mobility Operations",
        position_key="board",
        authority_level="L4",
    )


def _runtime(provider: str) -> AgentRuntimeProfile:
    return AgentRuntimeProfile(
        profile_key=f"{provider}-reasoning-v1",
        runtime_class=RuntimeClass.HOSTED_API,
        adapter_key=f"{provider}-adapter",
        provider_key=provider,
        model_key=f"{provider}-model",
        technical_capabilities=("reasoning", "structured_output"),
        available_tools=("browser", "shell"),
        independence_group=provider,
        profile_version=1,
        enabled=True,
    )


def _profiles() -> dict[str, AgentRuntimeProfile]:
    return {
        AUSTRIA_MOBILITY_PATHWAY_POSITION: _runtime("provider-a"),
        AUSTRIA_MOBILITY_REGULATORY_POSITION: _runtime("provider-b"),
    }


def _force_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.controlled_agents.is_llm_enabled", lambda: False)


def _authority_graph(session: Session) -> dict[str, object]:
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
        content_hash="snapshot-v1",
        content_text="Published Austrian mobility guidance.",
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
        rule_key=f"at-rule-{uuid4()}",
        statement="A governed Austrian mobility rule.",
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
        pathway_key=AUSTRIA_MOBILITY_OBJECTIVE_ROUTE,
        name="Austrian shortage-occupation mobility pathway",
        country="austria",
        domain="visa",
        catalogue_status="published",
        created_by="pytest",
    )
    session.add(pathway)
    session.commit()
    session.refresh(pathway)

    pathway_version = MobilityPathwayVersion(
        pathway_id=pathway.id,
        version_number=3,
        lifecycle_status="published",
        official_source_id=source.id,
        source_snapshot_id=snapshot.id,
        verified_rule_ids_json=json.dumps([str(rule.id)]),
        eligibility_criteria_json='{"criterion":"governed"}',
        metadata_json='{"scope":"test"}',
        effective_from=now_utc() - timedelta(days=10),
        human_review_required=True,
        approved_by="pytest-reviewer",
        published_at=now_utc() - timedelta(days=1),
        created_by="pytest",
    )
    session.add(pathway_version)
    session.commit()
    session.refresh(pathway_version)

    evidence = MobilityPathwayVersionEvidence(
        pathway_version_id=pathway_version.id,
        evidence_role="primary",
        official_source_id=source.id,
        source_snapshot_id=snapshot.id,
        required_for_publication=True,
        metadata_json='{"purpose":"primary authority"}',
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
        "pathway_version": pathway_version,
        "evidence": evidence,
        "policy": policy,
    }


def _reference_payload(kind: str, row: object) -> list[dict[str, str]]:
    return [
        {
            "kind": kind,
            "identifier": str(row.id),
            "version": canonical_fingerprint(row),
        }
    ]


def _second_published_version(session: Session, graph: dict[str, object]) -> MobilityPathwayVersion:
    first = graph["pathway_version"]
    row = MobilityPathwayVersion(
        pathway_id=first.pathway_id,
        version_number=first.version_number + 1,
        lifecycle_status="published",
        official_source_id=first.official_source_id,
        source_snapshot_id=first.source_snapshot_id,
        verified_rule_ids_json=first.verified_rule_ids_json,
        eligibility_criteria_json=first.eligibility_criteria_json,
        metadata_json='{"scope":"test-v2"}',
        effective_from=now_utc() - timedelta(days=1),
        human_review_required=True,
        approved_by="pytest-reviewer",
        published_at=now_utc(),
        created_by="pytest",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _assert_same_plan_ids(first, replay) -> None:
    assert replay.root_work_item.id == first.root_work_item.id
    assert replay.pathway_work_item.id == first.pathway_work_item.id
    assert replay.regulatory_work_item.id == first.regulatory_work_item.id


def test_source_grounded_k1_persists_real_authority_refs_and_l_projects_persisted_lineage(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ensure_foundation_positions(db_session, actor="pytest", repair_contracts=True)
    _force_deterministic(monkeypatch)
    graph = _authority_graph(db_session)
    pathway_version = graph["pathway_version"]
    context = _human_context()
    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key="at-rwr-shortage-2026-context-provenance",
        pathway_version_id=pathway_version.id,
    )

    assert plan.root_work_item.source_object_type is None
    assert plan.root_work_item.source_object_id is None
    assert plan.root_work_item.source_object_version is None
    for work in (plan.pathway_work_item, plan.regulatory_work_item):
        assert work.source_object_type == "mobility_pathway_version"
        assert work.source_object_id == str(pathway_version.id)
        assert work.source_object_version == str(pathway_version.version_number)

    execute_austria_specialists(
        db_session,
        context,
        plan,
        runtime_profiles=_profiles(),
    )

    expected_evidence = _reference_payload(
        "mobility_pathway_version_evidence",
        graph["evidence"],
    )
    expected_rules = _reference_payload("verified_rule", graph["rule"])
    expected_snapshots = _reference_payload("source_snapshot", graph["snapshot"])

    outputs = db_session.exec(
        select(OrganizationalActionOutput).where(
            OrganizationalActionOutput.work_item_id.in_(
                [plan.pathway_work_item.id, plan.regulatory_work_item.id]
            )
        )
    ).all()
    assert len(outputs) == 2
    for output in outputs:
        payload = json.loads(output.output_json)
        assert payload["context_evidence_refs"] == expected_evidence
        assert payload["context_verified_rule_refs"] == expected_rules
        assert payload["context_source_snapshot_refs"] == expected_snapshots

        run = db_session.get(AgentRun, UUID(payload["agent_run_id"]))
        assert run is not None
        run_input = json.loads(run.input_json)
        provenance = run_input["context"]["k1_provenance"]
        assert provenance["context_evidence_refs"] == expected_evidence
        assert provenance["context_verified_rule_refs"] == expected_rules
        assert provenance["context_source_snapshot_refs"] == expected_snapshots

    snapshot = austria_live_organization_snapshot(
        db_session,
        tenant_key="default",
        root_work_item_id=plan.root_work_item.id,
    )
    evidence = graph["evidence"]
    rule = graph["rule"]
    assert snapshot.domain_evidence_refs == (
        f"mobility_pathway_version_evidence:{evidence.id}@{canonical_fingerprint(evidence)}",
    )
    assert snapshot.verified_rule_refs == (
        f"verified_rule:{rule.id}@{canonical_fingerprint(rule)}",
    )


def test_l_rejects_ref_only_tampering_between_output_and_agent_run(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ensure_foundation_positions(db_session, actor="pytest", repair_contracts=True)
    _force_deterministic(monkeypatch)
    graph = _authority_graph(db_session)
    context = _human_context()
    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key="at-rwr-shortage-2026-context-ref-tamper",
        pathway_version_id=graph["pathway_version"].id,
    )
    execute_austria_specialists(
        db_session,
        context,
        plan,
        runtime_profiles=_profiles(),
    )

    output = db_session.exec(
        select(OrganizationalActionOutput).where(
            OrganizationalActionOutput.work_item_id == plan.pathway_work_item.id
        )
    ).one()
    payload = json.loads(output.output_json)
    payload["context_evidence_refs"][0]["identifier"] = "forged-evidence"
    output.output_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    db_session.add(output)
    db_session.commit()

    with pytest.raises(
        DependencyConflict,
        match="persisted context authority refs do not match the AgentRun provenance",
    ):
        austria_live_organization_snapshot(
            db_session,
            tenant_key="default",
            root_work_item_id=plan.root_work_item.id,
        )


def test_grounded_source_mutation_invalidates_completed_k1_readiness(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ensure_foundation_positions(db_session, actor="pytest", repair_contracts=True)
    _force_deterministic(monkeypatch)
    graph = _authority_graph(db_session)
    context = _human_context()
    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key="at-rwr-shortage-2026-source-mutation",
        pathway_version_id=graph["pathway_version"].id,
    )
    execute_austria_specialists(
        db_session,
        context,
        plan,
        runtime_profiles=_profiles(),
    )

    pathway_work = db_session.get(OrganizationalWorkItem, plan.pathway_work_item.id)
    assert pathway_work is not None
    pathway_work.source_object_id = str(uuid4())
    db_session.add(pathway_work)
    db_session.commit()

    readiness = austria_objective_readiness(
        db_session,
        tenant_key="default",
        root_work_item_id=plan.root_work_item.id,
    )
    assert readiness.ready_for_owner_synthesis is False
    assert AUSTRIA_MOBILITY_PATHWAY_POSITION in readiness.pending_positions
    assert any(
        "stale for the current completed WorkItem" in reason
        for reason in readiness.reasons
    )


def test_grounded_objective_replay_rejects_conflicting_pathway_source(db_session: Session) -> None:
    ensure_foundation_positions(db_session, actor="pytest", repair_contracts=True)
    graph = _authority_graph(db_session)
    first_version = graph["pathway_version"]
    second_version = _second_published_version(db_session, graph)
    context = _human_context()
    objective_key = "at-rwr-shortage-2026-grounded-replay"

    first = create_austria_mobility_objective(
        db_session,
        context,
        objective_key=objective_key,
        pathway_version_id=first_version.id,
    )

    with pytest.raises(DependencyConflict, match=SOURCE_REPLAY_CONFLICT):
        create_austria_mobility_objective(
            db_session,
            context,
            objective_key=objective_key,
            pathway_version_id=second_version.id,
        )

    pathway_work = db_session.get(OrganizationalWorkItem, first.pathway_work_item.id)
    regulatory_work = db_session.get(OrganizationalWorkItem, first.regulatory_work_item.id)
    assert pathway_work is not None
    assert regulatory_work is not None
    for work in (pathway_work, regulatory_work):
        assert work.source_object_type == "mobility_pathway_version"
        assert work.source_object_id == str(first_version.id)
        assert work.source_object_version == str(first_version.version_number)


def test_grounded_objective_same_source_replay_returns_same_work_items(db_session: Session) -> None:
    ensure_foundation_positions(db_session, actor="pytest", repair_contracts=True)
    graph = _authority_graph(db_session)
    version = graph["pathway_version"]
    context = _human_context()
    objective_key = "at-rwr-shortage-2026-same-source-replay"

    first = create_austria_mobility_objective(
        db_session,
        context,
        objective_key=objective_key,
        pathway_version_id=version.id,
    )
    replay = create_austria_mobility_objective(
        db_session,
        context,
        objective_key=objective_key,
        pathway_version_id=version.id,
    )

    _assert_same_plan_ids(first, replay)


def test_grounded_objective_replay_rejects_dropping_pathway_source(db_session: Session) -> None:
    ensure_foundation_positions(db_session, actor="pytest", repair_contracts=True)
    graph = _authority_graph(db_session)
    version = graph["pathway_version"]
    context = _human_context()
    objective_key = "at-rwr-shortage-2026-grounded-to-unbound"

    first = create_austria_mobility_objective(
        db_session,
        context,
        objective_key=objective_key,
        pathway_version_id=version.id,
    )

    with pytest.raises(DependencyConflict, match=SOURCE_REPLAY_CONFLICT):
        create_austria_mobility_objective(
            db_session,
            context,
            objective_key=objective_key,
        )

    pathway_work = db_session.get(OrganizationalWorkItem, first.pathway_work_item.id)
    regulatory_work = db_session.get(OrganizationalWorkItem, first.regulatory_work_item.id)
    assert pathway_work is not None
    assert regulatory_work is not None
    for work in (pathway_work, regulatory_work):
        assert work.source_object_type == "mobility_pathway_version"
        assert work.source_object_id == str(version.id)
        assert work.source_object_version == str(version.version_number)


def test_ungrounded_objective_replay_rejects_adding_pathway_source(db_session: Session) -> None:
    ensure_foundation_positions(db_session, actor="pytest", repair_contracts=True)
    graph = _authority_graph(db_session)
    version = graph["pathway_version"]
    context = _human_context()
    objective_key = "at-rwr-shortage-2026-unbound-to-grounded"

    first = create_austria_mobility_objective(
        db_session,
        context,
        objective_key=objective_key,
    )

    with pytest.raises(DependencyConflict, match=SOURCE_REPLAY_CONFLICT):
        create_austria_mobility_objective(
            db_session,
            context,
            objective_key=objective_key,
            pathway_version_id=version.id,
        )

    pathway_work = db_session.get(OrganizationalWorkItem, first.pathway_work_item.id)
    regulatory_work = db_session.get(OrganizationalWorkItem, first.regulatory_work_item.id)
    assert pathway_work is not None
    assert regulatory_work is not None
    for work in (pathway_work, regulatory_work):
        assert work.source_object_type is None
        assert work.source_object_id is None
        assert work.source_object_version is None


def test_grounded_objective_rejects_wrong_or_unpublished_source_before_topology(
    db_session: Session,
) -> None:
    ensure_foundation_positions(db_session, actor="pytest", repair_contracts=True)
    graph = _authority_graph(db_session)
    pathway = graph["pathway"]
    pathway_version = graph["pathway_version"]
    context = _human_context()

    pathway.pathway_key = f"other-route-{uuid4()}"
    db_session.add(pathway)
    db_session.commit()
    with pytest.raises(DependencyConflict, match="canonical Austria objective route"):
        create_austria_mobility_objective(
            db_session,
            context,
            objective_key="at-rwr-shortage-2026-wrong-source",
            pathway_version_id=pathway_version.id,
        )
    assert db_session.exec(select(OrganizationalWorkItem)).all() == []

    pathway.pathway_key = AUSTRIA_MOBILITY_OBJECTIVE_ROUTE
    pathway_version.lifecycle_status = "draft"
    pathway_version.published_at = None
    db_session.add_all([pathway, pathway_version])
    db_session.commit()
    with pytest.raises(DependencyConflict, match="version source is not published"):
        create_austria_mobility_objective(
            db_session,
            context,
            objective_key="at-rwr-shortage-2026-unpublished-source",
            pathway_version_id=pathway_version.id,
        )
    assert db_session.exec(select(OrganizationalWorkItem)).all() == []


def test_ungrounded_k1_remains_truthfully_empty(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ensure_foundation_positions(db_session, actor="pytest", repair_contracts=True)
    _force_deterministic(monkeypatch)
    context = _human_context()
    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key="at-rwr-shortage-2026-context-empty",
    )
    execute_austria_specialists(
        db_session,
        context,
        plan,
        runtime_profiles=_profiles(),
    )

    outputs = db_session.exec(
        select(OrganizationalActionOutput).where(
            OrganizationalActionOutput.work_item_id.in_(
                [plan.pathway_work_item.id, plan.regulatory_work_item.id]
            )
        )
    ).all()
    assert len(outputs) == len(AUSTRIA_MOBILITY_SPECIALIST_POSITIONS)
    for output in outputs:
        payload = json.loads(output.output_json)
        assert payload["context_evidence_refs"] == []
        assert payload["context_verified_rule_refs"] == []
        assert payload["context_source_snapshot_refs"] == []

    snapshot = austria_live_organization_snapshot(
        db_session,
        tenant_key="default",
        root_work_item_id=plan.root_work_item.id,
    )
    assert snapshot.domain_evidence_refs == ()
    assert snapshot.verified_rule_refs == ()
