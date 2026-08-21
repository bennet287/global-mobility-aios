"""Test the ``fractal.tui.fmt`` module.

Every helper is a pure string/``Text`` builder over the theme tokens, so the
suite is a parametrized formatter table: (input, rendered output) pairs, with
the glyph/color tokens asserted by name so a theme swap never breaks a test.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

import pytest
from rich.text import Text

from fractal.constants import STATUSES
from fractal.tui import fmt, theme

__all__ = [
    'test_dur_renders_compact_units',
    'test_money_renders_grouped_cents',
    'test_timestamp_and_clock_render_in_zone',
    'test_status_style_spans_the_lifecycle_vocabulary',
    'test_status_style_signal_override',
    'test_trunc_ellipsizes_and_col_pads',
    'test_cell_pads_by_visible_width',
    'test_toggle_boxes_each_label_with_air',
    'test_cap_bar_saturates_red_at_the_cap',
    'test_tree_lines_hang_continues_the_glyph_columns',
    'test_esc_neutralizes_untrusted_markup',
    'test_tree_lines_escapes_hostile_node_name',
]


@pytest.mark.parametrize(
    argnames=('secs', 'expected'),
    argvalues=[
        (None, theme.ELLIPSIS),
        (0.0, '0s'),
        (43.0, '43s'),
        (59.4, '59s'),
        (1080.0, '18m'),
        (7200.0, '2h'),
    ],
)
def test_dur_renders_compact_units(secs: Optional[float], expected: str) -> None:
    """Durations render compact (seconds / minutes / hours); none is ellipsis."""
    assert fmt.dur(secs) == expected


@pytest.mark.parametrize(
    argnames=('value', 'expected'),
    argvalues=[
        (None, theme.ELLIPSIS),
        (0.0, '$0.00'),
        (0.0432, '$0.04'),
        (1083.421, '$1,083.42'),
    ],
)
def test_money_renders_grouped_cents(value: Optional[float], expected: str) -> None:
    """Dollar figures render grouped to cents; none (not yet recorded) is ellipsis."""
    assert fmt.money(value) == expected


def test_timestamp_and_clock_render_in_zone() -> None:
    """Timestamps render in the given zone: date-time long, clock short."""
    at = dt.datetime(2026, 6, 7, 18, 0, 5, tzinfo=dt.UTC)
    assert fmt.timestamp(at, dt.UTC) == '2026-06-07 18:00:05'
    assert fmt.clock(at, dt.UTC) == '18:00:05'


def test_status_style_spans_the_lifecycle_vocabulary() -> None:
    """Every real status resolves a style; unknown strings degrade dim.

    The style table is keyed through ``fractal.constants.STATUSES``, so the
    live-shaped statuses render filled and everything settled hollow; garbage
    from a hand-edited ``.status`` file falls to the hollow dim default.
    """
    for status in STATUSES:
        glyph, _color = fmt.status_style(status)
        assert glyph in (theme.DOT_ON, theme.DOT_OFF)
    # live-shaped: active runs green, paused holds its slot in yellow
    assert fmt.status_style('active') == (theme.DOT_ON, theme.SUCCESS)
    assert fmt.status_style('paused') == (theme.DOT_ON, theme.WARNING)
    # settled examples across the color range
    assert fmt.status_style('completed') == (theme.DOT_OFF, theme.SUCCESS)
    assert fmt.status_style('killed') == (theme.DOT_OFF, theme.ERROR)
    assert fmt.status_style('garbage') == (theme.DOT_OFF, theme.DIM)


def test_status_style_signal_override() -> None:
    """A pending signal overrides the status color (the loop honors it next)."""
    assert fmt.status_style('active', 'kill') == (theme.DOT_ON, theme.ERROR)
    assert fmt.status_style('active', 'finish') == (theme.DOT_ON, theme.SUCCESS)


def test_trunc_ellipsizes_and_col_pads() -> None:
    """``trunc`` ellipsizes overflow; ``col`` pads short values to width."""
    assert fmt.trunc('abcdefgh', 5) == f'abcd{theme.ELLIPSIS}'
    assert fmt.trunc('abc', 5) == 'abc'
    assert fmt.col('abc', 5) == 'abc  '
    assert fmt.col('abcdefgh', 5) == f'abcd{theme.ELLIPSIS}'


def test_cell_pads_by_visible_width() -> None:
    """``cell`` pads/truncates by VISIBLE width, markup tokens excluded."""
    padded = fmt.cell(f'[{theme.SUCCESS}]{theme.DOT_ON}[/] name', 10)
    assert padded.cell_len == 10
    right = fmt.cell('42', 6, justify='right')
    assert right.plain == '    42'


def test_toggle_boxes_each_label_with_air() -> None:
    """Each segment is its label plus a space of air per side."""
    markup = fmt.toggle(('node', 'descendants'), 'node', lit=False)
    plain = Text.from_markup(markup).plain
    assert plain == ' node  descendants '
    # the active segment sits on the brighter resting chip, the inactive dims
    assert f'[{theme.INK} on {theme.SEL}]' in markup
    assert f'[{theme.CHROME} on {theme.SURFACE}]' in markup


def test_cap_bar_saturates_red_at_the_cap() -> None:
    """The gauge fills toward the cap and renders full red once it is hit."""
    assert theme.SUCCESS in fmt.cap_bar(0.5)
    assert theme.WARNING in fmt.cap_bar(0.5, warn=True)
    capped = fmt.cap_bar(1.2)
    assert theme.ERROR in capped
    assert theme.TRACK not in capped


def test_tree_lines_hang_continues_the_glyph_columns() -> None:
    """A tee hangs a pipe beneath it; an elbow's line ends, hanging indent."""
    row = {
        'name': 'n',
        'status': 'active',
        'signal': '',
        'is_user': False,
        'is_focused': False,
        'has_kids': False,
    }
    rows = [
        {**row, 'branch': 'main', 'depth': 0, 'has_kids': True},
        {**row, 'branch': 'main.a', 'depth': 1, 'has_kids': True},
        {**row, 'branch': 'main.a.x', 'depth': 2},
        {**row, 'branch': 'main.b', 'depth': 1},
    ]
    hangs = [hang for _, _, hang, _ in fmt.tree_lines(rows, set())]
    # root: nothing to continue; a's tee: pipe (b follows); x's elbow under
    # the continuing a: pipe then indent; b's elbow: indent
    assert hangs == [
        '',
        f'[{theme.DIM}]{theme.PIPE}[/]',
        f'[{theme.DIM}]{theme.PIPE}{theme.INDENT}[/]',
        f'[{theme.DIM}]{theme.INDENT}[/]',
    ]


