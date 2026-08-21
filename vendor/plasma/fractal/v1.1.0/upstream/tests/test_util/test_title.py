"""Test the ``fractal.util.title`` module."""

from __future__ import annotations

import pytest

from fractal.util import name_to_title

__all__ = ['test_name_to_title']


@pytest.mark.parametrize(
    argnames=('name', 'expected'),
    argvalues=[
        ('backend', 'Backend'),
        ('data_pipeline', 'Data Pipeline'),
        ('aloff_wallach_nu_invariant', 'Aloff Wallach Nu Invariant'),
        ('main', 'Main'),
    ],
)
def test_name_to_title(name: str, expected: str) -> None:
    """An underscore slug becomes a title-cased, space-separated display name."""
    assert name_to_title(name) == expected
