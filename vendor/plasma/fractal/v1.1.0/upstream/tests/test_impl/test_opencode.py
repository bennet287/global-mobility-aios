"""Test the ``fractal.impl.opencode`` module.

The opencode dialect end to end: the ``run --format json`` protocol with
its part-nested payloads parsed into normalized events, the per-step
cost accumulation closing ``final`` on the stop reason, the ``run``
argv builder, the ``opencode.json`` model default, and the SQLite-only
session storage degrading ``transcript()`` gracefully. Stream-level
cases drive the base ``Agent.stream`` driver against a real node
ledger.
"""

from __future__ import annotations

import json
import os
import pathlib
from typing import Any

import pytest

from fractal.cli.utils import StreamRenderer
from fractal.core.node import Node
from fractal.impl.opencode import OpencodeAgent, OpencodeParser

__all__ = [
    'test_capability_flags_report_provider_facts_opencode',
    'test_parser_maps_the_stream_protocol_opencode',
    'test_parser_captures_the_session_from_the_first_event',
    'test_parser_accumulates_step_finish_cost',
    'test_parser_costless_step_records_no_cost',
    'test_parser_surfaces_error_frames_opencode',
    'test_parser_tolerates_garbage_opencode',
    'test_events_render_through_the_production_renderer_opencode',
    'test_stream_records_cost_model_and_session_opencode',
    'test_stream_detached_keeps_session_unpersisted_opencode',
    'test_stream_fails_on_error_frames_opencode',
    'test_invocation_modes_build_the_pinned_argv_opencode',
    'test_config_model_reads_the_json_top_level',
    'test_seed_config_locks_down_sharing',
    'test_transcript_returns_the_exists_false_shape',
]

# session ids carry an underscore and mixed case -- the transcript-boundary
# charset must pass them end to end
_SESSION = 'ses_09e1cac7fffefI20JXGUDoU6M4'


def _frame(kind: str, part: dict[str, Any]) -> dict[str, Any]:
    """Wrap a part payload in the event envelope opencode emits."""
    return {'type': kind, 'timestamp': 0, 'sessionID': _SESSION, 'part': part}


def test_capability_flags_report_provider_facts_opencode(node_with_db: Node) -> None:
    """The provider facts consumers branch on, plus cost trackability."""
    backend = OpencodeAgent(node_with_db, 'opencode')
    assert backend.name == 'opencode'
    assert backend.config_file == 'opencode.json'
    assert backend.can_fork
    assert backend.mints_session
    assert not backend.needs_pricing
    assert backend.cost_scope == 'call'
    assert not backend.enforces_budget
    # opencode emits a result per step_finish (many per turn); the chat close
    # gate keys on this so only a final result ends the turn
    assert backend.results_per_step
    # a cost-reporting agent tracks spend with or without a model
    assert backend.tracks_cost()
    assert backend.tracks_cost('anything')


def test_parser_maps_the_stream_protocol_opencode() -> None:
    """One protocol implementation: session, text, tools, priced close."""
    parser = OpencodeParser()
    frames = [
        _frame('step_start', {'type': 'step-start'}),
        _frame('text', {'type': 'text', 'text': 'Running it now.'}),
        _frame('tool_use', {'type': 'tool', 'tool': 'bash'}),
        _frame('step_finish', {'type': 'step-finish', 'reason': 'stop', 'cost': 0.01}),
    ]
    events = [event for line in _lines(frames) for event in parser.feed(line)]
    assert [event.kind for event in events] == [
        'session',
        'text',
        'tool',
        'cost',
        'result',
    ]
    session, text, tool, cost, result = events
    assert session.session == _SESSION
    assert text.text == 'Running it now.'
    assert tool.tool == 'bash'
    assert cost.cost == pytest.approx(0.01)
    # the stop reason closes the invocation authoritatively
    assert result.final
    assert result.cost == pytest.approx(0.01)
    assert result.duration is not None
    assert result.duration >= 0.0


def test_parser_captures_the_session_from_the_first_event() -> None:
    """Every event carries ``sessionID``; only the first emits the fact."""
    parser = OpencodeParser()
    frames = [
        _frame('text', {'type': 'text', 'text': 'a'}),
        _frame('text', {'type': 'text', 'text': 'b'}),
    ]
    events = [event for line in _lines(frames) for event in parser.feed(line)]
    assert [event.kind for event in events] == ['session', 'text', 'text']
    assert parser.session == _SESSION


def test_parser_accumulates_step_finish_cost() -> None:
    """Each step flushes the running total; only the stop close is final."""
    parser = OpencodeParser()
    frames = [
        _frame(
            kind='step_finish',
            part={'type': 'step-finish', 'reason': 'tool-calls', 'cost': 0.01},
        ),
        _frame('step_finish', {'type': 'step-finish', 'reason': 'stop', 'cost': 0.02}),
    ]
    events = [event for line in _lines(frames) for event in parser.feed(line)]
    costs = [event.cost for event in events if event.kind == 'cost']
    assert costs == [pytest.approx(0.01), pytest.approx(0.03)]
    finals = [event.final for event in events if event.kind == 'result']
    # mid-run closes stay running estimates; the stop reason settles it
    assert finals == [False, True]
    assert parser.cost == pytest.approx(0.03)
    assert parser.final


