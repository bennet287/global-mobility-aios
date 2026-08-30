from __future__ import annotations

from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from labs.r3.observability.otel_lab import (
    FailingExporter,
    SECRET_CANARY,
    _span_summary,
    execute_guarded_operation,
    run_observability,
)


def test_observability_reference_run_is_clean() -> None:
    result = run_observability("otel-lab-20260830-001")

    assert result["failures"] == 0
    assert result["passes"] == len(result["outcomes"])
    assert result["feature_coverage"]["telemetry_truth_boundary"] is True


def test_sensitive_canary_is_not_exported() -> None:
    exporter = InMemorySpanExporter()
    execute_guarded_operation(
        exporter=exporter,
        run_id="otel-canary-20260830-001",
        request_id="request-001",
    )
    summary = _span_summary(exporter)

    assert summary["secret_canary_present"] is False
    assert SECRET_CANARY not in str(exporter.get_finished_spans())


def test_failed_export_does_not_change_denied_canonical_result() -> None:
    exporter = FailingExporter()
    result = execute_guarded_operation(
        exporter=exporter,
        run_id="otel-fail-20260830-001",
        request_id="request-002",
    )

    assert exporter.export_attempts == 3
    assert result == {
        "decision": "DENY",
        "reason_class": "HUMAN_APPROVAL_REQUIRED",
        "canonical_effects": 0,
    }
