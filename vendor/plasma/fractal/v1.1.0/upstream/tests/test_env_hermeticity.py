"""Tests that the suite is hermetic against a live node's exported env.

A running fractal node exports ``_NODE`` (plus ``NODE_DIR``, ``MAX_DEPTH``,
``MAX_CHILDREN``, ``MAX_COST``). If the suite inherits them, in-process
``Node.init()`` calls adopt the live node as parent via ``resolve_caller``
and create real stray nodes in the live DB. The autouse fixture in
``tests/conftest.py`` strips them; these tests guard that contract.
"""

from __future__ import annotations

import os

from fractal.core.node import Node

from .conftest import _LOOP_ENV_VARS

__all__ = [
    'test_loop_env_neutralized',
    'test_resolve_caller_is_none_in_hermetic_suite',
]


def test_loop_env_neutralized() -> None:
    """The inherited loop env must not leak into any test.

    With these set, ``Node.init()`` adopts the ambient node as parent
    (``resolve_caller``) and can spawn stray nodes in the live DB.
    """
    leaked = {var: os.environ[var] for var in _LOOP_ENV_VARS if var in os.environ}
    assert not leaked, f'loop env leaked into the suite: {leaked}'


def test_resolve_caller_is_none_in_hermetic_suite() -> None:
    """No ambient node is adopted as parent in a hermetic suite.

    ``Node.init()`` resolves its parent via ``resolve_caller`` and only
    falls back to its own repo when that is ``None``. If the ambient
    ``_NODE`` leaks, the live node is adopted instead -- the root of the
    stray-node bug. ``resolve_caller`` is read-only, so this is safe.
    """
    assert Node.resolve_caller() is None
