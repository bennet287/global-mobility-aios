"""Design tokens: the single source of colors, dimensions, and glyphs.

This is the only module in ``fractal.tui`` that may contain a hex color or a
glyph character, and the only home for a dimension literal that is shared
across render sites or consumed by the stylesheet (one-off local layout math
may stay inline). Colors flow to the stylesheet as
``$variables`` on the ``THEME`` (every slot is pinned there with its exact
hex, bypassing the HSL round-trip Textual's ``ColorSystem.generate`` applies to
the semantic slots) and to the Rich content markup by direct import
(``f'[{theme.SUCCESS}]...'`` -- content markup does not resolve ``$variables``).
Numeric tokens with a stylesheet consumer are injected by ``css_variables``;
the rest are Python ints used in width math. Glyphs are Python-only.

Two palettes share one key set: ``dark`` (the default, applied at import) and
``light``. ``select`` rebinds the module-level color tokens and rebuilds
``THEME`` -- every consumer reads the tokens as module attributes at render
time, so one call before the app constructs re-skins the whole cockpit
(``fractal open --light/--dark`` picks the palette).

The muted grey is deliberately two tokens: the plain in-card muted is the Rich
``dim`` attribute (``DIM``) in the dark palette (a picked grey in the light
one, where ``dim`` washes toward the background), the accent-tinted
header/footer grey is ``CHROME``.
"""

from __future__ import annotations

from textual.theme import Theme

__all__ = [
    'select',
    'THEME',
    'css_variables',
]


# ------ palettes


# the dark palette (the default): every picked hex tuned for a dark terminal
_DARK = {
    # semantic colors (Theme slots; pinned in the THEME so $primary etc. keep
    # the exact hex)
    'PRIMARY': '#cc8b6a',  # accent / focus (coral)
    'SUCCESS': '#87a06b',  # active / completed / true (green)
    'WARNING': '#c9a96b',  # stopped / number (yellow)
    'ERROR': '#c0655a',  # exited / killed / false (red)
    'INK': '#cdc8c0',  # body text (foreground)
    'BG': 'ansi_default',  # screen background: the terminal's own (never picked)
    'SURFACE': '#26231f',  # inputs, chips
    'PANEL': '#2c2824',  # composer, "you" bubbles
    # structural colors (exported as new $variables; absent from stock themes)
    'INK_BRIGHT': '#f0e7dc',  # brightest text (toggle active segment)
    'INK_INVERSE': '#1f1d1b',  # ink for chips on primary (never the terminal's)
    'CHROME': '#7c776f',  # warm muted: header / footer / labels
    'TITLE': '#9a938a',  # pane border-title
    'SEL': '#322d27',  # selected row / focused input
    'ZONE': '#262320',  # focused-zone tint
    'LIT': '#4a3a2a',  # active edit / option highlight
    'LIT_ACTIVE': '#5a4836',  # active toggle segment
    'TRACK': '#37332e',  # empty gauge track
    'BORDER': '#4a443c',  # pane border (blurred)
    'RULE': '#46423b',  # horizontal rules
    'OVERLAY': '#2a2723',  # combo / filter dropdown background
    'SCROLL': '#463f37',  # scrollbar handle
    'SCROLL_HOVER': '#5a534a',  # scrollbar handle (hover)
    'SCROLL_ACTIVE': '#6e675d',  # scrollbar handle (active)
    'SCROLL_BG': '#141210',  # scrollbar trough: darker than every pick, reads as air
    # the cool muted is the Rich `dim` attribute, not a hex (see module docstring)
    'DIM': 'dim',
}

