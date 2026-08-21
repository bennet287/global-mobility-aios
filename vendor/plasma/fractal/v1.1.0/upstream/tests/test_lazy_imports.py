"""Tests for lazy subpackage loading on the ``fractal`` package root."""

from __future__ import annotations

import importlib

import pytest

__all__ = ['test_tui_serves_lazily_from_the_root']


def test_tui_serves_lazily_from_the_root() -> None:
    """``fractal.tui`` resolves via the root's lazy hook; other names raise."""
    fractal = importlib.import_module('fractal')
    assert fractal.tui is importlib.import_module('fractal.tui')
    with pytest.raises(AttributeError):
        fractal.no_such_subpackage  # noqa: B018
