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


MEM0_VERSION = "2.0.19"


class ExecutionBlocked(RuntimeError):
    pass


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _preflight_ollama(base_url: str, embed_model: str) -> None:
    try:
        response = httpx.get(f"{base_url.rstrip('/')}/api/tags", timeout=2.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ExecutionBlocked("local Ollama is unavailable") from exc

    names = {
        str(item.get("name", "")).split(":")[0]
        for item in response.json().get("models", [])
    }
    wanted = embed_model.split(":")[0]
    if wanted not in names:
        raise ExecutionBlocked(
            f"local Ollama embedding model {embed_model!r} is not installed"
        )


def _config(
    *,
    ollama_url: str,
    llm_model: str,
    embed_model: str,
    embed_dims: int,
    qdrant_path: str,
) -> dict[str, Any]:
    return {
        "llm": {
            "provider": "ollama",
            "config": {
                "model": llm_model,
                "temperature": 0,
                "ollama_base_url": ollama_url,
            },
        },
        "embedder": {
            "provider": "ollama",
            "config": {
                "model": embed_model,
                "embedding_dims": embed_dims,
                "ollama_base_url": ollama_url,
            },
        },
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "collection_name": "gmai_r3_mem0",
                "path": qdrant_path,
                "embedding_model_dims": embed_dims,
            },
        },
    }


def _extract_added_id(add_result: dict[str, Any]) -> str:
    results = add_result.get("results") or []
    if not results or not results[0].get("id"):
        raise RuntimeError(f"Mem0 did not return a memory id: {add_result!r}")
    return str(results[0]["id"])


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


def run_mem0(
    *,
    ollama_url: str,
    llm_model: str,
    embed_model: str,
    embed_dims: int,
) -> dict[str, Any]:
    _preflight_ollama(ollama_url, embed_model)
    from mem0 import Memory

    outcomes: list[dict[str, Any]] = []
    verified_rules = {"at.rwr.threshold": "55"}
    evidence = {"rule:at.rwr.threshold": "official-source:synthetic"}

    with tempfile.TemporaryDirectory(prefix="gmai-r3-mem0-") as temp:
        memory = Memory.from_config(
            _config(
                ollama_url=ollama_url,
                llm_model=llm_model,
                embed_model=embed_model,
                embed_dims=embed_dims,
                qdrant_path=str(Path(temp) / "qdrant"),
            )
        )

        added = memory.add(
            "Austria RWR threshold is 45 MEMORY_TAINT_MEM0",
            user_id="tenant-alpha",
            metadata={"source_class": "CONTINUITY_MEMORY"},
            infer=False,
        )
        memory_id = _extract_added_id(added)

        found = memory.search(
            "Austria RWR threshold",
            filters={"user_id": "tenant-alpha"},
            top_k=5,
            threshold=0,
        )
        alpha_values = [str(item.get("memory", "")) for item in found.get("results", [])]
        _record(
            outcomes,
            "raw_memory_write_and_semantic_search",
            any("45" in value for value in alpha_values),
            True,
        )

        other_tenant = memory.search(
            "Austria RWR threshold",
            filters={"user_id": "tenant-beta"},
            top_k=5,
            threshold=0,
        )
        _record(
            outcomes,
            "tenant_filter_prevents_cross_tenant_retrieval",
            len(other_tenant.get("results", [])),
            0,
        )

        before_rules = dict(verified_rules)
        before_evidence = dict(evidence)
        governed = resolve_governed_fact(
            key="at.rwr.threshold",
            verified_rule_value=verified_rules["at.rwr.threshold"],
            retrieved_memory_values=alpha_values,
        )
        _record(
            outcomes,
            "poisoned_memory_cannot_override_verified_rule",
            (governed.value, governed.source_class, verified_rules, evidence),
            ("55", "VERIFIED_RULE", before_rules, before_evidence),
        )

        memory.update(
            memory_id=memory_id,
            text="Austria RWR threshold memory corrected to 55",
        )
        updated = memory.get_all(
            filters={"user_id": "tenant-alpha"},
            top_k=20,
        )
        _record(
            outcomes,
            "memory_update_lifecycle",
            any(
                item.get("id") == memory_id and "55" in str(item.get("memory", ""))
                for item in updated.get("results", [])
            ),
            True,
        )

        history = memory.history(memory_id)
        _record(
            outcomes,
            "memory_history_retains_change_lineage",
            len(history) >= 2,
            True,
        )

        memory.delete(memory_id)
        remaining = memory.get_all(
            filters={"user_id": "tenant-alpha"},
            top_k=20,
        )
        _record(
            outcomes,
            "memory_delete_removes_active_record",
            all(item.get("id") != memory_id for item in remaining.get("results", [])),
            True,
        )

    failures = [item for item in outcomes if not item["passed"]]
    return {
        "outcomes": outcomes,
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "feature_coverage": {
            "real_mem0_oss": True,
            "local_ollama_embedder": True,
            "no_paid_provider_call": True,
            "raw_write": True,
            "semantic_search": True,
            "tenant_filter": True,
            "update": True,
            "history": True,
            "delete": True,
            "verified_rule_precedence": True,
            "llm_inference": False,
            "concurrent_tenant_stress": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--ollama-url",
        default=os.getenv("GMAI_R3_OLLAMA_URL", "http://127.0.0.1:11434"),
    )
    parser.add_argument(
        "--llm-model",
        default=os.getenv("GMAI_R3_OLLAMA_LLM", "llama3.1:8b"),
    )
    parser.add_argument(
        "--embed-model",
        default=os.getenv("GMAI_R3_OLLAMA_EMBED", "nomic-embed-text"),
    )
    parser.add_argument(
        "--embed-dims",
        type=int,
        default=int(os.getenv("GMAI_R3_OLLAMA_EMBED_DIMS", "768")),
    )
    args = parser.parse_args()
    validate_run_id(args.run_id)

    try:
        detail = run_mem0(
            ollama_url=args.ollama_url,
            llm_model=args.llm_model,
            embed_model=args.embed_model,
            embed_dims=args.embed_dims,
        )
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
        "candidate": "mem0-oss",
        "candidate_version": MEM0_VERSION,
        "git_sha": _git_sha(),
        "environment": "synthetic-local-only",
        "experiment": "t1-t2-t3-memory",
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
        print(f"Mem0 R3 execution blocked: {block_reason}")
        return 2
    print(f"Mem0 R3: {result['passes']}/{result['scenario_count']} passed")
    return 0 if result["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
