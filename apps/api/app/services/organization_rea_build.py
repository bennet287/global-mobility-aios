"""Inspect signed package bytes without installing, extracting or executing REA.

The signer claims a build relation; this predicate proves only statement authenticity
and archive/installed snapshot equality. Source consumption and runtime closure remain
unproven, and every live execution/transport authority flag remains false.
"""
from dataclasses import dataclass
from datetime import timedelta
import hashlib
import json
import os
import re
from pathlib import Path
import stat
import sqlite3
from sqlalchemy.exc import OperationalError
import tarfile
from uuid import uuid4
import zlib

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import ValidationError
from app.models.domain import now_utc
from app.schemas_organization_rea_build import ReaSignedBuildStatement, package_path
from app.services.audit_log import record_audit
from app.services.organization_command import AuthorityDenied, InvalidTransition, canonical_fingerprint, canonical_json
from app.services import organization_rea_admission as admission, organization_rea_artifacts as artifact
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


def _installed_manifest(root):
    root_fd = artifact._directory(root)
    files, retained, visited, folded = [], [], 0, set()
    total = 0
    def walk(fd, prefix, depth):
        nonlocal visited, total
        before = os.fstat(fd)
        if depth > 80 or before.st_mode & 0o022:
            raise InvalidTransition('installed directory unsafe')
        names = sorted(os.listdir(fd))
        retained.append((os.dup(fd), _identity(before), names))
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
            if stat.S_ISDIR(child_stat.st_mode):
                child = os.open(name, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW, dir_fd=fd)
                try:
                    if _identity(os.fstat(child)) != _identity(child_stat):
                        raise InvalidTransition('installed directory changed during open')
                    walk(child, path, depth+1)
                finally:
                    os.close(child)
            elif stat.S_ISREG(child_stat.st_mode):
                if child_stat.st_mode & 0o222 or child_stat.st_nlink != 1 or child_stat.st_size > MAX_FILE:
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
                finally:
                    os.close(child)
            else:
                raise InvalidTransition('installed links/devices denied')
        if _identity(os.fstat(fd)) != _identity(before) or sorted(os.listdir(fd)) != names:
            raise InvalidTransition('installed directory changed during scan')
    try:
        walk(root_fd, '', 0)
        if not files:
            raise InvalidTransition('installed package empty')
        ancestors = {''}
        for file in files:
            parts = file['path'].split('/')
            ancestors.update('/'.join(parts[:i]) for i in range(1, len(parts)))
        if visited != len(files)+len(ancestors)-1:
            raise InvalidTransition('installed empty extra directory denied')
        for fd, identity, names in retained:
            if _identity(os.fstat(fd)) != identity or (names is not None and sorted(os.listdir(fd)) != names):
                raise InvalidTransition('installed snapshot changed before completion')
        return sorted(files, key=lambda v:v['path'])
    finally:
        for fd, _, _ in retained:
            os.close(fd)
        os.close(root_fd)


def inspect_rea_package(session, context, *, decision_id, attempt_id, receipt_id,
                        deployment_trust: admission.ReaDeploymentTrust,
                        build_trust: ReaBuildTrust, signed_statement: bytes):
    """Emit nonauthorizing evidence after fresh canonical and byte checks."""
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
        def fresh():
            current = admission.resolve_rea_provider_review(session, context, decision_id=decision_id, trust=deployment_trust)
            if canonical_fingerprint(current[1]) != canonical_fingerprint(contract):
                raise InvalidTransition('provider contract changed during package inspection')
            admission._attempt(session, context, work.id, attempt.id)
            artifact.revalidate_rea_artifact_custody(session, context, receipt_id=receipt_id, decision_id=authorized.decision_id, custody_root=deployment_trust.custody_root)
            require_fresh_time()
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
        installed = _installed_manifest(build_trust.installed_root)
        if installed != manifest:
            raise InvalidTransition('installed complete manifest differs from archive')
        result = dict(receipt_id=str(uuid4()), tenant_key=context.tenant_key, work_item_id=str(work.id), attempt_id=str(attempt.id), attempt_number=attempt.attempt_number,
            execution_token_sha256=hashlib.sha256(attempt.execution_token.encode()).hexdigest(), decision_id=str(row.id), contract_sha256=canonical_fingerprint(contract),
            artifact_decision_id=str(authorized.decision_id), artifact_sha256=authorized.artifact_sha256, custody_receipt_id=str(receipt_id),
            catalog_sha256=REA_LOCAL_CATALOG_SHA256, source_commit=REA_SOURCE_COMMIT, source_materials_sha256=REA_SOURCE_MATERIALS_SHA256,
            archive_sha256=scope.build_sha256, installed_manifest_sha256=canonical_fingerprint(installed), statement_sha256=canonical_fingerprint(signed),
            envelope_sha256=hashlib.sha256(signed_statement).hexdigest(), builder_key_sha256=hashlib.sha256(build_trust.builder_public_key).hexdigest(), builder_id=build_trust.builder_id, build_policy_sha256=build_trust.build_policy_sha256,
            signed_builder_statement_verified=True, package_archive_manifest_verified=True, installed_package_snapshot_matches=True,
            source_to_build_verified=False, publisher_verified=False, runtime_closure_verified=False, provider_ready=False, execution_authorized=False, live_transport_owned=False, isolation_verified=False,
            blockers=['actual_source_build_reproducibility_unproven','publisher_provenance_unproven','dependency_and_node_runtime_closure_unproven','immutable_installed_bytes_at_use_unproven','actual_worker_isolation_unproven','owned_live_transport_unproven','per_call_entitlement_and_resources_unadmitted'])
        evidence = {'result':result, 'signed_envelope':parsed}
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