# the light palette: the same keys (roles documented on _DARK) mirroring the
# dark palette's relations on a light terminal -- status hues darkened for
# contrast, text near-black, and the selection washes darker than the surface
# instead of lighter. The accent is teal rather than coral (a warm accent
# collides with the error red's hue on paper), so the near-grey neutral ramp
# tints cool toward it, exactly as dark's tints warm toward coral
_LIGHT = {
    'PRIMARY': '#307988',
    'SUCCESS': '#5f7d42',
    'WARNING': '#96782f',
    'ERROR': '#a5433a',
    'INK': '#242a2d',
    'BG': 'ansi_default',
    'SURFACE': '#e2e7e9',
    'PANEL': '#d7dee0',
    'INK_BRIGHT': '#14181a',
    'INK_INVERSE': '#eaf3f5',
    'CHROME': '#727d83',
    'TITLE': '#5e696e',
    'SEL': '#cdd8db',
    'ZONE': '#dce3e5',
    'LIT': '#b2d1d7',
    'LIT_ACTIVE': '#9ac4cb',
    'TRACK': '#ccd3d6',
    'BORDER': '#a4aeb2',
    'RULE': '#b4bdc0',
    'OVERLAY': '#e7ecee',
    'SCROLL': '#aab2b6',
    'SCROLL_HOVER': '#959ea3',
    'SCROLL_ACTIVE': '#808a8e',
    'SCROLL_BG': '#f4f6f7',
    # `dim` washes toward a light background; a picked mid grey reads instead
    'DIM': '#667075',
}

_PALETTES = {'dark': _DARK, 'light': _LIGHT}


# ------ dimensions


PANE_PAD = 2  # tree/radio/node pane horizontal padding
GAP = 2  # the grid unit (row gap, .cell margin)
BORDER_W = 1  # round-border thickness per side
SCROLLBAR_W = 1  # scrollbar gutter width
PANE_CHROME = 2 * BORDER_W + 2 * PANE_PAD  # any pane's border + padding columns
# node-pane chrome: borders + padding + scrollbar + one breathing column
NODE_CHROME = 2 * BORDER_W + 2 * PANE_PAD + SCROLLBAR_W + 1
# tree-pane chrome: borders + padding + a few-space right buffer past the row
TREE_CHROME = 2 * BORDER_W + 2 * PANE_PAD + 3
# drag-resize floors (each cap is half the live terminal, computed at drag time)
TREE_W_MIN = TREE_CHROME + 12  # tree pane: chrome + a readable label floor
MESSAGE_H_MIN = 12  # message pane: chrome + fields + composer + 3 transcript lines
NODE_WIDEN = 1.14  # breathing room past natural column content
NODE_FIT_MIN = 23  # explorer label-area floor (columns)
SESS_W, COST_W = 9, 10  # explorer/event-log value cluster columns
TIME_W = 8  # event log: HH:MM:SS time column
META_MIN = 4  # event log: min metadata before the ellipsis
IDENT_W = 13  # node card: ident label column (agent/model/session)
MEAS_W, BAR_W = 4, 12  # measures matrix: scope label, gauge width
EL_FIG_W, CO_FIG_W = 8, 20  # measures matrix: elapsed / cost figures
GAUGE_GAP = 3  # measures matrix: figure-to-gauge gap
SENDER_W, CHANNEL_W, PRIORITY_W = 14, 8, 8  # radio list columns (buffers use GAP)
RD_LABEL_W = 11  # radio detail: label column
# compose-field box widths (TCSS via $m-*-w; m_session also caps the shown
# value; node/channel size to their content at runtime)
M_SESSION_W, M_THREAD_W, M_PRIORITY_W = 12, 11, 5
HUG_PAD = 3  # content-hugging inputs: box padding + one column of air
REFRESH_S = 0.6  # poll cadence (seconds)
SPIN_S = 0.1  # chat spinner frame cadence (seconds)


# ------ glyphs


