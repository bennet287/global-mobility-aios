"""Inspect signed package bytes without installing, extracting or executing REA.

The signer claims a build relation; this predicate proves only statement authenticity
and archive/installed snapshot equality. Source consumption and runtime closure remain
unproven, and every live execution/transport authority flag remains false.
"""
from dataclasses import dataclass
from contextlib import contextmanager, ExitStack
from datetime import timedelta
import hashlib
import json
import os
import posixpath
import re
from pathlib import Path
import stat
import sqlite3
from sqlalchemy.exc import OperationalError
import tarfile
from uuid import uuid4
import zlib
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.services.organization_rea_runtime_footprint import ReaRuntimeFootprintTrust

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import ValidationError
from app.models.domain import now_utc
from app.schemas_organization_rea_build import ReaSignedBuildStatement, ReaPackageFile, package_path
from app.services.audit_log import record_audit
from app.services.organization_command import AuthorityDenied, InvalidTransition, canonical_fingerprint, canonical_json
from app.services import organization_rea_admission as admission, organization_rea_artifacts as artifact
from app.services import organization_rea_ci_attestation as trusted_ci
from app.services.organization_rea_catalog import _bounded_json, ReaCatalogInvalid, REA_SOURCE_COMMIT, REA_LOCAL_CATALOG_SHA256

MAX_EXPANDED = 256 * 1024 * 1024
MAX_FILE = 16 * 1024 * 1024
MAX_FILES = 10000
SOURCE = 'organization_rea_package_v1'
ACTION = 'organization.rea.package.inspect'
# Coordinator pins the complete reviewed Git source-material snapshot here.
REA_SOURCE_MATERIALS_SHA256 = 'a2215de5912f6f7a52573a3d450e75982afaa4c6a48a037894c8a94211bd1552'


@dataclass(frozen=True)
class ReaBuildTrust:
    """Independent deployment configuration; never supplied by a builder envelope."""
    builder_id: str
    builder_public_key: bytes
    build_policy_sha256: str
    installed_root: Path


@dataclass(frozen=True)
class ReaCompilationTrust:
    """Deployment locator plus redundant CI pins, never an authority owner.

    The current human Board-approved provider scope owns the accepted evidence
    identity. These deployment pins must match it exactly and remain non-public.
    """
    report_root: Path
    report_relative: str
    report_sha256: str
    candidate_sha: str
    repository: str
    run_id: str
    run_attempt: str
    workflow_sha256: str
    helper_sha256: str
    provider_decision_id: str
    provider_contract_sha256: str
    ci_attestation: trusted_ci.ReaCiAttestationTrust | None = None


