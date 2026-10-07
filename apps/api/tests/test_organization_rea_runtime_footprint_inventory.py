"""Physical inventory rejects undeclared payloads without executing Node or imports."""
from contextlib import ExitStack
from dataclasses import replace
from types import SimpleNamespace
import json
import os

import pytest

from app.services import organization_rea_build as build
from app.services import organization_rea_ci_attestation as ci
from app.services import organization_rea_runtime_footprint as footprint
from app.services.organization_command import canonical_fingerprint, canonical_json, InvalidTransition
from app.schemas_organization_rea_admission import ReaRuntimeFootprintEvidence


def locked(version='1.0.0', **kwargs):
    return dict(version=version, resolved='https://registry.npmjs.org/a/-/a-1.0.0.tgz', integrity='sha512-reviewed', **kwargs)


def topology():
    package = {'name': 'rea-agents', 'version': '3.2.1', 'dependencies': {'alpha': '1.0.0'}}
    root = dict(package)
    packages = {'': root, 'node_modules/alpha': locked(bin={'alpha': 'bin/main.js'}),
        'node_modules/alpha/node_modules/nested': locked(), 'node_modules/peer-only': locked(peer=True),
        'node_modules/linux-native': locked(optional=True, os=['linux'], cpu=['x64']),
        'node_modules/darwin-native': locked(optional=True, os=['darwin'], cpu=['x64']),
        'node_modules/development': locked(dev=True)}
    lock = dict(name='rea-agents', version='3.2.1', lockfileVersion=3, requires=True, packages=packages)
    return lock, package


def test_production_topology_retains_nested_peer_and_target_optional():
    lock, package = topology()
    assert set(footprint._production_packages(lock, package)) == {'node_modules/alpha', 'node_modules/alpha/node_modules/nested',
        'node_modules/peer-only', 'node_modules/linux-native'}


@pytest.mark.parametrize('field,value', [('link', True), ('hasInstallScript', True), ('inBundle', True), ('devOptional', True), ('dev', 1)])
def test_unsupported_production_flags_fail_closed(field, value):
    lock, package = topology()
    lock['packages']['node_modules/alpha'][field] = value
    with pytest.raises(InvalidTransition):
        footprint._production_packages(lock, package)


def test_missing_required_target_is_not_silently_omitted():
    lock, package = topology()
    lock['packages']['node_modules/darwin-native']['optional'] = False
    with pytest.raises(InvalidTransition, match='required package target'):
        footprint._production_packages(lock, package)


@pytest.mark.parametrize('rule,result', [(['linux'], True), (['!darwin'], True), (['!linux'], False), (['darwin'], False), (['any', '!linux'], False)])
def test_npm_target_allow_deny_rules(rule, result):
    assert footprint._target_applies(rule, 'linux') is result


def test_scoped_and_nested_bin_links_are_declared_at_the_correct_level():
    assert footprint._package_metadata('node_modules/@scope/tool', {'name': '@scope/tool', 'version': '1.0.0', 'bin': './bin.js'},
        locked(bin={'tool': 'bin.js'})) == {'node_modules/.bin/tool': '../@scope/tool/bin.js'}
    assert footprint._package_metadata('node_modules/alpha/node_modules/nested', {'name': 'nested', 'version': '1.0.0', 'bin': {'nested': 'bin.js'}},
        locked(bin={'nested': 'bin.js'})) == {'node_modules/alpha/node_modules/.bin/nested': '../nested/bin.js'}


@pytest.mark.parametrize('bin_decl', [{'bad': '../escape'}, {'../alias': 'main.js'}, {'bad': '/absolute'}, {'bad': 'folder/../escape'}])
def test_bin_targets_and_aliases_cannot_escape(bin_decl):
    with pytest.raises((ValueError, InvalidTransition)):
        footprint._bins(bin_decl, 'alpha')


def test_deepest_package_owner_exposes_undeclared_nested_package():
    assert footprint._owner('node_modules/alpha/node_modules/unknown/main.js') == 'node_modules/alpha/node_modules/unknown'
    assert footprint._owner('node_modules/@scope/tool/main.js') == 'node_modules/@scope/tool'
    assert footprint._owner('extra/main.js') is None


