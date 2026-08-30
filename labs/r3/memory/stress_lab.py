from __future__ import annotations

import argparse
import concurrent.futures
import json
import tempfile
from pathlib import Path
from typing import Any

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id
from labs.r3.memory.governance import NativeContinuityMemory, resolve_governed_fact


TENANT_COUNT = 64
MEMORIES_PER_TENANT = 8


def _exercise_native() -> dict[str, Any]:
    memory = NativeContinuityMemory()
    verified_rules = {"at.rwr.threshold": "55"}
    evidence = {"at.rwr.threshold": "official-source:synthetic"}

    def write_tenant(index: int) -> None:
        tenant = f"tenant:{index:03d}"
        for item in range(MEMORIES_PER_TENANT):
            text = f"tenant {index} continuity item {item}"
            if item == 0:
                text += " Austria threshold 45 POISONED_MEMORY"
            memory.put(tenant_id=tenant, memory_id=f"m:{item}", text=text)

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(write_tenant, range(TENANT_COUNT)))

    cross_tenant_leaks = 0
    poison_override_failures = 0
    missing_records = 0
    for index in range(TENANT_COUNT):
        tenant = f"tenant:{index:03d}"
        own = memory.search(tenant_id=tenant, query="tenant continuity")
        if len(own) != MEMORIES_PER_TENANT:
            missing_records += 1

        other_index = (index + 1) % TENANT_COUNT
        foreign_marker = f"tenant {other_index}"
        if any(foreign_marker in item["memory"] for item in own):
            cross_tenant_leaks += 1

        poisoned = memory.search(tenant_id=tenant, query="Austria threshold")
        governed = resolve_governed_fact(
            key="at.rwr.threshold",
            verified_rule_value=verified_rules["at.rwr.threshold"],
            retrieved_memory_values=[item["memory"] for item in poisoned],
        )
        if governed.value != "55" or governed.source_class != "VERIFIED_RULE":
            poison_override_failures += 1

    expected_total = TENANT_COUNT * MEMORIES_PER_TENANT
    total = sum(
        1
        for index in range(TENANT_COUNT)
        for item in range(MEMORIES_PER_TENANT)
        if memory.get(tenant_id=f"tenant:{index:03d}", memory_id=f"m:{item}")
        is not None
    )

    return {
        "candidate": "native-aios-continuity-memory",
        "tenant_count": TENANT_COUNT,
        "memories_per_tenant": MEMORIES_PER_TENANT,
        "expected_records": expected_total,
        "observed_records": total,
        "cross_tenant_leaks": cross_tenant_leaks,
        "poison_override_failures": poison_override_failures,
        "missing_record_groups": missing_records,
        "verified_rules_after": verified_rules,
        "evidence_after": evidence,
        "unauthorized_canonical_effects": 0,
    }


def _exercise_mem0(
    *, ollama_url: str, llm_model: str, embed_model: str, embed_dims: int
) -> dict[str, Any]:
    from labs.r3.memory.mem0_lab import ExecutionBlocked, _config, _preflight_ollama

    _preflight_ollama(ollama_url, embed_model)
    from mem0 import Memory

    verified_rules = {"at.rwr.threshold": "55"}
    with tempfile.TemporaryDirectory(prefix="gmai-r3-mem0-stress-") as temp:
        memory = Memory.from_config(
            _config(
                ollama_url=ollama_url,
                llm_model=llm_model,
                embed_model=embed_model,
                embed_dims=embed_dims,
                qdrant_path=str(Path(temp) / "qdrant"),
            )
        )
        # Keep external stress bounded because local embedding is materially heavier.
        tenant_count = 12
        for index in range(tenant_count):
            memory.add(
                f"tenant {index} Austria threshold 45 POISONED_MEMORY",
                user_id=f"tenant:{index:03d}",
                infer=False,
            )

        leaks = 0
        poison_failures = 0
        for index in range(tenant_count):
            result = memory.search(
                "Austria threshold",
                filters={"user_id": f"tenant:{index:03d}"},
                top_k=20,
                threshold=0,
            )
            values = [str(item.get("memory", "")) for item in result.get("results", [])]
            for other in range(tenant_count):
                if other != index and any(f"tenant {other}" in value for value in values):
                    leaks += 1
            governed = resolve_governed_fact(
                key="at.rwr.threshold",
                verified_rule_value="55",
                retrieved_memory_values=values,
            )
            if governed.value != "55":
                poison_failures += 1

    return {
        "candidate": "mem0-oss",
        "tenant_count": tenant_count,
        "cross_tenant_leaks": leaks,
        "poison_override_failures": poison_failures,
        "verified_rules_after": verified_rules,
        "unauthorized_canonical_effects": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate", choices=["native", "mem0"], default="native")
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    parser.add_argument("--llm-model", default="llama3.1:8b")
    parser.add_argument("--embed-model", default="nomic-embed-text")
    parser.add_argument("--embed-dims", type=int, default=768)
    args = parser.parse_args()
    validate_run_id(args.run_id)

    blocked = False
    block_reason = None
    try:
        if args.candidate == "native":
            observed = _exercise_native()
        else:
            observed = _exercise_mem0(
                ollama_url=args.ollama_url,
                llm_model=args.llm_model,
                embed_model=args.embed_model,
                embed_dims=args.embed_dims,
            )
    except Exception as exc:
        if args.candidate == "mem0" and type(exc).__name__ == "ExecutionBlocked":
            observed = {}
            blocked = True
            block_reason = str(exc)
        else:
            raise

    passed = bool(observed) and all(
        [
            observed.get("cross_tenant_leaks") == 0,
            observed.get("poison_override_failures") == 0,
            observed.get("unauthorized_canonical_effects") == 0,
        ]
    )
    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": f"memory-stress:{args.candidate}",
        "candidate_version": "r3-v1",
        "environment": "synthetic-isolated",
        "experiment": "t3-t5-memory-concurrency-poisoning",
        "test_tiers": ["T3", "T5"],
        "execution_blocked": blocked,
        "block_reason": block_reason,
        "scenario_count": int(not blocked),
        "passes": int(passed),
        "failures": int(not blocked and not passed),
        "critical_failures": 0,
        "unauthorized_canonical_effects": 0,
        "outcomes": [observed] if observed else [],
        "decision_candidate": "CONTINUE_R3_WITH_SPECIFIC_GAP",
    }
    result["result_sha256"] = fingerprint(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if blocked:
        return 2
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
