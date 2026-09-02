from __future__ import annotations

import hashlib
import json
import socket

import httpx
import pytest
from sqlmodel import Session, select

from app.core.config import settings
from app.models.domain import (
    AgentRun,
    OrganizationalActionOutput,
    OrganizationalWorkItem,
    RegulatoryChange,
    SourceMonitor,
    SourceSnapshot,
    now_utc,
)
from app.services.organization_command import DependencyConflict
from app.services.organization_governance import ensure_foundation_positions
from app.services.organization_mobility_fresh_retrieval import (
    attach_fresh_retrieval_evidence,
    refresh_austria_authority_snapshots,
    validate_action_output_fresh_retrieval_evidence,
)
from app.services.organization_mobility_live_diagnostics import (
    austria_live_specialist_runtime_quality,
)
from app.services.organization_mobility_live_organization import (
    austria_live_organization_snapshot,
)
from app.services.organization_mobility_live_provider_cycle import (
    execute_austria_live_provider_cycle,
)
from app.services.organization_mobility_objective_execution import execute_austria_specialists
from app.services.organization_mobility_objective_runtime import create_austria_mobility_objective
from tests.test_organization_mobility_context_provenance import (
    _authority_graph,
    _force_deterministic,
    _human_context,
    _profiles,
)


def _public_resolver(host: str, port: int, **kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]


def _plan_with_monitor(
    session: Session,
    *,
    objective_key: str,
):
    ensure_foundation_positions(
        session,
        actor="pytest-fresh-retrieval",
        repair_contracts=True,
    )
    graph = _authority_graph(session)
    source = graph["source"]
    snapshot = graph["snapshot"]
    content = snapshot.content_text or ""
    snapshot.content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)

    monitor = SourceMonitor(
        official_source_id=source.id,
        schedule_minutes=60,
        fetch_method="http",
        allowed_domains_json=json.dumps(["example.gv.at"]),
        max_redirects=2,
        parser_profile="generic",
        next_check_at=now_utc(),
    )
    session.add(monitor)
    session.commit()
    session.refresh(monitor)

    plan = create_austria_mobility_objective(
        session,
        _human_context(),
        objective_key=objective_key,
        pathway_version_id=graph["pathway_version"].id,
    )
    return graph, plan, monitor


def _matching_transport(content: str, *, etag: str = '"austria-v1"') -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/plain; charset=utf-8", "etag": etag},
            content=content.encode("utf-8"),
        )

    return httpx.MockTransport(handler)


def test_fresh_retrieval_unchanged_binds_to_exact_k1_outputs(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _force_deterministic(monkeypatch)
    graph, plan, _ = _plan_with_monitor(
        db_session,
        objective_key="at-rwr-shortage-2026-fresh-retrieval-unchanged",
    )
    content = graph["snapshot"].content_text or ""
    attestations = refresh_austria_authority_snapshots(
        db_session,
        plan,
        transport=_matching_transport(content),
        resolver=_public_resolver,
    )
    assert len(attestations) == 1
    attestation = next(iter(attestations.values()))
    assert attestation.retrieval_status == "unchanged"
    assert attestation.content_equivalent_to_governed is True
    assert attestation.freshness_verified is True

    results = execute_austria_specialists(
        db_session,
        _human_context(),
        plan,
        runtime_profiles=_profiles(),
    )
    for result in results:
        attached = attach_fresh_retrieval_evidence(
            db_session,
            action_output_id=result.action_output_id,
            agent_run_id=result.agent_run_id,
            execution_attempt_id=result.execution_attempt_id,
            work_item_id=result.work_item_id,
            position_key=result.position_key,
            attestations=attestations,
            actor="pytest-fresh-retrieval",
        )
        assert attached == 1
        output = db_session.get(OrganizationalActionOutput, result.action_output_id)
        agent_run = db_session.get(AgentRun, result.agent_run_id)
        assert output is not None and agent_run is not None
        assert validate_action_output_fresh_retrieval_evidence(
            db_session,
            output=output,
            agent_run=agent_run,
        ) == 1


def test_historical_verified_rule_snapshot_is_not_refetched_as_current_authority(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _force_deterministic(monkeypatch)
    graph, plan, _ = _plan_with_monitor(
        db_session,
        objective_key="at-rwr-shortage-2026-historical-rule-provenance",
    )
    current_snapshot = graph["snapshot"]
    source = graph["source"]
    rule = graph["rule"]

    historical_content = "Historical Austrian mobility guidance."
    historical_snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash=hashlib.sha256(historical_content.encode("utf-8")).hexdigest(),
        content_text=historical_content,
        http_status=200,
        retrieval_method="http",
        parser_version="pytest-v1",
        status="baseline",
    )
    db_session.add(historical_snapshot)
    db_session.commit()
    db_session.refresh(historical_snapshot)

    rule.source_snapshot_id = historical_snapshot.id
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)

    attestations = refresh_austria_authority_snapshots(
        db_session,
        plan,
        transport=_matching_transport(current_snapshot.content_text or ""),
        resolver=_public_resolver,
    )
    assert set(attestations) == {current_snapshot.id}
    assert historical_snapshot.id not in attestations

    results = execute_austria_specialists(
        db_session,
        _human_context(),
        plan,
        runtime_profiles=_profiles(),
    )
    for result in results:
        attached = attach_fresh_retrieval_evidence(
            db_session,
            action_output_id=result.action_output_id,
            agent_run_id=result.agent_run_id,
            execution_attempt_id=result.execution_attempt_id,
            work_item_id=result.work_item_id,
            position_key=result.position_key,
            attestations=attestations,
            actor="pytest-fresh-retrieval",
        )
        assert attached == 1

        output = db_session.get(OrganizationalActionOutput, result.action_output_id)
        agent_run = db_session.get(AgentRun, result.agent_run_id)
        assert output is not None and agent_run is not None

        payload = json.loads(output.output_json)
        context_snapshot_ids = {
            item["identifier"]
            for item in payload["context_source_snapshot_refs"]
        }
        assert context_snapshot_ids == {
            str(current_snapshot.id),
            str(historical_snapshot.id),
        }

        fresh_evidence = payload["fresh_retrieval_evidence"]
        assert fresh_evidence["attestation_count"] == 1
        assert {
            item["governed_source_snapshot_id"]
            for item in fresh_evidence["attestations"]
        } == {str(current_snapshot.id)}
        assert validate_action_output_fresh_retrieval_evidence(
            db_session,
            output=output,
            agent_run=agent_run,
        ) == 1


