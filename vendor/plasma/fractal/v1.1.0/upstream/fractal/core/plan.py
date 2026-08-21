"""Implements ``Plans`` class."""

from __future__ import annotations

import pathlib
import re
import typing
from typing import Optional

import fractal.util

if typing.TYPE_CHECKING:
    from .node import Node

__all__ = []


class Plans:
    """Plan files under the node's ``plans/`` directory."""

    def __init__(self: Plans, node: Node) -> None:
        """Initialize ``Plans``.

        Args:
            node: The owning ``Node`` instance.

        """
        self._node = node

    @property
    def node(self: Plans) -> Node:
        """Return the owning node."""
        return self._node

    def init(
        self: Plans,
        *,
        iter_ref: str,
        name: str,
        title: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> pathlib.Path:
        """Create a plan file seeded with its H1 and return its path.

        Names the file ``{timestamp}-{run.iter}-{name}.md`` -- the timestamp
        defaults to the current UTC time, so two plans written in the same
        iteration get distinct names -- and seeds ``# {run.iter} {title}`` as
        the first line so the run/iteration is human-readable in the file (the
        title defaults to the de-slugged ``name``). Plans are found later by
        globbing the ``{run.iter}`` segment (see :meth:`list`).

        Args:
            iter_ref: The ``{run}.{iter}`` reference (e.g. ``12.5``).
            name: Short descriptive slug for this plan (snake_case).
            title: H1 title; defaults to the de-slugged ``name`` when omitted.
            timestamp: Filename timestamp prefix; defaults to the current UTC
                time.

        Returns:
            Absolute path to the created plan file.

        """
        # validate the slug and the iteration reference at the filesystem
        # boundary (no traversal / odd names)
        if not re.fullmatch(r'[A-Za-z0-9_]+', name):
            raise ValueError(f'Invalid plan name: {name!r}')
        if not re.fullmatch(r'[0-9]+\.[0-9]+', iter_ref):
            raise ValueError(f'Invalid iteration reference: {iter_ref!r}')
        # stamp now (so same-iteration plans don't collide) and seed the H1
        timestamp = timestamp or fractal.util.time.utc_now()
        path = self._node.node_dir / 'plans' / f'{timestamp}-{iter_ref}-{name}.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        heading = title if title else fractal.util.name_to_title(name)
        # exclusive create -- an exact-name collision must surface rather
        # than silently replace the earlier plan
        with path.open('x', encoding='utf-8') as file:
            file.write(f'# {iter_ref} {heading}\n\n')
        return path

    def list(
        self: Plans,
        *,
        iter_ref: str,
    ) -> list[pathlib.Path]:
        """List an iteration's plan files.

        Resolves "this iteration's plans" by globbing the ``{run.iter}``
        segment, so it returns every plan the iteration wrote -- zero, one, or
        many -- regardless of each plan's own timestamp and without relying on
        modification time. Returns an empty list when the node has no plans
        directory yet.

        Args:
            iter_ref: The ``{run}.{iter}`` reference (e.g. ``12.5``).

        Returns:
            Matching plan paths, sorted by name (chronological by timestamp).

        """
        # validate the iteration reference at the glob boundary (a stray
        # metacharacter would match other iterations' plans)
        if not re.fullmatch(r'[0-9]+\.[0-9]+', iter_ref):
            raise ValueError(f'Invalid iteration reference: {iter_ref!r}')
        plans_dir = self._node.node_dir / 'plans'
        if not plans_dir.is_dir():
            return []
        return sorted(plans_dir.glob(f'*-{iter_ref}-*.md'))
