"""Governed correlation uses explicit synthetic package/report bytes, no REA run."""
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path

import pytest
from sqlmodel import select
from app.models.domain import AuditLog
from app.services import organization_rea_build as build
from app.services.organization_command import InvalidTransition, AuthorityDenied, canonical_json, canonical_fingerprint
from tests.test_organization_rea_build import package_setup, inspect, board, assert_no_audit


@pytest.fixture
def correlated(package_setup, tmp_path, db_session, board):
    state = package_setup
    materials = build._materials()
    contract = build.admission.resolve_rea_provider_review(db_session, board, decision_id=state['row'].id, trust=state['trust'])[1]
    ctx = dict(candidate='a'*40, repository='bennet287/global-mobility-aios',run_id='123',run_attempt='1',runner='ubuntu-24.04')
    source = dict(commit=build.REA_SOURCE_COMMIT,tree=materials['source_tree'],materials_sha256=build.REA_SOURCE_MATERIALS_SHA256,
                  dependency_lock_sha256=materials['dependency_lock_sha256'],reviewed_recipe_sha256=materials['recipe_sha256'],tracked_files=materials['file_count'],tracked_bytes=materials['total_bytes'])
    recipe = dict(helper_sha256='b'*64,workflow_sha256='c'*64,command='node node_modules/typescript/bin/tsc -p tsconfig.build.json',lifecycle_scripts=False,fresh_npm_cache=True)
    tools = dict(versions=dict(node='v24.18.0',npm='11.16.0',typescript='5.9.3'),input_sha256={k:'d'*64 for k in ('node','npm_cli','npm_package','typescript_package','typescript_entry','typescript_tsc','typescript_compiler')})
    dist = [dict(path=v['path'][5:],size=v['size'],sha256=v['sha256']) for v in state['manifest'] if v['path'].startswith('dist/')]
    repeat = dict(format='aios-rea-build-repeatability.v1',context=ctx,source=source,recipe=recipe,toolchain=tools,files=dist,
                  received_manifest_sha256={'a':'e'*64,'b':'f'*64},repeatability_observed=True,source_compiler_recipe_context_observed=True,
                  publisher_provenance_verified=False,runtime_dependency_closure_verified=False,installed_runtime_bytes_verified=False,isolation_verified=False,provider_ready=False,live_transport_owned=False,execution_authorized=False)
    report = dict(format='aios-rea-package-correlation.v1',repeatability=repeat,package=dict(archive_sha256=state['request'].scope.build_sha256,archive_bytes=state['request'].scope.build_bytes,files=state['manifest']),diagnostic_only=True)
    root = tmp_path/'report';root.mkdir()
    path = root/'correlation.json';path.write_bytes(canonical_json(report).encode());path.chmod(0o444);root.chmod(0o555)
    trust = build.ReaCompilationTrust(root,'correlation.json',hashlib.sha256(path.read_bytes()).hexdigest(),ctx['candidate'],ctx['repository'],ctx['run_id'],ctx['run_attempt'],recipe['workflow_sha256'],recipe['helper_sha256'],str(state['row'].id),canonical_fingerprint(contract))
    state.update(compilation_trust=trust,report=report,report_path=path)
    cleanup_fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        yield state
    finally:
        # Only the retained fixture directory; never follow a replaced path.
        os.fchmod(cleanup_fd,0o755)
        os.close(cleanup_fd)


