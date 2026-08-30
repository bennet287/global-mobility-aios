from __future__ import annotations

import copy
import json
from pathlib import Path

import httpx
import pytest

from labs.r3.authority.adapters import (
    OpenFgaAdapter,
    OpaAdapter,
    evaluate_aios_preflight,
)
from labs.r3.authority.benchmark import _percentile as benchmark_percentile
from labs.r3.authority.run_candidate import _percentile, _run
from labs.r3.common.generate_fixtures import build_authority_corpus
from labs.r3.common.harness import evaluate_reference
from labs.r3.common.verify_results import verify_result


OPA_POLICY = Path("labs/r3/authority/opa/authority.rego")


def _opa_transport(request: httpx.Request) -> httpx.Response:
    payload = json.loads(request.content)
    observed = evaluate_reference(payload["input"])
    return httpx.Response(
        200,
        json={
            "result": {
                "decision": observed.decision,
                "reason_class": observed.reason_class,
            }
        },
    )


def _openfga_transport(request: httpx.Request) -> httpx.Response:
    payload = json.loads(request.content)
    contextual = payload.get("contextual_tuples", {}).get("tuple_keys", [])
    return httpx.Response(200, json={"allowed": payload["tuple_key"] in contextual})


def test_opa_adapter_normalizes_identical_120_case_corpus() -> None:
    client = httpx.Client(
        base_url="http://opa.test", transport=httpx.MockTransport(_opa_transport)
    )
    adapter = OpaAdapter(base_url="http://opa.test", client=client)

    for scenario in build_authority_corpus()["scenarios"]:
        observed = adapter.decide(scenario["request"])
        assert observed.decision == scenario["expected"]["decision"]
        assert observed.reason_class == scenario["expected"]["reason_class"]


def test_openfga_adapter_normalizes_identical_120_case_corpus() -> None:
    client = httpx.Client(
        base_url="http://openfga.test",
        transport=httpx.MockTransport(_openfga_transport),
    )
    adapter = OpenFgaAdapter(
        base_url="http://openfga.test",
        store_id="store",
        authorization_model_id="model",
        client=client,
    )

    for scenario in build_authority_corpus()["scenarios"]:
        observed = adapter.decide(scenario["request"])
        assert observed.decision == scenario["expected"]["decision"]
        assert observed.reason_class == scenario["expected"]["reason_class"]


