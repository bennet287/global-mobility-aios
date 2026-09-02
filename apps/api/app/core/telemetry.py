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
from typing import TYPE_CHECKING

from app.core.config import settings

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)

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
