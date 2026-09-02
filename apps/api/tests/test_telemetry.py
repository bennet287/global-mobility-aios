from __future__ import annotations

import sys
from typing import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.telemetry import setup_telemetry


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
