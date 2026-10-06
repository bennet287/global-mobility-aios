"""Synthetic policy fixtures; actual CI bundles supply cryptographic proof."""
from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlmodel import select
from app.models.domain import AuditLog
from app.schemas_organization_rea_admission import ReaCompilationEvidence, ReaCiAttestationEvidence, ReaCiSourceRelationEvidence, ReaCompilerOutputsEvidence, ReaCompilerLaneEvidence
from app.services import organization_rea_ci_attestation as ci
from app.services import organization_rea_compiler_outputs as compiler
from app.services import organization_rea_build as build
from app.services.organization_command import InvalidTransition, canonical_json, canonical_fingerprint
from tests.test_organization_rea_ci_attestation import attested, raw_result
from tests.test_organization_rea_source_relation import witness
from tests.test_organization_rea_compilation import correlated, correlated_inspect, rewrite
from tests.test_organization_rea_build import package_setup, board, approve, assert_no_audit


@pytest.fixture
def compiled(attested,db_session,board):
    state=attested
    raw,args,_,_=witness(compiler=True)
    root=state['attestation_root'];root.chmod(0o755)
    (root/'witness.json').write_bytes(raw);(root/'witness.json').chmod(0o444)
    report=state['report'];repeated=report['repeatability']
    repeated['context']['candidate']=args['candidate_sha']
    repeated['recipe'].update(workflow_sha256=args['workflow_sha256'],helper_sha256=args['helper_sha256'])
    lane_pins={};lane_trust={};manifest_values={}
    for lane in ('a','b'):
        manifest_values[lane]=dict(format='aios-rea-build-job.v1',context=repeated['context'],job=lane,
            captured_at=datetime.now(timezone.utc).isoformat(),**{key:repeated[key] for key in ('source','toolchain','recipe','files')})
        manifest=canonical_json(manifest_values[lane]).encode();bundle=canonical_json({'synthetic':lane}).encode()
        for kind,data in (('manifest',manifest),('bundle',bundle)):
            target=root/f'{lane}-{kind}.json';target.write_bytes(data);target.chmod(0o444)
        lane_pins[lane]=ReaCompilerLaneEvidence(manifest_sha256=ci.sha(manifest),bundle_sha256=ci.sha(bundle),workflow_sha256=ci.sha(('reusable-'+lane+'\n').encode()))
        lane_trust[lane]=compiler.ReaCompilerLaneTrust(root,f'{lane}-manifest.json',root,f'{lane}-bundle.json',**lane_pins[lane].model_dump(mode='json'))
        repeated['received_manifest_sha256'][lane]=ci.sha(manifest)
    root.chmod(0o555)
    rewrite(state,report)
    request=state['request'].model_copy(deep=True);request.decision_key='compiler-'+uuid4().hex;request.supersedes_decision_id=state['row'].id
    payload=request.scope.compilation_evidence.model_dump(mode='json')
    payload.update(candidate_sha=args['candidate_sha'],report_sha256=state['compilation_trust'].report_sha256,workflow_sha256=args['workflow_sha256'],helper_sha256=args['helper_sha256'])
    source_pins=ReaCiSourceRelationEvidence(witness_sha256=ci.sha(raw),reviewed_verifier_sha256=args['pins'].reviewed_verifier_sha256,approved_base_sha=args['pins'].approved_base_sha)
    payload['ci_attestation'].update(ci_source_sha=args['ci_source_sha'],ci_workflow_sha=args['ci_workflow_sha'],source_relation=source_pins.model_dump(mode='json'),compiler_outputs=ReaCompilerOutputsEvidence(**lane_pins).model_dump(mode='json'))
    request.scope.compilation_evidence=ReaCompilationEvidence.model_validate(payload)
    row=approve(db_session,board,build.admission.propose_rea_provider_review(db_session,board,request))
    contract=build.admission.resolve_rea_provider_review(db_session,board,decision_id=row.id,trust=state['trust'])[1]
    old=state['compilation_trust']
    deployment=replace(old.ci_attestation,ci_source_sha=args['ci_source_sha'],ci_workflow_sha=args['ci_workflow_sha'],source_relation=replace(args['pins'],witness_root=root),compiler_outputs=compiler.ReaCompilerOutputsTrust(**lane_trust))
    state.update(row=row,request=request,manifest_values=manifest_values,compilation_trust=replace(old,candidate_sha=args['candidate_sha'],workflow_sha256=args['workflow_sha256'],helper_sha256=args['helper_sha256'],provider_decision_id=str(row.id),provider_contract_sha256=canonical_fingerprint(contract),ci_attestation=deployment))
    expected=ci.expected_identity(candidate=args['candidate_sha'],run_id=old.run_id,run_attempt=old.run_attempt,source_sha=args['ci_source_sha'],workflow_sha=args['ci_workflow_sha'],source_ref=deployment.source_ref,trigger=deployment.trigger)
    results={'report':raw_result(state['report_path'].read_bytes(),expected)}
    for lane in ('a','b'):
        result=raw_result((root/f'{lane}-manifest.json').read_bytes(),compiler._identity(expected,lane))
        result[0]['verificationResult']['statement']['subject'][0]['name']='manifest.json'
        results[lane]=result
    def install():
        script='#!/usr/bin/python3\nimport json,sys\nif sys.argv[1]=="--version":\n print("gh version 2.102.0 synthetic")\nelse:\n values=json.loads('+repr(json.dumps(results))+')\n value=json.load(open(sys.argv[3]))\n print(json.dumps(values[value.get("job","report")]))\n'
        state['install_cli'](body=script)
    state.update(compiler_results=results,compiler_expected=expected,install_compiler_cli=install)
    install()
    return state


