from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.services.organization_governance import ensure_foundation_positions
from app.services.organization_mobility_objective_execution import execute_austria_specialists
from app.services.organization_mobility_objective_runtime import create_austria_mobility_objective
from tests.test_organization_mobility_context_provenance import (
    _authority_graph,
    _force_deterministic,
    _human_context,
    _profiles,
    _reference_payload,
)


FRESH_RETRIEVAL_WARNING = (
    "fresh retrieval provenance is not present in the K.1 execution contract"
)


def test_live_projection_correlates_specialist_runtime_quality_without_overclaiming_freshness(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ensure_foundation_positions(
        db_session,
        actor="pytest-live-runtime-diagnostics",
        repair_contracts=True,
    )
    _force_deterministic(monkeypatch)
    graph = _authority_graph(db_session)
    pathway_version = graph["pathway_version"]
    context = _human_context()

    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key="at-rwr-shortage-2026-live-runtime-diagnostics",
        pathway_version_id=pathway_version.id,
    )
    results = execute_austria_specialists(
        db_session,
        context,
        plan,
        runtime_profiles=_profiles(),
    )
    by_position = {result.position_key: result for result in results}

    response = client.get(
        f"/api/v1/organization/transparency/live-organization/austria/"
        f"{plan.root_work_item.id}"
    )
    assert response.status_code == 200
    body = response.json()

    expected_evidence_count = len(
        _reference_payload("mobility_pathway_version_evidence", graph["evidence"])
    )
    expected_rule_count = len(_reference_payload("verified_rule", graph["rule"]))
    expected_snapshot_count = len(_reference_payload("source_snapshot", graph["snapshot"]))

    assert len(body["specialist_outputs"]) == len(results)
    for specialist in body["specialist_outputs"]:
        result = by_position[specialist["position_key"]]
        assert specialist["evidence_valid"] is True
        assert specialist["execution_attempt_id"] == str(result.execution_attempt_id)
        assert specialist["agent_run_id"] == str(result.agent_run_id)
        assert specialist["context_hash"] == result.context_hash
        assert specialist["runtime_binding_hash"] == result.runtime_binding_hash
        assert specialist["latency_ms"] == result.latency_ms
        assert specialist["retry_count"] == 0

        quality = specialist["runtime_quality"]
        assert quality["contract_version"] == "austria-mobility-runtime-quality.v1"
        assert quality["execution_mode"] == "deterministic_template"
        assert quality["provider_outcome"] == "not_invoked"
        assert quality["provider_egress_occurred"] is False
        assert quality["fallback_to_template"] is False
        assert quality["grounding_state"] == "authority_grounded"
        assert quality["evidence_ref_count"] == expected_evidence_count
        assert quality["verified_rule_ref_count"] == expected_rule_count
        assert quality["source_snapshot_ref_count"] == expected_snapshot_count
        assert quality["fresh_retrieval_provenance_present"] is False
        assert quality["provider_model_authority"] is False
        assert FRESH_RETRIEVAL_WARNING in quality["warnings"]
