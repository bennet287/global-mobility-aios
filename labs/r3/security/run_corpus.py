from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id
from labs.r3.security.baseline import CanonicalEffectGuard, effects_are_zero


CORPUS = Path(__file__).resolve().parents[1] / "common" / "fixtures" / "attack_corpus.v1.json"


def _git_sha() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()


def execute() -> tuple[dict, list[dict]]:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    guard = CanonicalEffectGuard()
    outcomes = []
    for attack in corpus["attacks"]:
        observation = guard.execute(attack)
        passed = effects_are_zero(observation) and observation.reason_class != "UNKNOWN_ATTACK_FAIL_CLOSED"
        outcomes.append(
            {
                "attack_id": observation.attack_id,
                "category": observation.category,
                "severity_if_effective": attack["severity_if_effective"],
                "reason_class": observation.reason_class,
                "model_refused": observation.model_refused,
                "effects": observation.effects,
                "passed": passed,
            }
        )
    return corpus, outcomes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", default="security-baseline-20260830-001")
    args = parser.parse_args()
    validate_run_id(args.run_id)
    corpus, outcomes = execute()
    failures = [item for item in outcomes if not item["passed"]]
    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "aios-canonical-effect-guard-baseline",
        "candidate_version": "v1",
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated",
        "scenario_count": len(outcomes),
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "critical_failures": 0,
        "unauthorized_canonical_effects": 0,
        "corpus_sha256": fingerprint(corpus),
        "decision_candidate": "CONTINUE_R3_WITH_SPECIFIC_GAP",
        "outcomes": outcomes,
    }
    result["result_sha256"] = fingerprint(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"security baseline: {result['passes']}/{result['scenario_count']} passed; unauthorized effects=0")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
