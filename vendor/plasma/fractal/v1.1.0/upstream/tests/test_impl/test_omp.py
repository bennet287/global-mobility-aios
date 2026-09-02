"""Test the ``fractal.impl.omp`` module.

The omp (Oh My Pi) dialect end to end: the ``-p --mode json`` NDJSON
protocol parsed into normalized events -- the session header, text
deltas nested under ``message_update``, tool-execution headers, per-turn
cost accumulation (turns are not cumulative), and the ``agent_end``
authoritative close -- the ``-p`` argv builder with the agent-minted
session, the cwd-slug transcript glob, and the
``PI_CODING_AGENT_DIR`` isolation. Stream-level cases drive the base
``Agent.stream`` driver against a real node ledger.
"""

from __future__ import annotations

import json
import os
import pathlib
from typing import Any, Optional

import pytest

from fractal.cli.utils import StreamRenderer
from fractal.core.node import Node
from fractal.impl.omp import OmpAgent, OmpParser

__all__ = [
    'test_capability_flags_report_provider_facts_omp',
    'test_parser_maps_the_stream_protocol_omp',
    'test_parser_captures_the_session_from_the_header_once',
    'test_parser_accumulates_per_turn_cost',
    'test_parser_costless_run_records_no_cost',
    'test_parser_surfaces_error_frames_omp',
    'test_parser_surfaces_a_turn_end_error_message',
    'test_parser_tolerates_garbage_omp',
    'test_events_render_through_the_production_renderer_omp',
    'test_stream_records_cost_model_and_session_omp',
    'test_stream_detached_keeps_session_unpersisted_omp',
    'test_stream_fails_on_error_frames_omp',
    'test_invocation_modes_build_the_pinned_argv_omp',
    'test_seed_config_yolo_approves',
    'test_transcript_globs_the_session_log',
]

# omp mints uuidv7 session ids
_SESSION = '019f6822-a48f-7000-bc7b-d8aa484b329e'


def _turn(cost: Optional[float], model: str = 'openai/gpt-5.5') -> dict[str, Any]:
    """A turn_end frame carrying per-turn usage and (optional) cost."""
    usage: dict[str, Any] = {'input': 10, 'output': 6, 'totalTokens': 16}
    if cost is not None:
        usage['cost'] = {'input': cost, 'output': 0, 'total': cost}
    return {'type': 'turn_end', 'message': {'model': model, 'usage': usage}}


def test_capability_flags_report_provider_facts_omp(node_with_db: Node) -> None:
    """The provider facts consumers branch on, plus cost trackability."""
    backend = OmpAgent(node_with_db, 'omp')
    assert backend.name == 'omp'
    assert backend.config_file == 'config.yml'
    assert backend.can_fork
    assert backend.mints_session
    assert not backend.needs_pricing
    assert backend.cost_scope == 'call'
    assert not backend.enforces_budget
    # a cost-reporting agent tracks spend with or without a model
    assert backend.tracks_cost()
    assert backend.tracks_cost('anything')


def test_parser_maps_the_stream_protocol_omp() -> None:
    """One protocol implementation: session, text, tool, cost, agent close."""
    parser = OmpParser()
    frames = [
        {'type': 'session', 'id': _SESSION},
        {'type': 'agent_start'},
        {'type': 'turn_start'},
        {
            'type': 'message_update',
            'assistantMessageEvent': {'type': 'text_delta', 'delta': 'probe-'},
        },
        {
            'type': 'message_update',
            'assistantMessageEvent': {'type': 'text_delta', 'delta': 'ok'},
        },
        {'type': 'tool_execution_start', 'toolName': 'bash', 'args': {}},
        _turn(0.01),
        {'type': 'agent_end', 'messages': []},
    ]
    events = [event for line in _lines(frames) for event in parser.feed(line)]
    # the session header names no model, so a second session event re-stamps
    # it once the turn frame reveals the served model
    assert [event.kind for event in events] == [
        'session',
        'text',
        'text',
        'tool',
        'session',
        'cost',
        'result',
    ]
    session, text_a, text_b, tool, restamp, cost, result = events
    assert session.session == _SESSION
    assert session.model is None
    assert text_a.text + text_b.text == 'probe-ok'
    assert tool.tool == 'bash'
    # the re-stamp carries the same session with the served model
    assert restamp.session == _SESSION
    assert restamp.model == 'openai/gpt-5.5'
    assert cost.cost == pytest.approx(0.01)
    # agent_end is the authoritative close
    assert result.final
    assert result.cost == pytest.approx(0.01)
    assert result.duration is not None
    assert result.duration >= 0.0
    # the served model rides the turn frame, and joins the served record
    assert parser.model == 'openai/gpt-5.5'
    assert parser.models == ['openai/gpt-5.5']


