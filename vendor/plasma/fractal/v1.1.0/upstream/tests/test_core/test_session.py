"""Test the ``fractal.core.session`` module.

``Sessions`` is a thin facade -- the per-iteration agent->session-id map
plus transcript resolution delegated to the backends -- pinned end-to-end
by the suites that consume it: session capture in ``test_agent`` and the
``test_impl`` backend modules, transcript resolution in ``test_record``,
and the chat and run-mode session weaving in ``test_chat`` and
``test_cli/test_run_modes``.
"""

from __future__ import annotations

__all__ = []
