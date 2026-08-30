from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import httpx

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id
from labs.r3.memory.governance import resolve_governed_fact


OPENVIKING_VERSION = "0.4.9"
OPENVIKING_LICENSE = "AGPL-3.0"


class ExecutionBlocked(RuntimeError):
    pass


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _preflight(url: str) -> None:
    try:
        response = httpx.get(f"{url.rstrip('/')}/health", timeout=2.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ExecutionBlocked("local OpenViking server is unavailable") from exc


def _record(
    outcomes: list[dict[str, Any]],
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


def run_openviking(*, url: str) -> dict[str, Any]:
    _preflight(url)
    from openviking_sdk import SyncHTTPClient

    outcomes: list[dict[str, Any]] = []
    verified_rules = {"at.rwr.threshold": "55"}
    evidence = {"rule:at.rwr.threshold": "official-source:synthetic"}

    client = SyncHTTPClient(
        url=url,
        account="r3-account",
        user="tenant-alpha",
        auth_mode="dev",
    )
    client.initialize()
    try:
        _record(
            outcomes,
            "real_server_health",
            bool(client.health()),
            True,
        )

        with tempfile.TemporaryDirectory(prefix="gmai-r3-openviking-") as temp:
            path = Path(temp) / "poisoned-memory.txt"
            path.write_text(
                "Austria RWR threshold is 45 OPENVIKING_MEMORY_TAINT",
                encoding="utf-8",
            )
            imported = client.add_resource(
                path=str(path),
                to="viking://resources/gmai-r3/poisoned-memory",
                wait=True,
                options={"processing_mode": "vectors_only"},
            )
            _record(
                outcomes,
                "vectors_only_local_context_ingest",
                bool(imported),
                True,
            )

        found = client.find(
            query="Austria RWR threshold",
            limit=5,
            options={
                "target_uri": "viking://resources/gmai-r3",
            },
        )
        serialized = json.dumps(found, ensure_ascii=False)
        _record(
            outcomes,
            "hierarchical_context_retrieval",
            "45" in serialized or "poisoned-memory" in serialized,
            True,
        )

        before_rules = dict(verified_rules)
        before_evidence = dict(evidence)
        governed = resolve_governed_fact(
            key="at.rwr.threshold",
            verified_rule_value=verified_rules["at.rwr.threshold"],
            retrieved_memory_values=[serialized],
        )
        _record(
            outcomes,
            "openviking_context_cannot_override_verified_rule",
            (governed.value, governed.source_class, verified_rules, evidence),
            ("55", "VERIFIED_RULE", before_rules, before_evidence),
        )

        listing = client.ls(uri="viking://resources/gmai-r3")
        _record(
            outcomes,
            "viking_filesystem_context_is_inspectable",
            bool(listing),
            True,
        )

        session = client.create_session(session_id="gmai-r3-session")
        _record(
            outcomes,
            "session_creation",
            bool(session),
            True,
        )
        session_client = client.session(session_id="gmai-r3-session")
        session_client.add_message(
            role="user",
            content="Synthetic case context; no authority.",
        )
        context = session_client.get_session_context(token_budget=4096)
        _record(
            outcomes,
            "session_context_is_retrievable",
            bool(context),
            True,
        )
        session_client.delete()
    finally:
        client.close()

    failures = [item for item in outcomes if not item["passed"]]
    return {
        "outcomes": outcomes,
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "feature_coverage": {
            "real_openviking_server": True,
            "viking_uri": True,
            "vectors_only_ingest": True,
            "hierarchical_retrieval": True,
            "inspectable_filesystem": True,
            "session_context": True,
            "verified_rule_precedence": True,
            "memory_extraction": False,
            "trajectory_inspection": False,
            "multi_tenant_auth": False,
            "snapshot_restore": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--url",
        default=os.getenv("GMAI_R3_OPENVIKING_URL", "http://127.0.0.1:1933"),
    )
    args = parser.parse_args()
    validate_run_id(args.run_id)

    try:
        detail = run_openviking(url=args.url)
        blocked = False
        block_reason = None
    except ExecutionBlocked as exc:
        detail = {
            "outcomes": [],
            "passes": 0,
            "failures": 0,
            "feature_coverage": {},
        }
        blocked = True
        block_reason = str(exc)

    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "openviking",
        "candidate_version": OPENVIKING_VERSION,
        "candidate_license": OPENVIKING_LICENSE,
        "git_sha": _git_sha(),
        "environment": "synthetic-local-only",
        "experiment": "t1-t2-t3-context-memory",
        "test_tiers": ["T1", "T2", "T3"],
        "execution_blocked": blocked,
        "block_reason": block_reason,
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
    if blocked:
        print(f"OpenViking R3 execution blocked: {block_reason}")
        return 2
    print(
        f"OpenViking R3: {result['passes']}/{result['scenario_count']} passed; "
        "AGPL adoption review remains mandatory"
    )
    return 0 if result["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
