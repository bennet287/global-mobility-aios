from __future__ import annotations

from pathlib import Path

from app.main import app


def test_app_uses_lifespan_startup_hook() -> None:
    assert app.router.lifespan_context is not None


def test_main_does_not_use_deprecated_on_event_startup() -> None:
    main_source = Path(__file__).resolve().parents[1] / "app" / "main.py"

    assert "@app.on_event" not in main_source.read_text(encoding="utf-8")