DOT_ON, DOT_OFF = '●', '○'  # filled (running) / hollow (settled) dot
CARET_OPEN, CARET_CLOSED = '▾', '▸'  # expanded / collapsed marker
PROMPT, SEP = '›', '·'  # composer prompt, center-dot separator
TEE, ELBOW, PIPE, INDENT = '├─ ', '└─ ', '│  ', '   '
BAR = '━'  # gauge fill
LINE = '─'  # date-separator rule
ELLIPSIS = '…'
EMPTY = '—'  # empty-value placeholder
RET, SHIFT, CTRL = '⏎', '⇧', '⌃'  # key hints
UP, DOWN, LEFT, RIGHT = '↑', '↓', '←', '→'  # arrow key hints
TOOL, WARN = '⚙', '⚠'  # chat tool-use / degraded-send markers
COPYRIGHT = '©'  # footer brand mark
SPINNER = ('⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏')  # chat in-flight


# NOTE: every color slot is pinned in `variables`, not just the structural ones --
#   App.get_css_variables computes {**generate(), **theme.variables} and
#   ColorSystem.generate round-trips the semantic slots through HSL (shifting
#   e.g. #cc8b6a -> #cb8b6a), so pinning is what keeps $primary byte-exact with
#   PRIMARY; the structural tokens do not exist in stock themes at all; they
#   must be present before the stylesheet first parses (at App.__init__)
def _build_theme(name: str, palette: dict[str, str]) -> Theme:
    """Build the textual ``Theme`` for ``palette``.

    Both palettes register under the one ``fractal`` name, so the app selects
    its theme the same way whichever palette is active.

    Args:
        name: The palette name (``dark`` or ``light``).
        palette: The palette's token mapping.

    Returns:
        The ``Theme`` with every color slot pinned in ``variables``.

    """
    return Theme(
        name='fractal',
        primary=palette['PRIMARY'],
        accent=palette['PRIMARY'],
        success=palette['SUCCESS'],
        warning=palette['WARNING'],
        error=palette['ERROR'],
        foreground=palette['INK'],
        background=palette['BG'],
        surface=palette['SURFACE'],
        panel=palette['PANEL'],
        dark=name == 'dark',
        variables={
            'primary': palette['PRIMARY'],
            'accent': palette['PRIMARY'],
            'success': palette['SUCCESS'],
            'warning': palette['WARNING'],
            'error': palette['ERROR'],
            'foreground': palette['INK'],
            'background': palette['BG'],
            'surface': palette['SURFACE'],
            'panel': palette['PANEL'],
            'ink-bright': palette['INK_BRIGHT'],
            'ink-inverse': palette['INK_INVERSE'],
            'chrome': palette['CHROME'],
            'title': palette['TITLE'],
            'sel': palette['SEL'],
            'zone': palette['ZONE'],
            'lit': palette['LIT'],
            'lit-active': palette['LIT_ACTIVE'],
            'track': palette['TRACK'],
            'border-dim': palette['BORDER'],
            'rule': palette['RULE'],
            'overlay': palette['OVERLAY'],
            'scroll': palette['SCROLL'],
            'scroll-hover': palette['SCROLL_HOVER'],
            'scroll-active': palette['SCROLL_ACTIVE'],
            'scroll-bg': palette['SCROLL_BG'],
        },
    )


def select(name: str) -> None:
    """Apply a palette: rebind the color tokens and rebuild ``THEME``.

    Every consumer reads the tokens as module attributes at render time, so
    one rebind before the app constructs re-skins the whole cockpit. Import
    applies ``dark``.

    Args:
        name: The palette name (``dark`` or ``light``).

    """
    global THEME
    palette = _PALETTES[name]
    globals().update(palette)
    THEME = _build_theme(name, palette)


select('dark')


def css_variables() -> dict[str, str]:
    """Return the numeric tokens the stylesheet consumes, as ``$name`` values.

    Only tokens with a real TCSS consumer are exported (the rest stay Python
    ints used in width math); the app merges these into its CSS variable table
    via ``get_theme_variable_defaults``.

    Returns:
        Mapping of CSS variable name to string value.

    """
    return {
        'pane-pad': str(PANE_PAD),
        'gap': str(GAP),
        'm-session-w': str(M_SESSION_W),
        'm-thread-w': str(M_THREAD_W),
        'm-priority-w': str(M_PRIORITY_W),
    }
