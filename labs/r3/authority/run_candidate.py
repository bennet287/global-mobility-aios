from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Any

from labs.r3.authority.adapters import OpenFgaAdapter, OpaAdapter
from labs.r3.authority.bootstrap_openfga import create_store_and_model
from labs.r3.common.harness import fingerprint, load_json, summarize_outcomes


ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "common" / "fixtures" / "authority_corpus.v1.json"
VERSIONS = {"openfga": "v1.18.1", "opa": "v1.19.1"}


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _percentile(values: list[float], percentile: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, (len(ordered) * percentile + 99) // 100 - 1)
    return round(ordered[index], 3)


def _run(adapter: Any, corpus: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    outcomes: list[dict[str, Any]] = []
    latencies: list[float] = []
    engine_calls = 0
    for scenario in corpus["scenarios"]:
        started = time.perf_counter()
        observed = adapter.decide(scenario["request"])
        latencies.append((time.perf_counter() - started) * 1000)
        engine_calls += int(observed.provider_called)
        expected = scenario["expected"]
        outcomes.append(
            {
                "scenario_id": scenario["scenario_id"],
                "expected_decision": expected["decision"],
                "observed_decision": observed.decision,
                "expected_reason_class": expected["reason_class"],
                "observed_reason_class": observed.reason_class,
                "provider_called": observed.provider_called,
                "passed": observed.decision == expected["decision"]
                and observed.reason_class == expected["reason_class"],
                "unauthorized_canonical_effects": [],
            }
        )
    metrics = {
        "engine_calls": engine_calls,
        "preflight_denials": len(outcomes) - engine_calls,
        "latency_ms": {
            "p50": _percentile(latencies, 50),
            "p95": _percentile(latencies, 95),
            "p99": _percentile(latencies, 99),
            "maximum": round(max(latencies, default=0.0), 3),
        },
    }
    return outcomes, metrics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", choices=sorted(VERSIONS), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--opa-url", default="http://127.0.0.1:18181")
    parser.add_argument("--openfga-url", default="http://127.0.0.1:18080")
    args = parser.parse_args()

    run_id = args.run_id or f"{args.candidate}-20260901-001"
    if args.candidate == "opa":
        adapter: Any = OpaAdapter(base_url=args.opa_url)
    else:
        store_id, model_id = create_store_and_model(base_url=args.openfga_url)
        adapter = OpenFgaAdapter(
            base_url=args.openfga_url,
            store_id=store_id,
            authorization_model_id=model_id,
        )

    corpus = load_json(CORPUS_PATH)
    outcomes, metrics = _run(adapter, corpus)
    result = summarize_outcomes(
        run_id=run_id,
        candidate=args.candidate,
        candidate_version=VERSIONS[args.candidate],
        git_sha=_git_sha(),
        corpus=corpus,
        outcomes=outcomes,
    )
    result.pop("result_sha256")
    result["environment"] = "synthetic-isolated-real-engine"
    result["experiment"] = "t1-real-engine-correctness"
    result["test_tiers"] = ["T1"]
    result["metrics"] = metrics
    result["result_sha256"] = fingerprint(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"{args.candidate} R3: {result['passes']}/{result['scenario_count']} passed; "
        f"critical_failures={result['critical_failures']}; output={args.output}"
    )
    return 0 if result["failures"] == 0 and result["critical_failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
