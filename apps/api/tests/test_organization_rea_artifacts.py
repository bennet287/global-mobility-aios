from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlmodel import select

from app.models.domain import AuditLog, OrganizationPosition, OrganizationalWorkItem, now_utc
from app.schemas_organization_rea_artifacts import ReaArtifactProposal, ReaArtifactScope
from app.services.organization_command import AuthorityDenied, IdempotencyConflict, InvalidTransition, OrganizationCommandContext, TenantMismatch
from app.services.organization_decision import record_executive_decision_outcome
from app.services.organization_rea_catalog import discover_rea_tools
from app.services import organization_rea_artifacts as rea


@pytest.fixture
def board():
    return OrganizationCommandContext(tenant_key="default", actor_id="reviewer", authenticated_user_id="reviewer", actor_type="human", role="admin", position_key="board")


@pytest.fixture
def work(db_session):
    position = OrganizationPosition(position_key="engineer", title="Engineer", department="engineering", authority_level="L1")
    row = OrganizationalWorkItem(idempotency_key="rea-work", title="Analyze", objective="Investigate behavior", department="engineering", authority_level="L1", assigned_position_key="engineer")
    db_session.add(position)
    db_session.add(row)
    db_session.commit()
    return row


def payload(work, **changes):
    scope = dict(artifact_sha256=hashlib.sha256(b"artifact").hexdigest(), artifact_bytes=8,
        source_reference="owned source", provenance="source release", custodian_reference="custodian", rights_reference="rights review",
        purpose="interoperability", reconstruction_scope="behavior only", exact_tools=[x.tool_id for x in discover_rea_tools()], expires_at=now_utc()+timedelta(days=1))
    scope.update(changes)
    return ReaArtifactProposal(decision_key="rea-review", work_item_id=work.id, scope=scope)


def approve(session, board, row):
    return record_executive_decision_outcome(session, board, decision_id=row.id, outcome="approved", reason="Reviewed artifact scope")


def reviewed(session, board, work):
    row = rea.propose_rea_artifact(session, board, payload(work))
    return approve(session, board, row)


def test_all_122_review_and_idempotency(db_session, board, work):
    request = payload(work)
    row = rea.propose_rea_artifact(db_session, board, request)
    assert rea.propose_rea_artifact(db_session, board, request).id == row.id
    with pytest.raises(InvalidTransition):
        rea.resolve_rea_artifact_authorization(db_session, board, decision_id=row.id)
    approve(db_session, board, row)
    result = rea.resolve_rea_artifact_authorization(db_session, board, decision_id=row.id)
    assert len(result.exact_tools) == 122 and result.execution_authorized is False
    changed = request.model_copy(update={"scope": request.scope.model_copy(update={"purpose": "different"})})
    with pytest.raises(IdempotencyConflict):
        rea.propose_rea_artifact(db_session, board, changed)


@pytest.mark.parametrize("changes", [dict(artifact_bytes=True),dict(artifact_bytes=0),dict(artifact_bytes=257*1024*1024),dict(artifact_sha256="A"*64),dict(purpose=" "),dict(provenance=2),dict(exact_tools=["engineering.reverse_engineering"]),dict(exact_tools=["*"]),dict(exact_tools=[discover_rea_tools()[0].tool_id]*2),dict(expires_at="2026-10-05T00:00:00"),dict(expires_at=123),dict(extra="unknown")])
def test_strict_scope(work, changes):
    with pytest.raises(ValidationError):
        payload(work, **changes)


@pytest.mark.parametrize("role,actor,position", [("operator","human","board"),("admin","agent","board"),("admin","human","ceo")])
def test_human_board_gate(db_session, work, role, actor, position):
    context = OrganizationCommandContext(tenant_key="default", actor_id="reviewer", authenticated_user_id="reviewer", actor_type=actor, role=role, position_key=position)
    with pytest.raises(AuthorityDenied):
        rea.propose_rea_artifact(db_session, context, payload(work))


