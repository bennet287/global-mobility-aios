"""Governed physical footprint evidence; inert payloads are never executed.

The lock fixture is the exact MIT donor input pinned by source materials. Package
metadata and bin payloads below are synthetic, explicitly reviewed test bytes.
"""
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
import json
import os

import pytest
from sqlmodel import select

from app.models.domain import AuditLog
from app.schemas_organization_rea_admission import ReaRuntimeFootprintEvidence, ReaProviderScope
from app.services import organization_rea_admission as admission
from app.services import organization_rea_build as build
from app.services import organization_rea_ci_attestation as ci
from app.services import organization_rea_runtime_footprint as runtime
from app.services.organization_command import AuthorityDenied, InvalidTransition, canonical_fingerprint, canonical_json
from tests.test_organization_rea_admission import board, approve, challenge, consume, lineage_snapshot
from tests.test_organization_rea_build import package_setup, members, inspect, assert_no_audit


@pytest.fixture
def runtime_setup(db_session, board, package_setup, tmp_path):
    state = package_setup
    root = tmp_path / 'runtime'; root.mkdir()
    reports = tmp_path / 'runtime-reports'; reports.mkdir()
    package_raw = next(raw for item, raw in members(state['archive']) if item.name == 'package/package.json')
    lock_raw = (Path(__file__).parent / 'fixtures/rea_runtime/package-lock.json').read_bytes()
    lock = json.loads(lock_raw)
    expected = runtime._production_packages(lock, json.loads(package_raw))
    contents = {'package.json': package_raw, 'package-lock.json': lock_raw,
        'bin/node': b'inert reviewed Node fixture, never executed',
        'node_modules/.package-lock.json': canonical_json({**lock, 'packages': expected}).encode()}
    links = {}
    for path, item in expected.items():
        name = path.rsplit('/node_modules/', 1)[-1] if '/node_modules/' in path else path[len('node_modules/'):]
        metadata = {'name': name, 'version': item['version']}
        for key in ('dependencies', 'optionalDependencies', 'peerDependencies', 'peerDependenciesMeta', 'bin'):
            if key in item: metadata[key] = item[key]
        contents[path + '/package.json'] = canonical_json(metadata).encode()
        for target in runtime._bins(metadata.get('bin', {}), name).values():
            contents[path + '/' + target] = b'inert bin payload'
        links.update(runtime._package_metadata(path, metadata, item))
    contents['node_modules/@lydell/node-pty-linux-x64/pty.node'] = b'inert native payload'
    for path, raw in contents.items():
        dest = root / path; dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw); dest.chmod(0o444)
    for path, target in links.items():
        dest = root / path; dest.parent.mkdir(parents=True, exist_ok=True); dest.symlink_to(target)
    for directory, _, _ in os.walk(root): os.chmod(directory, 0o555)
    with build._installed_snapshot(root, max_file=build.MAX_EXPANDED, allowed_links=links) as (files, _):
        report = dict(format='aios-rea-runtime-footprint.v1', target={'platform': 'linux', 'architecture': 'x64'},
            node_version='24.19.0', source_materials_sha256=build.REA_SOURCE_MATERIALS_SHA256,
            package_archive_sha256=state['request'].scope.build_sha256,
            package_manifest_sha256=canonical_fingerprint(state['manifest']), files=files,
            links=[{'path': path, 'target': target} for path, target in sorted(links.items())])
    raw = canonical_json(report).encode(); (reports / 'manifest.json').write_bytes(raw)
    (reports / 'manifest.json').chmod(0o444); reports.chmod(0o555)
    trust = runtime.ReaRuntimeFootprintTrust(root, reports, 'manifest.json', ci.sha(raw),
        ci.sha(contents['bin/node']), len(contents['bin/node']), '24.19.0', 'linux', 'x64')
    evidence = ReaRuntimeFootprintEvidence(**{key: getattr(trust, key) for key in
        ('manifest_sha256', 'node_sha256', 'node_bytes', 'node_version', 'platform', 'architecture')},
        review_reference='Board reviewed explicitly inert test fixture')
    request = state['request'].model_copy(deep=True)
    request.decision_key = 'runtime-footprint-review'; request.supersedes_decision_id = state['row'].id
    request.scope.runtime_footprint = evidence
    state['row'] = approve(db_session, board, admission.propose_rea_provider_review(db_session, board, request))
    state.update(request=request, runtime_trust=trust, runtime_root=root, runtime_reports=reports)
    return state


