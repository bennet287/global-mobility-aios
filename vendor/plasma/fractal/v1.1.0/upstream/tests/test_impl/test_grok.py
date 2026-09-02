"""Test the ``fractal.impl.grok`` module.

The grok dialect end to end: the ``streaming-json`` NDJSON protocol
(reasoning deltas suppressed, no tool frames on the wire, one terminal
``end`` frame carrying session, usage, and model) parsed into normalized
events, per-invocation pricing over the disjoint-cache usage shape via
the ``xai/`` alias chain, the ``--single`` argv builder with caller-minted
sessions, the ``[models] default`` config key, the url-encoded-cwd
transcript layout, and the auth write-through seeding. Stream-level
cases drive the base ``Agent.stream`` driver against a real node
ledger.
"""

from __future__ import annotations

import json
import os
import pathlib
import tomllib
import urllib.parse
import uuid
from typing import Any

import pytest

from fractal.cli.utils import StreamRenderer
from fractal.core import pricing
from fractal.core.node import Node
from fractal.impl import grok
from fractal.impl.grok import GrokAgent, GrokParser

__all__ = [
    'test_capability_flags_report_provider_facts_grok',
    'test_parser_maps_the_stream_protocol_grok',
    'test_parser_multi_model_usage_reads_as_unknown',
    'test_parser_suppresses_thought_frames',
    'test_parser_unpriced_model_records_no_cost_grok',
    'test_parser_prefers_the_wire_reported_cost',
    'test_parser_usage_absent_records_no_cost',
    'test_parser_surfaces_error_frames_grok',
    'test_parser_records_frozen_spend_on_an_error_frame',
    'test_parser_tolerates_garbage_grok',
    'test_events_render_through_the_production_renderer_grok',
    'test_rates_falls_back_to_the_xai_prefix',
    'test_compute_cost_prices_the_disjoint_buckets',
    'test_compute_cost_tolerates_explicit_null_buckets_grok',
    'test_compute_cost_unpriced_model_returns_none_grok',
    'test_stream_records_cost_model_and_session_grok',
    'test_stream_detached_keeps_session_unpersisted_grok',
    'test_stream_fails_on_error_frames_grok',
    'test_invocation_modes_build_the_pinned_argv_grok',
    'test_config_model_reads_the_models_default',
    'test_seed_config_always_approves',
    'test_seed_links_auth_write_through_grok',
    'test_transcript_resolves_the_encoded_worktree_layout',
]

# pricing keyed on the LiteLLM xai/ prefix so every lookup exercises the
# alias chain (grok's own CLI takes bare ids)
_PRICING = {
    'xai/grok-4.5': {
        'input_cost_per_token': 2e-6,
        'output_cost_per_token': 6e-6,
        'cache_read_input_token_cost': 5e-7,
    },
}

# terminal usage (grok convention: cache_read is DISJOINT from input;
# reasoning folds into output) and its hand-computed cost
_USAGE = {
    'input_tokens': 100,
    'cache_read_input_tokens': 1000,
    'output_tokens': 10,
    'reasoning_tokens': 4,
    'total_tokens': 1110,
}
_USAGE_COST = 100 * 2e-6 + 1000 * 5e-7 + 10 * 6e-6

# the terminal frame carries session, usage, and the served model
_END = {
    'type': 'end',
    'stopReason': 'EndTurn',
    'sessionId': '019f61e5-2f11-7c41-96ef-9a309ee69c57',
    'usage': _USAGE,
    'num_turns': 2,
    'modelUsage': {'grok-4.5': {'inputTokens': 100, 'modelCalls': 2}},
}


def test_capability_flags_report_provider_facts_grok(node_with_db: Node) -> None:
    """The provider facts consumers branch on, plus cost trackability."""
    backend = GrokAgent(node_with_db, 'grok')
    assert backend.name == 'grok'
    assert backend.config_file == 'config.toml'
    assert backend.can_fork
    assert not backend.mints_session
    assert not backend.needs_pricing
    assert backend.cost_scope == 'call'
    assert not backend.enforces_budget
    # a cost-reporting agent tracks spend with or without a model (the wire
    # carries the figure) -- so a capped grok-build node never wedges the
    # pricing pre-flight
    assert backend.tracks_cost('grok-4.5')
    assert backend.tracks_cost('mystery')
    assert backend.tracks_cost()


