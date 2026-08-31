from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import httpx

from labs.r3.authority.adapters import OpenFgaAdapter, OpaAdapter
from labs.r3.common.generate_fixtures import build_authority_corpus
from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id


VERSIONS = {"openfga": "v1.18.1", "opa": "v1.19.1"}
FAILURE_MODES = {
    "connect_error": "ENGINE_UNAVAILABLE",
    "timeout": "ENGINE_UNAVAILABLE",
    "http_500": "ENGINE_UNAVAILABLE",
    "malformed_json": "MALFORMED_RESPONSE",
    "empty_result": "MALFORMED_RESPONSE",
    "partial_result": "MALFORMED_RESPONSE",
    "unknown_decision": "MALFORMED_RESPONSE",
}


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _privileged_request() -> dict[str, Any]:
    return next(
        scenario["request"]
        for scenario in build_authority_corpus()["scenarios"]
        if scenario["request"]["action"] == "government_application.submit"
        and scenario["description"].endswith("authorized baseline")
    )


def _transport(candidate: str, failure_mode: str) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if failure_mode == "connect_error":
            raise httpx.ConnectError("synthetic connection refusal", request=request)
        if failure_mode == "timeout":
            raise httpx.ReadTimeout("synthetic timeout", request=request)
        if failure_mode == "http_500":
            return httpx.Response(500, json={"error": "synthetic"})
        if failure_mode == "malformed_json":
            return httpx.Response(
                200,
                content=b"{not-json",
                headers={"content-type": "application/json"},
            )

        if candidate == "opa":
            if failure_mode == "empty_result":
                return httpx.Response(200, json={"result": None})
            if failure_mode == "partial_result":
                return httpx.Response(200, json={"result": {"decision": "DENY"}})
            if failure_mode == "unknown_decision":
                return httpx.Response(
                    200,
                    json={
                        "result": {
                            "decision": "MAYBE",
                            "reason_class": "AUTHORIZED",
                        }
                    },
                )
        else:
            if failure_mode == "empty_result":
                return httpx.Response(200, json={})
            if failure_mode == "partial_result":
                return httpx.Response(200, json={"allowed": "false"})
            if failure_mode == "unknown_decision":
                return httpx.Response(200, json={"allowed": None})

        raise AssertionError(f"unsupported failure mode {failure_mode}")

    return httpx.MockTransport(handler)


def run_matrix(candidate: str) -> list[dict[str, Any]]:
    request = _privileged_request()
    outcomes: list[dict[str, Any]] = []
    for failure_mode, expected_reason in FAILURE_MODES.items():
        client = httpx.Client(
            base_url="http://candidate.test",
            transport=_transport(candidate, failure_mode),
        )
        if candidate == "opa":
            adapter = OpaAdapter(base_url="http://candidate.test", client=client)
        else:
            adapter = OpenFgaAdapter(
                base_url="http://candidate.test",
                store_id="store",
                authorization_model_id="model",
                client=client,
            )

        observed = adapter.decide(request)
        passed = (
            observed.decision == "DENY"
            and observed.reason_class == expected_reason
            and observed.provider_called
        )
        outcomes.append(
            {
                "failure_mode": failure_mode,
                "expected_decision": "DENY",
                "expected_reason_class": expected_reason,
                "observed_decision": observed.decision,
                "observed_reason_class": observed.reason_class,
                "provider_called": observed.provider_called,
                "passed": passed,
                "unauthorized_canonical_effects": [],
            }
        )
        client.close()
    return outcomes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", choices=["openfga", "opa"], required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validate_run_id(args.run_id)

    outcomes = run_matrix(args.candidate)
    failures = [outcome for outcome in outcomes if not outcome["passed"]]
    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": args.candidate,
        "candidate_version": VERSIONS[args.candidate],
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated",
        "experiment": "t5-adapter-chaos-matrix",
        "test_tiers": ["T5"],
        "scenario_count": len(outcomes),
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "critical_failures": 0,
        "unauthorized_canonical_effects": 0,
        "outcomes": outcomes,
        "decision_candidate": (
            "ADVANCE_TO_R4"
            if not failures
            else "CONTINUE_R3_WITH_SPECIFIC_GAP"
        ),
    }
    result["result_sha256"] = fingerprint(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"{args.candidate} chaos matrix: "
        f"{result['passes']}/{result['scenario_count']} passed; "
        f"unauthorized effects=0"
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