@pytest.fixture
def inert_runtime(tmp_path, monkeypatch):
    runtime = tmp_path / 'runtime'
    report_root = tmp_path / 'reports'
    runtime.mkdir(); report_root.mkdir()
    lock, package = topology()
    expected = footprint._production_packages(lock, package)
    contents = {'package.json': canonical_json(package).encode(), 'package-lock.json': canonical_json(lock).encode(),
        'bin/node': b'opaque reviewed bytes, never run',
        'node_modules/.package-lock.json': canonical_json({**lock, 'packages': expected}).encode()}
    for path, item in expected.items():
        name = path.rsplit('/node_modules/', 1)[-1] if '/node_modules/' in path else path[len('node_modules/'):]
        metadata = {'name': name, 'version': item['version']}
        if 'bin' in item:
            metadata['bin'] = item['bin']
            contents[path + '/bin/main.js'] = b'opaque JavaScript'
        contents[path + '/package.json'] = canonical_json(metadata).encode()
    for path, raw in contents.items():
        dest = runtime / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw); dest.chmod(0o444)
    alias = 'node_modules/.bin/alpha'
    target = '../alpha/bin/main.js'
    (runtime / alias).parent.mkdir()
    (runtime / alias).symlink_to(target)
    for directory, _, _ in os.walk(runtime):
        os.chmod(directory, 0o555)
    materials = {'files': [{'path': key, 'sha256': ci.sha(contents[key])} for key in ('package.json', 'package-lock.json')]}
    monkeypatch.setattr(build, '_materials', lambda: materials)
    with build._installed_snapshot(runtime, max_file=build.MAX_EXPANDED, allowed_links={alias: target}) as (files, _):
        report = dict(format='aios-rea-runtime-footprint.v1', target={'platform': 'linux', 'architecture': 'x64'},
            node_version='24.13.0', source_materials_sha256=build.REA_SOURCE_MATERIALS_SHA256,
            package_archive_sha256='a'*64, package_manifest_sha256=canonical_fingerprint([]), files=files,
            links=[{'path': alias, 'target': target}])
    def seal(value=report):
        report_root.chmod(0o755)
        path = report_root / 'report.json'
        if path.exists():
            path.chmod(0o644)
        raw = canonical_json(value).encode()
        path.write_bytes(raw); path.chmod(0o444); report_root.chmod(0o555)
        trust = footprint.ReaRuntimeFootprintTrust(runtime, report_root, 'report.json', ci.sha(raw), ci.sha(contents['bin/node']),
            len(contents['bin/node']), '24.13.0', 'linux', 'x64')
        approved = ReaRuntimeFootprintEvidence(**{key: getattr(trust, key) for key in ('manifest_sha256', 'node_sha256', 'node_bytes', 'node_version', 'platform', 'architecture')},
            review_reference='Human reviewed inert test footprint')
        return trust, approved
    trust, approved = seal()
    return SimpleNamespace(runtime=runtime, reports=report_root, trust=trust, approved=approved, report=report,
        seal=seal, scope=SimpleNamespace(platform='linux', build_sha256='a'*64))


def inspect(state, stack, trust=None, approved=None):
    return footprint.inspect_footprint(stack, trust or state.trust, approved or state.approved,
        scope=state.scope, package_manifest=[])


def test_inert_complete_inventory_passes_and_closes_descriptors(inert_runtime):
    with ExitStack() as stack:
        summary, revalidate = inspect(inert_runtime, stack)
        assert summary['production_package_count'] == 4
        assert summary['link_count'] == 1
        assert summary['node_sha256'] == inert_runtime.approved.node_sha256
        revalidate()


def test_deployment_and_board_pins_must_match(inert_runtime):
    with ExitStack() as stack, pytest.raises(InvalidTransition, match='Board review'):
        inspect(inert_runtime, stack, trust=replace(inert_runtime.trust, node_sha256='b'*64))


@pytest.mark.parametrize('field,value', [('package_archive_sha256', 'b'*64), ('package_manifest_sha256', 'c'*64),
    ('source_materials_sha256', 'd'*64), ('target', {'platform': 'darwin', 'architecture': 'x64'})])
def test_report_context_must_match_reviewed_package(inert_runtime, field, value):
    trust, approved = inert_runtime.seal({**inert_runtime.report, field: value})
    with ExitStack() as stack, pytest.raises(InvalidTransition, match='context differs'):
        inspect(inert_runtime, stack, trust=trust, approved=approved)


