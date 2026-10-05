from dataclasses import replace
from datetime import datetime, timedelta
import hashlib
import json
import os
from uuid import UUID, uuid4

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from pydantic import ValidationError
from sqlmodel import select

from app.models.domain import AuditLog, OrganizationPosition, OrganizationalWorkItem, now_utc
from app.schemas_organization_rea_artifacts import ReaArtifactProposal
from app.schemas_organization_rea_admission import ReaProviderProposal, ReaWorkerObservation
from app.services.organization_command import OrganizationCommandContext, InvalidTransition, AuthorityDenied, canonical_json, canonical_fingerprint
from app.services.organization_decision import record_executive_decision_outcome
from app.services.organization_governance import _claim_work_execution
from app.services.organization_rea_catalog import discover_rea_tools, ADVERTISED_FIELDS
from app.services import organization_rea_artifacts as artifact, organization_rea_admission as admission


@pytest.fixture
def board():
    return OrganizationCommandContext(tenant_key="default", actor_id="reviewer", authenticated_user_id="reviewer", actor_type="human", role="admin", position_key="board")


def approve(session, board, row):
    return record_executive_decision_outcome(session, board, decision_id=row.id, outcome="approved", reason="Reviewed")


def tool_matrix():
    result=[]
    for descriptor in discover_rea_tools():
        effects=[k for k,v in descriptor.contract()["effects"].items() if v and k!="idempotent"]
        result.append(dict(tool_id=descriptor.tool_id, disposition="candidate",provider="reviewed-provider",provider_version="1",effects=effects or ["no_declared_hazards"],review_reference="independent provider review"))
    return result


def build_setup(db_session, board, tmp_path):
    position=OrganizationPosition(position_key="engineer",title="Engineer",department="engineering",authority_level="L1")
    work=OrganizationalWorkItem(idempotency_key="admission-work",title="Investigate",objective="Behavioral analysis",department="engineering",authority_level="L1",assigned_position_key="engineer")
    db_session.add(position);db_session.add(work);db_session.commit()
    expiry=now_utc()+timedelta(days=1)
    artifact_request=ReaArtifactProposal(decision_key="artifact",work_item_id=work.id,scope=dict(artifact_sha256=hashlib.sha256(b"artifact").hexdigest(),artifact_bytes=8,source_reference="source",provenance="provenance",custodian_reference="custodian",rights_reference="review",purpose="interoperability",reconstruction_scope="behavior",exact_tools=[t.tool_id for t in discover_rea_tools()],expires_at=expiry))
    art=approve(db_session,board,artifact.propose_rea_artifact(db_session,board,artifact_request))
    source=tmp_path/"source";source.mkdir();(source/"target").write_bytes(b"artifact")
    custody=tmp_path/"custody";custody.mkdir(mode=0o700)
    receipt=artifact.stage_rea_artifact_custody(db_session,board,decision_id=art.id,source_root=source,source_relative="target",custody_root=custody)
    build=tmp_path/"build";build.mkdir();(build/"bundle").write_bytes(b"reviewed build");(build/"bundle").chmod(0o400)
    private=Ed25519PrivateKey.generate();public=private.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)
    scope=dict(build_sha256=hashlib.sha256(b"reviewed build").hexdigest(),build_bytes=14,build_review_reference="immutable bundle review",publisher_review_reference="publisher reference reviewed",worker_id="isolated-worker",worker_public_key_hex=public.hex(),isolation_policy_sha256="1"*64,isolation_review_reference="deployment policy",platform="linux",server_name="rea",server_version="3.2.1",protocol_version="2025-03-26",tools=tool_matrix(),expires_at=expiry-timedelta(minutes=1))
    request=ReaProviderProposal(decision_key="provider",artifact_decision_id=art.id,scope=scope)
    row=approve(db_session,board,admission.propose_rea_provider_review(db_session,board,request))
    trust=admission.ReaDeploymentTrust(build_root=build,build_relative="bundle",worker_id=scope["worker_id"],worker_public_key=public,isolation_policy_sha256=scope["isolation_policy_sha256"],custody_root=custody)
    work,attempt=_claim_work_execution(db_session,work.id,actor="worker")
    return dict(work=work,attempt=attempt,artifact=art,row=row,receipt=receipt,private=private,trust=trust,request=request)


