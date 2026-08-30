from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from labs.r3.common.harness import load_json, run_reference_corpus, summarize_outcomes


ROOT = Path(__file__).resolve().parent


def _git_sha() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", default="common-20260901-001")
    args = parser.parse_args()

    corpus = load_json(ROOT / "fixtures" / "authority_corpus.v1.json")
    outcomes = run_reference_corpus(corpus)
    result = summarize_outcomes(
        run_id=args.run_id,
        candidate="aios-r3-common-reference-oracle",
        candidate_version="v1",
        git_sha=_git_sha(),
        corpus=corpus,
        outcomes=outcomes,
        decision_candidate="CONTINUE_R3_WITH_SPECIFIC_GAP",
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"R3 common proof: {result['passes']}/{result['scenario_count']} passed; "
        f"critical_failures={result['critical_failures']}; output={args.output}"
    )
    return 0 if result["failures"] == 0 and result["critical_failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