def test_governed_signed_compiler_outputs_narrow_projection(db_session,board,compiled):
    result=correlated_inspect(db_session,board,compiled)
    assert result['compiler_workflow_outputs_authenticated'] is True
    assert result['candidate_to_ci_source_relation_verified'] is True
    for key in ('independent_compiler_causality_verified','source_to_build_verified','publisher_verified','runtime_closure_verified','provider_ready','execution_authorized','live_transport_owned','isolation_verified'):
        assert result[key] is False
    proof=json.loads(db_session.exec(select(AuditLog).where(AuditLog.action==build.ACTION)).one().after_state_json)['ci_attestation']
    assert proof['owning_github_execution_authenticated'] is False
    assert set(proof['compiler_outputs'])=={'a','b'}
    assert proof['compiler_outputs']['a']['certificate']['buildSignerURI'].endswith('/rea-source-build-a.yml@refs/pull/318/merge')
    assert proof['compiler_outputs']['a']['certificate']['buildConfigURI'].endswith('/rea-build-repeatability.yml@refs/pull/318/merge')
    assert 'files' not in proof['compiler_outputs']['a'] and str(compiled['attestation_root']) not in json.dumps(proof)


@pytest.mark.parametrize('mutation',['compare-signer','wrong-lane-signer','wrong-source','wrong-run','wrong-attempt','missing-cert','subject-name','subject-digest','timestamp'])
def test_compiler_identity_not_self_declared(db_session,board,compiled,mutation):
    verified=compiled['compiler_results']['a'][0]['verificationResult'];cert=verified['signature']['certificate']
    if mutation=='compare-signer':
        for key in ('subjectAlternativeName','buildSignerURI'):cert[key]=compiled['compiler_expected'][key]
    elif mutation=='wrong-lane-signer':
        for key in ('subjectAlternativeName','buildSignerURI'):cert[key]=compiled['compiler_results']['b'][0]['verificationResult']['signature']['certificate'][key]
    elif mutation=='wrong-source':cert['sourceRepositoryDigest']='1'*40
    elif mutation=='wrong-run':cert['runInvocationURI']=cert['runInvocationURI'].replace('/runs/123/','/runs/124/')
    elif mutation=='wrong-attempt':cert['runInvocationURI']=cert['runInvocationURI'].replace('/attempts/1','/attempts/2')
    elif mutation=='missing-cert':verified['signature'].pop('certificate')
    elif mutation=='subject-name':verified['statement']['subject'][0]['name']='correlation.json'
    elif mutation=='subject-digest':verified['statement']['subject'][0]['digest']['sha256']='0'*64
    else:verified['verifiedTimestamps']=[]
    compiled['install_compiler_cli']()
    with pytest.raises(InvalidTransition):correlated_inspect(db_session,board,compiled)
    assert_no_audit(db_session)