@pytest.mark.parametrize(
    argnames='hostile',
    argvalues=['[/]', '[link=file:///etc/passwd]open[/link]', '[bold]forged[/]'],
)
def test_esc_neutralizes_untrusted_markup(hostile: str) -> None:
    """``esc`` renders untrusted text literally instead of as markup.

    Agent- and message-authored strings reach the cockpit through markup
    f-strings; an unescaped ``[/]`` raises ``MarkupError`` (crashing the
    pane rebuild) and ``[link=...]`` injects terminal escape sequences.
    Escaping makes ``Text.from_markup`` parse the value as plain text with
    no styling.
    """
    rendered = Text.from_markup(fmt.esc(hostile))
    assert rendered.plain == hostile
    assert rendered.spans == []


def test_tree_lines_escapes_hostile_node_name() -> None:
    """A node title carrying markup renders literally in the tree label.

    Titles are agent-influenceable; without escaping, a stray ``[/]``
    would crash the whole-tree render and ``[link=...]`` would inject
    terminal escape sequences into the operator's cockpit.
    """
    hostile = '[link=file:///x]evil[/link]'
    rows = [
        {
            'name': hostile,
            'branch': 'main',
            'depth': 0,
            'status': 'active',
            'signal': '',
            'is_user': False,
            'is_focused': True,
            'has_kids': False,
        }
    ]
    labels = [label for _, _, _, label in fmt.tree_lines(rows, set())]
    # the label parses without MarkupError and shows the name verbatim
    assert Text.from_markup(labels[0]).plain == hostile