def test_parser_captures_the_session_from_the_header_once() -> None:
    """The session header is the first frame; only it emits the fact."""
    parser = OmpParser()
    frames = [
        {'type': 'session', 'id': _SESSION},
        {
            'type': 'message_update',
            'assistantMessageEvent': {'type': 'text_delta', 'delta': 'hi'},
        },
    ]
    events = [event for line in _lines(frames) for event in parser.feed(line)]
    assert [event.kind for event in events] == ['session', 'text']
    assert parser.session == _SESSION


def test_parser_accumulates_per_turn_cost() -> None:
    """Per-turn costs sum across the invocation (turns are not cumulative)."""
    parser = OmpParser()
    frames = [
        {'type': 'session', 'id': _SESSION},
        _turn(0.028),
        _turn(0.028),
        {'type': 'agent_end', 'messages': []},
    ]
    events = [event for line in _lines(frames) for event in parser.feed(line)]
    costs = [event.cost for event in events if event.kind == 'cost']
    assert costs == [pytest.approx(0.028), pytest.approx(0.056)]
    assert parser.cost == pytest.approx(0.056)
    assert parser.final


def test_parser_costless_run_records_no_cost() -> None:
    """A turn without a cost object closes without inventing a figure."""
    # the served model already matches, so no re-stamp fires -- the case is
    # about cost absence, not model capture
    parser = OmpParser(model='openai/gpt-5.5')
    frames = [
        {'type': 'session', 'id': _SESSION},
        _turn(None),
        {'type': 'agent_end', 'messages': []},
    ]
    events = [event for line in _lines(frames) for event in parser.feed(line)]
    assert [event.kind for event in events] == ['session', 'result']
    assert parser.cost is None


@pytest.mark.parametrize(
    argnames=('frame', 'detail'),
    argvalues=[
        pytest.param(
            {'type': 'error', 'message': 'provider down'},
            'provider down',
            id='error-message',
        ),
        pytest.param(
            {'type': 'extension_error', 'error': 'bad tool'},
            'bad tool',
            id='extension-error',
        ),
        pytest.param({'type': 'error'}, 'unknown error', id='bare'),
    ],
)
def test_parser_surfaces_error_frames_omp(frame: dict[str, Any], detail: str) -> None:
    """Any error-typed frame rides the stream and collects to fail the step."""
    parser = OmpParser()
    (event,) = parser.feed(json.dumps(frame))
    assert event.kind == 'error'
    assert event.message == detail
    assert parser.errors == [detail]


def test_parser_surfaces_a_turn_end_error_message() -> None:
    """An API failure rides a ``turn_end`` (``stopReason: error``), not an error frame.

    omp reports a 401/429/overload/context-overflow by exiting 0 with no
    error-typed frame -- the failure arrives as a normal ``turn_end`` whose
    ``message`` carries ``stopReason == 'error'`` and an ``errorMessage``.
    The parser must classify it so the step fails, not silently book
    ``completed`` while doing zero work.
    """
    parser = OmpParser()
    frame = {
        'type': 'turn_end',
        'message': {
            'model': 'claude-haiku-4-5',
            'stopReason': 'error',
            'errorMessage': '401 authentication_error: invalid x-api-key',
            'usage': {'cost': {'total': 0}},
        },
    }
    events = parser.feed(json.dumps(frame))
    assert any(event.kind == 'error' for event in events)
    assert parser.errors
    assert '401' in parser.errors[0]


def test_parser_tolerates_garbage_omp() -> None:
    """Malformed, non-object, and unknown lines yield nothing, never raise."""
    parser = OmpParser()
    junk = [
        '',
        '   ',
        'not json',
        '[1, 2]',
        '"text"',
        '{}',
        '{"type": "mystery"}',
        # a non-string type must not crash the substring error check
        '{"type": 5}',
    ]
    assert [event for line in junk for event in parser.feed(line)] == []
    assert parser.session is None
    assert parser.cost is None


