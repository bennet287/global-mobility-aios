"""Synthetic CLI policy tests; cryptographic proof comes from actual CI bundles."""
from dataclasses import replace
import hashlib
import io
import json
import os
from pathlib import Path
import shlex
import tarfile
from uuid import uuid4

import pytest
from sqlmodel import select
from app.models.domain import AuditLog
from app.schemas_organization_rea_admission import ReaCompilationEvidence, ReaCiAttestationEvidence
from app.services import organization_rea_ci_attestation as ci
from app.services import organization_rea_build as build
from app.services.organization_command import InvalidTransition, canonical_json, canonical_fingerprint
from tests.test_organization_rea_compilation import correlated, correlated_inspect
from tests.test_organization_rea_build import package_setup, board, approve, assert_no_audit


def raw_result(subject, expected):
    return [{'verificationResult': {'signature': {'certificate': {k:v for k,v in expected.items() if k!='context'}},
        'verifiedTimestamps': [{'type':'Tlog','timestamp':'2026-01-01T00:00:00Z','uri':'unrecorded'}],
        'statement': {'_type':'https://in-toto.io/Statement/v1','predicateType':'https://slsa.dev/provenance/v1',
          'subject':[{'name':'correlation.json','digest':{'sha256':ci.sha(subject)}}], 'predicate': {'identity':'not authority'}}}}]


@pytest.fixture
def attested(correlated, db_session, board, tmp_path, monkeypatch):
    state=correlated
    root=tmp_path/'attestation';root.mkdir()
    bundle=root/'bundle.json';bundle.write_bytes(b'{"synthetic":"not a signature"}');bundle.chmod(0o444)
    pins=dict(bundle_sha256=ci.sha(bundle.read_bytes()),ci_source_sha='1'*40,ci_workflow_sha='2'*40,
              source_ref='refs/pull/318/merge',trigger='pull_request')
    request=state['request'].model_copy(deep=True)
    request.decision_key='attested-'+uuid4().hex;request.supersedes_decision_id=state['row'].id
    evidence=request.scope.compilation_evidence.model_dump(mode='json');evidence['ci_attestation']=pins
    request.scope.compilation_evidence=ReaCompilationEvidence.model_validate(evidence)
    row=approve(db_session,board,build.admission.propose_rea_provider_review(db_session,board,request))
    contract=build.admission.resolve_rea_provider_review(db_session,board,decision_id=row.id,trust=state['trust'])[1]
    trust=ci.ReaCiAttestationTrust(root,'bundle.json',root,'cli.tar.gz',**pins)
    state.update(row=row,request=request,compilation_trust=replace(state['compilation_trust'],
        provider_decision_id=str(row.id),provider_contract_sha256=canonical_fingerprint(contract),ci_attestation=trust),bundle_path=bundle,attestation_root=root)
    expected=ci.expected_identity(candidate='a'*40,run_id='123',run_attempt='1',source_sha='1'*40,
        workflow_sha='2'*40,source_ref=pins['source_ref'],trigger=pins['trigger'])
    state['verified_result']=raw_result(state['report_path'].read_bytes(),expected)
    def install(value=None, body=None):
        root.chmod(0o755)
        raw=canonical_json(value if value is not None else state['verified_result'])
        script=("#!/bin/sh\nif [ \"$1\" = \"--version\" ]; then printf 'gh version 2.102.0 synthetic\\n'; else printf '%s' "+shlex.quote(raw)+"; fi\n") if body is None else body
        output=io.BytesIO()
        with tarfile.open(fileobj=output,mode='w:gz') as archive:
            item=tarfile.TarInfo(ci.CLI_MEMBER);item.size=len(script.encode());archive.addfile(item,io.BytesIO(script.encode()))
        path=root/'cli.tar.gz'
        if path.exists():path.chmod(0o644)
        path.write_bytes(output.getvalue());path.chmod(0o444)
        monkeypatch.setattr(ci,'CLI_ARCHIVE_SHA256',ci.sha(output.getvalue()))
        root.chmod(0o555)
    state['install_cli']=install;install()
    try:
        yield state
    finally:
        root.chmod(0o755)


def test_governed_fresh_cli_narrow_authentication(db_session,board,attested):
    result=correlated_inspect(db_session,board,attested)
    assert result['attesting_execution_identity_verified'] is True
    assert result['candidate_to_ci_source_relation_verified'] is False
    assert result['independent_compiler_causality_verified'] is False
    assert 'independent_compiler_causality_unproven' in result['blockers']
    for key in ('source_to_build_verified','publisher_verified','runtime_closure_verified','provider_ready','execution_authorized','live_transport_owned','isolation_verified'):
        assert result[key] is False
    evidence=json.loads(db_session.exec(select(AuditLog).where(AuditLog.action==build.ACTION)).one().after_state_json)
    proof=evidence['ci_attestation']
    assert proof['owning_github_execution_authenticated'] is False
    assert proof['verified_timestamps']==[{'type':'Tlog','timestamp':'2026-01-01T00:00:00Z'}]
    assert proof['certificate']['sourceRepositoryDigest']=='1'*40
    assert proof['certificate']['runInvocationURI'].endswith('/runs/123/attempts/1')
    assert str(attested['attestation_root']) not in canonical_json(evidence)
    assert 'unrecorded' not in canonical_json(evidence)