def _compilation_report(trust, *, decision_id, contract, manifest, scope):
    if type(trust) is not ReaCompilationTrust:
        raise AuthorityDenied('independent compilation trust missing')
    approved = scope.compilation_evidence
    if approved is None:
        raise AuthorityDenied('governed compilation evidence approval missing')
    approved_pins = {
        'report_sha256': approved.report_sha256, 'candidate_sha': approved.candidate_sha,
        'repository': approved.repository, 'run_id': approved.run_id, 'run_attempt': approved.run_attempt,
        'workflow_sha256': approved.workflow_sha256, 'helper_sha256': approved.helper_sha256,
    }
    supplied_pins = {
        'report_sha256': trust.report_sha256, 'candidate_sha': trust.candidate_sha,
        'repository': trust.repository, 'run_id': trust.run_id, 'run_attempt': trust.run_attempt,
        'workflow_sha256': trust.workflow_sha256, 'helper_sha256': trust.helper_sha256,
    }
    if canonical_json(supplied_pins) != canonical_json(approved_pins):
        raise InvalidTransition('compilation trust differs from governed review')
    digest_fields = (trust.report_sha256, trust.workflow_sha256, trust.helper_sha256, trust.provider_contract_sha256)
    if any(type(v) is not str or re.fullmatch(r'[0-9a-f]{64}', v) is None for v in digest_fields):
        raise InvalidTransition('compilation trust digest invalid')
    if type(trust.candidate_sha) is not str or re.fullmatch(r'[0-9a-f]{40}', trust.candidate_sha) is None or trust.repository != 'bennet287/global-mobility-aios':
        raise InvalidTransition('compilation trust candidate/repository invalid')
    if type(trust.run_id) is not str or re.fullmatch(r'[1-9][0-9]{0,19}', trust.run_id) is None or type(trust.run_attempt) is not str or re.fullmatch(r'[1-9][0-9]{0,5}', trust.run_attempt) is None:
        raise InvalidTransition('compilation trust run invalid')
    if type(trust.provider_decision_id) is not str or trust.provider_decision_id != str(decision_id) or trust.provider_contract_sha256 != canonical_fingerprint(contract):
        raise InvalidTransition('compilation trust canonical review differs')
    if type(trust.report_relative) is not str:
        raise InvalidTransition('compilation report relative path invalid')
    package_path(trust.report_relative)
    parent = artifact._directory(trust.report_root)
    try:
        parts = trust.report_relative.split('/')
        for part in parts[:-1]:
            if os.fstat(parent).st_mode & 0o222:
                raise InvalidTransition('compilation report directory writable')
            child = os.open(part, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW, dir_fd=parent)
            os.close(parent)
            parent = child
        parent_before = os.fstat(parent)
        if parent_before.st_mode & 0o222:
            raise InvalidTransition('compilation report directory writable')
        fd = os.open(parts[-1], os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK, dir_fd=parent)
    except Exception:
        os.close(parent)
        raise
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_mode & 0o222 or before.st_nlink != 1 or not 0 < before.st_size <= 4*1024*1024:
            raise InvalidTransition('compilation report file mode/link/size unsafe')
        chunks, count = [], 0
        while count <= before.st_size:
            chunk = os.read(fd, min(65536, before.st_size+1-count))
            if not chunk:
                break
            chunks.append(chunk)
            count += len(chunk)
        raw = b''.join(chunks)
        if _identity(os.fstat(fd)) != _identity(before) or _identity(os.fstat(parent)) != _identity(parent_before) or len(raw) != before.st_size or hashlib.sha256(raw).hexdigest() != trust.report_sha256:
            raise InvalidTransition('compilation report bytes differ')
    finally:
        os.close(fd)
        os.close(parent)
    report = _bounded_json(raw)
    def exact(value, expected, message):
        if canonical_json(value) != canonical_json(expected):
            raise InvalidTransition(message)
    def keys(value, expected):
        if type(value) is not dict or set(value) != set(expected):
            raise InvalidTransition('compilation report schema differs')
    keys(report, {'format', 'repeatability', 'package', 'diagnostic_only'})
    exact(report['format'], 'aios-rea-package-correlation.v1', 'compilation report format differs')
    exact(report['diagnostic_only'], True, 'compilation report diagnostic boundary differs')
    repeated = report['repeatability']
    true_flags = {'repeatability_observed', 'source_compiler_recipe_context_observed'}
    false_flags = {'publisher_provenance_verified','runtime_dependency_closure_verified','installed_runtime_bytes_verified','isolation_verified','provider_ready','live_transport_owned','execution_authorized'}
    keys(repeated, {'format','context','source','recipe','toolchain','files','received_manifest_sha256'} | true_flags | false_flags)
    exact(repeated['format'], 'aios-rea-build-repeatability.v1', 'repeatability format differs')
    for flag in true_flags:
        exact(repeated[flag], True, 'compilation observation flag differs')
    for flag in false_flags:
        exact(repeated[flag], False, 'compilation authority flag differs')
    expected_context = {'candidate':trust.candidate_sha,'repository':trust.repository,'run_id':trust.run_id,'run_attempt':trust.run_attempt,'runner':'ubuntu-24.04'}
    exact(repeated['context'], expected_context, 'compilation context differs')
    materials = _materials()
    expected_source = {'commit':REA_SOURCE_COMMIT,'tree':materials['source_tree'],'materials_sha256':REA_SOURCE_MATERIALS_SHA256,
                       'dependency_lock_sha256':materials['dependency_lock_sha256'],'reviewed_recipe_sha256':materials['recipe_sha256'],
                       'tracked_files':materials['file_count'],'tracked_bytes':materials['total_bytes']}
    exact(repeated['source'], expected_source, 'compilation source inputs differ')
    expected_recipe = {'helper_sha256':trust.helper_sha256,'workflow_sha256':trust.workflow_sha256,
                       'command':'node node_modules/typescript/bin/tsc -p tsconfig.build.json','lifecycle_scripts':False,'fresh_npm_cache':True}
    exact(repeated['recipe'], expected_recipe, 'compilation recipe differs')
    tools = repeated['toolchain']
    keys(tools, {'versions','input_sha256'})
    exact(tools['versions'], {'node':'v24.18.0','npm':'11.16.0','typescript':'5.9.3'}, 'compilation tool versions differ')
    keys(tools['input_sha256'], {'node','npm_cli','npm_package','typescript_package','typescript_entry','typescript_tsc','typescript_compiler'})
    if any(type(v) is not str or re.fullmatch(r'[0-9a-f]{64}', v) is None for v in tools['input_sha256'].values()):
        raise InvalidTransition('compilation tool hashes invalid')
    received = repeated['received_manifest_sha256']
    keys(received, {'a','b'})
    if any(type(v) is not str or re.fullmatch(r'[0-9a-f]{64}',v) is None for v in received.values()):
        raise InvalidTransition('received build manifest digests invalid')
    def validated_files(value):
        if type(value) is not list or not 1 <= len(value) <= MAX_FILES:
            raise InvalidTransition('compilation file list invalid')
        parsed = [ReaPackageFile.model_validate(v).model_dump() for v in value]
        paths = [v['path'] for v in parsed]
        if paths != sorted(paths) or len(set(paths)) != len(paths) or len({p.casefold() for p in paths}) != len(paths) or sum(v['size'] for v in parsed) > MAX_EXPANDED:
            raise InvalidTransition('compilation file list incomplete/unsafe')
        return parsed
    package = report['package']
    keys(package, {'archive_sha256','archive_bytes','files'})
    exact(package['archive_sha256'], scope.build_sha256, 'compilation approved archive digest differs')
    exact(package['archive_bytes'], scope.build_bytes, 'compilation approved archive size differs')
    exact(validated_files(package['files']), manifest, 'compilation complete package manifest differs')
    dist = [{'path':v['path'][5:],'size':v['size'],'sha256':v['sha256']} for v in manifest if v['path'].startswith('dist/')]
    exact(validated_files(repeated['files']), dist, 'compilation complete dist manifest differs')
    return {'report_sha256':trust.report_sha256,'context':expected_context,'workflow_sha256':trust.workflow_sha256,'helper_sha256':trust.helper_sha256,
            'provider_decision_id':str(decision_id),'provider_contract_sha256':trust.provider_contract_sha256,
            'governed_compilation_evidence_approved':True,
            'governed_compilation_evidence_sha256':canonical_fingerprint(approved.model_dump(mode='json')),
            'compiled_dist_manifest_sha256':canonical_fingerprint(dist),'compiled_dist_files':len(dist),'compiled_dist_bytes':sum(v['size'] for v in dist),
            'accepted_ci_bytes_assumed':True,'owning_github_execution_authenticated':False}


