from __future__ import annotations

import sys
from typing import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.telemetry import OrganizationSpanContext, organization_span, setup_telemetry


def _fresh_app() -> FastAPI:
    """Return a minimal FastAPI app for telemetry-only tests."""
    return FastAPI()


@pytest.fixture()
def telemetry_disabled() -> Generator[None, None, None]:
    original = settings.otel_enabled
    settings.otel_enabled = False
    yield
    settings.otel_enabled = original


@pytest.fixture()
def telemetry_enabled() -> Generator[None, None, None]:
    original = settings.otel_enabled
    settings.otel_enabled = True
    yield
    settings.otel_enabled = original


class TestTelemetryDisabled:
    def test_setup_telemetry_is_noop_when_disabled(self, telemetry_disabled, caplog):
        app = _fresh_app()
        with caplog.at_level("DEBUG", logger="app.core.telemetry"):
            setup_telemetry(app)
        assert "disabled" in caplog.text.lower()


class TestTelemetryEnabledWithoutPackages:
    def test_setup_telemetry_gracefully_skips_when_packages_missing(
        self, telemetry_enabled, monkeypatch, caplog
    ):
        """The API must remain startable even if OTEL_ENABLED=true without the SDK installed."""
        # Simulate the SDK not being installed by making the inner import fail.
        real_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__

        def _import_with_blocked_otel(name, *args, **kwargs):
            if name.startswith("opentelemetry"):
                raise ImportError(f"simulated missing package: {name}")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", _import_with_blocked_otel)
        # Ensure cached telemetry submodules are reloaded so the inner import sees the block.
        for mod in list(sys.modules):
            if mod.startswith("opentelemetry"):
                monkeypatch.delitem(sys.modules, mod, raising=False)

        app = _fresh_app()
        with caplog.at_level("WARNING", logger="app.core.telemetry"):
            setup_telemetry(app)

        assert "opentelemetry-instrumentation-fastapi is not installed" in caplog.text
        # The app object should still be usable.
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 404


class TestTelemetryEnabledWithPackages:
    def test_setup_telemetry_instruments_app_when_packages_available(
        self, telemetry_enabled, monkeypatch
    ):
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # noqa: F401
        except ImportError:
            pytest.skip("OpenTelemetry instrumentation packages not installed")

        # Avoid sending spans anywhere during the test by clearing the OTLP endpoint.
        monkeypatch.setattr(settings, "otel_exporter_otlp_endpoint", "")

        app = _fresh_app()
        setup_telemetry(app)

        # The FastAPIInstrumentor adds ASGI middleware that wraps routes in spans.
        # We verify the app remains reachable after instrumentation.
        @app.get("/telemetry-test")
        def _endpoint() -> dict:
            return {"ok": True}

        client = TestClient(app)
        response = client.get("/telemetry-test")
        assert response.status_code == 200
        assert response.json() == {"ok": True}


class _FakeSpan:
    def __init__(self) -> None:
        self.attributes: dict[str, object] = {}

    def set_attribute(self, key: str, value: object) -> None:
        self.attributes[key] = value


class _FakeSpanManager:
    def __init__(self, span: _FakeSpan, *, fail_exit: bool = False) -> None:
        self.span = span
        self.fail_exit = fail_exit

    def __enter__(self) -> _FakeSpan:
        return self.span

    def __exit__(self, *_args) -> None:
        if self.fail_exit:
            raise RuntimeError("telemetry shutdown only")


class _FakeTracer:
    def __init__(self, manager: _FakeSpanManager) -> None:
        self.manager = manager
        self.operation: str | None = None

    def start_as_current_span(self, operation: str) -> _FakeSpanManager:
        self.operation = operation
        return self.manager


def test_organization_span_emits_only_bounded_correlation_attributes(
    telemetry_enabled,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from uuid import UUID

    from opentelemetry import trace

    span = _FakeSpan()
    tracer = _FakeTracer(_FakeSpanManager(span))
    monkeypatch.setattr(trace, "get_tracer", lambda _name: tracer)
    root_id = UUID("00000000-0000-0000-0000-000000000001")
    work_id = UUID("00000000-0000-0000-0000-000000000002")

    with organization_span(
        "organization.mobility.specialist.execute",
        OrganizationSpanContext(root_id, work_id, "mobility_pathway_specialist"),
    ) as writer:
        writer.execution_identifiers(
            execution_attempt_id=UUID("00000000-0000-0000-0000-000000000003"),
            agent_run_id=UUID("00000000-0000-0000-0000-000000000004"),
            action_output_id=UUID("00000000-0000-0000-0000-000000000005"),
        )
        writer.execution_metrics(latency_ms=120, retry_count=1)
        writer.outcome("completed")

    assert tracer.operation == "organization.mobility.specialist.execute"
    assert span.attributes["aios.root_work_item.id"] == str(root_id)
    assert span.attributes["aios.work_item.id"] == str(work_id)
    assert span.attributes["aios.position.key"] == "mobility_pathway_specialist"
    assert span.attributes["aios.execution.latency_ms"] == 120
    assert span.attributes["aios.execution.retry_count"] == 1
    assert not any(
        forbidden in key
        for key in span.attributes
        for forbidden in ("tenant", "prompt", "secret", "evidence", "response")
    )


def test_organization_span_shutdown_failure_does_not_change_domain_result(
    telemetry_enabled,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from uuid import uuid4

    from opentelemetry import trace

    tracer = _FakeTracer(_FakeSpanManager(_FakeSpan(), fail_exit=True))
    monkeypatch.setattr(trace, "get_tracer", lambda _name: tracer)

    with organization_span(
        "organization.mobility.live_provider_cycle",
        OrganizationSpanContext(uuid4()),
    ):
        domain_result = "preserved"

    assert domain_result == "preserved"


def test_organization_span_rejects_unbounded_operation(telemetry_disabled) -> None:
    from uuid import uuid4

    with pytest.raises(ValueError, match="unsupported organization telemetry operation"):
        with organization_span("arbitrary.domain.payload", OrganizationSpanContext(uuid4())):
            pass