@pytest.mark.parametrize("delta", [timedelta(days=-1),timedelta(days=31)])
def test_expiry_bounds(db_session, board, work, delta):
    with pytest.raises(InvalidTransition):
        rea.propose_rea_artifact(db_session, board, payload(work, expires_at=now_utc()+delta))


@pytest.mark.parametrize("field,value", [("objective","changed"),("context_json",'{"changed":true}'),("assigned_position_key","other"),("status","cancelled"),("status","completed"),("cancel_requested_at",now_utc())])
def test_work_changes_deny(db_session, board, work, field, value):
    row = reviewed(db_session, board, work)
    setattr(work,field,value)
    db_session.add(work)
    db_session.commit()
    with pytest.raises(InvalidTransition):
        rea.resolve_rea_artifact_authorization(db_session,board,decision_id=row.id)


@pytest.mark.parametrize("field,value",[("version",2),("contract_json",'{"changed":true}'),("suspended_at",now_utc()),("status","retired")])
def test_position_changes_deny(db_session, board, work, field, value):
    row=reviewed(db_session,board,work)
    position=db_session.exec(select(OrganizationPosition)).one()
    setattr(position,field,value)
    db_session.add(position)
    db_session.commit()
    with pytest.raises(InvalidTransition):
        rea.resolve_rea_artifact_authorization(db_session,board,decision_id=row.id)


@pytest.mark.parametrize("action",["organization.decision.create","organization.decision.approved","organization.rea.artifact.propose"])
def test_missing_audit_deny(db_session,board,work,action):
    row=reviewed(db_session,board,work)
    log=db_session.exec(select(AuditLog).where(AuditLog.action==action)).one()
    db_session.delete(log)
    db_session.commit()
    with pytest.raises(InvalidTransition):
        rea.resolve_rea_artifact_authorization(db_session,board,decision_id=row.id)


def test_tamper_and_wrong_tenant(db_session,board,work):
    row=reviewed(db_session,board,work)
    other=OrganizationCommandContext(tenant_key="other",actor_id="reviewer",authenticated_user_id="reviewer",actor_type="human",role="admin",position_key="board")
    with pytest.raises(TenantMismatch):
        rea.resolve_rea_artifact_authorization(db_session,other,decision_id=row.id)
    row.source_object_version="0"*64
    db_session.add(row)
    db_session.commit()
    with pytest.raises(InvalidTransition):
        rea.resolve_rea_artifact_authorization(db_session,board,decision_id=row.id)


@pytest.mark.parametrize("outcome",[None,"approved","rejected"])
def test_revocation_successors_always_block_predecessor(db_session,board,work,outcome):
    row=reviewed(db_session,board,work)
    successor=rea.propose_rea_artifact_revocation(db_session,board,decision_id=row.id,decision_key="revocation",reason="Withdraw review")
    assert json.loads(successor.evidence_json)[0]["rea_revocation_reason"]=="Withdraw review"
    if outcome:
        record_executive_decision_outcome(db_session,board,decision_id=successor.id,outcome=outcome,reason="review")
    with pytest.raises(InvalidTransition):
        rea.resolve_rea_artifact_authorization(db_session,board,decision_id=row.id)
    with pytest.raises(InvalidTransition):
        rea.resolve_rea_artifact_authorization(db_session,board,decision_id=successor.id)


def roots(tmp_path):
    source=tmp_path/"source"
    source.mkdir()
    (source/"input").write_bytes(b"artifact")
    custody=tmp_path/"custody"
    custody.mkdir(mode=0o700)
    return source,custody


def test_custody_and_revalidation(db_session,board,work,tmp_path):
    row=reviewed(db_session,board,work)
    source,custody=roots(tmp_path)
    receipt=rea.stage_rea_artifact_custody(db_session,board,decision_id=row.id,source_root=source,source_relative="input",custody_root=custody)
    assert (custody/str(receipt)/"artifact").read_bytes()==b"artifact"
    assert rea.revalidate_rea_artifact_custody(db_session,board,receipt_id=receipt,decision_id=row.id,custody_root=custody).execution_authorized is False
    staged=custody/str(receipt)/"artifact"
    staged.chmod(0o600)
    staged.write_bytes(b"tampered")
    staged.chmod(0o400)
    with pytest.raises(InvalidTransition):
        rea.revalidate_rea_artifact_custody(db_session,board,receipt_id=receipt,decision_id=row.id,custody_root=custody)


