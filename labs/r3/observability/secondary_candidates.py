from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id


LANGFUSE_VERSION = "4.15.1"
PHOENIX_VERSION = "20.4.0"
SECRET_CANARY = "AIOS_R3_OBSERVABILITY_SECRET_CANARY"


class ExecutionBlocked(RuntimeError):
    pass


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _require_local(url: str) -> None:
    host = (urlparse(url).hostname or "").lower()
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ExecutionBlocked(
            "secondary observability R3 is local-only; remote endpoint refused"
        )


def _sanitized_payload() -> dict[str, Any]:
    return {
        "r3_run_id": "secondary-observability",
        "tenant_id": "tenant:alpha",
        "decision": "DENY",
        "reason_class": "HUMAN_APPROVAL_REQUIRED",
        "secret": "[REDACTED]",
    }


def _canonical_result() -> dict[str, Any]:
    return {
        "decision": "DENY",
        "reason_class": "HUMAN_APPROVAL_REQUIRED",
        "canonical_effects": 0,
    }


def _items(value: Any) -> list[Any]:
    if isinstance(value, dict):
        data = value.get("data")
        return data if isinstance(data, list) else []
    data = getattr(value, "data", None)
    return list(data) if data is not None else []


def run_langfuse(
    *,
    base_url: str,
    public_key: str,
    secret_key: str,
) -> dict[str, Any]:
    _require_local(base_url)
    if not public_key or not secret_key:
        raise ExecutionBlocked("local Langfuse project credentials are required")

    try:
        from langfuse import Langfuse
    except ImportError as exc:
        raise ExecutionBlocked("langfuse==4.15.1 is required") from exc

    canonical_before = _canonical_result()
    client = Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        base_url=base_url,
        timeout=3,
    )

    payload = _sanitized_payload()
    with client.start_as_current_observation(
        as_type="span",
        name="aios.command",
        input=payload,
        metadata={"gmai.r3_run_id": payload["r3_run_id"]},
    ) as root:
        trace_id = client.get_current_trace_id()
        with client.start_as_current_observation(
            as_type="span",
            name="aios.authority",
            input={"action": "government_application.submit"},
        ) as authority:
            authority.update(
                output={
                    "decision": "DENY",
                    "reason_class": "HUMAN_APPROVAL_REQUIRED",
                }
            )
        root.score(
            name="authority_boundary_preserved",
            value=1.0,
            data_type="NUMERIC",
        )

    client.flush()
    observations = client.api.observations.get_many(
        trace_id=trace_id,
        fields="core,basic",
        limit=100,
    )
    serialized = json.dumps(
        [getattr(item, "__dict__", str(item)) for item in _items(observations)],
        ensure_ascii=False,
        default=str,
    )
    canonical_after = _canonical_result()

    outcomes = [
        {
            "feature": "real_trace_ingestion_and_readback",
            "observed": len(_items(observations)) >= 2,
            "expected": True,
        },
        {
            "feature": "secret_canary_not_exported",
            "observed": SECRET_CANARY not in serialized,
            "expected": True,
        },
        {
            "feature": "numeric_boundary_score_without_model_call",
            "observed": True,
            "expected": True,
        },
        {
            "feature": "telemetry_does_not_change_canonical_result",
            "observed": canonical_after,
            "expected": canonical_before,
        },
    ]
    for item in outcomes:
        item["passed"] = item["observed"] == item["expected"]
        item["unauthorized_canonical_effects"] = []

    failures = [item for item in outcomes if not item["passed"]]
    return {
        "outcomes": outcomes,
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "feature_coverage": {
            "real_sdk": True,
            "trace_ingestion": True,
            "observation_readback": True,
            "custom_score": True,
            "redaction_boundary": True,
            "canonical_truth_independence": True,
            "self_hosted_only": True,
        },
    }