def test_missing_inventory_record_cannot_pass_under_new_manifest_pin(inert_runtime):
    report = {**inert_runtime.report, 'files': inert_runtime.report['files'][1:]}
    trust, approved = inert_runtime.seal(report)
    with ExitStack() as stack, pytest.raises(InvalidTransition, match='complete installed inventory'):
        inspect(inert_runtime, stack, trust=trust, approved=approved)


def test_boolean_size_is_not_accepted_as_integer_manifest_record(inert_runtime):
    records = [dict(item) for item in inert_runtime.report['files']]
    records[0]['size'] = True
    trust, approved = inert_runtime.seal({**inert_runtime.report, 'files': records})
    with ExitStack() as stack, pytest.raises(InvalidTransition, match='file record invalid'):
        inspect(inert_runtime, stack, trust=trust, approved=approved)


def test_reviewed_node_pin_must_match_actual_inventory(inert_runtime):
    trust = replace(inert_runtime.trust, node_sha256='b'*64)
    approved = inert_runtime.approved.model_copy(update={'node_sha256': 'b'*64})
    with ExitStack() as stack, pytest.raises(InvalidTransition, match='Node bytes differ'):
        inspect(inert_runtime, stack, trust=trust, approved=approved)


def test_extra_undeclared_package_rejected_even_if_manifest_pinned(inert_runtime):
    runtime = inert_runtime.runtime
    (runtime / 'node_modules').chmod(0o755)
    extra = runtime / 'node_modules/unknown'
    extra.mkdir(); (extra / 'payload').write_bytes(b'extra'); (extra / 'payload').chmod(0o444)
    extra.chmod(0o555); (runtime / 'node_modules').chmod(0o555)
    with build._installed_snapshot(runtime, max_file=build.MAX_EXPANDED, allowed_links={'node_modules/.bin/alpha': '../alpha/bin/main.js'}) as (files, _):
        trust, approved = inert_runtime.seal({**inert_runtime.report, 'files': files})
    with ExitStack() as stack, pytest.raises(InvalidTransition, match='extra package'):
        inspect(inert_runtime, stack, trust=trust, approved=approved)


@pytest.mark.parametrize('mutation', ['node_bytes', 'node_binding', 'report_bytes', 'report_binding', 'report_ancestor', 'bin_binding'])
def test_custody_barrier_detects_payload_report_and_namespace_changes(inert_runtime, mutation):
    with ExitStack() as stack:
        _, revalidate = inspect(inert_runtime, stack)
        if mutation == 'node_bytes':
            path = inert_runtime.runtime / 'bin/node'
            path.chmod(0o644); path.write_bytes(b'changed'); path.chmod(0o444)
        elif mutation == 'node_binding':
            parent = inert_runtime.runtime / 'bin'; parent.chmod(0o755)
            path = parent / 'node'; path.rename(parent / 'old')
            path.write_bytes(b'opaque reviewed bytes, never run'); path.chmod(0o444); parent.chmod(0o555)
        elif mutation == 'bin_binding':
            parent = inert_runtime.runtime / 'node_modules/.bin'; parent.chmod(0o755)
            (parent / 'alpha').unlink(); (parent / 'alpha').symlink_to('../peer-only/package.json'); parent.chmod(0o555)
        elif mutation == 'report_bytes':
            path = inert_runtime.reports / 'report.json'; path.chmod(0o644); path.write_bytes(b'{}'); path.chmod(0o444)
        elif mutation == 'report_binding':
            raw = (inert_runtime.reports / 'report.json').read_bytes()
            inert_runtime.reports.chmod(0o755)
            (inert_runtime.reports / 'report.json').unlink()
            (inert_runtime.reports / 'report.json').write_bytes(raw)
            (inert_runtime.reports / 'report.json').chmod(0o444); inert_runtime.reports.chmod(0o555)
        else:
            moved = inert_runtime.reports.with_name('moved-reports')
            inert_runtime.reports.rename(moved)
            inert_runtime.reports.mkdir(); inert_runtime.reports.chmod(0o555)
        with pytest.raises((InvalidTransition, OSError)):
            revalidate()