@pytest.mark.parametrize("relative",["../input","/input","nested/../input","./input","input/",""])
def test_path_traversal(db_session,board,work,tmp_path,relative):
    row=reviewed(db_session,board,work)
    source,custody=roots(tmp_path)
    with pytest.raises(InvalidTransition):
        rea.stage_rea_artifact_custody(db_session,board,decision_id=row.id,source_root=source,source_relative=relative,custody_root=custody)
    assert not list(custody.iterdir())


@pytest.mark.parametrize("case",["final_symlink","parent_symlink","fifo","wrong_hash","oversized"])
def test_custody_failure_cleanup(db_session,board,work,tmp_path,case):
    row=reviewed(db_session,board,work)
    source,custody=roots(tmp_path)
    relative="input"
    if case=="final_symlink":
        (source/"link").symlink_to(source/"input")
        relative="link"
    elif case=="parent_symlink":
        (source/"link").symlink_to(source,target_is_directory=True)
        relative="link/input"
    elif case=="fifo":
        os.mkfifo(source/"pipe")
        relative="pipe"
    else:
        (source/"input").write_bytes(b"wrong!!!" if case=="wrong_hash" else b"too large")
    with pytest.raises((InvalidTransition,OSError)):
        rea.stage_rea_artifact_custody(db_session,board,decision_id=row.id,source_root=source,source_relative=relative,custody_root=custody)
    assert not list(custody.iterdir())
    assert not db_session.exec(select(AuditLog).where(AuditLog.action=="organization.rea.artifact.custody")).all()


def test_replacement_approval_never_reenables_predecessor(db_session,board,work):
    old=reviewed(db_session,board,work)
    request=payload(work,purpose="new purpose").model_copy(update={"decision_key":"replacement","supersedes_decision_id":old.id})
    new=rea.propose_rea_artifact(db_session,board,request)
    approve(db_session,board,new)
    assert rea.resolve_rea_artifact_authorization(db_session,board,decision_id=new.id).decision_id==new.id
    new.status="expired"
    db_session.add(new)
    db_session.commit()
    with pytest.raises(InvalidTransition):
        rea.resolve_rea_artifact_authorization(db_session,board,decision_id=old.id)


def test_expiry_fresh_check(db_session,board,work,monkeypatch):
    row=reviewed(db_session,board,work)
    monkeypatch.setattr(rea,"now_utc",lambda:now_utc()+timedelta(days=2))
    with pytest.raises(InvalidTransition):
        rea.resolve_rea_artifact_authorization(db_session,board,decision_id=row.id)


def test_no_retroactive_witness_repair(db_session,board,work):
    request=payload(work)
    row=rea.propose_rea_artifact(db_session,board,request)
    approve(db_session,board,row)
    log=db_session.exec(select(AuditLog).where(AuditLog.action=="organization.rea.artifact.propose")).one()
    db_session.delete(log)
    db_session.commit()
    with pytest.raises(InvalidTransition):
        rea.propose_rea_artifact(db_session,board,request)


def test_assignment_away_and_back_invalidates(db_session,board,work):
    from app.services.organization_work import assign_work_item
    row=reviewed(db_session,board,work)
    assign_work_item(db_session,board,work_item_id=work.id,assigned_position_key="other",reason="move")
    assign_work_item(db_session,board,work_item_id=work.id,assigned_position_key="engineer",reason="return")
    with pytest.raises(InvalidTransition):
        rea.resolve_rea_artifact_authorization(db_session,board,decision_id=row.id)


@pytest.mark.parametrize("raw",['[{"kind":1,"kind":2}]','[NaN]','[Infinity]'])
def test_noncanonical_json_denied(db_session,board,work,raw):
    row=reviewed(db_session,board,work)
    row.conditions_json=raw
    db_session.add(row)
    db_session.commit()
    with pytest.raises(InvalidTransition):
        rea.resolve_rea_artifact_authorization(db_session,board,decision_id=row.id)


