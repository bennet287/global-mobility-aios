"""Inert USTAR test package includes pinned MIT source assets and synthetic dist."""
from dataclasses import replace
from datetime import timedelta
import gzip
import hashlib
import io
import json
import os
import shutil
from pathlib import Path
import tarfile

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from sqlmodel import select
from app.models.domain import AuditLog, now_utc
from app.services.organization_command import InvalidTransition, AuthorityDenied, canonical_json
from app.services import organization_rea_admission as admission, organization_rea_build as build
from app.services.organization_rea_catalog import REA_SOURCE_COMMIT, REA_LOCAL_CATALOG_SHA256
from tests.test_organization_rea_admission import board, build_setup, approve

FIXTURE = Path(__file__).parent/'fixtures'/'rea_build'/'synthetic_package.tar.gz'


def repack(members):
    buf=io.BytesIO()
    with tarfile.open(fileobj=buf,mode='w',format=tarfile.USTAR_FORMAT) as tar:
        for item,body in members:
            tar.addfile(item,io.BytesIO(body) if body is not None else None)
    return gzip.compress(buf.getvalue(),mtime=0)


def members(raw):
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as tar:
        return [(v,tar.extractfile(v).read() if v.isfile() else None) for v in tar]


@pytest.fixture
def package_setup(db_session,board,tmp_path):
    state=build_setup(db_session,board,tmp_path)
    archive=FIXTURE.read_bytes()
    bundle=state['trust'].build_root/'bundle';bundle.chmod(0o600);bundle.write_bytes(archive);bundle.chmod(0o400)
    request=state['request'].model_copy(deep=True)
    request.decision_key='package-provider';request.supersedes_decision_id=state['row'].id
    request.scope.build_sha256=hashlib.sha256(archive).hexdigest();request.scope.build_bytes=len(archive)
    state['row']=approve(db_session,board,admission.propose_rea_provider_review(db_session,board,request));state['request']=request
    manifest,_=build._archive_manifest(archive)
    installed=tmp_path/'installed';installed.mkdir(mode=0o755)
    for item,body in members(archive):
        target=installed/item.name.removeprefix('package/')
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(body);target.chmod(0o444)
    private=Ed25519PrivateKey.generate();public=private.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)
    trust=build.ReaBuildTrust('trusted-builder',public,'2'*64,installed)
    materials=build._materials();now=now_utc()
    statement=dict(kind='rea_builder_statement_v1',source_commit=REA_SOURCE_COMMIT,source_materials_sha256=build.REA_SOURCE_MATERIALS_SHA256,catalog_sha256=REA_LOCAL_CATALOG_SHA256,
        recipe_sha256=materials['recipe_sha256'],dependency_lock_sha256=materials['dependency_lock_sha256'],package_name='rea-agents',package_version='3.2.1',builder_id=trust.builder_id,build_policy_sha256=trust.build_policy_sha256,
        archive_sha256=request.scope.build_sha256,archive_bytes=len(archive),files=manifest,started_at=(now-timedelta(minutes=2)).isoformat(),finished_at=(now-timedelta(minutes=1)).isoformat())
    state.update(archive=archive,manifest=manifest,installed=installed,build_trust=trust,builder_private=private,statement=statement)
    return state


def envelope(state, **changes):
    statement={**state['statement'],**changes}
    return canonical_json(dict(statement=statement,signature_hex=state['builder_private'].sign(canonical_json(statement).encode()).hex())).encode()


def inspect(session,board,state,raw=None,**kwargs):
    return build.inspect_rea_package(session,board,decision_id=state['row'].id,attempt_id=state['attempt'].id,receipt_id=state['receipt'],deployment_trust=state['trust'],build_trust=state['build_trust'],signed_statement=raw or envelope(state),**kwargs)


def assert_no_audit(session):
    assert not session.exec(select(AuditLog).where(AuditLog.action==build.ACTION)).all()


def test_signed_package_and_installed_snapshot(db_session,board,package_setup):
    result=inspect(db_session,board,package_setup)
    assert all(result[k] for k in ['signed_builder_statement_verified','package_archive_manifest_verified','installed_package_snapshot_matches'])
    assert not any(result[k] for k in ['source_to_build_verified','publisher_verified','runtime_closure_verified','provider_ready','execution_authorized','live_transport_owned','isolation_verified'])
    assert 'dependency_and_node_runtime_closure_unproven' in result['blockers']
    encoded=canonical_json(result)
    assert str(package_setup['installed']) not in encoded and package_setup['attempt'].execution_token not in encoded
    logs=db_session.exec(select(AuditLog).where(AuditLog.action==build.ACTION)).all()
    assert len(logs)==1
    evidence=build.artifact._json(logs[0].after_state_json)
    assert evidence['result']==result
    signed=evidence['signed_envelope']
    package_setup['builder_private'].public_key().verify(bytes.fromhex(signed['signature_hex']),canonical_json(signed['statement']).encode())
    assert result['statement_sha256']==build.canonical_fingerprint(signed['statement'])


