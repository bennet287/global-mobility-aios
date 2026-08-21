"""Implements ``Sessions`` class."""

from __future__ import annotations

import json
import typing
from typing import Any, Optional

import fractal.util
from fractal.constants import SESSION_FILE

if typing.TYPE_CHECKING:
    from .node import Node

__all__ = []


class Sessions:
    """Per-iteration agent->session-id map plus transcript resolution."""

    def __init__(self: Sessions, node: Node) -> None:
        """Initialize ``Sessions``.

        Args:
            node: The owning ``Node`` instance.

        """
        self._node = node

    @property
    def node(self: Sessions) -> Node:
        """Return the owning node."""
        return self._node

    def get(self: Sessions, agent: str) -> Optional[str]:
        """Read an agent's session for the current iteration.

        The ``.session`` map holds the real, resumable, agent-specific
        session per agent. A missing key means the agent has no
        session started this iteration.

        Args:
            agent: Agent name.

        Returns:
            The agent's session, or ``None`` if not started.

        """
        sessions_path = self._node.node_dir / SESSION_FILE
        if sessions_path.exists():
            sessions = json.loads(sessions_path.read_text(encoding='utf-8'))
            return sessions.get(agent)
        return None

    def set(self: Sessions, agent: str, session: str) -> None:
        """Record an agent's session for the current iteration.

        Args:
            agent: Agent name.
            session: Real, agent-specific session.

        """
        # read existing sessions and merge
        sessions_path = self._node.node_dir / SESSION_FILE
        sessions = {}
        if sessions_path.exists():
            sessions = json.loads(sessions_path.read_text(encoding='utf-8'))
        sessions[agent] = session
        # write sessions -- atomic: the map rewrites every step, and a kill
        # mid-write would tear the file resume/continuity depend on
        text = json.dumps(sessions, indent=2)
        fractal.util.filesystem.write_atomic(sessions_path, text + '\n')

    def clear(self: Sessions) -> None:
        """Reset the per-iteration session map (start of each iteration)."""
        sessions_path = self._node.node_dir / SESSION_FILE
        fractal.util.filesystem.write_atomic(sessions_path, '{}\n')

    def transcript(self: Sessions, agent: str, session: str) -> dict[str, Any]:
        """Read an agent session's transcript for this node.

        Delegates to the agent backend, which owns the id validation, the
        provider's transcript layout, and the ownership-gated fallback
        discovery.

        Args:
            agent: Agent name (e.g. ``claude``).
            session: The agent session id (a ``session`` value off a step or
                iteration row).

        Returns:
            ``{agent, session, path, exists, content}`` -- ``content`` is the
            raw JSONL text (empty when absent).

        Raises:
            ValueError: If ``agent`` is unsupported, or ``session`` is not a
                bare session id (anything but ``[A-Za-z0-9_-]`` could escape
                the transcript directory).

        """
        return self._node.agent(agent).transcript(session)
