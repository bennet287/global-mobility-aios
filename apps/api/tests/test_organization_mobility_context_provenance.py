from __future__ import annotations

import json
from dataclasses import replace
from uuid import UUID

import pytest
from sqlmodel import Session, select

from app.models.domain import AgentRun, OrganizationActorType, OrganizationalActionOutput
from app.services.organization_agent_runtime import AgentRuntimeProfile, RuntimeClass
from app.services.organization_command import (
    DependencyConflict,
    OrganizationCommandContext,
    canonical_fingerprint,
)
from app.services.organization_context_broker import (
    ContextPurpose,
    ContextReference,
    build_work_item_context_bundle,
)
from app.services.organization_governance import ensure_foundation_positions
from app.services.organization_mobility_live_organization import austria_live_organization_snapshot
from app.services.organization_mobility_objective_execution import execute_austria_specialists
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_PATHWAY_POSITION,
    AUSTRIA_MOBILITY_REGULATORY_POSITION,
    AUSTRIA_MOBILITY_SPECIALIST_POSITIONS,
    create_austria_mobility_objective,
)


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


def _grounded_context_builder(
    session: Session,
    *,
    tenant_key: str,
    position_key: str,
    work_item_id,
    purpose: ContextPurpose,
):
    base = build_work_item_context_bundle(
        session,
        tenant_key=tenant_key,
        position_key=position_key,
        work_item_id=work_item_id,
        purpose=purpose,
    )
    short = (
        "pathway"
        if position_key == AUSTRIA_MOBILITY_PATHWAY_POSITION
        else "regulatory"
    )
    evidence_refs = (
        ContextReference(
            kind="evidence",
            identifier=f"at-{short}-evidence",
            version="2026",
        ),
    )
    verified_rule_refs = (
        ContextReference(
            kind="verified_rule",
            identifier=f"at-{short}-rule",
            version="2026.1",
        ),
    )
    source_snapshot_refs = (
        ContextReference(
            kind="source_snapshot",
            identifier="at-official-source-snapshot",
            version="2026-08-22",
        ),
    )
    context_hash = canonical_fingerprint(
        {
            "base_context_hash": base.context_hash,
            "position_key": position_key,
            "fixture": "source-grounded-context-provenance",
        }
    )
    return replace(
        base,
        evidence_refs=evidence_refs,
        verified_rule_refs=verified_rule_refs,
        source_snapshot_refs=source_snapshot_refs,
        context_hash=context_hash,
    )


def test_k1_persists_consumed_context_refs_and_l_projects_only_persisted_lineage(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ensure_foundation_positions(db_session, actor="pytest", repair_contracts=True)
    _force_deterministic(monkeypatch)
    monkeypatch.setattr(
        "app.services.organization_mobility_objective_execution.build_work_item_context_bundle",
        _grounded_context_builder,
    )
    context = _human_context()
    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key="at-rwr-shortage-2026-context-provenance",
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
    assert len(outputs) == 2
    for output in outputs:
        payload = json.loads(output.output_json)
        position_key = output.accountable_position_key
        short = (
            "pathway"
            if position_key == AUSTRIA_MOBILITY_PATHWAY_POSITION
            else "regulatory"
        )
        expected_evidence = [
            {
                "kind": "evidence",
                "identifier": f"at-{short}-evidence",
                "version": "2026",
            }
        ]
        expected_rules = [
            {
                "kind": "verified_rule",
                "identifier": f"at-{short}-rule",
                "version": "2026.1",
            }
        ]
        expected_snapshots = [
            {
                "kind": "source_snapshot",
                "identifier": "at-official-source-snapshot",
                "version": "2026-08-22",
            }
        ]
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
    assert snapshot.domain_evidence_refs == (
        "evidence:at-pathway-evidence@2026",
        "evidence:at-regulatory-evidence@2026",
    )
    assert snapshot.verified_rule_refs == (
        "verified_rule:at-pathway-rule@2026.1",
        "verified_rule:at-regulatory-rule@2026.1",
    )


def test_l_rejects_ref_only_tampering_between_output_and_agent_run(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ensure_foundation_positions(db_session, actor="pytest", repair_contracts=True)
    _force_deterministic(monkeypatch)
    monkeypatch.setattr(
        "app.services.organization_mobility_objective_execution.build_work_item_context_bundle",
        _grounded_context_builder,
    )
    context = _human_context()
    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key="at-rwr-shortage-2026-context-ref-tamper",
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