def _materials():
    raw = (Path(__file__).parent / 'rea_catalog' / 'build_materials.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != REA_SOURCE_MATERIALS_SHA256:
        raise InvalidTransition('reviewed source-material snapshot digest differs')
    value = _bounded_json(raw)
    if value.get('source_commit') != REA_SOURCE_COMMIT or value.get('package_name') != 'rea-agents' or value.get('package_version') != '3.2.1':
        raise InvalidTransition('source-material identity differs')
    return value


def _read_archive(trust, scope):
    fd = artifact._source_file(trust.build_root, trust.build_relative)
    try:
        before = os.fstat(fd)
        if before.st_mode & 0o222 or before.st_nlink != 1 or before.st_size != scope.build_bytes:
            raise InvalidTransition('archive mode/link/size differs')
        chunks = []
        size = 0
        while True:
            chunk = os.read(fd, min(1024*1024, scope.build_bytes+1-size))
            if not chunk:
                break
            size += len(chunk)
            if size > scope.build_bytes:
                raise InvalidTransition('archive grew')
            chunks.append(chunk)
        raw = b''.join(chunks)
        after = os.fstat(fd)
        if _identity(before) != _identity(after) or len(raw) != scope.build_bytes or hashlib.sha256(raw).hexdigest() != scope.build_sha256:
            raise InvalidTransition('archive changed or digest differs')
        return raw
    finally:
        os.close(fd)


def _identity(s):
    return (s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def _archive_manifest(raw):
    """One bounded gzip stream of plain USTAR records; no aliases/extensions."""
    decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
    expanded = bytearray()
    for offset in range(0, len(raw), 1024*1024):
        pending = raw[offset:offset+1024*1024]
        while pending:
            expanded.extend(decoder.decompress(pending, MAX_EXPANDED+1-len(expanded)))
            if len(expanded) > MAX_EXPANDED:
                raise InvalidTransition('expanded archive exceeds bound')
            pending = decoder.unconsumed_tail
        if decoder.unused_data:
            raise InvalidTransition('concatenated gzip or trailing bytes denied')
    if not decoder.eof:
        raise InvalidTransition('incomplete gzip stream')
    data = bytes(expanded)
    if len(data) % 512:
        raise InvalidTransition('tar alignment differs')
    files, contents, seen, folded = [], {}, set(), set()
    offset = 0
    while offset + 512 <= len(data):
        header = data[offset:offset+512]
        if header == bytes(512):
            if len(data)-offset < 1024 or any(data[offset:]):
                raise InvalidTransition('tar trailer or extra stream invalid')
            return sorted(files, key=lambda v:v['path']), contents
        if header[257:263] != b'ustar\x00' or header[263:265] != b'00':
            raise InvalidTransition('only plain USTAR headers admitted')
        # TarInfo also accepts GNU base-256 integers under USTAR magic.
        # Admit only the profile's ASCII octal fields with padding at their ends.
        for start, end in ((100,108), (108,116), (116,124), (124,136), (136,148), (148,156), (329,337), (337,345)):
            pattern = rb' *[0-7]*[\x00 ]*' if start >= 329 else rb' *[0-7]+[\x00 ]*'
            if re.fullmatch(pattern, header[start:end]) is None:
                raise InvalidTransition('non-octal USTAR numeric field denied')
        for text_field in (header[:100], header[157:257], header[345:500]):
            if b'\x00' in text_field and any(text_field.split(b'\x00',1)[1]):
                raise InvalidTransition('noncanonical tar text padding denied')
        item = tarfile.TarInfo.frombuf(header, 'utf-8', 'strict')
        if item.type not in {tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.DIRTYPE} or item.linkname or item.pax_headers or item.sparse:
            raise InvalidTransition('archive links/devices/extensions denied')
        name = item.name
        if item.isdir() and name.endswith('/'):
            name = name[:-1]
        package_path(name)
        if name in seen or name.casefold() in folded or len(seen) >= MAX_FILES:
            raise InvalidTransition('duplicate or excessive archive entries')
        seen.add(name)
        folded.add(name.casefold())
        if name != 'package' and not name.startswith('package/'):
            raise InvalidTransition('archive requires package prefix')
        if name == 'package' and not item.isdir():
            raise InvalidTransition('package root must be directory')
        if item.size < 0 or item.size > MAX_FILE or (item.isdir() and item.size != 0):
            raise InvalidTransition('archive member size invalid')
        offset += 512
        end = offset+item.size
        padded = offset+((item.size+511)//512)*512
        if padded > len(data) or any(data[end:padded]):
            raise InvalidTransition('archive body/padding invalid')
        if item.isfile():
            path = name[len('package/'):]
            body = data[offset:end]
            files.append(dict(path=path, size=item.size, sha256=hashlib.sha256(body).hexdigest()))
            if path == 'package.json':
                contents[path] = body
        offset = padded
    raise InvalidTransition('missing tar trailer')


def _verify_source_assets(files, contents, materials):
    by_path = {v['path']:v for v in files}
    if 'package.json' not in contents:
        raise InvalidTransition('package metadata missing')
    package = _bounded_json(contents['package.json'])
    if type(package) is not dict or package.get('name') != 'rea-agents' or package.get('version') != '3.2.1' or package.get('bin') != {'rea':'scripts/rea.mjs', 'rea-agents':'scripts/rea.mjs'}:
        raise InvalidTransition('package identity/bin differs')
    # Complete source assets selected by the pinned source package's files list.
    declared = package.get('files')
    if type(declared) is not list or any(type(p) is not str for p in declared):
        raise InvalidTransition('source package files declaration invalid')
    required = {'package.json','LICENSE','README.md'}
    for path in materials:
        if any(path == prefix or path.startswith(prefix+'/') for prefix in declared if prefix != 'dist'):
            required.add(path)
    for path in required:
        source = materials.get(path)
        observed = by_path.get(path)
        if source is None or observed is None or observed['sha256'] != source['sha256'] or observed['size'] != source['size']:
            raise InvalidTransition('required shipped source asset differs')
    for path, observed in by_path.items():
        if path in materials and (observed['sha256'] != materials[path]['sha256'] or observed['size'] != materials[path]['size']):
            raise InvalidTransition('shipped source asset differs from reviewed input')
    if not {'dist/main.js', 'dist/mcpDoctor.js', 'dist/cli.js', 'dist/cliOutput.js'} <= set(by_path):
        raise InvalidTransition('generated dist package output missing')


@contextmanager
def _installed_snapshot(root, *, max_file=None, allowed_links=None):
    """Retain the inspected objects and namespace bindings through audit commit.

    External ancestors bind only object/type/mode: unrelated sibling activity is
    not package drift. The installed subtree retains complete stat identities and
    directory inventories. This does not freeze bytes for later provider use.
    """
    if not isinstance(root, Path) or not root.is_absolute() or any(part in {'.', '..'} for part in root.parts):
        raise InvalidTransition('custody roots must be explicit absolute paths')
    if max_file is None:
        max_file = MAX_FILE
    if allowed_links is None:
        allowed_links = {}
    if type(max_file) is not int or not 0 < max_file <= MAX_EXPANDED or type(allowed_links) is not dict:
        raise InvalidTransition('installed snapshot policy invalid')
    files, retained, visited, folded = [], [], 0, set()
    ancestors, bindings = [], []
    links, regular_paths = [], set()
    total = 0
    def ancestor_identity(value):
        return (value.st_dev, value.st_ino, value.st_mode)
    def revalidate():
        for parent, name, child, identity in ancestors:
            if ancestor_identity(os.fstat(child)) != identity or ancestor_identity(os.stat(name, dir_fd=parent, follow_symlinks=False)) != identity:
                raise InvalidTransition('installed ancestor path binding changed')
        for fd, identity, names in retained:
            if _identity(os.fstat(fd)) != identity or (names is not None and sorted(os.listdir(fd)) != names):
                raise InvalidTransition('installed snapshot changed before completion')
        for parent, name, identity in bindings:
            if _identity(os.stat(name, dir_fd=parent, follow_symlinks=False)) != identity:
                raise InvalidTransition('installed package path binding changed')
        for parent, name, target, _ in links:
            if os.readlink(name, dir_fd=parent) != target:
                raise InvalidTransition('installed declared link changed')
    def walk(fd, prefix, depth):
        nonlocal visited, total
        before = os.fstat(fd)
        if depth > 80 or before.st_mode & 0o022:
            raise InvalidTransition('installed directory unsafe')
        names = sorted(os.listdir(fd))
        held_parent = os.dup(fd)
        retained.append((held_parent, _identity(before), names))
        for name in names:
            visited += 1
            if visited > MAX_FILES:
                raise InvalidTransition('installed entry count exceeds bound')
            path = prefix+'/'+name if prefix else name
            package_path(path)
            if path.casefold() in folded:
                raise InvalidTransition('installed casefold collision denied')
            folded.add(path.casefold())
            child_stat = os.stat(name, dir_fd=fd, follow_symlinks=False)
            bindings.append((held_parent, name, _identity(child_stat)))
            if stat.S_ISDIR(child_stat.st_mode):
                child = os.open(name, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW, dir_fd=fd)
                try:
                    if _identity(os.fstat(child)) != _identity(child_stat):
                        raise InvalidTransition('installed directory changed during open')
                    walk(child, path, depth+1)
                finally:
                    os.close(child)
            elif stat.S_ISREG(child_stat.st_mode):
                if child_stat.st_mode & 0o222 or child_stat.st_nlink != 1 or child_stat.st_size > max_file:
                    raise InvalidTransition('installed file mode/link/size unsafe')
                total += child_stat.st_size
                if total > MAX_EXPANDED:
                    raise InvalidTransition('installed total exceeds bound')
                child = os.open(name, os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK, dir_fd=fd)
                try:
                    if _identity(os.fstat(child)) != _identity(child_stat):
                        raise InvalidTransition('installed file changed during open')
                    digest = artifact._bytes(child, child_stat.st_size)
                    if _identity(os.fstat(child)) != _identity(child_stat):
                        raise InvalidTransition('installed file changed during read')
                    retained.append((os.dup(child), _identity(child_stat), None))
                    files.append(dict(path=path,size=child_stat.st_size,sha256=digest))
                    regular_paths.add(path)
                finally:
                    os.close(child)
            elif stat.S_ISLNK(child_stat.st_mode) and path in allowed_links:
                target = os.readlink(name, dir_fd=fd)
                if type(allowed_links[path]) is not str or target != allowed_links[path] or target.startswith('/') or '\\' in target or any(ord(c) < 32 or ord(c) == 127 for c in target):
                    raise InvalidTransition('installed declared link target unsafe')
                destination = posixpath.normpath(posixpath.join(prefix, target))
                package_path(destination)
                child = os.open(name, os.O_PATH|os.O_NOFOLLOW, dir_fd=fd)
                try:
                    if child_stat.st_nlink != 1 or _identity(os.fstat(child)) != _identity(child_stat):
                        raise InvalidTransition('installed declared link changed during open')
                    retained.append((os.dup(child), _identity(child_stat), None))
                    raw_target = target.encode('utf-8')
                    if len(raw_target) != child_stat.st_size:
                        raise InvalidTransition('installed declared link size differs')
                    files.append(dict(path=path,size=child_stat.st_size,sha256=hashlib.sha256(raw_target).hexdigest()))
                    links.append((held_parent, name, target, destination))
                    total += child_stat.st_size
                    if total > MAX_EXPANDED:
                        raise InvalidTransition('installed total exceeds bound')
                finally:
                    os.close(child)
            else:
                raise InvalidTransition('installed links/devices denied')
        if _identity(os.fstat(fd)) != _identity(before) or sorted(os.listdir(fd)) != names:
            raise InvalidTransition('installed directory changed during scan')
    root_chain = []
    try:
        root_fd = os.open('/', os.O_RDONLY|os.O_DIRECTORY)
        root_chain.append(root_fd)
        for name in root.parts[1:]:
            child = os.open(name, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW, dir_fd=root_fd)
            root_chain.append(child)
            ancestors.append((root_fd, name, child, ancestor_identity(os.fstat(child))))
            root_fd = child
        walk(root_fd, '', 0)
        if not files:
            raise InvalidTransition('installed package empty')
        if len(links) != len(allowed_links) or any(destination not in regular_paths for _, _, _, destination in links):
            raise InvalidTransition('installed declared link absent or target not regular')
        directories = {''}
        for file in files:
            parts = file['path'].split('/')
            directories.update('/'.join(parts[:i]) for i in range(1, len(parts)))
        if visited != len(files)+len(directories)-1:
            raise InvalidTransition('installed empty extra directory denied')
        revalidate()
        yield sorted(files, key=lambda v:v['path']), revalidate
    finally:
        for fd, _, _ in retained:
            os.close(fd)
        for fd in reversed(root_chain):
            os.close(fd)


def _installed_manifest(root):
    with _installed_snapshot(root) as (files, _):
        return files


def inspect_rea_package(session, context, *, decision_id, attempt_id, receipt_id,
                        deployment_trust: admission.ReaDeploymentTrust,
                        build_trust: ReaBuildTrust, signed_statement: bytes,
                        compilation_trust: ReaCompilationTrust | None = None,
                        runtime_trust: 'ReaRuntimeFootprintTrust | None' = None):
    """Emit nonauthorizing evidence after fresh canonical and byte checks."""
    installed_custody = ExitStack()
    try:
        parsed = _bounded_json(signed_statement)
        envelope = ReaSignedBuildStatement.model_validate(parsed)
        statement = envelope.statement
        if type(build_trust) is not ReaBuildTrust or type(build_trust.builder_public_key) is not bytes or len(build_trust.builder_public_key) != 32 or statement.builder_id != build_trust.builder_id or statement.build_policy_sha256 != build_trust.build_policy_sha256:
            raise AuthorityDenied('independent builder trust differs')
        # Authenticate exact received statement values, including ISO timestamp spelling.
        signed = parsed['statement']
        try:
            Ed25519PublicKey.from_public_bytes(build_trust.builder_public_key).verify(bytes.fromhex(envelope.signature_hex), canonical_json(signed).encode())
        except (ValueError, InvalidSignature) as exc:
            raise AuthorityDenied('builder statement signature invalid') from exc
        if statement.source_commit != REA_SOURCE_COMMIT or statement.source_materials_sha256 != REA_SOURCE_MATERIALS_SHA256 or statement.catalog_sha256 != REA_LOCAL_CATALOG_SHA256:
            raise InvalidTransition('builder source/catalog commitment differs')
        material_snapshot = _materials()
        if statement.recipe_sha256 != material_snapshot['recipe_sha256'] or statement.dependency_lock_sha256 != material_snapshot['dependency_lock_sha256']:
            raise InvalidTransition('builder recipe/dependency input commitment differs')
        materials = {v['path']:v for v in material_snapshot['files']}
        row, contract, scope, authorized = admission.resolve_rea_provider_review(session, context, decision_id=decision_id, trust=deployment_trust)
        work, attempt = admission._barrier(session, context, authorized.work_item_id, attempt_id)
        compilation_summary = None
        attestation_summary = None
        revalidate_attestation = None
        revalidate_installed = None
        runtime_summary = None
        revalidate_runtime = None
        manifest = None
        def fresh():
            current = admission.resolve_rea_provider_review(session, context, decision_id=decision_id, trust=deployment_trust)
            if canonical_fingerprint(current[1]) != canonical_fingerprint(contract):
                raise InvalidTransition('provider contract changed during package inspection')
            admission._attempt(session, context, work.id, attempt.id)
            artifact.revalidate_rea_artifact_custody(session, context, receipt_id=receipt_id, decision_id=authorized.decision_id, custody_root=deployment_trust.custody_root)
            require_fresh_time()
            if revalidate_attestation is not None:
                revalidate_attestation()
            if compilation_summary is not None:
                current_report = _compilation_report(compilation_trust, decision_id=row.id, contract=contract, manifest=manifest, scope=scope)
                if canonical_json(current_report) != canonical_json(compilation_summary):
                    raise InvalidTransition('compilation report changed during inspection')
            if revalidate_installed is not None:
                revalidate_installed()
            if revalidate_runtime is not None:
                revalidate_runtime()
        def require_fresh_time():
            now = artifact._utc(now_utc())
            if not statement.started_at <= statement.finished_at <= now < min(scope.expires_at, authorized.expires_at) or now-statement.finished_at > timedelta(hours=24):
                raise InvalidTransition('builder statement chronology/age/authorization invalid')
        fresh()
        if statement.archive_sha256 != scope.build_sha256 or statement.archive_bytes != scope.build_bytes:
            raise InvalidTransition('builder archive differs from approved review')
        archive = _read_archive(deployment_trust, scope)
        manifest, contents = _archive_manifest(archive)
        if manifest != [v.model_dump() for v in statement.files]:
            raise InvalidTransition('archive complete manifest differs from signed claim')
        _verify_source_assets(manifest, contents, materials)
        installed, revalidate_installed = installed_custody.enter_context(_installed_snapshot(build_trust.installed_root))
        if installed != manifest:
            raise InvalidTransition('installed complete manifest differs from archive')
        if runtime_trust is not None:
            if scope.runtime_footprint is None:
                raise AuthorityDenied('governed runtime footprint evidence required')
            from app.services import organization_rea_runtime_footprint as runtime
            runtime_summary, revalidate_runtime = runtime.inspect_footprint(installed_custody, runtime_trust,
                scope.runtime_footprint, scope=scope, package_manifest=manifest)
        if compilation_trust is not None:
            compilation_summary = _compilation_report(compilation_trust, decision_id=row.id, contract=contract, manifest=manifest, scope=scope)
            approved_attestation = scope.compilation_evidence.ci_attestation
            if approved_attestation is not None or compilation_trust.ci_attestation is not None:
                attestation_summary, revalidate_attestation = trusted_ci.authenticate(compilation_trust, approved_attestation)
        result = dict(receipt_id=str(uuid4()), tenant_key=context.tenant_key, work_item_id=str(work.id), attempt_id=str(attempt.id), attempt_number=attempt.attempt_number,
            execution_token_sha256=hashlib.sha256(attempt.execution_token.encode()).hexdigest(), decision_id=str(row.id), contract_sha256=canonical_fingerprint(contract),
            artifact_decision_id=str(authorized.decision_id), artifact_sha256=authorized.artifact_sha256, custody_receipt_id=str(receipt_id),
            catalog_sha256=REA_LOCAL_CATALOG_SHA256, source_commit=REA_SOURCE_COMMIT, source_materials_sha256=REA_SOURCE_MATERIALS_SHA256,
            archive_sha256=scope.build_sha256, installed_manifest_sha256=canonical_fingerprint(installed), statement_sha256=canonical_fingerprint(signed),
            envelope_sha256=hashlib.sha256(signed_statement).hexdigest(), builder_key_sha256=hashlib.sha256(build_trust.builder_public_key).hexdigest(), builder_id=build_trust.builder_id, build_policy_sha256=build_trust.build_policy_sha256,
            signed_builder_statement_verified=True, package_archive_manifest_verified=True, installed_package_snapshot_matches=True,
            source_to_build_verified=False, publisher_verified=False, runtime_closure_verified=False, provider_ready=False, execution_authorized=False, live_transport_owned=False, isolation_verified=False,
            blockers=['actual_source_build_reproducibility_unproven','publisher_provenance_unproven','dependency_and_node_runtime_closure_unproven','immutable_installed_bytes_at_use_unproven','actual_worker_isolation_unproven','owned_live_transport_unproven','per_call_entitlement_and_resources_unadmitted'])
        if compilation_summary is not None:
            result['blockers'] = ['authenticated_ci_execution_provenance_unproven' if value == 'actual_source_build_reproducibility_unproven' else value for value in result['blockers']]
            result['compiled_package_dist_matches'] = True
            result['governed_compilation_evidence_approved'] = True
            result['governed_compilation_evidence_sha256'] = compilation_summary['governed_compilation_evidence_sha256']
            result['compilation_report_sha256'] = compilation_summary['report_sha256']
        if runtime_summary is not None:
            result['reviewed_runtime_footprint_matches'] = True
            result['runtime_footprint_sha256'] = runtime_summary['manifest_sha256']
        if attestation_summary is not None:
            result['attesting_execution_identity_verified'] = True
            result['candidate_to_ci_source_relation_verified'] = attestation_summary['candidate_to_ci_source_relation_verified']
            if attestation_summary['candidate_to_ci_source_relation_verified']:
                result['committed_recipe_bytes_match_review'] = True
            if attestation_summary.get('compiler_workflow_outputs_authenticated') is True:
                result['compiler_workflow_outputs_authenticated'] = True
            result['independent_compiler_causality_verified'] = False
            result['blockers'] = ['independent_compiler_causality_unproven' if value == 'authenticated_ci_execution_provenance_unproven' else value for value in result['blockers']]
        evidence = {'result':result, 'signed_envelope':parsed}
        if attestation_summary is not None:
            evidence['ci_attestation'] = attestation_summary
        if compilation_summary is not None:
            evidence['compilation_correlation'] = compilation_summary
        if runtime_summary is not None:
            evidence['runtime_footprint'] = runtime_summary
        serialized_evidence = json.dumps(evidence, ensure_ascii=True, sort_keys=True)
        if len(canonical_json(evidence).encode()) > artifact.MAX_AUDIT_BYTES or len(serialized_evidence.encode()) > artifact.MAX_AUDIT_BYTES:
            raise InvalidTransition('signed package evidence exceeds audit JSON bounds')
        artifact._json(serialized_evidence, limit=artifact.MAX_AUDIT_BYTES)
        fresh()
        record_audit(session, action=ACTION, entity_type='rea_package_inspection', entity_id=result['receipt_id'], after_state=evidence, actor=context.actor_id, source=SOURCE)
        fresh()
        require_fresh_time()
        session.commit()
        return result
    except OperationalError as exc:
        session.rollback()
        if getattr(exc.orig,'sqlstate',None) not in {'40001','40P01','55P03'} and (getattr(exc.orig,'sqlite_errorcode',0) & 0xff) not in {sqlite3.SQLITE_BUSY,sqlite3.SQLITE_LOCKED}:
            raise
        raise InvalidTransition('package inspection database serialization failed') from exc
    except (ValidationError, ReaCatalogInvalid, zlib.error, tarfile.TarError, UnicodeError, ValueError, OSError) as exc:
        session.rollback()
        raise InvalidTransition('invalid or unsafe package inspection input') from exc
    except Exception:
        session.rollback()
        raise
    finally:
        installed_custody.close()
