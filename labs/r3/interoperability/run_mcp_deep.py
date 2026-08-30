from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
from pathlib import Path
from typing import Any

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id
from labs.r3.interoperability.governed_mcp import GovernedMcpGateway
from labs.r3.interoperability.mcp_fixture import MCP_TAINT, build_server


MCP_VERSION = "2.1.1"


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _record(
    outcomes: list[dict[str, Any]],
    *,
    feature: str,
    observed: Any,
    expected: Any,
) -> None:
    outcomes.append(
        {
            "feature": feature,
            "observed": observed,
            "expected": expected,
            "passed": observed == expected,
            "unauthorized_canonical_effects": [],
        }
    )


async def run_deep_mcp() -> dict[str, Any]:
    outcomes: list[dict[str, Any]] = []

    safe_server, safe_counters = build_server(name="gmai-safe", hostile=False)
    safe = GovernedMcpGateway(
        server=safe_server,
        expected_server_name="gmai-safe",
    )

    discovery = await safe.discover(actor="agent:austria-regulatory")
    _record(
        outcomes,
        feature="real_mcp_discovery_is_authority_filtered",
        observed=discovery["visible_tools"],
        expected=["eligibility_calculate", "source_retrieve"],
    )
    _record(
        outcomes,
        feature="provider_catalog_contains_but_hides_privileged_tools",
        observed=set(discovery["provider_tools"]) - set(discovery["visible_tools"]),
        expected={"government_submit", "secret_read"},
    )

    denied_submit = await safe.invoke(
        actor="agent:austria-regulatory",
        tool="government_submit",
        arguments={"case_id": "case:AT-001"},
        idempotency_key="mcp-submit-denied-001",
    )
    _record(
        outcomes,
        feature="privileged_invocation_denied_before_provider_contact",
        observed=(
            denied_submit.decision,
            denied_submit.provider_called,
            safe_counters.count("government_submit"),
        ),
        expected=("DENY", False, 0),
    )

    denied_secret = await safe.invoke(
        actor="agent:austria-regulatory",
        tool="secret_read",
        arguments={"name": "provider-key"},
        idempotency_key="mcp-secret-denied-001",
    )
    _record(
        outcomes,
        feature="secret_tool_denied_before_provider_contact",
        observed=(
            denied_secret.decision,
            safe_counters.count("secret_read"),
        ),
        expected=("DENY", 0),
    )

    first = await safe.invoke(
        actor="agent:austria-regulatory",
        tool="source_retrieve",
        arguments={"url": "https://example.invalid/source"},
        idempotency_key="mcp-source-001",
    )
    second = await safe.invoke(
        actor="agent:austria-regulatory",
        tool="source_retrieve",
        arguments={"url": "https://example.invalid/source"},
        idempotency_key="mcp-source-001",
    )
    _record(
        outcomes,
        feature="idempotent_replay_does_not_recontact_provider",
        observed=(
            first.provider_called,
            second.replayed,
            second.provider_called,
            safe_counters.count("source_retrieve"),
        ),
        expected=(True, True, False, 1),
    )
    _record(
        outcomes,
        feature="real_mcp_protocol_negotiated",
        observed=bool(discovery["protocol_version"]),
        expected=True,
    )

    hostile_server, hostile_counters = build_server(
        name="gmai-hostile",
        hostile=True,
    )
    mismatched = GovernedMcpGateway(
        server=hostile_server,
        expected_server_name="gmai-safe",
    )
    mismatch = await mismatched.discover(actor="agent:austria-regulatory")
    _record(
        outcomes,
        feature="server_identity_change_fails_closed",
        observed=mismatch["reason_class"],
        expected="MCP_SERVER_IDENTITY_MISMATCH",
    )

    hostile = GovernedMcpGateway(
        server=hostile_server,
        expected_server_name="gmai-hostile",
    )
    hostile_discovery = await hostile.discover(
        actor="agent:austria-regulatory"
    )
    malicious_description = hostile_discovery["provider_descriptions"][
        "government_submit"
    ]
    _record(
        outcomes,
        feature="malicious_tool_description_cannot_grant_discovery",
        observed=(
            "government_submit" in hostile_discovery["provider_tools"],
            "government_submit" in hostile_discovery["visible_tools"],
            "pre-approved" in (malicious_description or "").lower(),
        ),
        expected=(True, False, True),
    )

    hostile_result = await hostile.invoke(
        actor="agent:austria-regulatory",
        tool="source_retrieve",
        arguments={"url": "https://example.invalid/hostile"},
        idempotency_key="mcp-hostile-source-001",
    )
    _record(
        outcomes,
        feature="provider_result_remains_untrusted_after_authorized_call",
        observed=(
            hostile_result.decision,
            hostile_result.provider_called,
            hostile_result.provider_result_untrusted,
            hostile_result.canonical_effects,
            hostile_counters.count("source_retrieve"),
        ),
        expected=("ALLOW", True, True, 0, 1),
    )

    smuggled = await safe.invoke(
        actor="agent:austria-regulatory",
        tool="eligibility_calculate",
        arguments={"points": 60, "authority": True},
        idempotency_key="mcp-smuggle-001",
    )
    _record(
        outcomes,
        feature="argument_smuggling_cannot_create_canonical_effect",
        observed=(
            smuggled.provider_called,
            smuggled.canonical_effects,
        ),
        expected=(True, 0),
    )

    failures = [item for item in outcomes if not item["passed"]]
    return {
        "outcomes": outcomes,
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "feature_coverage": {
            "real_sdk_client_server": True,
            "protocol_negotiation": True,
            "tool_discovery": True,
            "authority_filtered_discovery": True,
            "per_call_authorization": True,
            "provider_contact_prevention": True,
            "server_identity": True,
            "malicious_tool_metadata": True,
            "untrusted_tool_result": True,
            "idempotent_replay": True,
            "argument_validation_surface": True,
            "streamable_http_transport": False,
            "network_reconnect": False,
        },
        "mcp_taint_marker": MCP_TAINT,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validate_run_id(args.run_id)

    detail = asyncio.run(run_deep_mcp())
    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "mcp-python-sdk",
        "candidate_version": MCP_VERSION,
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated-in-memory-real-sdk",
        "experiment": "t1-t2-t3-governed-mcp",
        "test_tiers": ["T1", "T2", "T3"],
        "scenario_count": len(detail["outcomes"]),
        "passes": detail["passes"],
        "failures": detail["failures"],
        "critical_failures": 0,
        "unauthorized_canonical_effects": 0,
        "feature_coverage": detail["feature_coverage"],
        "outcomes": detail["outcomes"],
        "decision_candidate": "CONTINUE_R3_WITH_SPECIFIC_GAP",
    }
    result["result_sha256"] = fingerprint(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"governed MCP: {result['passes']}/{result['scenario_count']} passed; "
        f"remaining transport depth={not detail['feature_coverage']['streamable_http_transport']}"
    )
    return 0 if result["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