def test_parser_costless_step_records_no_cost() -> None:
    """A step without a numeric cost closes without inventing a figure."""
    parser = OpencodeParser()
    frames = [_frame('step_finish', {'type': 'step-finish', 'reason': 'stop'})]
    events = [event for line in _lines(frames) for event in parser.feed(line)]
    # the session fact still leads; no cost event fires
    assert [event.kind for event in events] == ['session', 'result']
    assert parser.cost is None


@pytest.mark.parametrize(
    argnames=('error', 'detail'),
    argvalues=[
        pytest.param(
            {'name': 'UnknownError', 'data': {'message': 'server error'}},
            'server error',
            id='data-message',
        ),
        pytest.param({'name': 'AbortedError', 'data': {}}, 'AbortedError', id='name'),
        pytest.param({}, 'unknown error', id='bare'),
        # the payload's shape varies -- a plain string, or a dict whose own
        # data field is a string -- and neither must crash the parse
        pytest.param(
            'ProviderAuthError: bad key', 'ProviderAuthError: bad key', id='string'
        ),
        pytest.param({'name': 'X', 'data': 'boom'}, 'boom', id='string-data'),
    ],
)
def test_parser_surfaces_error_frames_opencode(error: Any, detail: str) -> None:
    """Errors ride the JSON stream and collect to fail the step."""
    parser = OpencodeParser()
    frame = {'type': 'error', 'timestamp': 0, 'sessionID': _SESSION, 'error': error}
    session, event = parser.feed(json.dumps(frame))
    # the error frame still stamps the session fact first
    assert session.kind == 'session'
    assert event.kind == 'error'
    assert event.message == detail
    assert parser.errors == [detail]


def test_parser_tolerates_garbage_opencode() -> None:
    """Malformed, non-object, and unknown lines yield nothing, never raise."""
    parser = OpencodeParser()
    junk = ['', '   ', 'not json', '[1, 2]', '"text"', '{}', '{"type": "mystery"}']
    assert [event for line in junk for event in parser.feed(line)] == []
    assert parser.session is None
    assert parser.cost is None


