"""Test the ``fractal.exceptions`` module."""

from __future__ import annotations

from fractal.exceptions import AbstractMethodError

__all__ = ['test_abstract_method_error_names_the_concrete_class']


def test_abstract_method_error_names_the_concrete_class() -> None:
    """The error reads as ``NotImplementedError`` naming the concrete class."""

    class Concrete:
        """Concrete class leaving a mandatory hook unimplemented."""

    error = AbstractMethodError(Concrete())
    assert isinstance(error, NotImplementedError)
    assert 'Concrete' in str(error)