@pytest.fixture
def setup(db_session,board,tmp_path):
    return build_setup(db_session,board,tmp_path)


def challenge(session, board, setup):
    return admission.issue_rea_worker_challenge(session,board,decision_id=setup["row"].id,attempt_id=setup["attempt"].id,receipt_id=setup["receipt"],trust=setup["trust"])


def observation(setup, ch, **changes):
    tools=canonical_json({"tools":[{k:v for k,v in t.contract().items() if k in ADVERTISED_FIELDS} for t in discover_rea_tools()]}).encode()
    scope=setup["request"].scope
    reported={k:getattr(scope,k) for k in ("worker_id","build_sha256","package_name","package_version","server_name","server_version","protocol_version","platform","isolation_policy_sha256")}
    reported.update(session_id=ch["session_id"],provider_matrix_sha256=canonical_fingerprint(scope.model_dump(mode="json")["tools"]))
    reported.update(changes)
    signed=dict(challenge=ch,reported=reported,tools_observation_sha256=hashlib.sha256(tools).hexdigest())
    return ReaWorkerObservation(**signed,signature_hex=setup["private"].sign(canonical_json(signed).encode()).hex()),tools


def consume(session,board,setup,ch,obs=None,tools=None):
    if obs is None:obs,tools=observation(setup,ch)
    return admission.consume_rea_worker_observation(session,board,challenge_id=UUID(ch["challenge_id"]),observation=obs,tools_observation=tools,trust=setup["trust"])


def test_full_review_build_worker_statement_single_use(db_session,board,setup):
    assert admission.propose_rea_provider_review(db_session,board,setup["request"]).id==setup["row"].id
    before=setup["work"].updated_at
    ch=challenge(db_session,board,setup)
    result=consume(db_session,board,setup,ch)
    assert result["reviewed_build_bytes_verified"] and result["worker_signature_verified"]
    assert not any(result[k] for k in ("live_transport_owned","provider_ready","isolation_verified","execution_authorized"))
    db_session.refresh(setup["work"]);assert setup["work"].updated_at==before
    with pytest.raises(InvalidTransition):consume(db_session,board,setup,ch)


@pytest.mark.parametrize("field,value",[("worker_id","other"),("worker_public_key",b"0"*32),("isolation_policy_sha256","0"*64)])
def test_independent_deployment_anchor(db_session,board,setup,field,value):
    with pytest.raises(AuthorityDenied):admission.resolve_rea_provider_review(db_session,board,decision_id=setup["row"].id,trust=replace(setup["trust"],**{field:value}))


@pytest.mark.parametrize("field,value",[("worker_id","different"),("build_sha256","0"*64),("protocol_version","wrong"),("platform","macos"),("session_id",str(uuid4())),("isolation_policy_sha256","0"*64),("provider_matrix_sha256","0"*64)])
def test_signed_reported_drift(db_session,board,setup,field,value):
    ch=challenge(db_session,board,setup);obs,tools=observation(setup,ch,**{field:value})
    with pytest.raises(InvalidTransition):consume(db_session,board,setup,ch,obs,tools)
    assert not db_session.exec(select(AuditLog).where(AuditLog.action==admission.CONSUME)).all()


def test_wrong_signer_and_catalog(db_session,board,setup):
    ch=challenge(db_session,board,setup);obs,tools=observation(setup,ch)
    with pytest.raises(AuthorityDenied):consume(db_session,board,setup,ch,obs.model_copy(update={"signature_hex":"0"*128}),tools)
    with pytest.raises(InvalidTransition):consume(db_session,board,setup,ch,obs,b'{"tools":[]}')