@pytest.mark.parametrize('field', ['issuer','subjectAlternativeName','buildSignerURI','buildSignerDigest','runnerEnvironment','sourceRepositoryURI','sourceRepositoryDigest','sourceRepositoryRef','sourceRepositoryIdentifier','sourceRepositoryOwnerURI','sourceRepositoryOwnerIdentifier','buildConfigURI','buildConfigDigest','buildTrigger','runInvocationURI'])
def test_fresh_cli_all_certificate_pins(db_session,board,attested,field):
    attested['verified_result'][0]['verificationResult']['signature']['certificate'][field]='wrong'
    attested['install_cli']()
    with pytest.raises(InvalidTransition,match='certificate'):correlated_inspect(db_session,board,attested)
    assert_no_audit(db_session)


@pytest.mark.parametrize('field', ['bundle_sha256','ci_source_sha','ci_workflow_sha','source_ref','trigger'])
def test_raw_deployment_pins_must_match_board(db_session,board,attested,field):
    trust=attested['compilation_trust']
    attested['compilation_trust']=replace(trust,ci_attestation=replace(trust.ci_attestation,**{field:'wrong'}))
    with pytest.raises(InvalidTransition,match='pins'):correlated_inspect(db_session,board,attested)
    assert_no_audit(db_session)


def test_review_requires_raw_deployment_locator(db_session,board,attested):
    attested['compilation_trust']=replace(attested['compilation_trust'],ci_attestation=None)
    with pytest.raises(InvalidTransition,match='trust missing'):correlated_inspect(db_session,board,attested)
    assert_no_audit(db_session)


@pytest.mark.parametrize('mutation',['mode','hardlink','symlink','fifo','oversize','bytes'])
def test_bundle_immutable_physical_bounds(db_session,board,attested,tmp_path,mutation):
    root=attested['attestation_root'];root.chmod(0o755);path=attested['bundle_path']
    if mutation=='mode':path.chmod(0o644)
    elif mutation=='hardlink':os.link(path,tmp_path/'other')
    elif mutation=='symlink':path.unlink();path.symlink_to(attested['report_path'])
    elif mutation=='fifo':path.unlink();os.mkfifo(path)
    else:
        path.chmod(0o644);path.write_bytes(b'x'*(ci.MAX_JSON+1) if mutation=='oversize' else b'{}');path.chmod(0o444)
    root.chmod(0o555)
    with pytest.raises(InvalidTransition):correlated_inspect(db_session,board,attested)
    assert_no_audit(db_session)


@pytest.mark.parametrize('target',['bundle','cli','report'])
def test_raw_inputs_rechecked_after_audit(db_session,board,attested,monkeypatch,target):
    original=build.record_audit
    def changed(*args,**kwargs):
        result=original(*args,**kwargs)
        path=attested['bundle_path'] if target=='bundle' else attested['attestation_root']/'cli.tar.gz' if target=='cli' else attested['report_path']
        path.chmod(0o644);path.write_bytes(path.read_bytes()+b' ');path.chmod(0o444)
        return result
    monkeypatch.setattr(build,'record_audit',changed)
    with pytest.raises(InvalidTransition):correlated_inspect(db_session,board,attested)
    assert_no_audit(db_session)


def test_cli_failure_fails_closed(db_session,board,attested):
    attested['install_cli'](body='#!/bin/sh\nif [ "$1" = "--version" ]; then echo "gh version 2.102.0 synthetic"; else exit 1; fi\n')
    with pytest.raises(InvalidTransition,match='process failed'):correlated_inspect(db_session,board,attested)
    assert_no_audit(db_session)


def test_no_credentials_proxies_or_custom_trust_inherited(tmp_path,monkeypatch):
    for key in ('GH_TOKEN','GITHUB_TOKEN','HTTP_PROXY','HTTPS_PROXY','SSL_CERT_FILE','SIGSTORE_ROOT_FILE','GH_CONFIG_DIR'):
        monkeypatch.setenv(key,'attacker')
    env=ci.minimal_environment(tmp_path)
    assert all(key not in env for key in ('GH_TOKEN','GITHUB_TOKEN','HTTP_PROXY','HTTPS_PROXY','SSL_CERT_FILE','SIGSTORE_ROOT_FILE'))
    assert env['GH_CONFIG_DIR']==str(tmp_path/'config')


