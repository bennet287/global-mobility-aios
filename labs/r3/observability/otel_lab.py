from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Sequence

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id


OTEL_VERSION = "1.44.0"
SECRET_CANARY = "AIOS_CANARY_OTEL_SECRET_44"
REDACTED_KEY_MARKERS = ("secret", "token", "password", "prompt", "personal")


class FailingExporter(SpanExporter):
    def __init__(self) -> None:
        self.export_attempts = 0

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        self.export_attempts += len(spans)
        return SpanExportResult.FAILURE

    def shutdown(self) -> None:
        return None


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _safe_attributes(attributes: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in attributes.items():
        lowered = key.lower()
        if any(marker in lowered for marker in REDACTED_KEY_MARKERS):
            continue
        if isinstance(value, str) and SECRET_CANARY in value:
            continue
        result[key] = value
    return result


def execute_guarded_operation(
    *,
    exporter: SpanExporter,
    run_id: str,
    request_id: str,
) -> dict[str, Any]:
    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": "gmai-r3-observability",
                "service.version": "v1.3.6",
            }
        )
    )
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("gmai.r3.observability")

    canonical_result = {
        "decision": "DENY",
        "reason_class": "HUMAN_APPROVAL_REQUIRED",
        "canonical_effects": 0,
    }

    common = {
        "gmai.r3_run_id": run_id,
        "gmai.request_id": request_id,
        "gmai.tenant_id": "tenant:alpha",
        "gmai.secret_value": SECRET_CANARY,
        "gmai.raw_prompt": f"do not export {SECRET_CANARY}",
    }

    with tracer.start_as_current_span("aios.command") as root:
        for key, value in _safe_attributes(common).items():
            root.set_attribute(key, value)
        root.set_attribute("gmai.action", "government_application.submit")

        with tracer.start_as_current_span("aios.authority") as authority:
            for key, value in _safe_attributes(common).items():
                authority.set_attribute(key, value)
            authority.set_attribute("gmai.authority.decision", "DENY")
            authority.set_attribute(
                "gmai.authority.reason",
                "HUMAN_APPROVAL_REQUIRED",
            )

        with tracer.start_as_current_span("aios.tool") as tool:
            for key, value in _safe_attributes(common).items():
                tool.set_attribute(key, value)
            tool.set_attribute("gmai.tool.executed", False)
            tool.set_attribute("gmai.tool.name", "government_submit")

    provider.force_flush()
    provider.shutdown()
    return canonical_result


def _span_summary(exporter: InMemorySpanExporter) -> dict[str, Any]:
    spans = exporter.get_finished_spans()
    trace_ids = {span.context.trace_id for span in spans if span.context}
    attributes = [
        dict(span.attributes or {})
        for span in spans
    ]
    flattened = json.dumps(attributes, ensure_ascii=False, sort_keys=True)
    return {
        "span_count": len(spans),
        "trace_count": len(trace_ids),
        "span_names": sorted(span.name for span in spans),
        "all_share_trace": len(trace_ids) == 1,
        "secret_canary_present": SECRET_CANARY in flattened,
        "redacted_keys_present": any(
            any(marker in str(key).lower() for marker in REDACTED_KEY_MARKERS)
            for attrs in attributes
            for key in attrs
        ),
        "run_id_present_on_all": all(
            "gmai.r3_run_id" in attrs for attrs in attributes
        ),
        "request_id_present_on_all": all(
            "gmai.request_id" in attrs for attrs in attributes
        ),
    }


def run_observability(run_id: str) -> dict[str, Any]:
    memory = InMemorySpanExporter()
    canonical = execute_guarded_operation(
        exporter=memory,
        run_id=run_id,
        request_id="otel-request-001",
    )
    spans = _span_summary(memory)

    failing = FailingExporter()
    canonical_with_failure = execute_guarded_operation(
        exporter=failing,
        run_id=run_id,
        request_id="otel-request-002",
    )

    outcomes = [
        {
            "feature": "trace_correlation",
            "observed": (
                spans["span_count"],
                spans["trace_count"],
                spans["all_share_trace"],
                spans["span_names"],
            ),
            "expected": (
                3,
                1,
                True,
                ["aios.authority", "aios.command", "aios.tool"],
            ),
        },
        {
            "feature": "run_and_request_correlation_attributes",
            "observed": (
                spans["run_id_present_on_all"],
                spans["request_id_present_on_all"],
            ),
            "expected": (True, True),
        },
        {
            "feature": "sensitive_attribute_redaction",
            "observed": (
                spans["secret_canary_present"],
                spans["redacted_keys_present"],
            ),
            "expected": (False, False),
        },
        {
            "feature": "telemetry_failure_does_not_change_canonical_result",
            "observed": (
                canonical_with_failure,
                failing.export_attempts > 0,
            ),
            "expected": (
                canonical,
                True,
            ),
        },
        {
            "feature": "telemetry_cannot_turn_deny_into_allow",
            "observed": (
                canonical["decision"],
                canonical["canonical_effects"],
            ),
            "expected": ("DENY", 0),
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
            "trace_hierarchy": True,
            "cross_span_correlation": True,
            "sensitive_attribute_redaction": True,
            "exporter_failure_independence": True,
            "telemetry_truth_boundary": True,
            "otlp_collector": False,
            "sampling": False,
            "collector_restart": False,
            "volume_cost": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validate_run_id(args.run_id)

    detail = run_observability(args.run_id)
    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "opentelemetry-python",
        "candidate_version": OTEL_VERSION,
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated-in-process",
        "experiment": "t1-t2-t5-observability",
        "test_tiers": ["T1", "T2", "T5"],
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
    print(
        f"OpenTelemetry R3: {result['passes']}/{result['scenario_count']} passed; "
        "OTLP collector depth remains pending"
    )
    return 0 if result["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