@pytest.mark.parametrize('lane',['a','b'])
@pytest.mark.parametrize('field',['manifest_sha256','bundle_sha256','workflow_sha256'])
def test_compiler_deployment_pins_are_board_owned(db_session,board,compiled,lane,field):
    old=compiled['compilation_trust'];outputs=old.ci_attestation.compiler_outputs
    outputs=replace(outputs,**{lane:replace(getattr(outputs,lane),**{field:'0'*64})})
    compiled['compilation_trust']=replace(old,ci_attestation=replace(old.ci_attestation,compiler_outputs=outputs))
    with pytest.raises(InvalidTransition,match='pins'):correlated_inspect(db_session,board,compiled)
    assert_no_audit(db_session)


@pytest.mark.parametrize('lane',['a','b'])
@pytest.mark.parametrize('kind',['manifest','bundle'])
def test_all_compiler_raw_inputs_revalidated_after_audit(db_session,board,compiled,monkeypatch,lane,kind):
    original=build.record_audit
    def mutate(*args,**kwargs):
        result=original(*args,**kwargs)
        path=compiled['attestation_root']/f'{lane}-{kind}.json'
        path.chmod(0o644);path.write_bytes(path.read_bytes()+b' ');path.chmod(0o444)
        return result
    monkeypatch.setattr(build,'record_audit',mutate)
    with pytest.raises(InvalidTransition):correlated_inspect(db_session,board,compiled)
    assert_no_audit(db_session)


def test_compiler_outputs_missing_source_relation_rejected_by_typed_contract():
    evidence=dict(bundle_sha256='a'*64,ci_source_sha='b'*40,ci_workflow_sha='b'*40,source_ref='refs/pull/1/merge',trigger='pull_request')
    lane=dict(manifest_sha256='c'*64,bundle_sha256='d'*64,workflow_sha256='e'*64)
    with pytest.raises(ValidationError,match='source relation'):
        ReaCiAttestationEvidence.model_validate({**evidence,'compiler_outputs':dict(a=lane,b=lane)})
    for value in (evidence,{**evidence,'compiler_outputs':None}):
        assert ReaCiAttestationEvidence.model_validate(value).model_dump(mode='json')==value


@pytest.mark.parametrize('mutation',['job','context','source','recipe','toolchain','files','extra','future','invalid-time'])
def test_authenticated_manifest_cannot_disagree_with_received_report(compiled,mutation):
    """Repin every byte/subject digest: semantic mismatch still fails."""
    value=json.loads(canonical_json(compiled['manifest_values']['a']))
    if mutation=='job':value['job']='b'
    elif mutation=='context':value['context']['run_attempt']='2'
    elif mutation=='source':value['source']['commit']='0'*40
    elif mutation=='recipe':value['recipe']['lifecycle_scripts']=True
    elif mutation=='toolchain':value['toolchain']['versions']['node']='v1'
    elif mutation=='files':value['files'].pop()
    elif mutation=='extra':value['extra']=True
    elif mutation=='future':value['captured_at']='2999-01-01T00:00:00+00:00'
    else:value['captured_at']='2026-99-99T00:00:00+00:00'
    raw=canonical_json(value).encode()
    report=json.loads(compiled['report_path'].read_bytes())
    report['repeatability']['received_manifest_sha256']['a']=ci.sha(raw)
    old=compiled['compilation_trust'].ci_attestation.compiler_outputs
    trust=replace(old,a=replace(old.a,manifest_sha256=ci.sha(raw)))
    result=raw_result(raw,compiler._identity(compiled['compiler_expected'],'a'))
    result[0]['verificationResult']['statement']['subject'][0]['name']='manifest.json'
    compiled['compiler_results']['a']=result
    compiled['install_compiler_cli']()
    snapshots=[(raw,None,None),((compiled['attestation_root']/'a-bundle.json').read_bytes(),None,None),((compiled['attestation_root']/'b-manifest.json').read_bytes(),None,None),((compiled['attestation_root']/'b-bundle.json').read_bytes(),None,None)]
    with pytest.raises(InvalidTransition):
        compiler.authenticate(canonical_json(report).encode(),(compiled['attestation_root']/'cli.tar.gz').read_bytes(),compiled['compiler_expected'],trust,snapshots)


