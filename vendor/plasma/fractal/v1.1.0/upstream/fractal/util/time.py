"""Functions for UTC timestamps and elapsed durations."""

from __future__ import annotations

import datetime as dt
import time

__all__ = []


def utc_now() -> str:
    """Return current UTC time as ISO 8601 (millisecond precision).

    Matches the ``strftime('%Y-%m-%dT%H:%M:%fZ')`` format used by the SQL
    ``created_at`` defaults (``core/schema.sql``), so the Python-sourced
    ``started_at``/``ended_at`` stamps share the same precision and sort
    against them.
    """
    result = dt.datetime.now(dt.UTC)
    milliseconds = result.microsecond // 1000
    return result.strftime('%Y-%m-%dT%H:%M:%S.') + f'{milliseconds:03d}Z'


def elapsed(started_at: str) -> float:
    """Compute seconds elapsed since a start timestamp.

    Args:
        started_at: ISO 8601 timestamp with fractional seconds.

    Returns:
        Elapsed seconds as a float.

    Examples:
        >>> 0.0 <= elapsed(utc_now()) < 1.0
        True

    """
    parsed = dt.datetime.strptime(started_at, '%Y-%m-%dT%H:%M:%S.%fZ')
    parsed = parsed.replace(tzinfo=dt.UTC)
    return time.time() - parsed.timestamp()
