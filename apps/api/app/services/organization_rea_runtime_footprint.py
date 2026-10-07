"""Reviewed physical Node/dependency inventory, without importing or executing it.

The manifest binds opaque payload bytes to a reviewed commitment. Node's version
is a reviewed label; upstream authenticity, ABI compatibility and immutable
future use do not follow from this scan.
"""
from dataclasses import dataclass
from contextlib import contextmanager
from pathlib import Path
import os
import posixpath
import re

from app.services import organization_rea_ci_attestation as ci
from app.services.organization_command import canonical_fingerprint
from app.schemas_organization_rea_build import package_path


@dataclass(frozen=True)
class ReaRuntimeFootprintTrust:
    runtime_root: Path
    manifest_root: Path
    manifest_relative: str
    manifest_sha256: str
    node_sha256: str
    node_bytes: int
    node_version: str
    platform: str
    architecture: str


_NAME = r'(?:@[a-zA-Z0-9_.-]+/)?[a-zA-Z0-9_.-]+'
_PACKAGE = re.compile(r'^node_modules/' + _NAME + r'(?:/node_modules/' + _NAME + r')*$')
_DIGEST = re.compile(r'^[0-9a-f]{64}$')


@contextmanager
def _report_snapshot(root, relative):
    """Keep report namespace ancestors and leaf bound through the owning audit."""
    ci.require(isinstance(root, Path) and root.is_absolute() and not any(part in {'.', '..'} for part in root.parts), 'runtime report root invalid')
    package_path(relative)
    descriptors, bindings = [], []
    ancestor_identity = lambda value: (value.st_dev, value.st_ino, value.st_mode)
    identity = lambda value: (value.st_dev, value.st_ino, value.st_mode, value.st_nlink, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
    try:
        parent = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
        descriptors.append(parent)
        for name in list(root.parts[1:]) + relative.split('/')[:-1]:
            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            descriptors.append(child)
            bindings.append((parent, name, child, ancestor_identity(os.fstat(child))))
            parent = child
        name = relative.split('/')[-1]
        leaf = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        descriptors.append(leaf)
        raw, leaf_identity, parent_identity = ci.immutable_snapshot(root, relative, ci.MAX_JSON)
        ci.require(identity(os.fstat(leaf)) == leaf_identity and identity(os.fstat(parent)) == parent_identity, 'runtime report changed during custody binding')
        def revalidate():
            for base, component, child, expected in bindings:
                ci.require(ancestor_identity(os.fstat(child)) == expected
                    and ancestor_identity(os.stat(component, dir_fd=base, follow_symlinks=False)) == expected,
                    'runtime report ancestor binding changed')
            ci.require(identity(os.fstat(leaf)) == leaf_identity
                and identity(os.stat(name, dir_fd=parent, follow_symlinks=False)) == leaf_identity
                and identity(os.fstat(parent)) == parent_identity, 'runtime report custody changed')
            current, current_identity, current_parent = ci.immutable_snapshot(root, relative, ci.MAX_JSON)
            ci.require(current == raw and current_identity == leaf_identity and current_parent == parent_identity, 'runtime report bytes changed')
        revalidate()
        yield raw, revalidate
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _target_applies(rule, target):
    ci.require(type(rule) is list and bool(rule) and all(type(v) is str and v for v in rule), 'runtime target rule invalid')
    positives = [v for v in rule if not v.startswith('!')]
    return '!' + target not in rule and (not positives or target in positives or 'any' in positives)


def _production_packages(lock, package):
    """Use the reviewed npm v3 topology, retaining peer and nested production nodes."""
    ci.require(type(lock) is dict and set(lock) == {'name', 'version', 'lockfileVersion', 'requires', 'packages'}
        and type(lock['lockfileVersion']) is int and lock['lockfileVersion'] == 3 and lock['requires'] is True,
        'runtime requires exact npm lock v3')
    ci.require(type(package) is dict and type(lock['packages']) is dict and '' in lock['packages'], 'runtime root package missing')
    root = lock['packages']['']
    ci.require(type(root) is dict and lock['name'] == package.get('name') == root.get('name') == 'rea-agents'
        and lock['version'] == package.get('version') == root.get('version') == '3.2.1', 'runtime package identity differs')
    for key in ('dependencies', 'devDependencies', 'optionalDependencies', 'bin', 'engines'):
        ci.require(root.get(key, {}) == package.get(key, {}), 'runtime root package declarations differ')
    result = {}
    for path, item in lock['packages'].items():
        if not path:
            continue
        ci.require(type(path) is str and _PACKAGE.fullmatch(path) is not None and type(item) is dict, 'runtime package topology invalid')
        package_path(path)
        for flag in ('dev', 'optional', 'peer', 'devOptional', 'link', 'inBundle', 'hasInstallScript'):
            ci.require(flag not in item or type(item[flag]) is bool, 'runtime lock flag invalid')
        if item.get('dev'):
            continue
        ci.require(not any(item.get(flag) for flag in ('devOptional', 'link', 'inBundle', 'hasInstallScript')),
            'runtime production lock mode unsupported')
        applicable = all(_target_applies(item[key], target) for key, target in (('os', 'linux'), ('cpu', 'x64')) if key in item)
        if not applicable:
            ci.require(item.get('optional') is True, 'runtime required package target unavailable')
            continue
        ci.require(type(item.get('version')) is str and bool(item['version'])
            and type(item.get('resolved')) is str and item['resolved'].startswith('https://registry.npmjs.org/')
            and type(item.get('integrity')) is str and item['integrity'].startswith('sha512-'), 'runtime package lock identity missing')
        result[path] = item
    ci.require(bool(result) and len(result) <= 10000, 'runtime production topology empty or excessive')
    return result


def _bins(value, name):
    if type(value) is str:
        value = {name.split('/')[-1]: value}
    ci.require(type(value) is dict, 'runtime bin declaration invalid')
    result = {}
    for alias, target in value.items():
        ci.require(type(alias) is str and re.fullmatch(r'[a-zA-Z0-9_.-]+', alias) is not None and alias not in {'.', '..'}, 'runtime bin alias invalid')
        ci.require(type(target) is str, 'runtime bin target invalid')
        if target.startswith('./'):
            target = target[2:]
        package_path(target)
        result[alias] = target
    return result


def _package_metadata(path, metadata, locked):
    name = path.rsplit('/node_modules/', 1)[-1] if '/node_modules/' in path else path[len('node_modules/'):]
    ci.require(type(metadata) is dict and metadata.get('name') == name and metadata.get('version') == locked['version'], 'runtime installed package identity differs')
    for key in ('dependencies', 'optionalDependencies', 'peerDependencies', 'peerDependenciesMeta'):
        ci.require(metadata.get(key, {}) == locked.get(key, {}), 'runtime installed dependency declarations differ')
    declared = _bins(metadata.get('bin', {}), name)
    ci.require(declared == _bins(locked.get('bin', {}), name), 'runtime installed bin declarations differ')
    base = path.rsplit('/', 2)[0] if name.startswith('@') else path.rsplit('/', 1)[0]
    return {base + '/.bin/' + alias: posixpath.relpath(path + '/' + target, base + '/.bin') for alias, target in declared.items()}


def _owner(path):
    """Return the deepest npm package namespace, rejecting unknown nested packages."""
    parts = path.split('/')
    index = 0
    owner = None
    while index < len(parts) and parts[index] == 'node_modules':
        index += 1
        if index >= len(parts) or parts[index] == '.bin':
            return owner
        scoped = parts[index].startswith('@')
        index += 2 if scoped else 1
        if index > len(parts):
            return None
        owner = '/'.join(parts[:index])
    return owner


def inspect_footprint(stack, trust, approved, *, scope, package_manifest):
    """Retain complete readonly inventory and revalidate its custody at audit barriers."""
    # Lazy import permits build's owning workflow to call this predicate.
    from app.services import organization_rea_build as build
    ci.require(type(trust) is ReaRuntimeFootprintTrust and approved is not None, 'runtime footprint deployment/review missing')
    pins = {key: getattr(trust, key) for key in ('manifest_sha256', 'node_sha256', 'node_bytes', 'node_version', 'platform', 'architecture')}
    ci.require(pins == {key: getattr(approved, key) for key in pins}, 'runtime footprint deployment pins differ from Board review')
    ci.require(all(type(pins[key]) is str and _DIGEST.fullmatch(pins[key]) for key in ('manifest_sha256', 'node_sha256'))
        and type(trust.node_bytes) is int and 0 < trust.node_bytes <= build.MAX_EXPANDED
        and trust.platform == scope.platform == 'linux' and trust.architecture == 'x64', 'runtime footprint target/pins unsupported')
    ci.require(type(trust.node_version) is str and len(trust.node_version) <= 32 and re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', trust.node_version), 'runtime reviewed Node label invalid')
    major, minor, _ = map(int, trust.node_version.split('.'))
    ci.require((major == 22 and minor >= 19) or major > 24 or (major == 24 and minor >= 11), 'runtime reviewed Node engine label unsupported')
    # Separate evidence namespace prevents the inventory from authenticating itself.
    ci.require(isinstance(trust.runtime_root, Path) and isinstance(trust.manifest_root, Path)
        and trust.runtime_root.is_absolute() and trust.manifest_root.is_absolute()
        and not trust.manifest_root.is_relative_to(trust.runtime_root), 'runtime evidence root must be separate')
    raw, revalidate_report = stack.enter_context(_report_snapshot(trust.manifest_root, trust.manifest_relative))
    ci.require(ci.sha(raw) == trust.manifest_sha256, 'runtime footprint manifest pin differs')
    report = ci.parse_json(raw)
    ci.require(type(report) is dict and set(report) == {'format', 'target', 'node_version', 'source_materials_sha256',
        'package_archive_sha256', 'package_manifest_sha256', 'files', 'links'}
        and report['format'] == 'aios-rea-runtime-footprint.v1', 'runtime footprint manifest schema differs')
    ci.require(type(report['files']) is list and 0 < len(report['files']) <= build.MAX_FILES, 'runtime footprint file list invalid')
    for item in report['files']:
        ci.require(type(item) is dict and set(item) == {'path', 'size', 'sha256'}
            and type(item['size']) is int and 0 <= item['size'] <= build.MAX_EXPANDED
            and type(item['sha256']) is str and _DIGEST.fullmatch(item['sha256']), 'runtime footprint file record invalid')
        package_path(item['path'])
    paths = [item['path'] for item in report['files']]
    ci.require(paths == sorted(paths) and len(set(paths)) == len(paths)
        and len({path.casefold() for path in paths}) == len(paths)
        and sum(item['size'] for item in report['files']) <= build.MAX_EXPANDED, 'runtime footprint manifest sorting/bounds invalid')
    ci.require(report['target'] == {'platform': 'linux', 'architecture': 'x64'} and report['node_version'] == trust.node_version
        and report['source_materials_sha256'] == build.REA_SOURCE_MATERIALS_SHA256
        and report['package_archive_sha256'] == scope.build_sha256
        and report['package_manifest_sha256'] == canonical_fingerprint(package_manifest), 'runtime footprint reviewed package context differs')
    materials = {item['path']: item for item in build._materials()['files']}
    metadata_raw = {}
    def read_json(relative):
        content, _, _ = ci.immutable_snapshot(trust.runtime_root, relative, ci.MAX_JSON)
        metadata_raw[relative] = content
        return ci.parse_json(content)
    package = read_json('package.json')
    lock = read_json('package-lock.json')
    ci.require(all(ci.sha(metadata_raw[key]) == materials[key]['sha256'] for key in ('package.json', 'package-lock.json')), 'runtime source package/lock digest differs')
    expected = _production_packages(lock, package)
    hidden = read_json('node_modules/.package-lock.json')
    ci.require(type(hidden) is dict and set(hidden) == {'name', 'version', 'lockfileVersion', 'requires', 'packages'}
        and hidden['name'] == 'rea-agents' and hidden['version'] == '3.2.1' and type(hidden['lockfileVersion']) is int
        and hidden['lockfileVersion'] == 3 and hidden['requires'] is True and hidden['packages'] == expected,
        'runtime installed npm topology differs from complete reviewed production lock')
    links = {}
    for path, item in sorted(expected.items()):
        declared = _package_metadata(path, read_json(path + '/package.json'), item)
        ci.require(not (set(links) & set(declared)), 'runtime bin alias collision denied')
        links.update(declared)
    declared_links = [{'path': path, 'target': target} for path, target in sorted(links.items())]
    ci.require(report['links'] == declared_links, 'runtime manifest links differ from locked declarations')
    files, revalidate_inventory = stack.enter_context(build._installed_snapshot(trust.runtime_root, max_file=build.MAX_EXPANDED, allowed_links=links))
    ci.require(report['files'] == files, 'runtime complete installed inventory differs from manifest')
    by_path = {item['path']: item for item in files}
    ci.require(by_path.get('bin/node') == {'path': 'bin/node', 'size': trust.node_bytes, 'sha256': trust.node_sha256}, 'runtime Node bytes differ from reviewed pin')
    for path, content in metadata_raw.items():
        ci.require(by_path.get(path) == {'path': path, 'size': len(content), 'sha256': ci.sha(content)}, 'runtime metadata changed during inventory')
    for path in by_path:
        if path in {'bin/node', 'package.json', 'package-lock.json', 'node_modules/.package-lock.json'} or path in links:
            continue
        ci.require(_owner(path) in expected, 'runtime extra package/file namespace denied')
    def revalidate():
        revalidate_inventory()
        revalidate_report()
    revalidate()
    return {'manifest_sha256': trust.manifest_sha256, 'node_sha256': trust.node_sha256,
        'node_bytes': trust.node_bytes, 'node_version': trust.node_version, 'platform': trust.platform,
        'architecture': trust.architecture, 'source_materials_sha256': build.REA_SOURCE_MATERIALS_SHA256,
        'package_archive_sha256': scope.build_sha256, 'package_manifest_sha256': report['package_manifest_sha256'],
        'production_package_count': len(expected), 'file_count': len(files), 'link_count': len(links),
        'total_bytes': sum(item['size'] for item in files)}, revalidate