@pytest.mark.parametrize("mode",["writable","tampered","symlink","traversal"])
def test_unsafe_build_denied(db_session,board,setup,mode):
    path=setup["trust"].build_root/"bundle"
    if mode=="writable":path.chmod(0o600)
    elif mode=="tampered":path.chmod(0o600);path.write_bytes(b"bad build data");path.chmod(0o400)
    elif mode=="symlink":path.unlink();path.symlink_to("missing")
    else:setup["trust"]=replace(setup["trust"],build_relative="../build/bundle")
    with pytest.raises(InvalidTransition):challenge(db_session,board,setup)


@pytest.mark.parametrize("field,value",[("status","completed"),("execution_token","changed"),("execution_attempts",2),("cancel_requested_at",now_utc()),("objective","changed")])
def test_stale_work_challenge_denial(db_session,board,setup,field,value):
    ch=challenge(db_session,board,setup)
    setattr(setup["work"],field,value);db_session.add(setup["work"]);db_session.commit()
    with pytest.raises(InvalidTransition):consume(db_session,board,setup,ch)


@pytest.mark.parametrize("action",[admission.PROPOSE,"organization.decision.approved","organization_work_execution_started"])
def test_missing_lineage_denies(db_session,board,setup,action):
    logs=db_session.exec(select(AuditLog).where(AuditLog.action==action)).all()
    for log in logs:db_session.delete(log)
    db_session.commit()
    with pytest.raises(InvalidTransition):challenge(db_session,board,setup)


def test_expiry_and_original_challenge_change(db_session,board,setup,monkeypatch):
    ch=challenge(db_session,board,setup)
    monkeypatch.setattr(admission,"now_utc",lambda:now_utc()+timedelta(minutes=6))
    with pytest.raises(InvalidTransition):consume(db_session,board,setup,ch)


@pytest.mark.parametrize("mutation",["partial","duplicate","unsupported","effect_omission","wildcard","key_bad","extra","naive"])
def test_strict_review_schema(setup,mutation):
    data=setup["request"].model_dump(mode="json")
    if mutation=="partial":data["scope"]["tools"].pop()
    elif mutation=="duplicate":data["scope"]["tools"][1]=data["scope"]["tools"][0]
    elif mutation=="unsupported":data["scope"]["tools"][0]["disposition"]="supported"
    elif mutation=="effect_omission":data["scope"]["tools"][0]["effects"]=["no_declared_hazards"]
    elif mutation=="wildcard":data["scope"]["tools"][0]["tool_id"]="*"
    elif mutation=="key_bad":data["scope"]["worker_public_key_hex"]="bad"
    elif mutation=="extra":data["scope"]["private_key"]="forbidden"
    else:data["scope"]["expires_at"]="2026-10-06T00:00:00"
    with pytest.raises(ValidationError):ReaProviderProposal.model_validate(data)


def test_aggregate_bounds_before_creation(db_session,board,setup):
    data=setup["request"].model_dump(mode="json");data["decision_key"]="oversize"
    for entry in data["scope"]["tools"]:entry["review_reference"]="界"*2000
    from app.models.domain import ExecutiveDecision
    with pytest.raises(InvalidTransition):admission.propose_rea_provider_review(db_session,board,ReaProviderProposal.model_validate(data))
    assert db_session.exec(select(ExecutiveDecision).where(ExecutiveDecision.decision_key=="oversize")).first() is None


def test_unicode_review_roundtrip(db_session,board,setup):
    data=setup["request"].model_dump(mode="json");data["decision_key"]="unicode"
    for entry in data["scope"]["tools"]:entry["review_reference"]="確認"*15
    row=approve(db_session,board,admission.propose_rea_provider_review(db_session,board,ReaProviderProposal.model_validate(data)))
    assert admission.resolve_rea_provider_review(db_session,board,decision_id=row.id,trust=setup["trust"])[0].id==row.id


def test_challenge_numeric_type_substitution(db_session,board,setup):
    ch=challenge(db_session,board,setup);ch=dict(ch,attempt_number=True)
    obs,tools=observation(setup,ch)
    with pytest.raises(InvalidTransition):consume(db_session,board,setup,ch,obs,tools)