def test_fresh_retrieval_304_uses_prior_snapshot_producing_run(
    db_session: Session,
) -> None:
    graph, plan, monitor = _plan_with_monitor(
        db_session,
        objective_key="at-rwr-shortage-2026-fresh-retrieval-304",
    )
    content = graph["snapshot"].content_text or ""
    first = refresh_austria_authority_snapshots(
        db_session,
        plan,
        transport=_matching_transport(content),
        resolver=_public_resolver,
    )
    first_attestation = next(iter(first.values()))
    assert first_attestation.retrieval_status == "unchanged"
    db_session.refresh(monitor)
    assert monitor.etag == '"austria-v1"'

    def not_modified(request: httpx.Request) -> httpx.Response:
        assert request.headers["if-none-match"] == '"austria-v1"'
        return httpx.Response(304, headers={"etag": '"austria-v1"'})

    second = refresh_austria_authority_snapshots(
        db_session,
        plan,
        transport=httpx.MockTransport(not_modified),
        resolver=_public_resolver,
    )
    second_attestation = next(iter(second.values()))
    assert second_attestation.retrieval_status == "not_modified"
    assert second_attestation.source_retrieval_run_id != first_attestation.source_retrieval_run_id
    assert (
        second_attestation.snapshot_basis_retrieval_run_id
        == first_attestation.source_retrieval_run_id
    )
    assert second_attestation.content_hash == first_attestation.content_hash


def test_changed_official_source_fails_before_k1_and_persists_review_change(
    db_session: Session,
) -> None:
    _, plan, _ = _plan_with_monitor(
        db_session,
        objective_key="at-rwr-shortage-2026-fresh-retrieval-change",
    )
    attempts_before = {
        work.id: work.execution_attempts
        for work in (plan.pathway_work_item, plan.regulatory_work_item)
    }

    with pytest.raises(
        DependencyConflict,
        match="detected changed content",
    ):
        refresh_austria_authority_snapshots(
            db_session,
            plan,
            transport=_matching_transport("Changed Austrian mobility guidance."),
            resolver=_public_resolver,
        )

    changes = list(db_session.exec(select(RegulatoryChange)).all())
    assert len(changes) == 1
    assert changes[0].status == "pending_review"
    for work_item_id, attempt_count in attempts_before.items():
        work = db_session.get(OrganizationalWorkItem, work_item_id)
        assert work is not None
        assert work.execution_attempts == attempt_count