@pytest.mark.parametrize("adapter_kind", ["opa", "openfga"])
def test_engine_outage_fails_closed(adapter_kind: str) -> None:
    def unavailable(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("synthetic outage", request=request)

    client = httpx.Client(
        base_url="http://candidate.test", transport=httpx.MockTransport(unavailable)
    )
    if adapter_kind == "opa":
        adapter = OpaAdapter(base_url="http://candidate.test", client=client)
    else:
        adapter = OpenFgaAdapter(
            base_url="http://candidate.test",
            store_id="store",
            authorization_model_id="model",
            client=client,
        )
    request = copy.deepcopy(
        next(
            scenario["request"]
            for scenario in build_authority_corpus()["scenarios"]
            if scenario["request"]["action"] == "government_application.submit"
        )
    )

    observed = adapter.decide(request)

    assert observed.decision == "DENY"
    assert observed.reason_class == "ENGINE_UNAVAILABLE"
    assert observed.provider_called is True


def test_openfga_hard_deny_happens_before_provider_contact() -> None:
    calls = 0

    def should_not_run(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500)

    client = httpx.Client(
        base_url="http://openfga.test",
        transport=httpx.MockTransport(should_not_run),
    )
    adapter = OpenFgaAdapter(
        base_url="http://openfga.test",
        store_id="store",
        authorization_model_id="model",
        client=client,
    )
    request = copy.deepcopy(build_authority_corpus()["scenarios"][0]["request"])
    request["resource"]["tenant_id"] = "tenant:beta"
    request["context"]["same_tenant"] = True

    observed = adapter.decide(request)

    assert observed.decision == "DENY"
    assert observed.reason_class == "CROSS_TENANT"
    assert observed.provider_called is False
    assert calls == 0


def test_openfga_agent_cannot_grant_authority_to_itself() -> None:
    calls = 0

    def should_not_run(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500)

    client = httpx.Client(
        base_url="http://openfga.test",
        transport=httpx.MockTransport(should_not_run),
    )
    adapter = OpenFgaAdapter(
        base_url="http://openfga.test",
        store_id="store",
        authorization_model_id="model",
        client=client,
    )
    request = copy.deepcopy(
        next(
            scenario["request"]
            for scenario in build_authority_corpus()["scenarios"]
            if scenario["request"]["action"] == "authority.grant"
        )
    )
    request["actor"]["id"] = request["acting_for"]

    observed = adapter.decide(request)

    assert observed.decision == "DENY"
    assert observed.reason_class == "SELF_ESCALATION"
    assert observed.provider_called is False
    assert calls == 0


def test_preflight_ignores_context_attempt_to_remove_canonical_requirements() -> None:
    request = copy.deepcopy(
        next(
            scenario["request"]
            for scenario in build_authority_corpus()["scenarios"]
            if scenario["request"]["action"] == "government_application.submit"
            and scenario["description"].endswith("authorized baseline")
        )
    )
    request["jurisdiction"] = "DE"
    request["human_approval"] = False
    request["context"]["required_jurisdiction"] = None
    request["context"]["human_approval_required"] = False
    request["context"]["authority_required"] = False

    observed = evaluate_aios_preflight(request)

    assert observed is not None
    assert observed.decision == "DENY"
    assert observed.reason_class == "JURISDICTION_MISMATCH"


def test_opa_policy_derives_mandatory_requirements_from_canonical_metadata() -> None:
    policy = OPA_POLICY.read_text(encoding="utf-8")

    assert "canonical_actions :=" in policy
    assert "input.context.authority_required" not in policy
    assert "input.context.human_approval_required" not in policy
    assert "input.context.required_jurisdiction" not in policy
    assert "input.context.same_tenant" not in policy
    assert "input.context.known_action" not in policy


@pytest.mark.parametrize("adapter_kind", ["opa", "openfga"])
def test_invalid_json_candidate_response_fails_closed_as_malformed(
    adapter_kind: str,
) -> None:
    client = httpx.Client(
        base_url="http://candidate.test",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                content=b"{not-json",
                headers={"content-type": "application/json"},
            )
        ),
    )
    if adapter_kind == "opa":
        adapter = OpaAdapter(base_url="http://candidate.test", client=client)
    else:
        adapter = OpenFgaAdapter(
            base_url="http://candidate.test",
            store_id="store",
            authorization_model_id="model",
            client=client,
        )

    request = next(
        scenario["request"]
        for scenario in build_authority_corpus()["scenarios"]
        if scenario["request"]["action"] == "government_application.submit"
        and scenario["description"].endswith("authorized baseline")
    )
    observed = adapter.decide(request)

    assert observed.decision == "DENY"
    assert observed.reason_class == "MALFORMED_RESPONSE"
    assert observed.provider_called is True


def test_malformed_candidate_response_fails_closed() -> None:
    client = httpx.Client(
        base_url="http://opa.test",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={})),
    )
    adapter = OpaAdapter(base_url="http://opa.test", client=client)

    observed = adapter.decide(build_authority_corpus()["scenarios"][0]["request"])

    assert observed.decision == "DENY"
    assert observed.reason_class == "MALFORMED_RESPONSE"


def test_candidate_runner_emits_latency_and_call_split() -> None:
    client = httpx.Client(
        base_url="http://openfga.test",
        transport=httpx.MockTransport(_openfga_transport),
    )
    adapter = OpenFgaAdapter(
        base_url="http://openfga.test",
        store_id="store",
        authorization_model_id="model",
        client=client,
    )

    outcomes, metrics = _run(adapter, build_authority_corpus())

    assert len(outcomes) == 120
    assert all(outcome["passed"] for outcome in outcomes)
    assert metrics["engine_calls"] > 0
    assert metrics["preflight_denials"] > 0
    assert metrics["engine_calls"] + metrics["preflight_denials"] == 120
    assert set(metrics["latency_ms"]) == {"p50", "p95", "p99", "maximum"}


def test_percentile_is_deterministic() -> None:
    assert _percentile([1.0, 2.0, 3.0, 4.0], 50) == 2.0
    assert _percentile([1.0, 2.0, 3.0, 4.0], 95) == 4.0
    assert benchmark_percentile([1.0, 2.0, 3.0, 4.0], 99) == 4.0


def test_all_authority_evidence_artifacts_are_fingerprinted() -> None:
    paths = sorted(Path("labs/r3/authority/results").glob("*.json"))

    assert len(paths) >= 7
    for path in paths:
        verify_result(path)
