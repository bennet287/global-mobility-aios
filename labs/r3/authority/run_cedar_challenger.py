from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from labs.r3.authority.cedar_adapter import run_challenger_corpus
from labs.r3.common.harness import fingerprint, load_json, summarize_outcomes, validate_run_id


ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "common" / "fixtures" / "authority_corpus.v1.json"
VERSION = "v4.12.0"


HARDCATEGORY_ACTIONS = {
    "authority.grant",
    "client.communication.send",
    "government_application.submit",
    "legal.conclusion.publish",
    "verified_rule.write",
    "a2a.task.delegate",
    "mcp.tool.invoke",
}


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _select_hard_scenarios(scenarios: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        scenario
        for scenario in scenarios
        if scenario["request"]["action"] in HARDCATEGORY_ACTIONS
        or scenario["request"].get("context", {}).get("same_tenant") is False
        or scenario["request"].get("delegation", {}).get("status")
        in {"expired", "revoked"}
        or scenario["request"].get("context", {}).get(
            "human_approval_required"
        )
        is True
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--use-reference-fallback",
        action="store_true",
        help=(
            "diagnostic only: evaluate against the AIOS reference oracle; "
            "never qualifies as empirical Cedar evidence"
        ),
    )
    parser.add_argument(
        "--hard-subset-only",
        action="store_true",
        help="run the hardest authority scenarios instead of the full corpus",
    )
    args = parser.parse_args()
    validate_run_id(args.run_id)

    corpus = load_json(CORPUS_PATH)
    scenarios = corpus["scenarios"]
    if args.hard_subset_only:
        scenarios = _select_hard_scenarios(scenarios)

    outcomes = run_challenger_corpus(
        scenarios=scenarios,
        use_reference_fallback=args.use_reference_fallback,
    )
    result = summarize_outcomes(
        run_id=args.run_id,
        candidate="cedar",
        candidate_version=VERSION,
        git_sha=_git_sha(),
        corpus=corpus,
        outcomes=outcomes,
    )
    result.pop("result_sha256")

    fallback_count = sum(
        1 for outcome in outcomes if outcome["used_reference_fallback"]
    )
    provider_calls = sum(1 for outcome in outcomes if outcome["provider_called"])
    real_execution_count = sum(
        1
        for outcome in outcomes
        if outcome["provider_called"] and not outcome["used_reference_fallback"]
    )

    result.update(
        {
            "hard_subset_only": args.hard_subset_only,
            "provider_calls": provider_calls,
            "reference_fallback_count": fallback_count,
            "real_cedar_execution_count": real_execution_count,
            "used_reference_fallback": fallback_count > 0,
        }
    )
    if fallback_count or real_execution_count != len(outcomes):
        result["decision_candidate"] = "CONTINUE_R3_WITH_SPECIFIC_GAP"

    result["result_sha256"] = fingerprint(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"cedar challenger: {result['passes']}/{result['scenario_count']} passed; "
        f"failures={result['failures']}; hard_subset={args.hard_subset_only}; "
        f"real_executions={real_execution_count}; fallback={fallback_count}; "
        f"output={args.output}"
    )

    qualifies = (
        result["failures"] == 0
        and result["critical_failures"] == 0
        and fallback_count == 0
        and real_execution_count == len(outcomes)
    )
    return 0 if qualifies else 2


if __name__ == "__main__":
    raise SystemExit(main())