def test_historical_nested_absence_and_null_serialization(correlated):
    original=correlated['request'].scope.compilation_evidence.model_dump(mode='json')
    assert 'ci_attestation' not in original
    assert ReaCompilationEvidence.model_validate(original).model_dump(mode='json')==original
    explicit={**original,'ci_attestation':None}
    assert ReaCompilationEvidence.model_validate(explicit).model_dump(mode='json')==explicit


def test_unchanged_pre_attestation_proposal_retry(db_session,board,correlated):
    original=correlated['row'].conditions_json
    row=build.admission.propose_rea_provider_review(db_session,board,correlated['request'])
    assert row.id==correlated['row'].id and row.conditions_json==original


@pytest.mark.parametrize('mutation', ['timestamps', 'future', 'subject', 'statement', 'copied-predicate'])
def test_witness_subject_and_predicate_cannot_authorize(db_session,board,attested,mutation):
    verified=attested['verified_result'][0]['verificationResult']
    if mutation=='timestamps':verified.pop('verifiedTimestamps')
    elif mutation=='future':verified['verifiedTimestamps'][0]['timestamp']='2999-01-01T00:00:00Z'
    elif mutation=='subject':verified['statement']['subject'][0]['digest']['sha256']='0'*64
    elif mutation=='statement':verified.pop('statement')
    else:
        certificate=verified['signature'].pop('certificate')
        verified['statement']['predicate']=certificate
    attested['install_cli']()
    with pytest.raises(InvalidTransition):correlated_inspect(db_session,board,attested)
    assert_no_audit(db_session)


def test_runtime_cli_archive_pin_rejects_untrusted_binary(tmp_path):
    with pytest.raises(InvalidTransition,match='pin mismatch'):
        ci.extract_cli(b'not the pinned CLI', tmp_path)


def test_runtime_process_bounds_and_timeout(tmp_path,monkeypatch):
    monkeypatch.setattr(ci,'MAX_PROCESS',1024)
    with pytest.raises(InvalidTransition,match='output bound'):
        ci.bounded_process(['/bin/sh','-c','yes x'],cwd=tmp_path,env={'PATH':'/usr/bin:/bin'},timeout=2)
    with pytest.raises(InvalidTransition,match='timeout'):
        ci.bounded_process(['/bin/sh','-c','sleep 3'],cwd=tmp_path,env={'PATH':'/usr/bin:/bin'},timeout=0.05)


def test_raw_report_replacement_with_same_bytes_during_audit_denied(db_session,board,attested,monkeypatch):
    original=build.record_audit
    def changed(*args,**kwargs):
        result=original(*args,**kwargs)
        path=attested['report_path'];raw=path.read_bytes();root=path.parent;root.chmod(0o755)
        path.unlink();path.write_bytes(raw);path.chmod(0o444);root.chmod(0o555)
        return result
    monkeypatch.setattr(build,'record_audit',changed)
    with pytest.raises(InvalidTransition,match='changed'):correlated_inspect(db_session,board,attested)
    assert_no_audit(db_session)


def test_canonical_authority_cancel_during_fresh_verifier_denied(db_session,board,attested,monkeypatch):
    from app.models.domain import now_utc
    original=ci.bounded_process
    def cancelled(argv,**kwargs):
        result=original(argv,**kwargs)
        if 'attestation' in argv:
            attested['work'].cancel_requested_at=now_utc();db_session.add(attested['work']);db_session.flush()
        return result
    monkeypatch.setattr(ci,'bounded_process',cancelled)
    with pytest.raises(InvalidTransition):correlated_inspect(db_session,board,attested)
    assert_no_audit(db_session)



def test_runtime_orphan_pipe_cleanup_after_parent_exit(tmp_path):
    import signal
    import time
    marker=tmp_path/'descendant.pid'
    with pytest.raises(InvalidTransition,match='timeout'):
        ci.bounded_process(['/bin/sh','-c',f'sleep 30 & echo $! > {marker}; exit 0'],cwd=tmp_path,env={'PATH':'/usr/bin:/bin'},timeout=0.1)
    pid=int(marker.read_text())
    deadline=time.monotonic()+2
    while time.monotonic()<deadline:
        status=Path(f'/proc/{pid}/stat')
        if not status.exists() or status.read_text().split()[2]=='Z':
            break
        time.sleep(0.01)
    else:
        try:
            os.kill(pid,signal.SIGKILL)
        except ProcessLookupError:
            # The descendant exited between the last observation and cleanup.
            return
        pytest.fail('verifier descendant remained running after timeout')
