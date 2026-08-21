"""Test the ``fractal.util.time`` module."""

from __future__ import annotations

import re

import fractal.util.time
from tests._helpers import _past_timestamp

__all__ = [
    'test_utc_now_matches_sql_timestamp_format',
    'test_elapsed_measures_wall_clock_elapsed',
]


def test_utc_now_matches_sql_timestamp_format() -> None:
    """``utc_now`` stamps carry millisecond precision in the SQL default shape.

    The fixed-width format is what lets Python-sourced stamps sort lexically
    against the SQL ``strftime`` defaults.
    """
    stamp = fractal.util.time.utc_now()
    assert re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z', stamp)


def test_elapsed_measures_wall_clock_elapsed() -> None:
    """``elapsed`` returns seconds since a back-dated timestamp."""
    elapsed = fractal.util.time.elapsed(_past_timestamp(5.0))
    assert 5.0 <= elapsed < 6.0
