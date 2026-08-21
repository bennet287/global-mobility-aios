"""Test the ``fractal.util.duration`` module."""

from __future__ import annotations

import pytest

from fractal.util import format_age, parse_duration_seconds

__all__ = [
    'test_parse_duration_seconds_reads_suffixes',
    'test_parse_duration_seconds_rejects_malformed',
    'test_format_age_truncates_to_largest_unit',
]


@pytest.mark.parametrize(
    argnames=('value', 'expected'),
    argvalues=[
        ('30s', 30.0),
        ('10m', 600.0),
        ('1.5h', 5400.0),
        ('2d', 172800.0),
        ('0s', 0.0),
    ],
)
def test_parse_duration_seconds_reads_suffixes(value: str, expected: float) -> None:
    """``parse_duration_seconds`` converts ``s``/``m``/``h``/``d`` magnitudes to seconds."""
    assert parse_duration_seconds(value) == expected


@pytest.mark.parametrize('value', ['30', 'abc', 'm', '', '10x'])
def test_parse_duration_seconds_rejects_malformed(value: str) -> None:
    """``parse_duration_seconds`` returns ``None`` for a missing/unknown suffix."""
    assert parse_duration_seconds(value) is None


@pytest.mark.parametrize(
    argnames=('seconds', 'expected'),
    argvalues=[
        (43.0, '43s'),
        (59.9, '59s'),
        (1_080.0, '18m'),
        (3_599.0, '59m'),
        (90_000.0, '25h'),
    ],
)
def test_format_age_truncates_to_largest_unit(seconds: float, expected: str) -> None:
    """``format_age`` truncates, so ``60s``/``60m`` never render at a boundary."""
    assert format_age(seconds) == expected