def test_malformed_start_audit(db_session,board,setup):
    log=db_session.exec(select(AuditLog).where(AuditLog.action=="organization_work_execution_started")).one()
    log.after_state_json="[]";db_session.add(log);db_session.commit()
    with pytest.raises(InvalidTransition):challenge(db_session,board,setup)


def test_two_session_single_use_file_sqlite_or_postgres(db_session,board,tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from sqlmodel import Session, SQLModel, create_engine
    external=bool(os.getenv("GMAI_TEST_DATABASE_URL"))
    engine=db_session.get_bind() if external else create_engine("sqlite:///"+str(tmp_path/"race.sqlite"),connect_args={"check_same_thread":False,"timeout":3})
    if not external:SQLModel.metadata.create_all(engine)
    try:
        with Session(engine) as initial:
            state=build_setup(initial,board,tmp_path)
            ch=challenge(initial,board,state);obs,tools=observation(state,ch)
            # Materialize model IDs before dropping the builder transaction.
            for key in ("work","attempt","artifact","row"):state[key].id
            initial.rollback()
            sync=Barrier(2)
            def call():
                with Session(engine) as independent:
                    sync.wait(timeout=10)
                    try:
                        consume(independent,board,state,ch,obs,tools)
                        return True
                    except InvalidTransition:
                        return False
            with ThreadPoolExecutor(max_workers=2) as pool:
                results=list(pool.map(lambda _:call(),range(2)))
            assert sorted(results)==[False,True]
            with Session(engine) as verify:
                assert len(verify.exec(select(AuditLog).where(AuditLog.action==admission.CONSUME)).all())==1
    finally:
        if not external:SQLModel.metadata.drop_all(engine);engine.dispose()


def test_provider_proposal_http_auth_and_generic_approval(client,db_session,board,setup):
    data=setup["request"].model_dump(mode="json");data["decision_key"]="http-provider"
    path="/api/v1/organization/engineering/rea/provider-proposals"
    for role in ("operator","reviewer","read_only"):
        response=client.post(path,json=data,headers={"X-GMAI-Role":role,"X-GMAI-User":"reviewer","x-actor-type":"human","x-position":"board"})
        assert response.status_code==403
    response=client.post(path,json=data,headers={"X-GMAI-Role":"admin","X-GMAI-User":"reviewer"})
    assert response.status_code==201,response.text
    row_id=response.json()["id"]
    response=client.post(f"/api/v1/organization/decisions/records/{row_id}/outcome",json={"outcome":"approved","reason":"Reviewed"},headers={"X-GMAI-Role":"admin","X-GMAI-User":"reviewer"})
    assert response.status_code==200,response.text
    assert admission.resolve_rea_provider_review(db_session,board,decision_id=UUID(row_id),trust=setup["trust"])[0].id==UUID(row_id)


@pytest.mark.parametrize("raw",[b'{"challenge":{},"challenge":{}}',b'{"challenge":NaN}',b'\xff',b"[]",b"{"*600000])
def test_raw_statement_json_bounds(raw):
    with pytest.raises(InvalidTransition):admission.parse_rea_worker_observation(raw)


def test_api_duplicate_raw_and_forbidden_identity(client,setup):
    path="/api/v1/organization/engineering/rea/provider-proposals"
    response=client.post(path,content=b'{"decision_key":"one","decision_key":"two"}',headers={"Content-Type":"application/json"})
    assert response.status_code==422
    data=setup["request"].model_dump(mode="json");data["tenant_key"]="other"
    assert client.post(path,json=data).status_code==422


@pytest.mark.parametrize("field,value",[("worker_public_key_hex","A"*64),("build_bytes",True),("protocol_version",2),("publisher_review_reference","\x00"),("build_review_reference","\ud800"),("server_name","other"),("server_version","4")])
def test_strict_identity_inputs(setup,field,value):
    data=setup["request"].model_dump(mode="json");data["scope"][field]=value
    with pytest.raises(ValidationError):ReaProviderProposal.model_validate(data)


@pytest.mark.parametrize("field,value",[("source_object_version","0"*64),("status","rejected"),("decision_reason","tampered")])
def test_provider_canonical_mutation_denied(db_session,board,setup,field,value):
    setattr(setup["row"],field,value);db_session.add(setup["row"]);db_session.commit()
    with pytest.raises(InvalidTransition):challenge(db_session,board,setup)


def test_provider_successor_blocks_and_pending_denied(db_session,board,setup):
    data=setup["request"].model_dump(mode="json");data["decision_key"]="replacement";data["supersedes_decision_id"]=str(setup["row"].id)
    successor=admission.propose_rea_provider_review(db_session,board,ReaProviderProposal.model_validate(data))
    with pytest.raises(InvalidTransition):challenge(db_session,board,setup)
    with pytest.raises(InvalidTransition):admission.resolve_rea_provider_review(db_session,board,decision_id=successor.id,trust=setup["trust"])


def test_proposal_context_and_wrong_tenant(db_session,board,setup):
    from dataclasses import replace
    from app.services.organization_command import TenantMismatch
    with pytest.raises(AuthorityDenied):admission.propose_rea_provider_review(db_session,replace(board,actor_type="agent"),setup["request"])
    with pytest.raises(TenantMismatch):admission.resolve_rea_provider_review(db_session,replace(board,tenant_key="other"),decision_id=setup["row"].id,trust=setup["trust"])


def test_consumption_audit_failure_rolls_back(db_session,board,setup,monkeypatch):
    ch=challenge(db_session,board,setup)
    original=admission.record_audit
    def fail(*args,**kwargs):
        if kwargs["action"]==admission.CONSUME:raise RuntimeError("audit write failed")
        return original(*args,**kwargs)
    monkeypatch.setattr(admission,"record_audit",fail)
    with pytest.raises(RuntimeError,match="audit write failed"):consume(db_session,board,setup,ch)
    monkeypatch.setattr(admission,"record_audit",original)
    assert consume(db_session,board,setup,ch)["worker_signature_verified"]


@pytest.mark.parametrize("change",[{"kind":"other"},{"unknown":True},{"nonce":"00 "*32},{"issued_at":"2000-01-01T00:00:00+00:00"}])
def test_corrupt_persisted_challenge_envelope(db_session,board,setup,change):
    ch=challenge(db_session,board,setup);ch.update(change)
    log=db_session.exec(select(AuditLog).where(AuditLog.action==admission.CHALLENGE)).one()
    log.after_state_json=json.dumps(ch);db_session.add(log);db_session.commit()
    obs,tools=observation(setup,ch)
    with pytest.raises(InvalidTransition):consume(db_session,board,setup,ch,obs,tools)


@pytest.mark.parametrize("stage",["catalog","audit"])
def test_expiry_during_verification_or_witness_leaves_nonce_unconsumed(db_session,board,setup,monkeypatch,stage):
    ch=challenge(db_session,board,setup)
    obs,tools=observation(setup,ch)
    expired=datetime.fromisoformat(ch["expires_at"])
    if stage=="catalog":
        original=admission.compare_rea_tools_observation
        def delayed_catalog(raw):
            result=original(raw)
            monkeypatch.setattr(admission,"now_utc",lambda:expired)
            return result
        monkeypatch.setattr(admission,"compare_rea_tools_observation",delayed_catalog)
    else:
        original=admission.record_audit
        def delayed_audit(*args,**kwargs):
            result=original(*args,**kwargs)
            if kwargs["action"]==admission.CONSUME:
                monkeypatch.setattr(admission,"now_utc",lambda:expired)
            return result
        monkeypatch.setattr(admission,"record_audit",delayed_audit)
    with pytest.raises(InvalidTransition,match="expired before consumption"):
        consume(db_session,board,setup,ch,obs,tools)
    assert not db_session.exec(select(AuditLog).where(AuditLog.action==admission.CONSUME)).all()
