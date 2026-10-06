"""Hash-bound Git object proofs. No Git execution or candidate module loading."""
import base64
import binascii
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from app.services.organization_command import InvalidTransition
from app.services.organization_rea_catalog import _bounded_json

MAX_WITNESS = 4_000_000
PATHS = ('.github/workflows/rea-build-repeatability.yml', 'scripts/rea_build_repeatability.py', 'scripts/rea_ci_attestation.py')

def require(condition, message):
    if not condition:
        raise InvalidTransition('CI source relation: ' + message)

def object_sha(kind, raw):
    return hashlib.sha1(kind.encode() + b' ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()

@dataclass(frozen=True)
class ReaCiSourceRelationTrust:
    witness_root: Path
    witness_relative: str
    witness_sha256: str
    reviewed_verifier_sha256: str
    approved_base_sha: str | None = None


def commit(raw):
    require(0 < len(raw) <= 128 * 1024 and b'\0' not in raw and b'\n\n' in raw, 'invalid commit bytes')
    header = raw.split(b'\n\n', 1)[0].split(b'\n')
    require(re.fullmatch(rb'tree [0-9a-f]{40}', header[0]) is not None, 'commit tree header')
    tree = header[0][5:].decode()
    index = 1
    parents = []
    while index < len(header) and header[index].startswith(b'parent '):
        require(re.fullmatch(rb'parent [0-9a-f]{40}', header[index]) is not None, 'commit parent header')
        parents.append(header[index][7:].decode()); index += 1
    require(len(parents) <= 16 and len(set(parents)) == len(parents), 'commit parent bounds')
    seen = set()
    last = None
    for line in header[index:]:
        if line.startswith(b' '):
            require(last == b'gpgsig', 'unexpected commit continuation')
            continue
        key, separator, value = line.partition(b' ')
        require(separator and value and key in (b'author', b'committer', b'encoding', b'gpgsig') and key not in seen, 'unsupported commit header')
        if key in (b'author', b'committer'):
            require(re.fullmatch(rb'.+ <[^<>\n]+> [0-9]+ [+-][0-9]{4}', value) is not None, 'commit identity header')
        seen.add(key); last = key
    require(b'author' in seen and b'committer' in seen, 'commit identities missing')
    return tree, parents


def tree(raw):
    require(len(raw) <= 1024 * 1024, 'tree size bound')
    entries = {}
    order = []
    offset = 0
    while offset < len(raw):
        require(len(entries) < 20000, 'tree entry bound')
        end = raw.find(b'\0', offset)
        require(end > offset and end + 21 <= len(raw), 'truncated tree entry')
        mode, separator, name = raw[offset:end].partition(b' ')
        require(separator and mode in (b'40000', b'100644', b'100755'), 'unsupported tree mode')
        require(name not in (b'', b'.', b'..') and name.lower() != b'.git' and b'/' not in name and all(32 <= c <= 126 for c in name), 'unsafe tree name')
        require(name not in entries, 'duplicate tree entry')
        require(raw[end+1:end+21] != b'\0' * 20, 'null tree object identity')
        entries[name] = (mode.decode(), raw[end+1:end+21].hex())
        order.append(name + (b'/' if mode == b'40000' else b''))
        offset = end + 21
    require(order == sorted(order), 'noncanonical tree ordering')
    return entries


def verify(raw, *, candidate_sha, ci_source_sha, ci_workflow_sha, trigger, pins, workflow_sha256, helper_sha256):
    require(0 < len(raw) <= MAX_WITNESS and hashlib.sha256(raw).hexdigest() == pins.witness_sha256, 'witness digest or bound')
    require(ci_source_sha == ci_workflow_sha, 'inline workflow/source identity mismatch')
    try:
        value = _bounded_json(raw)
    except ValueError as exc:
        raise InvalidTransition("CI source relation: invalid bounded witness JSON") from exc
    require(type(value) is dict and set(value) == {'format', 'objects'} and value['format'] == 'aios-rea-ci-source-witness.v1', 'witness shape')
    objects = value['objects']
    require(type(objects) is dict and 1 <= len(objects) <= 16, 'object count bound')
    decoded = {}
    total = 0
    for oid, item in objects.items():
        require(type(oid) is str and re.fullmatch(r'[0-9a-f]{40}', oid) is not None, 'object identity')
        require(type(item) is dict and set(item) == {'type', 'data_base64'} and item['type'] in ('commit','tree','blob') and type(item['data_base64']) is str, 'object shape')
        try:
            data = base64.b64decode(item['data_base64'], validate=True)
        except (ValueError, binascii.Error) as exc:
            raise InvalidTransition('CI source relation: invalid object encoding') from exc
        require(base64.b64encode(data).decode() == item['data_base64'] and len(data) <= 1024 * 1024 and object_sha(item['type'], data) == oid, 'object hash or encoding mismatch')
        total += len(data)
        require(total <= MAX_WITNESS, 'decoded object byte bound')
        decoded[oid] = (item['type'], data)
    used = set()
    def get(oid, kind):
        require(oid in decoded and decoded[oid][0] == kind, 'missing or mistyped object')
        used.add(oid)
        return decoded[oid][1]
    candidate_tree, _ = commit(get(candidate_sha, 'commit'))
    source_tree, parents = commit(get(ci_source_sha, 'commit'))
    if trigger == 'pull_request':
        require(type(pins.approved_base_sha) is str and re.fullmatch(r'[0-9a-f]{40}', pins.approved_base_sha) is not None, 'approved PR base missing')
        require(parents == [pins.approved_base_sha, candidate_sha], 'ordered PR parents mismatch')
    else:
        require(trigger == 'workflow_dispatch' and pins.approved_base_sha is None and ci_source_sha == candidate_sha, 'dispatch cannot grant PR relation')
    require(source_tree == candidate_tree, 'candidate/source trees differ')
    file_pins = (workflow_sha256, helper_sha256, pins.reviewed_verifier_sha256)
    for path, digest in zip(PATHS, file_pins):
        current = source_tree
        parts = path.split('/')
        for index, name in enumerate(parts):
            entries = tree(get(current, 'tree'))
            require(name.encode() in entries, 'recipe path missing')
            mode, current = entries[name.encode()]
            if index < len(parts)-1:
                require(mode == '40000', 'recipe parent is not a tree')
            else:
                require(mode == '100644', 'recipe is not a regular reviewed blob')
                require(hashlib.sha256(get(current, 'blob')).hexdigest() == digest, 'reviewed recipe blob mismatch')
    require(used == set(decoded), 'extraneous witness objects')
    return dict(witness_sha256=pins.witness_sha256, approved_base_sha=pins.approved_base_sha,
        candidate_sha=candidate_sha, ci_source_sha=ci_source_sha, shared_tree_sha=candidate_tree,
        reviewed_workflow_sha256=workflow_sha256, reviewed_build_helper_sha256=helper_sha256,
        reviewed_verifier_sha256=pins.reviewed_verifier_sha256, object_count=len(used),
        candidate_to_ci_source_relation_verified=True, committed_recipe_bytes_match_review=True)