@pytest.mark.parametrize('field,value',[('builder_id','other'),('build_policy_sha256','0'*64),('source_commit','0'*40),('source_materials_sha256','0'*64),('catalog_sha256','0'*64),('recipe_sha256','0'*64),('dependency_lock_sha256','0'*64),('archive_sha256','0'*64),('archive_bytes',1),('package_version','9.9.9'),('finished_at',(now_utc()-timedelta(days=2)).isoformat()),('started_at',(now_utc()+timedelta(hours=1)).isoformat())])
def test_statement_drift_denied(db_session,board,package_setup,field,value):
    with pytest.raises((InvalidTransition,AuthorityDenied)):
        inspect(db_session,board,package_setup,envelope(package_setup,**{field:value}))
    assert_no_audit(db_session)


def test_wrong_builder_key(db_session,board,package_setup):
    package_setup['build_trust']=replace(package_setup['build_trust'],builder_public_key=b'0'*32)
    with pytest.raises(AuthorityDenied):inspect(db_session,board,package_setup)
    assert_no_audit(db_session)


@pytest.mark.parametrize('mode',['extra','empty-directory','tamper','writable','symlink','hardlink','unsafe-directory','fifo'])
def test_installed_mutations_denied(db_session,board,package_setup,mode):
    root=package_setup['installed'];target=root/'dist'/'main.js'
    if mode=='extra':(root/'.hidden').write_bytes(b'extra')
    elif mode=='empty-directory':(root/'empty').mkdir()
    elif mode=='tamper':target.chmod(0o600);target.write_bytes(b'tampered');target.chmod(0o444)
    elif mode=='writable':target.chmod(0o644)
    elif mode=='symlink':target.unlink();target.symlink_to('/etc/passwd')
    elif mode=='hardlink':os.link(target,root/'alias')
    elif mode=='unsafe-directory':(root/'dist').chmod(0o777)
    else:os.mkfifo(root/'pipe')
    with pytest.raises(InvalidTransition):inspect(db_session,board,package_setup)
    assert_no_audit(db_session)


@pytest.mark.parametrize('raw',[b'{"statement":{},"statement":{}}',b'{"statement":NaN}',b'{"statement":"\\ud800"}',b'[]',b'x'*(4*1024*1024+1)])
def test_bounded_json_denied(db_session,board,package_setup,raw):
    with pytest.raises(InvalidTransition):inspect(db_session,board,package_setup,raw)
    assert_no_audit(db_session)


@pytest.mark.parametrize('mode',['traversal','duplicate','symlink','hardlink','fifo','pax','oversize','gzip-extra','tar-extra','truncated','source-tamper','source-missing'])
def test_archive_profile_denied(mode):
    raw=FIXTURE.read_bytes();items=members(raw)
    if mode=='gzip-extra':raw+=gzip.compress(b'other')
    elif mode=='tar-extra':raw=gzip.compress(gzip.decompress(raw)+b'x'*512)
    elif mode=='truncated':raw=raw[:-1]
    elif mode=='source-tamper':items[0]=(items[0][0],b'tamper');items[0][0].size=6;raw=repack(items)
    elif mode=='source-missing':items=[(i,b) for i,b in items if i.name!='package/LICENSE'];raw=repack(items)
    else:
        info=tarfile.TarInfo('package/extra');body=b''
        if mode=='traversal':info.name='package/../escape'
        elif mode=='duplicate':info.name=items[0][0].name
        elif mode=='symlink':info.type=tarfile.SYMTYPE;info.linkname='target';body=None
        elif mode=='hardlink':info.type=tarfile.LNKTYPE;info.linkname=items[0][0].name;body=None
        elif mode=='fifo':info.type=tarfile.FIFOTYPE;body=None
        elif mode=='pax':info.type=tarfile.XHDTYPE
        elif mode=='oversize':info.size=build.MAX_FILE+1;body=b'0'*info.size
        items.append((info,body));raw=repack(items)
    with pytest.raises((InvalidTransition,ValueError)):
        manifest,contents=build._archive_manifest(raw)
        materials=build._materials()
        build._verify_source_assets(manifest,contents,{v['path']:v for v in materials['files']})


