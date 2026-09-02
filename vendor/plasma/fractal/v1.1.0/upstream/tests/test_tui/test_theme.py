"""Test the ``fractal.tui.theme`` module.

Minimal mirror: the stylesheet's token feed must resolve. Every color slot is
pinned on the ``THEME`` byte-exact (bypassing Textual's HSL round-trip) in
both palettes, the palettes share one key set, and the numeric tokens with a
TCSS consumer arrive as stylesheet-ready strings.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator

import pytest

from fractal.tui import theme
from fractal.tui.app import FractalApp

__all__ = [
    'test_every_color_slot_is_pinned_byte_exact',
    'test_palettes_share_one_key_set',
    'test_css_variables_are_stylesheet_ready',
    'test_light_palette_boots_the_cockpit',
]


@pytest.fixture(autouse=True)
def _restore_palette() -> Iterator[None]:
    """Restore the default palette (the selection is module-global state)."""
    yield
    theme.select('dark')


@pytest.mark.parametrize('palette', ['dark', 'light'])
def test_every_color_slot_is_pinned_byte_exact(palette: str) -> None:
    """``THEME.variables`` pins each slot with its exact token, per palette.

    ``ColorSystem.generate`` round-trips the semantic slots through HSL
    (shifting e.g. ``#cc8b6a``), so a slot missing from ``variables`` would
    drift off its Python twin and content markup would stop matching the
    stylesheet.
    """
    theme.select(palette)
    pinned = theme.THEME.variables
    assert pinned['primary'] == theme.PRIMARY
    assert pinned['success'] == theme.SUCCESS
    assert pinned['warning'] == theme.WARNING
    assert pinned['error'] == theme.ERROR
    assert pinned['foreground'] == theme.INK
    assert pinned['background'] == theme.BG
    assert pinned['surface'] == theme.SURFACE
    assert pinned['panel'] == theme.PANEL
    # the structural tokens exist in no stock theme: they must all be present
    # before the first stylesheet parse or boot fails
    assert pinned['chrome'] == theme.CHROME
    assert pinned['sel'] == theme.SEL
    assert pinned['overlay'] == theme.OVERLAY
    # both palettes pass the terminal's own background through
    assert theme.BG == 'ansi_default'
    assert theme.THEME.dark is (palette == 'dark')


def test_palettes_share_one_key_set() -> None:
    """The palettes cover the same tokens (a slot added to one lands in both).

    A key present in only one palette would leave a module attribute stale --
    or a ``$variable`` unresolved -- the moment the other palette is selected.
    """
    assert theme._DARK.keys() == theme._LIGHT.keys()


def test_css_variables_are_stylesheet_ready() -> None:
    """The numeric tokens with a TCSS consumer export as ``$name`` strings."""
    variables = theme.css_variables()
    assert variables['pane-pad'] == str(theme.PANE_PAD)
    assert variables['gap'] == str(theme.GAP)
    assert variables['m-session-w'] == str(theme.M_SESSION_W)
    assert all(isinstance(value, str) for value in variables.values())


async def test_light_palette_boots_the_cockpit(
    cockpit_app: Callable[..., FractalApp],
) -> None:
    """The light palette resolves the stylesheet and reaches the screen."""
    theme.select('light')
    app = cockpit_app()
    async with app.run_test(size=(150, 48)) as pilot:
        await pilot.pause()
        # the booted app serves the light tokens, not the import-time dark
        assert app.get_css_variables()['surface'] == theme._LIGHT['SURFACE']
        assert app.get_css_variables()['foreground'] == theme._LIGHT['INK']