def test_events_render_through_the_production_renderer_opencode(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Parsed events drive the CLI renderer: messages, errors, cost close."""
    parser = OpencodeParser()
    render = StreamRenderer()
    frames = [
        _frame('text', {'type': 'text', 'text': 'Done.'}),
        {
            'type': 'error',
            'timestamp': 0,
            'sessionID': _SESSION,
            'error': {'name': 'UnknownError', 'data': {'message': 'rate limited'}},
        },
        _frame('step_finish', {'type': 'step-finish', 'reason': 'stop', 'cost': 0.01}),
    ]
    for line in _lines(frames):
        for event in parser.feed(line):
            render(event)
    captured = capsys.readouterr()
    assert 'Done.' in captured.out
    # the close prints the recorded spend, not a placeholder
    assert ', $0.0100' in captured.out
    assert 'agent error: rate limited' in captured.err


def test_stream_records_cost_model_and_session_opencode(node_with_db: Node) -> None:
    """The stream driver lands session, model, and summed cost on the ledger."""
    node = node_with_db
    backend = OpencodeAgent(node, 'opencode')
    (step_id,) = _steps(node, 1)
    frames = [
        _frame(
            kind='step_finish',
            part={'type': 'step-finish', 'reason': 'tool-calls', 'cost': 0.01},
        ),
        _frame('step_finish', {'type': 'step-finish', 'reason': 'stop', 'cost': 0.02}),
    ]
    result = backend.stream(
        _lines(frames),
        step_id=step_id,
        model='openrouter/moonshotai/kimi-k2',
    )
    row = node.db.read('steps', where={'step_id': step_id})[0]
    assert row['agent'] == 'opencode'
    # the underscore/mixed-case id survives record and readback end to end
    assert row['session'] == _SESSION
    assert row['model'] == 'openrouter/moonshotai/kimi-k2'
    assert row['cost'] == pytest.approx(0.03)
    assert node.sessions.get('opencode') == _SESSION
    assert result.session == _SESSION
    assert result.cost == pytest.approx(0.03)


def test_stream_detached_keeps_session_unpersisted_opencode(node_with_db: Node) -> None:
    """A detached turn stamps the step row but never persists ``.session``."""
    node = node_with_db
    backend = OpencodeAgent(node, 'opencode')
    (step_id,) = _steps(node, 1)
    frames = [_frame('text', {'type': 'text', 'text': 'hi'})]
    backend.stream(_lines(frames), step_id=step_id, detached=True)
    row = node.db.read('steps', where={'step_id': step_id})[0]
    assert row['session'] == _SESSION
    assert node.sessions.get('opencode') is None


def test_stream_fails_on_error_frames_opencode(node_with_db: Node) -> None:
    """A stream-borne error fails the step even after a fully drained stdout."""
    backend = OpencodeAgent(node_with_db, 'opencode')
    frame = {
        'type': 'error',
        'timestamp': 0,
        'sessionID': _SESSION,
        'error': {'name': 'UnknownError', 'data': {'message': 'server error'}},
    }
    with pytest.raises(
        RuntimeError,
        match='opencode reported an error: server error',
    ):
        backend.stream([json.dumps(frame)])


def test_invocation_modes_build_the_pinned_argv_opencode(node_with_db: Node) -> None:
    """Fresh/resume/fork/model/effort land their exact argv and env."""
    node = node_with_db
    backend = OpencodeAgent(node, 'opencode')
    # fresh runs carry no session flag; opencode mints the id itself
    fresh = backend.invocation('hi')
    assert fresh.argv == ('opencode', 'run', '--format', 'json', '--auto', '--', 'hi')
    assert fresh.session is None
    # resume continues the minted session in place
    resume = backend.invocation('hi', session='ses-7')
    assert resume.argv == (
        'opencode',
        'run',
        '--format',
        'json',
        '--auto',
        '--session',
        'ses-7',
        '--',
        'hi',
    )
    # fork branches the session before continuing
    fork = backend.invocation('hi', session='ses-7', fork=True)
    assert fork.argv == (
        'opencode',
        'run',
        '--format',
        'json',
        '--auto',
        '--session',
        'ses-7',
        '--fork',
        '--',
        'hi',
    )
    # the model rides -m, effort rides --variant, the prompt stays final
    tuned = backend.invocation(
        'hi',
        model='openrouter/moonshotai/kimi-k2',
        effort='high',
    )
    assert tuned.argv == (
        'opencode',
        'run',
        '--format',
        'json',
        '--auto',
        '-m',
        'openrouter/moonshotai/kimi-k2',
        '--variant',
        'high',
        '--',
        'hi',
    )
    # a dash-leading message is protected by the sentinel, not parsed as a flag
    dashed = backend.invocation('-1 on that idea')
    assert dashed.argv[-2:] == ('--', '-1 on that idea')
    # opencode runs in the worktree over the FULL environment plus the node
    # config pointer
    assert fresh.cwd == node.worktree
    assert fresh.env['OPENCODE_CONFIG'] == str(
        node.node_dir / '.opencode' / 'opencode.json'
    )
    assert fresh.env['PATH'] == os.environ['PATH']


def test_config_model_reads_the_json_top_level(node_with_db: Node) -> None:
    """Only a real top-level string model key names the default."""
    node = node_with_db
    backend = OpencodeAgent(node, 'opencode')
    config = node.node_dir / '.opencode' / 'opencode.json'
    # no config file names no model
    assert backend.config_model() is None
    config.parent.mkdir()
    # a malformed config names no model
    config.write_text('not json', encoding='utf-8')
    assert backend.config_model() is None
    # a non-string model names no model
    config.write_text('{"model": 5}', encoding='utf-8')
    assert backend.config_model() is None
    # the top-level key wins
    config.write_text(
        '{"model": "openrouter/anthropic/claude-haiku-4.5"}',
        encoding='utf-8',
    )
    assert backend.config_model() == 'openrouter/anthropic/claude-haiku-4.5'


def test_seed_config_locks_down_sharing(tmp_path: pathlib.Path) -> None:
    """The packaged opencode seed allows tools and disables share/update."""
    node_dir = tmp_path / 'node'
    (node_dir / 'skills').mkdir(parents=True)
    OpencodeAgent.seed(node_dir)
    config = json.loads(
        (node_dir / '.opencode' / 'opencode.json').read_text(encoding='utf-8')
    )
    assert config['permission'] == 'allow'
    assert config['share'] == 'disabled'
    assert config['autoupdate'] is False


def test_transcript_returns_the_exists_false_shape(node_with_db: Node) -> None:
    """Sessions live in opencode's SQLite store; no file means a clean miss."""
    backend = OpencodeAgent(node_with_db, 'opencode')
    # the underscore id passes the transcript boundary without raising
    transcript = backend.transcript(_SESSION)
    assert transcript == {
        'agent': 'opencode',
        'session': _SESSION,
        'path': None,
        'exists': False,
        'content': '',
    }
    # path traversal still refuses at the boundary
    with pytest.raises(ValueError, match='Invalid session id'):
        backend.transcript('../escape')


# ------ helpers


def _lines(frames: list[dict[str, Any]]) -> list[str]:
    """Encode provider frames as agent stdout lines."""
    return [json.dumps(frame) + '\n' for frame in frames]


def _steps(node: Node, count: int) -> list[int]:
    """Create a run/iteration chain carrying ``count`` step rows."""
    run_id = node.record.run_start()
    iter_id = node.record.iter_start(run_id=run_id, iter=1)
    return [
        node.record.step_start(
            iter_id=iter_id,
            run_id=run_id,
            step=step,
            step_name='EXECUTE',
        )
        for step in range(1, count + 1)
    ]