def test_custody_audit_failure_cleans_files(db_session,board,work,tmp_path,monkeypatch):
    row=reviewed(db_session,board,work)
    source,custody=roots(tmp_path)
    def fail(*args,**kwargs):
        raise RuntimeError("audit unavailable")
    monkeypatch.setattr(rea,"record_audit",fail)
    with pytest.raises(RuntimeError,match="audit unavailable"):
        rea.stage_rea_artifact_custody(db_session,board,decision_id=row.id,source_root=source,source_relative="input",custody_root=custody)
    assert not list(custody.iterdir())


def test_custody_auth_changed_during_copy_cleanup(db_session,board,work,tmp_path,monkeypatch):
    row=reviewed(db_session,board,work)
    source,custody=roots(tmp_path)
    original=rea._bytes
    changed=False
    def mutate(fd,size,output_fd=None):
        nonlocal changed
        digest=original(fd,size,output_fd)
        if output_fd is not None and not changed:
            changed=True
            work.status="cancelled"
            db_session.add(work)
            db_session.commit()
        return digest
    monkeypatch.setattr(rea,"_bytes",mutate)
    with pytest.raises(InvalidTransition):
        rea.stage_rea_artifact_custody(db_session,board,decision_id=row.id,source_root=source,source_relative="input",custody_root=custody)
    assert not list(custody.iterdir())


def test_receipt_only_committed_witness(db_session,board,work,tmp_path):
    row=reviewed(db_session,board,work)
    source,custody=roots(tmp_path)
    receipt=rea.stage_rea_artifact_custody(db_session,board,decision_id=row.id,source_root=source,source_relative="input",custody_root=custody)
    with pytest.raises(InvalidTransition):
        rea.revalidate_rea_artifact_custody(db_session,board,receipt_id=uuid4(),decision_id=row.id,custody_root=custody)
    with pytest.raises(InvalidTransition):
        rea.revalidate_rea_artifact_custody(db_session,board,receipt_id={"receipt_id":receipt,"path":str(source/"input")},decision_id=row.id,custody_root=custody)
    audit=db_session.exec(select(AuditLog).where(AuditLog.action=="organization.rea.artifact.custody")).one()
    db_session.delete(audit)
    db_session.commit()
    with pytest.raises(InvalidTransition):
        rea.revalidate_rea_artifact_custody(db_session,board,receipt_id=receipt,decision_id=row.id,custody_root=custody)


def test_max_unicode_scope_full_catalog_usable(db_session,board,work):
    request=payload(work,source_reference="🧪"*2000,provenance="🧪"*2000,custodian_reference="🧪"*2000,rights_reference="🧪"*2000,purpose="🧪"*2000,reconstruction_scope="🧪"*2000)
    row=rea.propose_rea_artifact(db_session,board,request)
    approve(db_session,board,row)
    assert len(rea.resolve_rea_artifact_authorization(db_session,board,decision_id=row.id).exact_tools)==122


def test_rea_http_gate_scope_and_cross_tenant(client,db_session,board,work):
    raw_client=client
    from app.main import app
    from app.routers.organization_records import organization_command_context
    base="/api/v1/organization/engineering/rea"
    app.dependency_overrides[organization_command_context]=lambda:board
    try:
        body=payload(work).model_dump(mode="json")
        response=raw_client.post(base+"/artifact-proposals",json=body)
        assert response.status_code==201,response.text
        decision=response.json()["id"]
        assert raw_client.get(base+f"/artifact-authorizations/{decision}").status_code==409
        result=raw_client.post(f"/api/v1/organization/decisions/records/{decision}/outcome",json={"outcome":"approved","reason":"reviewed"})
        assert result.status_code==200,result.text
        result=raw_client.get(base+f"/artifact-authorizations/{decision}")
        assert result.status_code==200 and result.json()["execution_authorized"] is False
        other=OrganizationCommandContext(tenant_key="other",actor_id="reviewer",authenticated_user_id="reviewer",actor_type="human",role="admin",position_key="board")
        app.dependency_overrides[organization_command_context]=lambda:other
        response=raw_client.get(base+f"/artifact-authorizations/{decision}")
        assert response.status_code==404 and "default" not in response.text
        app.dependency_overrides[organization_command_context]=lambda:board
        bad=dict(body,actor_id="forged")
        assert raw_client.post(base+"/artifact-proposals",json=bad).status_code==422
        duplicate=json.dumps(body).replace('"decision_key": "rea-review"','"decision_key": "first", "decision_key": "rea-review"')
        assert raw_client.post(base+"/artifact-proposals",content=duplicate,headers={"Content-Type":"application/json"}).status_code==422
    finally:
        app.dependency_overrides.pop(organization_command_context,None)


