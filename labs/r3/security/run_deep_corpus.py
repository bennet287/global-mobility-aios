from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id
from labs.r3.security.deep_target import DeepSecurityTarget, all_effects_zero


CORPUS = Path(__file__).resolve().parent / "deep_attack_corpus.v2.json"


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def execute() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    target = DeepSecurityTarget()
    outcomes: list[dict[str, Any]] = []

    for attack in corpus["attacks"]:
        observation = target.execute(attack)
        expected = attack["expected"]
        expected_taints = sorted(attack.get("expected_taints", []))
        observed_taints = sorted(observation.taints_observed)
        passed = (
            all_effects_zero(observation.effects)
            and observation.reason_class in expected["allowed_reason_classes"]
            and observed_taints == expected_taints
        )
        outcomes.append(
            {
                "attack_id": observation.attack_id,
                "category": observation.category,
                "surface": attack["surface"],
                "requested_action": attack.get("requested_action"),
                "reason_class": observation.reason_class,
                "before_sha256": observation.before_sha256,
                "after_sha256": observation.after_sha256,
                "effects": observation.effects,
                "taints_observed": observed_taints,
                "passed": passed,
            }
        )

    return corpus, outcomes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    validate_run_id(args.run_id)

    corpus, outcomes = execute()
    failures = [item for item in outcomes if not item["passed"]]
    unauthorized = sum(
        sum(item["effects"].values())
        for item in outcomes
    )
    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "aios-deep-security-target",
        "candidate_version": "v2",
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated-stateful",
        "experiment": "t4-state-diff-adversarial-corpus",
        "test_tiers": ["T1", "T4"],
        "scenario_count": len(outcomes),
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "critical_failures": unauthorized,
        "unauthorized_canonical_effects": unauthorized,
        "corpus_sha256": fingerprint(corpus),
        "outcomes": outcomes,
        "decision_candidate": (
            "CONTINUE_R3_WITH_SPECIFIC_GAP"
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
        f"deep security corpus: {result['passes']}/{result['scenario_count']} passed; "
        f"unauthorized effects={unauthorized}"
    )
    return 0 if not failures and unauthorized == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