def test_parser_maps_the_stream_protocol_grok(monkeypatch: pytest.MonkeyPatch) -> None:
    """One protocol implementation: text deltas, then the priced end close."""
    monkeypatch.setattr(pricing, '_load', lambda: _PRICING)
    parser = GrokParser()
    frames = [
        {'type': 'text', 'data': 'do'},
        {'type': 'text', 'data': 'ne'},
        _END,
    ]
    events = [event for line in _lines(frames) for event in parser.feed(line)]
    assert [event.kind for event in events] == [
        'text',
        'text',
        'session',
        'cost',
        'result',
    ]
    text_a, text_b, session, cost, result = events
    assert text_a.text + text_b.text == 'done'
    assert session.session == _END['sessionId']
    # the stream-reported model rides the modelUsage key, and joins the
    # served record the loop's drop check reads
    assert session.model == 'grok-4.5'
    assert parser.models == ['grok-4.5']
    assert cost.cost == pytest.approx(_USAGE_COST)
    # the end frame closes the invocation authoritatively
    assert result.final
    assert result.cost == pytest.approx(_USAGE_COST)
    assert result.turns == 2
    assert result.duration is not None
    assert result.duration >= 0.0


def test_parser_multi_model_usage_reads_as_unknown() -> None:
    """A multi-entry modelUsage names no served model.

    The terminal frame is grok's only model report, and a multi-entry
    usage is ambiguous -- an auxiliary model beside the serving one, not
    necessarily a substitution -- so no entry joins the served record:
    the drop check reads "stream named none" and falls back to the step
    row, which carries the pin.
    """
    parser = GrokParser(model='grok-4.5')
    end = {
        **_END,
        'modelUsage': {
            'grok-4.5': {'inputTokens': 100, 'modelCalls': 2},
            'grok-3-mini': {'inputTokens': 5, 'modelCalls': 1},
        },
    }
    events = [event for line in _lines([end]) for event in parser.feed(line)]
    session = next(event for event in events if event.kind == 'session')
    # the configured model stands and the served record stays empty
    assert session.model == 'grok-4.5'
    assert parser.models == []


def test_parser_suppresses_thought_frames() -> None:
    """Reasoning deltas stay unrendered, mirroring claude's thinking."""
    parser = GrokParser()
    frames = [
        {'type': 'thought', 'data': 'The'},
        {'type': 'thought', 'data': ' plan'},
        {'type': 'text', 'data': 'ok'},
    ]
    events = [event for line in _lines(frames) for event in parser.feed(line)]
    assert [event.kind for event in events] == ['text']


def test_parser_unpriced_model_records_no_cost_grok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unknown/unpriced model closes without inventing a figure."""
    monkeypatch.setattr(pricing, '_load', lambda: {})
    parser = GrokParser()
    events = [event for line in _lines([_END]) for event in parser.feed(line)]
    assert [event.kind for event in events] == ['session', 'result']
    assert parser.cost is None


def test_parser_prefers_the_wire_reported_cost(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A ``total_cost_usd`` on the end frame wins over token pricing.

    Grok's pool model (``grok-build``) carries no LiteLLM price entry, so
    token pricing would drop real spend to NULL -- but the end frame stamps
    the authoritative ``total_cost_usd`` for API-key traffic. The parser
    records the wire figure rather than losing the spend.
    """
    monkeypatch.setattr(pricing, '_load', lambda: {})  # nothing is priceable
    parser = GrokParser()
    end = {**_END, 'total_cost_usd': 0.0512}
    events = [event for line in _lines([end]) for event in parser.feed(line)]
    costs = [event for event in events if event.kind == 'cost']
    assert len(costs) == 1
    assert costs[0].cost == pytest.approx(0.0512)
    assert parser.cost == pytest.approx(0.0512)