def test_archive_bomb_bounded(monkeypatch):
    monkeypatch.setattr(build,'MAX_EXPANDED',2048)
    with pytest.raises(InvalidTransition):build._archive_manifest(gzip.compress(b'0'*1000000))


@pytest.mark.parametrize('field,value',[('status','completed'),('execution_token','stale'),('execution_attempts',3),('cancel_requested_at',now_utc()),('objective','changed')])
def test_current_canonical_work_required(db_session,board,package_setup,field,value):
    work=package_setup['work'];setattr(work,field,value);db_session.add(work);db_session.commit()
    with pytest.raises(InvalidTransition):inspect(db_session,board,package_setup)
    assert_no_audit(db_session)


def test_commit_failure_rolls_back_witness(db_session,board,package_setup,monkeypatch):
    monkeypatch.setattr(db_session,'commit',lambda: (_ for _ in ()).throw(RuntimeError('failure')))
    with pytest.raises(RuntimeError):inspect(db_session,board,package_setup)
    assert_no_audit(db_session)


def test_expiry_during_audit_rolls_back(db_session,board,package_setup,monkeypatch):
    original=build.record_audit
    def expire(*args,**kwargs):
        original(*args,**kwargs)
        monkeypatch.setattr(build,'now_utc',lambda:package_setup['request'].scope.expires_at+timedelta(seconds=1))
    monkeypatch.setattr(build,'record_audit',expire)
    with pytest.raises(InvalidTransition):inspect(db_session,board,package_setup)
    assert_no_audit(db_session)


@pytest.mark.parametrize('barrier', ['before-audit', 'after-audit'])
@pytest.mark.parametrize('mutation', ['replace-file', 'rewrite-file', 'restore-file', 'add-file', 'remove-file',
    'replace-directory', 'replace-root', 'replace-ancestor', 'symlink-root', 'symlink-ancestor'])
def test_installed_custody_mutation_rolls_back(db_session,board,package_setup,monkeypatch,barrier,mutation):
    state=package_setup
    # Put the installed root under a dedicated ancestor so other custody inputs
    # remain valid when the installed ancestor is replaced.
    ancestor=state['installed'].parent/'package-parent';ancestor.mkdir()
    root=ancestor/'installed';state['installed'].rename(root)
    state['installed']=root;state['build_trust']=replace(state['build_trust'],installed_root=root)
    target=root/'dist'/'main.js'
    changed=False
    def mutate():
        nonlocal changed
        changed=True
        if mutation=='replace-file':
            raw=target.read_bytes();target.unlink();target.write_bytes(raw);target.chmod(0o444)
        elif mutation in {'rewrite-file', 'restore-file'}:
            raw=target.read_bytes();target.chmod(0o600)
            target.write_bytes(b'x'*len(raw))
            if mutation=='restore-file':target.write_bytes(raw)
            target.chmod(0o444)
        elif mutation=='add-file':(root/'dist'/'extra').write_bytes(b'extra')
        elif mutation=='remove-file':target.unlink()
        else:
            selected=root/'dist' if mutation=='replace-directory' else ancestor if 'ancestor' in mutation else root
            held=selected.with_name(selected.name+'-old');selected.rename(held)
            if mutation.startswith('symlink-'):selected.symlink_to(held,target_is_directory=True)
            else:shutil.copytree(held,selected)
    if barrier=='before-audit':
        original=build.artifact.revalidate_rea_artifact_custody;calls=0
        def custody(*args,**kwargs):
            nonlocal calls
            result=original(*args,**kwargs);calls+=1
            if calls==2:mutate()
            return result
        monkeypatch.setattr(build.artifact,'revalidate_rea_artifact_custody',custody)
    else:
        original=build.record_audit
        def audit(*args,**kwargs):
            original(*args,**kwargs);mutate()
        monkeypatch.setattr(build,'record_audit',audit)
    with pytest.raises(InvalidTransition):inspect(db_session,board,state)
    assert changed
    assert_no_audit(db_session)