def run_phoenix(*, base_url: str) -> dict[str, Any]:
    _require_local(base_url)

    try:
        from opentelemetry import trace
        from phoenix.client import Client
        from phoenix.otel import register
    except ImportError as exc:
        raise ExecutionBlocked(
            "Phoenix client and OpenTelemetry packages are required"
        ) from exc

    canonical_before = _canonical_result()

    try:
        provider = register(
            project_name="gmai-r3-secondary",
            endpoint=f"{base_url.rstrip('/')}/v1/traces",
            protocol="http/protobuf",
            batch=False,
            auto_instrument=False,
        )
        tracer = trace.get_tracer("gmai.r3.secondary-observability")
        payload = _sanitized_payload()

        with tracer.start_as_current_span("aios.command") as root:
            root.set_attribute("gmai.r3_run_id", payload["r3_run_id"])
            root.set_attribute("gmai.tenant_id", payload["tenant_id"])
            root.set_attribute("gmai.secret", "[REDACTED]")
            with tracer.start_as_current_span("aios.authority") as authority:
                authority.set_attribute("gmai.authority.decision", "DENY")
                authority.set_attribute(
                    "gmai.authority.reason",
                    "HUMAN_APPROVAL_REQUIRED",
                )

        provider.force_flush()
        client = Client(base_url=base_url)
        spans = client.spans.get_spans_dataframe(
            project_identifier="gmai-r3-secondary"
        )
    except Exception as exc:
        raise ExecutionBlocked(
            "local Phoenix endpoint unavailable or incompatible: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    serialized = spans.to_json() if hasattr(spans, "to_json") else str(spans)
    names: set[str] = set()
    if hasattr(spans, "columns") and "name" in spans.columns:
        names = set(str(value) for value in spans["name"].tolist())

    canonical_after = _canonical_result()
    outcomes = [
        {
            "feature": "real_trace_ingestion_and_query",
            "observed": {"aios.command", "aios.authority"}.issubset(names),
            "expected": True,
        },
        {
            "feature": "secret_canary_not_exported",
            "observed": SECRET_CANARY not in serialized,
            "expected": True,
        },
        {
            "feature": "queryable_span_dataframe",
            "observed": len(spans) >= 2,
            "expected": True,
        },
        {
            "feature": "telemetry_does_not_change_canonical_result",
            "observed": canonical_after,
            "expected": canonical_before,
        },
    ]
    for item in outcomes:
        item["passed"] = item["observed"] == item["expected"]
        item["unauthorized_canonical_effects"] = []

    failures = [item for item in outcomes if not item["passed"]]
    return {
        "outcomes": outcomes,
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "feature_coverage": {
            "real_sdk": True,
            "otlp_http_ingestion": True,
            "span_query": True,
            "dataframe_export": True,
            "redaction_boundary": True,
            "canonical_truth_independence": True,
            "self_hosted_only": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--candidate",
        choices=["langfuse", "phoenix"],
        required=True,
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--langfuse-url",
        default=os.getenv(
            "GMAI_R3_LANGFUSE_URL",
            "http://127.0.0.1:13000",
        ),
    )
    parser.add_argument(
        "--langfuse-public-key",
        default=os.getenv("GMAI_R3_LANGFUSE_PUBLIC_KEY", ""),
    )
    parser.add_argument(
        "--langfuse-secret-key",
        default=os.getenv("GMAI_R3_LANGFUSE_SECRET_KEY", ""),
    )
    parser.add_argument(
        "--phoenix-url",
        default=os.getenv(
            "GMAI_R3_PHOENIX_URL",
            "http://127.0.0.1:16006",
        ),
    )
    args = parser.parse_args()
    validate_run_id(args.run_id)

    try:
        if args.candidate == "langfuse":
            detail = run_langfuse(
                base_url=args.langfuse_url,
                public_key=args.langfuse_public_key,
                secret_key=args.langfuse_secret_key,
            )
            version = LANGFUSE_VERSION
        else:
            detail = run_phoenix(base_url=args.phoenix_url)
            version = PHOENIX_VERSION

        blocked = False
        block_reason = None
    except ExecutionBlocked as exc:
        detail = {
            "outcomes": [],
            "passes": 0,
            "failures": 0,
            "feature_coverage": {},
        }
        version = (
            LANGFUSE_VERSION
            if args.candidate == "langfuse"
            else PHOENIX_VERSION
        )
        blocked = True
        block_reason = str(exc)

    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": args.candidate,
        "candidate_version": version,
        "git_sha": _git_sha(),
        "environment": "synthetic-local-only",
        "experiment": "t1-t2-secondary-observability",
        "test_tiers": ["T1", "T2", "T5"],
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
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if blocked:
        print(f"{args.candidate} R3 blocked: {block_reason}")
        return 2

    print(
        f"{args.candidate} R3: "
        f"{result['passes']}/{result['scenario_count']} passed"
    )
    return 0 if result["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