def test_reviewed_footprint_is_non_authorizing(db_session, board, runtime_setup):
    state = runtime_setup
    result = inspect(db_session, board, state, runtime_trust=state['runtime_trust'])
    assert result['reviewed_runtime_footprint_matches'] is True
    assert not any(result[key] for key in ('runtime_closure_verified', 'provider_ready', 'execution_authorized', 'isolation_verified'))
    assert 'dependency_and_node_runtime_closure_unproven' in result['blockers']
    log = db_session.exec(select(AuditLog).where(AuditLog.action == build.ACTION)).one()
    summary = build.artifact._json(log.after_state_json)['runtime_footprint']
    assert summary['production_package_count'] == 136
    assert summary['link_count'] == 13
    encoded = canonical_json(summary)
    assert str(state['runtime_root']) not in encoded
    assert state['attempt'].execution_token not in encoded
    assert len(admission._contract(state['row'])[1].tools) == 122


def test_deployment_locator_cannot_supply_missing_board_approval(db_session, board, package_setup, tmp_path):
    trust = runtime.ReaRuntimeFootprintTrust(tmp_path, tmp_path / 'report', 'manifest.json', 'a'*64, 'b'*64, 1, '24.19.0', 'linux', 'x64')
    with pytest.raises(AuthorityDenied, match='governed runtime footprint'):
        inspect(db_session, board, package_setup, runtime_trust=trust)
    assert_no_audit(db_session)


def test_runtime_review_does_not_require_optional_inspection(db_session, board, runtime_setup):
    result = inspect(db_session, board, runtime_setup)
    assert 'reviewed_runtime_footprint_matches' not in result
    assert result['provider_ready'] is False


def test_positive_review_cannot_be_removed_on_retry(db_session, board, runtime_setup):
    from app.services.organization_command import IdempotencyConflict
    before = lineage_snapshot(db_session, runtime_setup['row'])
    request = runtime_setup['request'].model_copy(deep=True)
    request.scope.runtime_footprint = None
    with pytest.raises(IdempotencyConflict): admission.propose_rea_provider_review(db_session, board, request)
    assert lineage_snapshot(db_session, runtime_setup['row']) == before


@pytest.mark.parametrize('version', ['22.18.9', '23.99.0', '24.10.9', '24.19.0-alpha', '9'*40 + '.0.0'])
def test_reviewed_node_label_rejects_unsupported_or_unbounded_versions(version):
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ReaRuntimeFootprintEvidence(manifest_sha256='a'*64, node_sha256='b'*64, node_bytes=1,
            node_version=version, platform='linux', architecture='x64', review_reference='Reviewed inert fixture')