def test_unrelated_ancestor_sibling_activity_allowed(db_session,board,package_setup,monkeypatch):
    original=build.record_audit
    def audit(*args,**kwargs):
        original(*args,**kwargs)
        (package_setup['installed'].parent/'unrelated').write_bytes(b'not package content')
    monkeypatch.setattr(build,'record_audit',audit)
    result=inspect(db_session,board,package_setup)
    assert result['installed_package_snapshot_matches'] is True
    assert result['execution_authorized'] is False
    assert 'immutable_installed_bytes_at_use_unproven' in result['blockers']


@pytest.mark.parametrize('failure', ['none', 'scan', 'revalidate', 'open'])
def test_installed_snapshot_descriptor_cleanup(package_setup,monkeypatch,failure):
    before=set(os.listdir('/proc/self/fd'))
    root=package_setup['installed']
    if failure=='scan':os.mkfifo(root/'bad-pipe')
    elif failure=='open':
        original=build.os.open;calls=0
        def fail_open(*args,**kwargs):
            nonlocal calls
            calls+=1
            if calls==3:raise OSError('injected descriptor acquisition failure')
            return original(*args,**kwargs)
        monkeypatch.setattr(build.os,'open',fail_open)
    def observe():
        with build._installed_snapshot(root) as (manifest,revalidate):
            assert manifest==package_setup['manifest']
            assert len(os.listdir('/proc/self/fd'))>len(before)
            if failure=='revalidate':(root/'dist'/'main.js').chmod(0o644)
            revalidate()
    if failure=='none':observe()
    else:
        with pytest.raises((InvalidTransition,OSError)):observe()
    assert set(os.listdir('/proc/self/fd'))==before


@pytest.mark.parametrize('failure', ['none', 'audit', 'commit'])
def test_installed_descriptors_retained_until_commit(db_session,board,package_setup,monkeypatch,failure):
    closed=False
    original=build._installed_snapshot
    from contextlib import contextmanager
    @contextmanager
    def snapshot(root):
        nonlocal closed
        try:
            with original(root) as value:yield value
        finally:closed=True
    monkeypatch.setattr(build,'_installed_snapshot',snapshot)
    original_audit=build.record_audit
    def audit(*args,**kwargs):
        assert not closed
        original_audit(*args,**kwargs)
        if failure=='audit':raise RuntimeError('injected audit failure')
    monkeypatch.setattr(build,'record_audit',audit)
    original_commit=db_session.commit
    def commit():
        assert not closed
        if failure=='commit':raise RuntimeError('injected commit failure')
        original_commit()
    monkeypatch.setattr(db_session,'commit',commit)
    if failure=='none':inspect(db_session,board,package_setup)
    else:
        with pytest.raises(RuntimeError):inspect(db_session,board,package_setup)
        assert_no_audit(db_session)
    assert closed


@pytest.mark.parametrize('path',['/absolute','../escape','a/./b','a//b','a\\b','a\x00b','a\nb'])
def test_manifest_unsafe_paths_denied(db_session,board,package_setup,path):
    files=[dict(v) for v in package_setup['manifest']];files[0]['path']=path
    with pytest.raises(InvalidTransition):inspect(db_session,board,package_setup,envelope(package_setup,files=files))
    assert_no_audit(db_session)


@pytest.mark.parametrize('mode',['duplicate','unsorted','casefold','float-size','bool-size','extra-field'])
def test_manifest_strict_complete_schema(db_session,board,package_setup,mode):
    files=[dict(v) for v in package_setup['manifest']]
    if mode=='duplicate':files.append(files[0])
    elif mode=='unsorted':files.reverse()
    elif mode=='casefold':files.append({**files[0],'path':files[0]['path'].lower()});files.sort(key=lambda v:v['path'])
    elif mode=='float-size':files[0]['size']=float(files[0]['size'])
    elif mode=='bool-size':files[0]['size']=True
    else:files[0]['unexpected']=True
    with pytest.raises(InvalidTransition):inspect(db_session,board,package_setup,envelope(package_setup,files=files))
    assert_no_audit(db_session)


def test_archive_casefold_and_generated_minimum():
    items=members(FIXTURE.read_bytes())
    item=tarfile.TarInfo('package/license');item.size=0
    with pytest.raises(InvalidTransition):build._archive_manifest(repack(items+[(item,b'')]))
    items=[(i,b) for i,b in items if i.name!='package/dist/main.js']
    manifest,contents=build._archive_manifest(repack(items))
    materials=build._materials()
    with pytest.raises(InvalidTransition):build._verify_source_assets(manifest,contents,{v['path']:v for v in materials['files']})