@pytest.mark.parametrize("action,raw",[("organization.decision.create","[]"),("organization.decision.create",'{"created_at":"bad"}'),("organization.decision.approved","[]"),("organization.decision.approved",'{"created_at":"bad"}')])
def test_malformed_persisted_audits_fail_closed(db_session,board,work,action,raw):
    row=reviewed(db_session,board,work)
    log=db_session.exec(select(AuditLog).where(AuditLog.action==action)).one()
    log.after_state_json=raw
    db_session.add(log)
    db_session.commit()
    with pytest.raises(InvalidTransition):
        rea.resolve_rea_artifact_authorization(db_session,board,decision_id=row.id)


def test_malformed_contract_operation_fail_closed(db_session,board,work):
    row=reviewed(db_session,board,work)
    data=json.loads(row.conditions_json)
    data[0]["operation"]=[]
    row.conditions_json=json.dumps(data)
    db_session.add(row)
    db_session.commit()
    with pytest.raises(InvalidTransition):
        rea.resolve_rea_artifact_authorization(db_session,board,decision_id=row.id)


def test_real_http_identity_binding(client,db_session,work):
    base="/api/v1/organization/engineering/rea"
    request=payload(work,source_reference="🧪"*2000,provenance="🧪"*2000,custodian_reference="🧪"*2000,rights_reference="🧪"*2000,purpose="🧪"*2000,reconstruction_scope="🧪"*2000).model_dump(mode="json")
    response=client.post(base+"/artifact-proposals",content=json.dumps(request),headers={"Content-Type":"application/json","X-GMAI-Tenant":"other","X-GMAI-Actor":"forged"})
    assert response.status_code==201,response.text
    decision=response.json()["id"]
    from app.models.domain import ExecutiveDecision
    assert db_session.exec(select(ExecutiveDecision).where(ExecutiveDecision.decision_key=="rea-review")).one().tenant_key=="default"
    log=db_session.exec(select(AuditLog).where(AuditLog.action=="organization.rea.artifact.propose")).one()
    assert log.actor=="pytest-admin"
    response=client.post(f"/api/v1/organization/decisions/records/{decision}/outcome",json={"outcome":"approved","reason":"review"})
    assert response.status_code==200,response.text
    operator={"X-GMAI-Role":"operator","X-GMAI-User":"operator","X-GMAI-Position":"board"}
    denied=dict(request,decision_key="operator-attempt")
    assert client.post(base+"/artifact-proposals",json=denied,headers=operator).status_code==403
    assert client.post(base+f"/artifact-authorizations/{decision}/revocations",json={"decision_key":"revoke","reason":"withdraw"},headers=operator).status_code==403
    denied=dict(request,tenant_key="other")
    assert client.post(base+"/artifact-proposals",json=denied).status_code==422
    duplicate='{"decision_key":"r1","decision_key":"r2","reason":"withdraw"}'
    assert client.post(base+f"/artifact-authorizations/{decision}/revocations",content=duplicate,headers={"Content-Type":"application/json"}).status_code==422
    response=client.post(base+f"/artifact-authorizations/{decision}/revocations",json={"decision_key":"revoked","reason":"withdraw"})
    assert response.status_code==201,response.text