@pytest.mark.parametrize(
    argnames='end',
    argvalues=[
        pytest.param(
            {key: value for key, value in _END.items() if key != 'usage'},
            id='absent',
        ),
        pytest.param({**_END, 'usage': None}, id='present-null'),
    ],
)
def test_parser_usage_absent_records_no_cost(
    end: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An end frame without usage closes NULL (unpriced), never $0.

    Grok's protocol carries spend fields on the end frame only when
    available; a priced model must not book an authoritative $0 for an
    absent (or present-null) usage -- the cost is unknowable, not zero.
    """
    monkeypatch.setattr(pricing, '_load', lambda: _PRICING)
    parser = GrokParser()
    events = [event for line in _lines([end]) for event in parser.feed(line)]
    assert [event.kind for event in events] == ['session', 'result']
    assert parser.cost is None


def test_parser_surfaces_error_frames_grok() -> None:
    """Errors ride the JSON stream flat and collect to fail the step."""
    parser = GrokParser()
    frame = {'type': 'error', 'message': "Couldn't set model 'bogus'"}
    (event,) = parser.feed(json.dumps(frame))
    assert event.kind == 'error'
    assert event.message == "Couldn't set model 'bogus'"
    assert parser.errors == ["Couldn't set model 'bogus'"]


def test_parser_records_frozen_spend_on_an_error_frame() -> None:
    """A prompt-level failure freezes spend on the error frame -- record it.

    No end frame follows a prompt-level failure, so the error frame's spend
    is the invocation's only cost fact; dropping it books the burned tokens
    at NULL, and the retry re-burns unrecorded. The wire figure is
    authoritative (grok stamps it), so it is recorded even for an unpriceable
    pool model.
    """
    parser = GrokParser()
    frame = {
        'type': 'error',
        'message': 'context length exceeded',
        'total_cost_usd': 0.033,
    }
    events = parser.feed(json.dumps(frame))
    kinds = [event.kind for event in events]
    assert 'cost' in kinds
    assert 'error' in kinds
    assert parser.cost == pytest.approx(0.033)
    assert parser.errors == ['context length exceeded']


def test_parser_tolerates_garbage_grok() -> None:
    """Malformed, non-object, and unknown lines yield nothing, never raise."""
    parser = GrokParser()
    junk = ['', '   ', 'not json', '[1, 2]', '"text"', '{}', '{"type": "mystery"}']
    assert [event for line in junk for event in parser.feed(line)] == []
    assert parser.session is None
    assert parser.cost is None


def test_events_render_through_the_production_renderer_grok(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Parsed events drive the CLI renderer: messages, errors, cost close."""
    monkeypatch.setattr(pricing, '_load', lambda: _PRICING)
    parser = GrokParser()
    render = StreamRenderer()
    frames = [
        {'type': 'text', 'data': 'Done.'},
        {'type': 'error', 'message': 'rate limited'},
        _END,
    ]
    for line in _lines(frames):
        for event in parser.feed(line):
            render(event)
    captured = capsys.readouterr()
    assert 'Done.' in captured.out
    # the final close prints the terminal frame's turns and priced spend
    assert '— 2 turns, ' in captured.out
    assert f', ${_USAGE_COST:.4f}' in captured.out
    assert 'agent error: rate limited' in captured.err


def test_rates_falls_back_to_the_xai_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The alias chain: exact key wins, the xai/ prefix covers bare ids."""
    monkeypatch.setattr(
        pricing,
        '_load',
        lambda: {**_PRICING, 'grok-exact': {'input_cost_per_token': 1e-6}},
    )
    # an exact hit never consults the prefix
    assert grok._rates('grok-exact') == {'input_cost_per_token': 1e-6}
    # a bare id resolves through the xai/ prefix
    assert grok._rates('grok-4.5') is not None
    # both misses return None (unpriced), never a guessed entry
    assert grok._rates('mystery') is None


def test_compute_cost_prices_the_disjoint_buckets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cache-read is disjoint from input; reasoning is never re-priced."""
    monkeypatch.setattr(pricing, '_load', lambda: _PRICING)
    assert grok._compute_cost(_USAGE, 'grok-4.5') == pytest.approx(_USAGE_COST)


def test_compute_cost_tolerates_explicit_null_buckets_grok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A gateway may send a usage bucket as explicit null, not just absent.

    ``usage.get(key, 0.0)`` skips its default on a present-null key, so the
    coercion reads ``or 0.0`` -- else ``None * rate`` raises and kills the
    stream reader (the loop then SIGKILLs the agent group).
    """
    monkeypatch.setattr(pricing, '_load', lambda: _PRICING)
    null_bucket = {**_USAGE, 'cache_read_input_tokens': None}
    # the null bucket coerces to zero, so its cache-read term drops out
    expected = _USAGE_COST - 1000 * 5e-7
    assert grok._compute_cost(null_bucket, 'grok-4.5') == pytest.approx(expected)


def test_compute_cost_unpriced_model_returns_none_grok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No model or an unpriced model yields no figure."""
    monkeypatch.setattr(pricing, '_load', lambda: {})
    assert grok._compute_cost(_USAGE) is None
    assert grok._compute_cost(_USAGE, 'mystery') is None


def test_stream_records_cost_model_and_session_grok(
    node_with_db: Node,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The stream driver lands session, model, and priced cost on the ledger."""
    monkeypatch.setattr(pricing, '_load', lambda: _PRICING)
    node = node_with_db
    backend = GrokAgent(node, 'grok')
    (step_id,) = _steps(node, 1)
    result = backend.stream(_lines([_END]), step_id=step_id, model='grok-4.5')
    row = node.db.read('steps', where={'step_id': step_id})[0]
    assert row['agent'] == 'grok'
    assert row['session'] == _END['sessionId']
    assert row['model'] == 'grok-4.5'
    assert row['cost'] == pytest.approx(_USAGE_COST)
    assert node.sessions.get('grok') == _END['sessionId']
    assert result.session == _END['sessionId']
    assert result.cost == pytest.approx(_USAGE_COST)


def test_stream_detached_keeps_session_unpersisted_grok(
    node_with_db: Node,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A detached turn stamps the step row but never persists ``.session``."""
    # pin pricing so the priced/unpriced path is host-independent
    monkeypatch.setattr(pricing, '_load', lambda: _PRICING)
    node = node_with_db
    backend = GrokAgent(node, 'grok')
    (step_id,) = _steps(node, 1)
    backend.stream(_lines([_END]), step_id=step_id, detached=True)
    row = node.db.read('steps', where={'step_id': step_id})[0]
    assert row['session'] == _END['sessionId']
    assert node.sessions.get('grok') is None


def test_stream_fails_on_error_frames_grok(node_with_db: Node) -> None:
    """A stream-borne error fails the step even after a fully drained stdout."""
    backend = GrokAgent(node_with_db, 'grok')
    frames = [{'type': 'error', 'message': 'model not supported'}]
    with pytest.raises(
        RuntimeError,
        match='grok reported an error: model not supported',
    ):
        backend.stream(_lines(frames))


def test_invocation_modes_build_the_pinned_argv_grok(node_with_db: Node) -> None:
    """Fresh/resume/fork/model/effort land their exact argv and env."""
    node = node_with_db
    backend = GrokAgent(node, 'grok')
    head = ('grok', '--single=hi', '--output-format', 'streaming-json')
    # fresh sessions launch on the centrally minted id (-s names a NEW one)
    fresh = backend.invocation('hi')
    assert fresh.argv == (*head, '--always-approve', '-s', fresh.session)
    # the attached = form carries a dash-leading message as the message,
    # never parsed as a flag (grok's -p rejects a dash-leading value token)
    dashed = backend.invocation('-1 on that idea')
    assert dashed.argv[1] == '--single=-1 on that idea'
    # the minted id is a real uuid the end frame later echoes back
    assert uuid.UUID(fresh.session)
    # resume continues the session in place
    resume = backend.invocation('hi', session='sess-7')
    assert resume.argv == (*head, '--always-approve', '-r', 'sess-7')
    # fork branches to a grok-minted id
    fork = backend.invocation('hi', session='sess-7', fork=True)
    assert fork.argv == (*head, '--always-approve', '-r', 'sess-7', '--fork-session')
    # the model rides -m and effort rides --reasoning-effort
    tuned = backend.invocation('hi', model='grok-4.5', effort='low')
    assert tuned.argv == (
        *head,
        '--always-approve',
        '-m',
        'grok-4.5',
        '--reasoning-effort',
        'low',
        '-s',
        tuned.session,
    )
    # grok runs in the worktree over the FULL environment plus GROK_HOME
    assert fresh.cwd == node.worktree
    assert fresh.env['GROK_HOME'] == str(node.node_dir / '.grok')
    assert fresh.env['PATH'] == os.environ['PATH']


def test_config_model_reads_the_models_default(node_with_db: Node) -> None:
    """Only ``[models] default`` names the default; top-level keys do not."""
    node = node_with_db
    backend = GrokAgent(node, 'grok')
    config = node.node_dir / '.grok' / 'config.toml'
    # no config file names no model
    assert backend.config_model() is None
    config.parent.mkdir()
    # a top-level model key is not grok's default vocabulary
    config.write_text('model = "top-level"\n', encoding='utf-8')
    assert backend.config_model() is None
    # a malformed config names no model
    config.write_text('models = not toml\n', encoding='utf-8')
    assert backend.config_model() is None
    # the [models] default wins
    config.write_text('[models]\ndefault = "grok-4.5"\n', encoding='utf-8')
    assert backend.config_model() == 'grok-4.5'


def test_seed_config_always_approves(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The packaged grok seed approves tools and disables self-update."""
    monkeypatch.setenv('GROK_HOME', str(tmp_path / 'global-home'))
    node_dir = tmp_path / 'node'
    (node_dir / 'skills').mkdir(parents=True)
    GrokAgent.seed(node_dir)
    config = tomllib.loads(
        (node_dir / '.grok' / 'config.toml').read_text(encoding='utf-8')
    )
    assert config['ui']['permission_mode'] == 'always-approve'
    assert config['cli']['auto_update'] is False


def test_seed_links_auth_write_through_grok(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Auth stays global: the node links through to the canonical file.

    A parent node's ``GROK_HOME`` carries an ``auth.json`` that is itself
    a symlink; the seed canonicalizes through the chain so the node's link
    never dangles when the intermediate node is reset or deleted, and a
    token refresh through the link updates the global file (the secret is
    never copied into the node).
    """
    # the real global home holds the credential; a parent node links to it
    real_home = tmp_path / 'real-home'
    real_home.mkdir()
    (real_home / 'auth.json').write_text('{"secret": 1}\n', encoding='utf-8')
    parent_home = tmp_path / 'parent-home'
    parent_home.mkdir()
    (parent_home / 'auth.json').symlink_to(real_home / 'auth.json')
    monkeypatch.setenv('GROK_HOME', str(parent_home))
    node_dir = tmp_path / 'node'
    (node_dir / 'skills').mkdir(parents=True)
    GrokAgent.seed(node_dir)
    link = node_dir / '.grok' / 'auth.json'
    assert link.is_symlink()
    # the chain canonicalizes to the real file, not the parent's link
    assert link.resolve() == (real_home / 'auth.json').resolve()
    assert json.loads(link.read_text(encoding='utf-8')) == {'secret': 1}
    # a pre-auth seed (no credential written yet) still canonicalizes through
    # the chain, so the link never dangles once the user logs in and the
    # intermediate node is reset or deleted
    (real_home / 'auth.json').unlink()
    fresh_dir = tmp_path / 'fresh-node'
    (fresh_dir / 'skills').mkdir(parents=True)
    GrokAgent.seed(fresh_dir)
    target = (real_home / 'auth.json').resolve()
    assert (fresh_dir / '.grok' / 'auth.json').readlink() == target


def test_transcript_resolves_the_encoded_worktree_layout(
    node_with_db: Node,
) -> None:
    """The events log nests under the url-encoded absolute worktree path."""
    node = node_with_db
    backend = GrokAgent(node, 'grok')
    session = '019f61e5-2f11-7c41-96ef-9a309ee69c57'
    slug = urllib.parse.quote(str(node.worktree), safe='')
    expected = node.node_dir / '.grok' / 'sessions' / slug / session / 'events.jsonl'
    # the expected path returns even while absent, so a poller can wait
    transcript = backend.transcript(session)
    assert transcript['path'] == str(expected)
    assert transcript['exists'] is False
    # a written log resolves and reads back
    expected.parent.mkdir(parents=True)
    expected.write_text('{"type": "end"}\n', encoding='utf-8')
    transcript = backend.transcript(session)
    assert transcript['exists'] is True
    assert transcript['content'] == '{"type": "end"}\n'


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