@pytest.mark.parametrize('barrier', ['before-audit', 'after-audit'])
@pytest.mark.parametrize('mutation', ['node-replacement', 'native-rewrite', 'link-replacement', 'report-replacement', 'runtime-replacement'])
def test_runtime_custody_denial_rolls_back(db_session, board, runtime_setup, monkeypatch, barrier, mutation):
    state = runtime_setup; changed = False
    def mutate():
        nonlocal changed
        changed = True
        if mutation == 'runtime-replacement':
            import shutil
            root = state['runtime_root']; old = root.with_name('old-runtime')
            root.rename(old); shutil.copytree(old, root, symlinks=True)
            return
        path = (state['runtime_reports'] / 'manifest.json' if mutation == 'report-replacement' else
            state['runtime_root'] / ('node_modules/.bin/rea' if mutation == 'link-replacement' else
                'node_modules/@lydell/node-pty-linux-x64/pty.node' if mutation == 'native-rewrite' else 'bin/node'))
        if mutation == 'link-replacement':
            path = next((state['runtime_root'] / 'node_modules/.bin').iterdir())
        path.parent.chmod(0o755)
        if mutation == 'link-replacement':
            target = os.readlink(path); path.unlink(); path.symlink_to(target)
        elif mutation == 'native-rewrite':
            path.chmod(0o644); path.write_bytes(b'changed native payload'); path.chmod(0o444)
        else:
            raw = path.read_bytes(); old = path.with_name(path.name + '-held'); path.rename(old)
            path.write_bytes(raw); path.chmod(0o444)
        path.parent.chmod(0o555)
    if barrier == 'before-audit':
        original = build.artifact.revalidate_rea_artifact_custody; calls = 0
        def custody(*args, **kwargs):
            nonlocal calls
            result = original(*args, **kwargs); calls += 1
            if calls == 2: mutate()
            return result
        monkeypatch.setattr(build.artifact, 'revalidate_rea_artifact_custody', custody)
    else:
        original = build.record_audit
        def audit(*args, **kwargs): original(*args, **kwargs); mutate()
        monkeypatch.setattr(build, 'record_audit', audit)
    with pytest.raises(InvalidTransition): inspect(db_session, board, state, runtime_trust=state['runtime_trust'])
    assert changed
    assert_no_audit(db_session)


@pytest.mark.parametrize('failure', ['none', 'audit', 'commit'])
def test_runtime_descriptors_retained_through_commit_and_closed(db_session, board, runtime_setup, monkeypatch, failure):
    state = runtime_setup; active = False
    original = runtime._report_snapshot
    @contextmanager
    def snapshot(*args, **kwargs):
        nonlocal active
        with original(*args, **kwargs) as value:
            active = True
            try: yield value
            finally: active = False
    monkeypatch.setattr(runtime, '_report_snapshot', snapshot)
    original_audit = build.record_audit
    def audit(*args, **kwargs):
        assert active
        original_audit(*args, **kwargs)
        if failure == 'audit': raise RuntimeError('injected audit failure')
    monkeypatch.setattr(build, 'record_audit', audit)
    original_commit = db_session.commit
    def commit():
        assert active
        if failure == 'commit': raise RuntimeError('injected commit failure')
        original_commit()
    monkeypatch.setattr(db_session, 'commit', commit)
    before = set(os.listdir('/proc/self/fd'))
    if failure == 'none': inspect(db_session, board, state, runtime_trust=state['runtime_trust'])
    else:
        with pytest.raises(RuntimeError): inspect(db_session, board, state, runtime_trust=state['runtime_trust'])
        assert_no_audit(db_session)
    assert not active
    assert set(os.listdir('/proc/self/fd')) == before


@pytest.mark.parametrize('compilation_present', [False, True])
@pytest.mark.parametrize('runtime_present', [False, True])
def test_nullable_evidence_history_preserves_fingerprint_and_lineage(db_session, board, tmp_path, monkeypatch, compilation_present, runtime_present):
    original = ReaProviderScope.model_dump
    def prior(self, *args, **kwargs):
        value = original(self, *args, **kwargs)
        for key, present in [('compilation_evidence', compilation_present), ('runtime_footprint', runtime_present)]:
            if present: value[key] = None
            else: value.pop(key, None)
        return value
    with monkeypatch.context() as historical:
        historical.setattr(ReaProviderScope, 'model_dump', prior)
        state = package_setup.__wrapped__(db_session, board, tmp_path)
    before = lineage_snapshot(db_session, state['row'])
    original_contract = build.artifact._json(state['row'].conditions_json)[0]
    assert admission._contract(state['row'])[0] == original_contract
    ch = challenge(db_session, board, state)
    assert ch['scope'] == original_contract['scope']
    consume(db_session, board, state, ch)
    assert admission.propose_rea_provider_review(db_session, board, state['request']).id == state['row'].id
    assert inspect(db_session, board, state)['provider_ready'] is False
    assert lineage_snapshot(db_session, state['row']) == before