def test_retained_descriptor_detects_earlier_file_change(package_setup,monkeypatch):
    root=package_setup['installed'];target=root/'LICENSE';second=(root/'README.md').stat().st_ino
    original=build.artifact._bytes
    def change(fd,size,*args):
        digest=original(fd,size,*args)
        if os.fstat(fd).st_ino==second:
            target.chmod(0o600);target.write_bytes(b'changed while later file scanned');target.chmod(0o444)
        return digest
    monkeypatch.setattr(build.artifact,'_bytes',change)
    with pytest.raises(InvalidTransition):build._installed_manifest(root)


def test_expiry_after_final_custody_check(db_session,board,package_setup,monkeypatch):
    original=build.artifact.revalidate_rea_artifact_custody;calls=0
    def expire(*args,**kwargs):
        nonlocal calls
        result=original(*args,**kwargs);calls+=1
        if calls==3:
            monkeypatch.setattr(build,'now_utc',lambda:package_setup['request'].scope.expires_at+timedelta(seconds=1))
        return result
    monkeypatch.setattr(build.artifact,'revalidate_rea_artifact_custody',expire)
    with pytest.raises(InvalidTransition):inspect(db_session,board,package_setup)
    assert calls==3
    assert_no_audit(db_session)


@pytest.mark.parametrize('action',[admission.PROPOSE,'organization.decision.approved','organization_work_execution_started','organization.rea.artifact.custody'])
def test_canonical_review_attempt_custody_witnesses_required(db_session,board,package_setup,action):
    logs=db_session.exec(select(AuditLog).where(AuditLog.action==action)).all()
    for row in logs:db_session.delete(row)
    db_session.commit()
    with pytest.raises(InvalidTransition):inspect(db_session,board,package_setup)
    assert_no_audit(db_session)


def test_equivalent_time_spelling_requires_new_signature(db_session,board,package_setup):
    raw=json.loads(envelope(package_setup))
    raw['statement']['finished_at']=raw['statement']['finished_at'].replace('+00:00','Z')
    with pytest.raises(AuthorityDenied):inspect(db_session,board,package_setup,canonical_json(raw).encode())
    assert_no_audit(db_session)
    result=inspect(db_session,board,package_setup,envelope(package_setup,finished_at=raw['statement']['finished_at']))
    assert result['signed_builder_statement_verified']


def test_evidence_aggregate_bound_rejects_before_witness(db_session,board,package_setup,monkeypatch):
    monkeypatch.setattr(build.artifact,'MAX_AUDIT_BYTES',1000)
    with pytest.raises(InvalidTransition):inspect(db_session,board,package_setup)
    assert_no_audit(db_session)


@pytest.mark.parametrize('value',['1791190000',1791190000,True,'2026-10-05T12:00:00'])
def test_builder_timestamp_requires_explicit_aware_iso(db_session,board,package_setup,value):
    with pytest.raises(InvalidTransition):inspect(db_session,board,package_setup,envelope(package_setup,finished_at=value))
    assert_no_audit(db_session)


def rewrite_first_header(start, end, replacement):
    raw=bytearray(gzip.decompress(FIXTURE.read_bytes()))
    raw[start:end]=replacement
    if start!=148:
        raw[148:156]=b' '*8
        checksum=sum(raw[:512])
        raw[148:156]=f'{checksum:06o}\0 '.encode('ascii')
    return gzip.compress(bytes(raw),mtime=0)


@pytest.mark.parametrize('start,end',[(100,108),(108,116),(116,124),(124,136),(136,148),(148,156),(329,337),(337,345)])
def test_archive_base256_numeric_extension_denied(start,end):
    original=gzip.decompress(FIXTURE.read_bytes())[start:end]
    value=int(original.strip(b'\x00 '),8) if original.strip(b'\x00 ') else 0
    raw=rewrite_first_header(start,end,b'\x80'+value.to_bytes(end-start-1,'big'))
    with pytest.raises(InvalidTransition):build._archive_manifest(raw)


@pytest.mark.parametrize('version',[b'99',b'\x00\x00'])
def test_archive_non_ustar_version_denied(version):
    with pytest.raises(InvalidTransition):build._archive_manifest(rewrite_first_header(263,265,version))


@pytest.mark.parametrize('field',[b'00000000009\0',b'-0000000001\0',b'0001\x00000000\0'])
def test_archive_noncanonical_octal_numeric_denied(field):
    with pytest.raises(InvalidTransition):build._archive_manifest(rewrite_first_header(124,136,field))