def rewrite(state, report=None, raw=None):
    path=state['report_path'];path.chmod(0o644)
    path.write_bytes(raw if raw is not None else canonical_json(report or state['report']).encode());path.chmod(0o444)
    state['compilation_trust']=replace(state['compilation_trust'],report_sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def correlated_inspect(session, board, state):
    return inspect(session,board,state,compilation_trust=state['compilation_trust'])


def test_complete_correlation_narrow_evidence(db_session,board,correlated):
    result=correlated_inspect(db_session,board,correlated)
    assert result['compiled_package_dist_matches'] is True
    assert 'authenticated_ci_execution_provenance_unproven' in result['blockers']
    assert 'actual_source_build_reproducibility_unproven' not in result['blockers']
    for key in ('source_to_build_verified','publisher_verified','runtime_closure_verified','provider_ready','execution_authorized','live_transport_owned','isolation_verified'):
        assert result[key] is False
    evidence=build.artifact._json(db_session.exec(select(AuditLog).where(AuditLog.action==build.ACTION)).one().after_state_json)
    summary=evidence['compilation_correlation']
    assert summary['compiled_dist_files']==4 and summary['owning_github_execution_authenticated'] is False
    assert summary['accepted_ci_bytes_assumed'] is True
    assert 'files' not in summary and 'repeatability' not in summary
    assert str(correlated['report_path']) not in canonical_json(evidence)
    assert len(canonical_json(evidence).encode())<build.artifact.MAX_AUDIT_BYTES


def test_default_inspector_shape_unchanged(db_session,board,package_setup):
    result=inspect(db_session,board,package_setup)
    assert 'compiled_package_dist_matches' not in result
    assert 'actual_source_build_reproducibility_unproven' in result['blockers']


@pytest.mark.parametrize('mutation', [
    lambda r:r.update(format='other'), lambda r:r.update(extra=True),lambda r:r.update(diagnostic_only=1),
    lambda r:r['repeatability'].update(extra=True),lambda r:r['repeatability']['context'].update(candidate='0'*40),
    lambda r:r['repeatability']['context'].update(repository='other/repo'),lambda r:r['repeatability']['context'].update(run_id='999'),
    lambda r:r['repeatability']['context'].update(run_attempt='2'),lambda r:r['repeatability']['source'].update(commit='0'*40),
    lambda r:r['repeatability']['source'].update(tree='0'*40),lambda r:r['repeatability']['source'].update(tracked_files=True),
    lambda r:r['repeatability']['source'].update(dependency_lock_sha256='0'*64),
    lambda r:r['repeatability']['recipe'].update(helper_sha256='0'*64),lambda r:r['repeatability']['recipe'].update(lifecycle_scripts=True),
    lambda r:r['repeatability']['recipe'].update(fresh_npm_cache=1),lambda r:r['repeatability']['toolchain']['versions'].update(node='v22.0.0'),
    lambda r:r['repeatability']['toolchain']['input_sha256'].update(node=True),lambda r:r['repeatability']['received_manifest_sha256'].update(a='wrong'),
    lambda r:r['repeatability'].update(provider_ready=True),lambda r:r['repeatability'].update(execution_authorized=True),
    lambda r:r['repeatability'].update(isolation_verified=True),lambda r:r['repeatability'].update(repeatability_observed=1),
    lambda r:r['repeatability']['files'].pop(),lambda r:r['repeatability']['files'].append(dict(path='extra.js',size=0,sha256='0'*64)),
    lambda r:r['repeatability']['files'][0].update(sha256='0'*64),lambda r:r['repeatability']['files'][0].update(size=True),
    lambda r:r['package'].update(archive_sha256='0'*64),lambda r:r['package'].update(archive_bytes=True),
    lambda r:r['package']['files'].pop(),lambda r:r['package']['files'][0].update(sha256='0'*64),
])
def test_strict_report_drift_denied(db_session,board,correlated,mutation):
    report=json.loads(canonical_json(correlated['report']));mutation(report);rewrite(correlated,report)
    with pytest.raises((InvalidTransition,AuthorityDenied)):
        correlated_inspect(db_session,board,correlated)
    assert_no_audit(db_session)


@pytest.mark.parametrize('field,value',[('candidate_sha','0'*40),('repository','other/repo'),('run_id','456'),('run_attempt','2'),('helper_sha256','0'*64),('workflow_sha256','0'*64),('report_sha256','0'*64),('provider_decision_id','00000000-0000-0000-0000-000000000000'),('provider_contract_sha256','0'*64)])
def test_independent_pins_and_review_binding(db_session,board,correlated,field,value):
    correlated['compilation_trust']=replace(correlated['compilation_trust'],**{field:value})
    with pytest.raises((InvalidTransition,AuthorityDenied)):
        correlated_inspect(db_session,board,correlated)
    assert_no_audit(db_session)


@pytest.mark.parametrize('mutation',['writable','writable-root','symlink','hardlink','fifo','traversal','root-symlink','oversize'])
def test_report_physical_boundary(db_session,board,correlated,mutation,tmp_path):
    path=correlated['report_path'];root=path.parent
    if mutation=='writable':path.chmod(0o644)
    elif mutation=='writable-root':root.chmod(0o755)
    elif mutation=='traversal':correlated['compilation_trust']=replace(correlated['compilation_trust'],report_relative='../report/correlation.json')
    elif mutation=='root-symlink':
        link=tmp_path/'link';link.symlink_to(root,target_is_directory=True)
        correlated['compilation_trust']=replace(correlated['compilation_trust'],report_root=link)
    else:
        root.chmod(0o755)
        if mutation=='symlink':
            other=tmp_path/'other';other.write_bytes(path.read_bytes());path.unlink();path.symlink_to(other)
        elif mutation=='hardlink':os.link(path,tmp_path/'other')
        elif mutation=='fifo':path.unlink();os.mkfifo(path)
        else:path.chmod(0o644);path.write_bytes(b'x'*(4*1024*1024+1));path.chmod(0o444)
        root.chmod(0o555)
    with pytest.raises((InvalidTransition,AuthorityDenied)):
        correlated_inspect(db_session,board,correlated)
    assert_no_audit(db_session)


def test_report_rechecked_before_audit_and_commit(db_session,board,correlated,monkeypatch):
    original=build._compilation_report;calls=0
    def mutate(*args,**kwargs):
        nonlocal calls
        calls+=1
        if calls==2:
            correlated['report_path'].chmod(0o644)
        return original(*args,**kwargs)
    monkeypatch.setattr(build,'_compilation_report',mutate)
    with pytest.raises(InvalidTransition):correlated_inspect(db_session,board,correlated)
    assert calls==2
    assert_no_audit(db_session)


@pytest.mark.parametrize('raw',[b'{"format":"one","format":"two"}',b'{"a":NaN}',b'{"a":Infinity}',b'{"a":1e400}',b'"\\ud800"'])
def test_raw_report_strict_even_with_independent_digest(db_session,board,correlated,raw):
    rewrite(correlated,raw=raw)
    with pytest.raises(InvalidTransition):correlated_inspect(db_session,board,correlated)
    assert_no_audit(db_session)


@pytest.mark.parametrize('mutation',['delete','replace','authority'])
def test_report_changes_during_audit_rollback(db_session,board,correlated,monkeypatch,mutation):
    original=build.record_audit
    def changed(*args,**kwargs):
        result=original(*args,**kwargs)
        root=correlated['report_path'].parent;root.chmod(0o755)
        if mutation=='delete':correlated['report_path'].unlink()
        elif mutation=='replace':
            correlated['report_path'].unlink();correlated['report_path'].write_bytes(b'{}');correlated['report_path'].chmod(0o444)
        else:
            correlated['report']['repeatability']['execution_authorized']=True
            rewrite(correlated)
        root.chmod(0o555)
        return result
    monkeypatch.setattr(build,'record_audit',changed)
    with pytest.raises(InvalidTransition):correlated_inspect(db_session,board,correlated)
    assert_no_audit(db_session)


def test_complete_report_cannot_omit_additional_approved_dist(correlated,db_session,board):
    state=correlated
    contract=build.admission.resolve_rea_provider_review(db_session,board,decision_id=state['row'].id,trust=state['trust'])[1]
    manifest=sorted(state['manifest']+[dict(path='dist/extra.js',size=1,sha256='a'*64)],key=lambda v:v['path'])
    state['report']['package']['files']=manifest;rewrite(state)
    with pytest.raises(InvalidTransition,match='complete dist'):
        build._compilation_report(state['compilation_trust'],decision_id=state['row'].id,contract=contract,manifest=manifest,scope=state['request'].scope)


def test_signed_statement_freshness_still_required(db_session,board,correlated):
    from datetime import timedelta
    from app.models.domain import now_utc
    from tests.test_organization_rea_build import envelope
    with pytest.raises(InvalidTransition):
        inspect(db_session,board,correlated,envelope(correlated,finished_at=(now_utc()-timedelta(days=2)).isoformat()),compilation_trust=correlated['compilation_trust'])
    assert_no_audit(db_session)


@pytest.mark.parametrize('section', ['dist','package'])
@pytest.mark.parametrize('mutation',['duplicate','casefold','unsorted','float-size','extra-field'])
def test_complete_manifest_schema_both_sections(db_session,board,correlated,section,mutation):
    files=correlated['report']['repeatability']['files'] if section=='dist' else correlated['report']['package']['files']
    if mutation=='duplicate':files.append(dict(files[0]))
    elif mutation=='casefold':files.append({**files[0],'path':files[0]['path'].upper()});files.sort(key=lambda v:v['path'])
    elif mutation=='unsorted':files.reverse()
    elif mutation=='float-size':files[0]['size']=float(files[0]['size'])
    else:files[0]['extra']=True
    rewrite(correlated)
    with pytest.raises(InvalidTransition):correlated_inspect(db_session,board,correlated)
    assert_no_audit(db_session)


@pytest.mark.parametrize('flag',['publisher_provenance_verified','runtime_dependency_closure_verified','installed_runtime_bytes_verified','live_transport_owned'])
def test_no_report_self_authority(db_session,board,correlated,flag):
    correlated['report']['repeatability'][flag]=True;rewrite(correlated)
    with pytest.raises(InvalidTransition):correlated_inspect(db_session,board,correlated)
    assert_no_audit(db_session)


def test_current_work_cancel_during_correlation_audit_denied(db_session,board,correlated,monkeypatch):
    from app.models.domain import now_utc
    original=build.record_audit
    def cancelled(*args,**kwargs):
        result=original(*args,**kwargs)
        work=correlated['work'];work.cancel_requested_at=now_utc();db_session.add(work);db_session.flush()
        return result
    monkeypatch.setattr(build,'record_audit',cancelled)
    with pytest.raises(InvalidTransition):correlated_inspect(db_session,board,correlated)
    assert_no_audit(db_session)


def test_current_review_rejection_during_correlation_denied(db_session,board,correlated,monkeypatch):
    original=build.record_audit
    def rejected(*args,**kwargs):
        result=original(*args,**kwargs)
        row=correlated['row'];row.status='rejected';db_session.add(row);db_session.flush()
        return result
    monkeypatch.setattr(build,'record_audit',rejected)
    with pytest.raises(InvalidTransition):correlated_inspect(db_session,board,correlated)
    assert_no_audit(db_session)
