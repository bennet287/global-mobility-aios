"""Tests for TUI packaging: the stylesheet must ship inside the package."""

from __future__ import annotations

import pathlib
import tomllib

import fractal.tui

__all__ = ['test_stylesheet_ships_as_package_data']


def test_stylesheet_ships_as_package_data() -> None:
    """``app.tcss`` must ship beside ``fractal.tui.app``.

    ``FractalApp.CSS_PATH`` resolves the stylesheet next to the module (like
    ``schema.sql``), so under a non-editable install a missing file crashes
    ``fractal open`` at App construction. A wheel packs no bare ``.tcss``
    unless pyproject's poetry ``include`` lists it explicitly -- pin both the
    file and the include entry.
    """
    package = pathlib.Path(fractal.tui.__file__).parent
    stylesheet = package / 'app.tcss'
    assert stylesheet.is_file(), (
        'app.tcss missing from the fractal.tui package; under a non-editable '
        'install FractalApp would raise at stylesheet parse'
    )
    pyproject = package.parent.parent / 'pyproject.toml'
    build = tomllib.loads(pyproject.read_text(encoding='utf-8'))
    includes = [entry['path'] for entry in build['tool']['poetry']['include']]
    assert 'fractal/tui/app.tcss' in includes, (
        'pyproject include must list fractal/tui/app.tcss or wheels ship '
        'without the stylesheet'
    )