def test_custody_commit_failure_rolls_back_witness_and_cleans_files(db_session,board,work,tmp_path,monkeypatch):
    row=reviewed(db_session,board,work)
    source,custody=roots(tmp_path)
    original_commit=db_session.commit
    def fail_commit():
        db_session.flush()
        raise RuntimeError("commit failed")
    monkeypatch.setattr(db_session,"commit",fail_commit)
    with pytest.raises(RuntimeError,match="commit failed"):
        rea.stage_rea_artifact_custody(db_session,board,decision_id=row.id,source_root=source,source_relative="input",custody_root=custody)
    monkeypatch.setattr(db_session,"commit",original_commit)
    assert not list(custody.iterdir())
    assert not db_session.exec(select(AuditLog).where(AuditLog.action=="organization.rea.artifact.custody")).all()


@pytest.mark.parametrize("approve_orphan",[False,True])
def test_proposal_witness_commit_failure_is_fail_closed(db_session,board,work,monkeypatch,approve_orphan):
    from app.models.domain import ExecutiveDecision
    request=payload(work)
    original=db_session.commit
    count=0
    def fail_second():
        nonlocal count
        count+=1
        if count==2:
            db_session.flush()
            raise RuntimeError("typed witness commit failed")
        original()
    monkeypatch.setattr(db_session,"commit",fail_second)
    with pytest.raises(RuntimeError,match="typed witness commit failed"):
        rea.propose_rea_artifact(db_session,board,request)
    monkeypatch.setattr(db_session,"commit",original)
    orphan=db_session.exec(select(ExecutiveDecision)).one()
    assert orphan.status=="pending_board"
    assert not db_session.exec(select(AuditLog).where(AuditLog.action=="organization.rea.artifact.propose")).all()
    with pytest.raises(InvalidTransition):
        rea.resolve_rea_artifact_authorization(db_session,board,decision_id=orphan.id)
    if approve_orphan:
        approve(db_session,board,orphan)
        with pytest.raises(InvalidTransition):
            rea.propose_rea_artifact(db_session,board,request)
    else:
        assert rea.propose_rea_artifact(db_session,board,request).id==orphan.id
        approve(db_session,board,orphan)
        assert rea.resolve_rea_artifact_authorization(db_session,board,decision_id=orphan.id).execution_authorized is False


def test_source_changed_during_read_cleanup(db_session,board,work,tmp_path,monkeypatch):
    row=reviewed(db_session,board,work)
    source,custody=roots(tmp_path)
    original=rea.os.read
    mutated=False
    def change(fd,count):
        nonlocal mutated
        chunk=original(fd,count)
        if chunk and not mutated:
            mutated=True
            (source/"input").write_bytes(b"changed!")
        return chunk
    monkeypatch.setattr(rea.os,"read",change)
    with pytest.raises(InvalidTransition):
        rea.stage_rea_artifact_custody(db_session,board,decision_id=row.id,source_root=source,source_relative="input",custody_root=custody)
    assert not list(custody.iterdir())


def test_staged_symlink_and_wrong_root_deny(db_session,board,work,tmp_path):
    row=reviewed(db_session,board,work)
    source,custody=roots(tmp_path)
    receipt=rea.stage_rea_artifact_custody(db_session,board,decision_id=row.id,source_root=source,source_relative="input",custody_root=custody)
    other=tmp_path/"other"
    other.mkdir(mode=0o700)
    with pytest.raises(InvalidTransition):
        rea.revalidate_rea_artifact_custody(db_session,board,receipt_id=receipt,decision_id=row.id,custody_root=other)
    staged=custody/str(receipt)/"artifact"
    staged.unlink()
    staged.symlink_to(source/"input")
    with pytest.raises(InvalidTransition):
        rea.revalidate_rea_artifact_custody(db_session,board,receipt_id=receipt,decision_id=row.id,custody_root=custody)


def test_lone_surrogate_input_rejected(work):
    with pytest.raises(ValidationError):
        payload(work, purpose="\ud800")
    request = payload(work).model_dump()
    request["decision_key"] = "\ud800"
    with pytest.raises(ValidationError):
        ReaArtifactProposal.model_validate(request)
