"""Functions for deriving display titles."""

from __future__ import annotations

__all__ = ['name_to_title']


def name_to_title(name: str) -> str:
    """Turn a node-name slug into a display title (``foo_bar`` -> ``Foo Bar``).

    Args:
        name: A node name -- a leaf slug of letters, digits, and underscores.

    Returns:
        The de-slugged, title-cased name.

    Examples:
        >>> name_to_title('foo_bar')
        'Foo Bar'
        >>> name_to_title('foo_')
        'Foo'

    """
    # collapse whitespace so leading/trailing/repeated underscores do not
    # leak stray-space titles (e.g. foo_ -> 'Foo' rather than 'Foo ')
    return ' '.join(name.replace('_', ' ').split()).title()
