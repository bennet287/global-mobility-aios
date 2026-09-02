"""Implements ``TuiActions`` -- the cockpit's only write surface.

The single module that calls mutating ``Radio``
methods, invoked exclusively from explicit key/submit handlers (never on a
read/poll path). The acting identity is always the **user (root) node** -- the
human at the cockpit; a send's target (whose channel-space hosts the message)
is passed as ``node=<branch>``. All message methods take a ``message_uuid``
(globally unique), and every read lands a ``reads`` receipt naming the root.
"""

from __future__ import annotations

import typing
from typing import Optional

from fractal.core.radio import Radio

if typing.TYPE_CHECKING:
    from .data import TuiData

__all__ = ['TuiActions']


class TuiActions:
    """Explicit radio writes (send / reply / react / save / read receipt)."""

    def __init__(self: TuiActions, data: TuiData) -> None:
        """Initialize ``TuiActions``.

        Args:
            data: The read stack (supplies the root node the writes act as).

        """
        self._data = data
        self._radio = Radio(data.root)

    def send(
        self: TuiActions,
        *,
        target: str,
        channel: str,
        subject: str,
        data: str,
        priority: int,
    ) -> str:
        """Send a message to ``target``'s channel as the root node.

        Args:
            target: The branch whose channel receives the message.
            channel: The channel name.
            subject: The message subject.
            data: The message body.
            priority: Priority (0-10).

        Returns:
            The new message's 8-char UUID.

        """
        message_uuid, _, _ = self._radio.send(
            node=target,
            channel=channel,
            subject=subject,
            data=data,
            priority=priority,
        )
        return message_uuid

    def reply(
        self: TuiActions,
        *,
        message_uuid: str,
        data: str,
        priority: Optional[int] = None,
    ) -> str:
        """Reply to a message (routed to its resolved destination).

        Args:
            message_uuid: The parent message's UUID.
            data: The reply body.
            priority: Priority override (inherits the parent's when omitted).

        Returns:
            The reply's 8-char UUID.

        """
        reply_uuid, _, _ = self._radio.reply(
            message_uuid=message_uuid,
            data=data,
            priority=priority,
        )
        return reply_uuid

    def react(self: TuiActions, *, message_uuid: str, value: int) -> None:
        """React (+1/-1) to a message as the root node."""
        self._radio.react(message_uuid, value)

    def save(self: TuiActions, *, message_uuid: str) -> None:
        """Save a message into the root's archive."""
        self._radio.save(message_uuid)

    def read(self: TuiActions, *, message_uuid: str) -> dict:
        """Mark a message read (called only when the user opens it).

        Writes a ``reads`` receipt naming the root -- the unread dot clears
        on the next snapshot.

        Returns:
            The message row, unpacked from ``Radio.read``'s one-row list.

        """
        [message] = self._radio.read(message_uuid)
        return message
