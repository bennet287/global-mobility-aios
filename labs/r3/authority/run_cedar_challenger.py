from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from labs.r3.authority.cedar_adapter import run_challenger_corpus
from labs.r3.common.generate_fixtures import build_authority_corpus
from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, load_json, summarize_outcomes, validate_run_id


ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "common" / "fixtures" / "authority_corpus.v1.json"
VERSION = "v0.1.0-reference-oracle"


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
        s
        for s in scenarios
        if s["request"]["action"] in HARDCATEGORY_ACTIONS
        or s["request"].get("context", {}).get("same_tenant") is False
        or s["request"].get("delegation", {}).get("status") in {"expired", "revoked"}
        or s["request"].get("context", {}).get("human_approval_required") is True
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--use-reference-fallback",
        action="store_true",
        help="evaluate against the AIOS reference oracle instead of a real Cedar CLI",
    )
    parser.add_argument(
        "--hard-subset-only",
        action="store_true",
        help="run only the ~30-40 hardest scenarios",
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
    result["hard_subset_only"] = args.hard_subset_only
    result["used_reference_fallback"] = args.use_reference_fallback
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
        f"fallback={args.use_reference_fallback}; output={args.output}"
    )
    return 0 if result["failures"] == 0 and result["critical_failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