def test_live_cycle_rejects_previously_attempted_specialist_before_retrieval(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, plan, _ = _plan_with_monitor(
        db_session,
        objective_key="at-rwr-shortage-2026-consumed-live-candidate",
    )

    work = db_session.get(
        OrganizationalWorkItem,
        plan.pathway_work_item.id,
    )
    assert work is not None
    work.status = "running"
    work.execution_attempts = 1
    db_session.add(work)
    db_session.commit()

    monkeypatch.setattr(settings, "llm_provider", "deepseek")
    monkeypatch.setattr(settings, "deepseek_model", "deepseek-chat")
    monkeypatch.setattr(settings, "deepseek_api_key", "test-only-key")
    monkeypatch.setattr(settings, "llm_fallback_to_template", False)

    retrieval_called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal retrieval_called
        retrieval_called = True
        return httpx.Response(500)

    with pytest.raises(
        DependencyConflict,
        match="execution_attempts=1",
    ):
        execute_austria_live_provider_cycle(
            db_session,
            tenant_key="default",
            root_work_item_id=plan.root_work_item.id,
            retrieval_transport=httpx.MockTransport(handler),
            retrieval_resolver=_public_resolver,
        )

    assert retrieval_called is False


def test_live_cycle_checks_provider_configuration_before_source_retrieval(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, plan, _ = _plan_with_monitor(
        db_session,
        objective_key="at-rwr-shortage-2026-provider-before-retrieval",
    )
    monkeypatch.setattr(settings, "llm_provider", "")
    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(500)

    with pytest.raises(DependencyConflict, match="requires one configured provider"):
        execute_austria_live_provider_cycle(
            db_session,
            tenant_key="default",
            root_work_item_id=plan.root_work_item.id,
            retrieval_transport=httpx.MockTransport(handler),
            retrieval_resolver=_public_resolver,
        )
    assert called is False


def test_guarded_cycle_projects_validated_freshness_without_promoting_deterministic_to_live(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _force_deterministic(monkeypatch)
    graph, plan, _ = _plan_with_monitor(
        db_session,
        objective_key="at-rwr-shortage-2026-fresh-cycle-negative-control",
    )
    monkeypatch.setattr(settings, "llm_provider", "deepseek")
    monkeypatch.setattr(settings, "deepseek_model", "deepseek-chat")
    monkeypatch.setattr(settings, "deepseek_api_key", "test-only-key")
    monkeypatch.setattr(settings, "llm_fallback_to_template", False)

    evaluation = execute_austria_live_provider_cycle(
        db_session,
        tenant_key="default",
        root_work_item_id=plan.root_work_item.id,
        retrieval_transport=_matching_transport(graph["snapshot"].content_text or ""),
        retrieval_resolver=_public_resolver,
    )

    assert evaluation.fresh_retrieval_provenance_complete is True
    assert evaluation.all_specialists_authority_grounded is True
    assert evaluation.all_specialists_live_provider_succeeded is False
    assert evaluation.live_provider_acceptance_candidate is False
    assert evaluation.full_l_reasoning_evidence_candidate is False
    assert all(
        item.fresh_retrieval_provenance_present is True
        and item.execution_mode == "deterministic_template"
        and item.provider_outcome == "not_invoked"
        and item.live_provider_succeeded is False
        for item in evaluation.specialist_evaluations
    )

    live_snapshot = austria_live_organization_snapshot(
        db_session,
        tenant_key="default",
        root_work_item_id=plan.root_work_item.id,
    )
    assert live_snapshot.ready_for_owner_synthesis is True
    for specialist in live_snapshot.specialist_outputs:
        quality = austria_live_specialist_runtime_quality(db_session, specialist)
        assert quality is not None
        assert quality.fresh_retrieval_provenance_present is True
        assert "fresh official-source equivalence verified before K.1" in quality.warnings


def test_tampered_freshness_stamp_fails_durable_revalidation(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _force_deterministic(monkeypatch)
    graph, plan, _ = _plan_with_monitor(
        db_session,
        objective_key="at-rwr-shortage-2026-fresh-cycle-tamper",
    )
    monkeypatch.setattr(settings, "llm_provider", "deepseek")
    monkeypatch.setattr(settings, "deepseek_model", "deepseek-chat")
    monkeypatch.setattr(settings, "deepseek_api_key", "test-only-key")
    monkeypatch.setattr(settings, "llm_fallback_to_template", False)
    evaluation = execute_austria_live_provider_cycle(
        db_session,
        tenant_key="default",
        root_work_item_id=plan.root_work_item.id,
        retrieval_transport=_matching_transport(graph["snapshot"].content_text or ""),
        retrieval_resolver=_public_resolver,
    )
    specialist = evaluation.specialist_evaluations[0]
    output = db_session.get(OrganizationalActionOutput, specialist.action_output_id)
    agent_run = db_session.get(AgentRun, specialist.agent_run_id)
    assert output is not None and agent_run is not None

    payload = json.loads(output.output_json)
    payload["fresh_retrieval_evidence"]["attestations"][0]["content_hash"] = "forged"
    output.output_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    db_session.add(output)
    db_session.commit()

    with pytest.raises(DependencyConflict, match="content-equivalence proof diverged"):
        validate_action_output_fresh_retrieval_evidence(
            db_session,
            output=output,
            agent_run=agent_run,
        )