@pytest.mark.parametrize('kind',['manifest','bundle'])
@pytest.mark.parametrize('mutation',['writable','hardlink','symlink','oversize'])
def test_compiler_immutable_raw_custody(db_session,board,compiled,tmp_path,kind,mutation):
    import os
    root=compiled['attestation_root'];root.chmod(0o755)
    path=root/f'a-{kind}.json'
    if mutation=='writable':path.chmod(0o644)
    elif mutation=='hardlink':os.link(path,tmp_path/'other')
    elif mutation=='symlink':path.unlink();path.symlink_to(compiled['report_path'])
    else:path.chmod(0o644);path.write_bytes(b'x'*(ci.MAX_JSON+1));path.chmod(0o444)
    root.chmod(0o555)
    with pytest.raises(InvalidTransition):correlated_inspect(db_session,board,compiled)
    assert_no_audit(db_session)


def test_reused_lane_evidence_denied(compiled):
    old=compiled['compilation_trust'].ci_attestation.compiler_outputs
    approved=compiled['request'].scope.compilation_evidence.ci_attestation.compiler_outputs
    copied=ReaCompilerOutputsEvidence(a=approved.a,b=approved.a)
    with pytest.raises(InvalidTransition,match='reuse'):
        compiler.reviewed_pins(replace(old,b=old.a),copied)


def test_two_reviewed_reusable_workflows_required_in_git_witness():
    from app.services import organization_rea_source_relation as relation
    raw,args,_,_=witness(compiler=True)
    pins={lane:ci.sha(('reusable-'+lane+'\n').encode()) for lane in ('a','b')}
    summary=relation.verify(raw,**args,compiler_workflow_pins=pins)
    assert summary['reviewed_compiler_workflows_sha256']==pins
    for value in (None,{'a':pins['a']},{**pins,'a':'0'*64}):
        with pytest.raises(InvalidTransition):relation.verify(raw,**args,compiler_workflow_pins=value)


def test_fixed_reusable_compilation_precedes_attestation_and_no_caller_inputs():
    import yaml
    root=Path(__file__).resolve().parents[3]
    for lane in ('a','b'):
        text=(root/f'.github/workflows/rea-source-build-{lane}.yml').read_text()
        workflow=yaml.safe_load(text)
        # PyYAML's YAML1.1 spelling makes `on` a boolean; either accepted key
        # remains a single workflow_call trigger with no configurable inputs.
        assert workflow.get('on',workflow.get(True)) == {'workflow_call':None}
        job=workflow['jobs']['compile']
        assert 'head.repo.full_name == github.repository' in job['if']
        assert job['permissions']=={'contents':'read','id-token':'write','attestations':'write'}
        steps=job['steps']
        capture=next(i for i,s in enumerate(steps) if 'rea_build_repeatability.py capture' in s.get('run',''))
        compile_step=next(i for i,s in enumerate(steps) if s.get('name','').startswith('Compile directly'))
        attest=next(i for i,s in enumerate(steps) if s.get('uses','').startswith('actions/attest@'))
        assert compile_step<capture<attest
        assert steps[attest]['with']=={'subject-path':f'rea-build-{lane}/manifest.json'}
        assert 'secrets: inherit' not in text and 'inputs.' not in text and 'download-artifact' not in text


def test_canonical_work_cancel_during_compiler_verification_denied(db_session,board,compiled,monkeypatch):
    from app.models.domain import now_utc
    original=ci.bounded_process
    def cancelled(argv,**kwargs):
        value=original(argv,**kwargs)
        if len(argv)>3 and argv[1:3]==['attestation','verify'] and argv[3].endswith('/manifest.json'):
            compiled['work'].cancel_requested_at=now_utc();db_session.add(compiled['work']);db_session.flush()
        return value
    monkeypatch.setattr(ci,'bounded_process',cancelled)
    with pytest.raises(InvalidTransition):correlated_inspect(db_session,board,compiled)
    assert_no_audit(db_session)


def test_existing_attestation_proposal_retry_keeps_absent_compiler_field(db_session,board,attested):
    original=attested['row'].conditions_json
    row=build.admission.propose_rea_provider_review(db_session,board,attested['request'])
    assert row.id==attested['row'].id and row.conditions_json==original
    assert 'compiler_outputs' not in attested['request'].scope.compilation_evidence.ci_attestation.model_dump(mode='json')