def test_events_render_through_the_production_renderer_omp(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Parsed events drive the CLI renderer: messages, errors, cost close."""
    parser = OmpParser()
    render = StreamRenderer()
    frames = [
        {'type': 'session', 'id': _SESSION},
        {
            'type': 'message_update',
            'assistantMessageEvent': {'type': 'text_delta', 'delta': 'Done.'},
        },
        {'type': 'error', 'message': 'rate limited'},
        _turn(0.01),
        {'type': 'agent_end', 'messages': []},
    ]
    for line in _lines(frames):
        for event in parser.feed(line):
            render(event)
    captured = capsys.readouterr()
    assert 'Done.' in captured.out
    assert ', $0.0100' in captured.out
    assert 'agent error: rate limited' in captured.err


def test_stream_records_cost_model_and_session_omp(node_with_db: Node) -> None:
    """The stream driver lands session, model, and summed cost on the ledger."""
    node = node_with_db
    backend = OmpAgent(node, 'omp')
    (step_id,) = _steps(node, 1)
    frames = [
        {'type': 'session', 'id': _SESSION},
        _turn(0.02),
        _turn(0.02),
        {'type': 'agent_end', 'messages': []},
    ]
    result = backend.stream(
        _lines(frames),
        step_id=step_id,
        model='openrouter/anthropic/claude-haiku-4.5',
    )
    row = node.db.read('steps', where={'step_id': step_id})[0]
    assert row['agent'] == 'omp'
    assert row['session'] == _SESSION
    # the stream-served model overwrites the configured fallback on the row
    # (omp reports the resolved id, provider prefix stripped)
    assert row['model'] == 'openai/gpt-5.5'
    assert row['cost'] == pytest.approx(0.04)
    assert node.sessions.get('omp') == _SESSION
    assert result.session == _SESSION
    assert result.cost == pytest.approx(0.04)


def test_stream_detached_keeps_session_unpersisted_omp(node_with_db: Node) -> None:
    """A detached turn stamps the step row but never persists ``.session``."""
    node = node_with_db
    backend = OmpAgent(node, 'omp')
    (step_id,) = _steps(node, 1)
    frames = [{'type': 'session', 'id': _SESSION}]
    backend.stream(_lines(frames), step_id=step_id, detached=True)
    row = node.db.read('steps', where={'step_id': step_id})[0]
    assert row['session'] == _SESSION
    assert node.sessions.get('omp') is None


def test_stream_fails_on_error_frames_omp(node_with_db: Node) -> None:
    """A stream-borne error fails the step even after a fully drained stdout."""
    backend = OmpAgent(node_with_db, 'omp')
    frames = [{'type': 'error', 'message': 'provider down'}]
    with pytest.raises(RuntimeError, match='omp reported an error: provider down'):
        backend.stream(_lines(frames))


def test_invocation_modes_build_the_pinned_argv_omp(node_with_db: Node) -> None:
    """Fresh/resume/fork/model/effort land their exact argv and env."""
    node = node_with_db
    backend = OmpAgent(node, 'omp')
    head = ('omp', '-p', '--mode', 'json', '--yolo')
    # fresh runs carry no session flag; omp mints the id itself
    fresh = backend.invocation('hi')
    assert fresh.argv == (*head, '--', 'hi')
    assert fresh.session is None
    # resume continues the minted session in place
    resume = backend.invocation('hi', session='019f-7')
    assert resume.argv == (*head, '-r', '019f-7', '--', 'hi')
    # fork branches the session to a new id
    fork = backend.invocation('hi', session='019f-7', fork=True)
    assert fork.argv == (*head, '--fork', '019f-7', '--', 'hi')
    # the model rides --model, effort rides --thinking, the prompt stays final
    tuned = backend.invocation(
        'hi',
        model='openrouter/anthropic/claude-haiku-4.5',
        effort='high',
    )
    assert tuned.argv == (
        *head,
        '--model',
        'openrouter/anthropic/claude-haiku-4.5',
        '--thinking',
        'high',
        '--',
        'hi',
    )
    # a dash-leading message is protected by the sentinel, not parsed as a flag
    dashed = backend.invocation('-1 on that idea')
    assert dashed.argv[-2:] == ('--', '-1 on that idea')
    # omp runs in the worktree over the FULL environment plus the agent-dir
    # isolation pointer
    assert fresh.cwd == node.worktree
    assert fresh.env['PI_CODING_AGENT_DIR'] == str(node.node_dir / '.omp')
    assert fresh.env['PATH'] == os.environ['PATH']


def test_seed_config_yolo_approves(tmp_path: pathlib.Path) -> None:
    """The packaged omp seed auto-approves tool calls."""
    node_dir = tmp_path / 'node'
    (node_dir / 'skills').mkdir(parents=True)
    OmpAgent.seed(node_dir)
    config = (node_dir / '.omp' / 'config.yml').read_text(encoding='utf-8')
    assert 'approvalMode: yolo' in config


def test_transcript_globs_the_session_log(node_with_db: Node) -> None:
    """The session log resolves under the node's own omp home."""
    node = node_with_db
    backend = OmpAgent(node, 'omp')
    # omp derives the directory name from the cwd via its own slug scheme,
    # so the lookup wildcards it
    sessions = node.node_dir / '.omp' / 'sessions' / '-cwd-slug'
    sessions.mkdir(parents=True)
    log = sessions / f'2026-07-15T23-35-28-655Z_{_SESSION}.jsonl'
    log.write_text('{"type": "session"}\n', encoding='utf-8')
    transcript = backend.transcript(_SESSION)
    assert transcript['exists'] is True
    assert transcript['path'] == str(log)


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
