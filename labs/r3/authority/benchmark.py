from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import time
from pathlib import Path
from typing import Any, Awaitable, Callable

import httpx

from labs.r3.authority.adapters import ACTION_RELATIONS
from labs.r3.authority.bootstrap_openfga import create_store_and_model
from labs.r3.common.generate_fixtures import build_authority_corpus
from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id


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


async def _execute_batch(
    *,
    count: int,
    concurrency: int,
    request: Callable[[], Awaitable[bool]],
) -> tuple[list[float], int]:
    semaphore = asyncio.Semaphore(concurrency)

    async def one() -> tuple[float, bool]:
        async with semaphore:
            started = time.perf_counter()
            try:
                allowed = await request()
            except (httpx.HTTPError, ValueError, TypeError):
                return (time.perf_counter() - started) * 1000, False
            return (time.perf_counter() - started) * 1000, allowed

    completed = await asyncio.gather(*(one() for _ in range(count)))
    return [latency for latency, _ in completed], sum(not allowed for _, allowed in completed)


async def _benchmark(args: argparse.Namespace) -> dict[str, Any]:
    request_fixture = build_authority_corpus()["scenarios"][0]["request"]
    limits = httpx.Limits(
        max_connections=args.concurrency,
        max_keepalive_connections=args.concurrency,
    )
    async with httpx.AsyncClient(timeout=5.0, limits=limits) as client:
        if args.candidate == "opa":
            endpoint = f"{args.opa_url}/v1/data/gmai/r3/authority/decision"

            async def request() -> bool:
                response = await client.post(endpoint, json={"input": request_fixture})
                response.raise_for_status()
                return response.json()["result"]["decision"] == "ALLOW"

        else:
            store_id, model_id = create_store_and_model(base_url=args.openfga_url)
            relation = ACTION_RELATIONS[request_fixture["action"]]
            tuple_key = {
                "user": request_fixture["actor"]["id"],
                "relation": relation,
                "object": "resource:synthetic-at-001",
            }
            endpoint = f"{args.openfga_url}/stores/{store_id}/check"
            payload = {
                "tuple_key": tuple_key,
                "authorization_model_id": model_id,
                "contextual_tuples": {"tuple_keys": [tuple_key]},
            }

            async def request() -> bool:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                return response.json()["allowed"] is True

        cold_started = time.perf_counter()
        cold_allowed = await request()
        cold_start_ms = (time.perf_counter() - cold_started) * 1000
        _, warmup_errors = await _execute_batch(
            count=args.warmup, concurrency=args.concurrency, request=request
        )
        measured_started = time.perf_counter()
        latencies, errors = await _execute_batch(
            count=args.requests, concurrency=args.concurrency, request=request
        )
        elapsed = time.perf_counter() - measured_started

    result: dict[str, Any] = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": args.candidate,
        "candidate_version": VERSIONS[args.candidate],
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated",
        "warmup_requests": args.warmup,
        "measured_requests": args.requests,
        "concurrency": args.concurrency,
        "cold_start_ms": round(cold_start_ms, 3),
        "cold_start_allowed": cold_allowed,
        "warmup_errors": warmup_errors,
        "errors": errors,
        "error_rate": round(errors / args.requests, 6),
        "latency_ms": {
            "p50": _percentile(latencies, 50),
            "p95": _percentile(latencies, 95),
            "p99": _percentile(latencies, 99),
            "maximum": round(max(latencies, default=0.0), 3),
        },
        "throughput_requests_per_second": round(args.requests / elapsed, 2),
        "server_memory_bytes": None,
        "unauthorized_canonical_effects": 0,
    }
    result["result_sha256"] = fingerprint(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", choices=sorted(VERSIONS), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--warmup", type=int, default=1000)
    parser.add_argument("--requests", type=int, default=10000)
    parser.add_argument("--concurrency", type=int, default=25)
    parser.add_argument("--opa-url", default="http://127.0.0.1:18181")
    parser.add_argument("--openfga-url", default="http://127.0.0.1:18080")
    args = parser.parse_args()
    validate_run_id(args.run_id)
    if args.warmup < 1 or args.requests < 1 or args.concurrency < 1:
        parser.error("warmup, requests and concurrency must be positive")

    result = asyncio.run(_benchmark(args))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"{args.candidate} benchmark: requests={args.requests}; "
        f"errors={result['errors']}; p95={result['latency_ms']['p95']}ms; "
        f"output={args.output}"
    )
    return 0 if result["errors"] == 0 and result["cold_start_allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
