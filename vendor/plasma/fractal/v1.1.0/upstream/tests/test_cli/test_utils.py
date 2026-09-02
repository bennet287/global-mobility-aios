"""Test the ``fractal.cli.utils`` module.

The helpers are pinned where they surface: ``parse_reserve_budget`` in
``test_reserve_budget``, node resolution in ``test_signal_guards``, and
the ``command`` error wrapper behaviorally across the ``test_cli``
suites. ``StreamRenderer``'s piped-stream ordering lives here (its
per-provider event rendering is pinned in ``test_impl``).
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

__all__ = [
    'test_renderer_keeps_piped_output_ordered_with_stderr',
]

# the chat command's epilogue in miniature: a streamed reply, the closing
# summary, then the session id echoed to stderr
_CHAT_TAIL = """
import typer
from fractal.cli.utils import StreamRenderer
from fractal.core.agent import StreamEvent

render = StreamRenderer()
render(StreamEvent(kind='text', text='streamed reply'))
render(StreamEvent(kind='result', final=True, cost=0.01, turns=1, duration=1.0))
render.close()
typer.echo('session: abc', err=True)
"""


def test_renderer_keeps_piped_output_ordered_with_stderr() -> None:
    """Renderer writes flush through, so stderr echoes never overtake them.

    Piped stdout is block-buffered while stderr is write-through: an
    unflushed closing summary would sit in the buffer and let the driving
    command's ``session:`` echo land mid-reply in a merged capture (the
    operator's ``2>&1`` view). Every renderer write flushes, so the merged
    stream keeps the reply, then the summary, then the session line.
    """
    root = pathlib.Path(__file__).resolve().parents[2]
    env = dict(os.environ)
    env['PYTHONPATH'] = os.pathsep.join(
        part for part in (str(root), env.get('PYTHONPATH', '')) if part
    )
    result = subprocess.run(
        [sys.executable, '-c', _CHAT_TAIL],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        timeout=60,
    )
    merged = result.stdout
    assert result.returncode == 0, merged
    # reply, then closing summary, then the session line -- in write order
    assert merged.index('streamed reply') < merged.index('— ')
    assert merged.index('— ') < merged.index('session: abc')
    # the session line starts on its own line, never mid-reply
    assert '\nsession: abc' in merged
