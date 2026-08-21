"""Functions for parsing and formatting durations."""

from __future__ import annotations

import re
from typing import Optional

__all__ = [
    'parse_duration_seconds',
    'format_age',
]

_SUFFIX_SECONDS = {
    's': 1,
    'm': 60,
    'h': 3_600,
    'd': 86_400,
}


def parse_duration_seconds(value: str) -> Optional[float]:
    """Parse a duration string (e.g. ``30s``, ``10m``, ``1.5h``, ``2d``) into seconds.

    Args:
        value: Duration string of the form ``<number><s|m|h|d>``.

    Returns:
        Seconds, or ``None`` when ``value`` is not ``<number><s|m|h|d>`` --
        callers decide whether to raise or fall back.

    Examples:
        >>> parse_duration_seconds('30s')
        30.0
        >>> parse_duration_seconds('1.5h')
        5400.0
        >>> parse_duration_seconds('soon') is None
        True

    """
    match = re.fullmatch(r'([0-9]*\.?[0-9]+)([smhd])', value.strip())
    if match is None:
        return None
    return float(match.group(1)) * _SUFFIX_SECONDS[match.group(2)]


def format_age(seconds: float) -> str:
    """Render elapsed seconds as a compact age (``43s`` / ``18m`` / ``1h``).

    Args:
        seconds: Elapsed seconds.

    Returns:
        The age truncated to its largest unit (seconds, minutes, or hours).

    Examples:
        >>> format_age(43.0)
        '43s'
        >>> format_age(1_080.0)
        '18m'
        >>> format_age(90_000.0)
        '25h'

    """
    # truncate, never round -- rounding up crosses a unit boundary ('60s')
    if seconds < 60:
        return f'{int(seconds)}s'
    if seconds < 3_600:
        return f'{int(seconds / 60)}m'
    return f'{int(seconds / 3_600)}h'
