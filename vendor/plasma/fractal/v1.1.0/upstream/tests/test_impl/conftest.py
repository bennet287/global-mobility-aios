"""Shared fixtures for the ``fractal`` impl backend tests.

The backends bind to the same minimal DB-backed node the core seam tests
drive, so the fixtures are reused from ``tests.test_core.conftest``
rather than duplicating the repo scaffold.
"""

from __future__ import annotations

from tests.test_core.conftest import git_repo, node_with_db  # noqa: F401
