"""Optional OpenTelemetry instrumentation for the FastAPI backend.

This module is a bounded Technology Radar V1.1 Wave 1 pilot. It keeps the API
startable whether or not the OpenTelemetry SDK is installed, and it is disabled
by default. When enabled, it instruments the FastAPI application with
vendor-neutral traces and exports them via OTLP.

The adapter follows the AIOS Semantic Sovereignty Principle: telemetry remains
engineering trace only and never substitutes for OrganizationActivity,
AuditLog, evidence provenance, or business authority records.
"""

from __future__ import annotations

import logging
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterator
from uuid import UUID

from app.core.config import settings

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)

_ORGANIZATION_OPERATIONS = frozenset(
    {
        "organization.mobility.live_provider_cycle",
        "organization.mobility.specialist.execute",
    }
)


@dataclass(frozen=True, slots=True)
class OrganizationSpanContext:
    """Privacy-bounded correlation identifiers for one durable execution path."""

    root_work_item_id: UUID
    work_item_id: UUID | None = None
    position_key: str | None = None


class OrganizationTelemetrySpan:
    """Narrow telemetry writer; arbitrary domain payloads cannot be attached."""

    def __init__(self, span: object | None) -> None:
        self._span = span

    def _set(self, key: str, value: str | int | bool) -> None:
        if self._span is None:
            return
        try:
            self._span.set_attribute(key, value)  # type: ignore[attr-defined]
        except Exception:
            logger.debug("OpenTelemetry span attribute write failed", exc_info=True)

    def execution_identifiers(
        self,
        *,
        execution_attempt_id: UUID,
        agent_run_id: UUID,
        action_output_id: UUID,
    ) -> None:
        self._set("aios.execution_attempt.id", str(execution_attempt_id))
        self._set("aios.agent_run.id", str(agent_run_id))
        self._set("aios.action_output.id", str(action_output_id))

    def execution_metrics(self, *, latency_ms: int, retry_count: int) -> None:
        self._set("aios.execution.latency_ms", max(0, latency_ms))
        self._set("aios.execution.retry_count", max(0, retry_count))

    def fresh_snapshot_count(self, count: int) -> None:
        self._set("aios.fresh_retrieval.snapshot_count", max(0, count))

    def acceptance_candidate(self, value: bool) -> None:
        self._set("aios.acceptance.full_l_candidate", value)

    def outcome(self, value: str) -> None:
        if value not in {"completed", "failed", "replayed", "rejected"}:
            raise ValueError("unsupported organization telemetry outcome")
        self._set("aios.execution.outcome", value)


@contextmanager
def organization_span(
    operation: str,
    context: OrganizationSpanContext,
) -> Iterator[OrganizationTelemetrySpan]:
    """Create a fail-open, privacy-allowlisted span for canonical L correlation.

    Telemetry startup, writes, and shutdown are deliberately unable to change the
    domain result. Tenant identifiers, prompts, evidence content, secrets, and
    provider responses are not accepted by this contract.
    """

    if operation not in _ORGANIZATION_OPERATIONS:
        raise ValueError("unsupported organization telemetry operation")
    if not settings.otel_enabled:
        yield OrganizationTelemetrySpan(None)
        return

    try:
        from opentelemetry import trace

        span_manager = trace.get_tracer(__name__).start_as_current_span(operation)
        span = span_manager.__enter__()
    except Exception:
        logger.debug("OpenTelemetry organization span startup failed", exc_info=True)
        yield OrganizationTelemetrySpan(None)
        return

    writer = OrganizationTelemetrySpan(span)
    writer._set("aios.root_work_item.id", str(context.root_work_item_id))
    if context.work_item_id is not None:
        writer._set("aios.work_item.id", str(context.work_item_id))
    if context.position_key is not None:
        writer._set("aios.position.key", context.position_key)

    try:
        yield writer
    except BaseException:
        error_info = sys.exc_info()
        try:
            span_manager.__exit__(*error_info)
        except Exception:
            logger.debug("OpenTelemetry organization span shutdown failed", exc_info=True)
        raise
    else:
        try:
            span_manager.__exit__(None, None, None)
        except Exception:
            logger.debug("OpenTelemetry organization span shutdown failed", exc_info=True)

_RESOURCE_ATTRIBUTES = {
    "service.name": settings.otel_service_name,
    "service.version": settings.otel_service_version,
}


def _configure_tracing() -> None:
    """Set up a tracer provider and OTLP exporter if an endpoint is configured."""
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create(_RESOURCE_ATTRIBUTES)
    provider = TracerProvider(resource=resource)

    endpoint = settings.otel_exporter_otlp_endpoint.strip()
    if endpoint:
        # OTLP exporter is optional; import only when needed.
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        exporter = OTLPSpanExporter(endpoint=endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        logger.info("OpenTelemetry OTLP trace exporter configured for %s", endpoint)
    else:
        logger.info("OpenTelemetry tracing enabled without OTLP exporter (in-process only)")

    trace.set_tracer_provider(provider)


def setup_telemetry(app: "FastAPI") -> None:
    """Instrument the FastAPI app when OpenTelemetry is enabled and installed.

    Missing packages are logged as a warning and the app continues to start
    normally. This preserves the local-first, dependency-optional posture of the
    pilot.
    """
    if not settings.otel_enabled:
        logger.debug("OpenTelemetry instrumentation disabled (OTEL_ENABLED=false)")
        return

    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    except ImportError:  # pragma: no cover - exercised by a dedicated fallback test
        logger.warning(
            "OTEL_ENABLED=true but opentelemetry-instrumentation-fastapi is not installed; "
            "continuing without telemetry."
        )
        return

    try:
        _configure_tracing()
        FastAPIInstrumentor.instrument_app(app)
        logger.info("OpenTelemetry FastAPI instrumentation enabled")
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.warning("OpenTelemetry instrumentation failed: %s; continuing without it.", exc)
