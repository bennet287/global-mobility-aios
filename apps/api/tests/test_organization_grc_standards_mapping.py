from __future__ import annotations
from uuid import uuid4
import pytest
from sqlmodel import Session, select

from app.models.domain import OrganizationControl, OrganizationRecordReference, OrganizationReferenceRole, OrganizationReferenceTargetType, OrganizationalWorkItem, OfficialSource
from app.models.organization_standards_mapping import OrganizationStandardsMapping
from app.services.organization_grc_standards_mapping import create_standards_mapping, project_standards_mappings
from app.services.organization_command import InvalidReference, NotFound
from tests.test_organization_autonomy_promotion_policy import _board_context, _position, _profile, _policy

def _evidence(session: Session, *, tenant="default") -> OrganizationRecordReference:
    work = OrganizationalWorkItem(
        idempotency_key=f"18f-work-{uuid4()}", tenant_key=tenant, work_type="organizational",
        objective_key="18f-evidence", phase_key="18F", title="Standards evidence",
        objective="Concrete AIOS implementation evidence.", department="Security",
        authority_level="L4", assigned_position_key="board", risk_level="high",
    )
    session.add(work); session.flush()
    source = OfficialSource(country="AT", domain="governance", name="AIOS implementation evidence", url=f"https://example.invalid/{uuid4()}")
    session.add(source); session.flush()
    row = OrganizationRecordReference(
        reference_key=f"18f:evidence:{uuid4()}", record_fingerprint="e"*64, tenant_key=tenant,
        work_item_id=work.id, reference_role=OrganizationReferenceRole.evidence,
        target_type=OrganizationReferenceTargetType.official_source, target_id=str(source.id),
        label="Concrete implementation evidence", created_by="pytest",
    )
    session.add(row); session.commit(); session.refresh(row)
    return row

def _control(session: Session) -> OrganizationControl:
    row = OrganizationControl(control_key="global", status="active", reason="Governed global pause control", changed_by="pytest")
    session.add(row); session.commit(); session.refresh(row)
    return row

def _payload(control, evidence, *, key="18f:test", state="current", supersedes=None):
    return dict(
        mapping_key=key, target_type="organization_control", target_id=control.id,
        framework_key="example-framework", framework_version="2026",
        requirement_id="CTRL-1", source_reference="publisher:example-framework:2026:CTRL-1",
        justification="Declared traceability to concrete AIOS implementation evidence; no compliance conclusion.",
        evidence_reference_ids=[evidence.id], mapping_state=state, supersedes_mapping_id=supersedes,
    )

def test_standards_mapping_api_is_admin_only_and_explicitly_non_certifying(client, db_session: Session):
    control, evidence = _control(db_session), _evidence(db_session)
    payload = {**_payload(control,evidence), "target_id":str(control.id), "evidence_reference_ids":[str(evidence.id)]}
    denied = client.post("/api/v1/organization/grc/standards-mappings",json=payload,headers={"X-GMAI-Role":"operator","X-GMAI-User":"operator"})
    assert denied.status_code == 403
    created = client.post("/api/v1/organization/grc/standards-mappings",json=payload)
    assert created.status_code == 201, created.text
    body=created.json()
    assert body["traceability_conclusion"] == "declared_mapping_only"
    assert any("does not establish certification" in item for item in body["limitations"])
    assert created.headers["cache-control"] == "no-store"
    replay=client.post("/api/v1/organization/grc/standards-mappings",json=payload)
    assert replay.status_code == 201 and replay.json()["id"] == body["id"]
    assert len(db_session.exec(select(OrganizationStandardsMapping)).all()) == 1
    denied_read = client.get("/api/v1/organization/grc/standards-mappings", headers={"X-GMAI-Role": "operator", "X-GMAI-User": "operator"})
    assert denied_read.status_code == 403

def test_mapping_requires_real_tenant_evidence_role(db_session: Session):
    board=_board_context(); control=_control(db_session); evidence=_evidence(db_session)
    evidence.reference_role=OrganizationReferenceRole.supports; db_session.add(evidence); db_session.commit()
    import pytest
    from app.services.organization_command import InvalidReference, NotFound
    with pytest.raises(InvalidReference,match="must use evidence"):
        create_standards_mapping(db_session,board,**_payload(control,evidence))
    other=_evidence(db_session,tenant="other")
    with pytest.raises(NotFound):
        create_standards_mapping(db_session,board,**_payload(control,other,key="18f:cross"))

def test_mapping_withdrawal_and_control_drift_fail_closed(db_session: Session):
    board=_board_context(); control=_control(db_session); evidence=_evidence(db_session)
    first=create_standards_mapping(db_session,board,**_payload(control,evidence))
    assert [row.id for row in project_standards_mappings(db_session,board)] == [first.id]
    withdrawn=create_standards_mapping(db_session,board,**_payload(control,evidence,key="18f:withdrawn",state="withdrawn",supersedes=first.id))
    assert withdrawn.supersedes_mapping_id == first.id
    assert project_standards_mappings(db_session,board) == ()
    control.reason="Changed authoritative control state"; db_session.add(control); db_session.commit()
    assert project_standards_mappings(db_session,board) == ()

def test_mapping_absence_is_empty_not_noncompliance(db_session: Session):
    assert project_standards_mappings(db_session,_board_context()) == ()


def _policy_target(session: Session):
    board = _board_context()
    _position(session)
    _profile(session, board)
    return _policy(session, board, key="18f-v1")


@pytest.mark.parametrize("transition", ["paused", "deleted"])
def test_stale_global_control_is_omitted_without_hiding_valid_policy_mapping(db_session: Session, transition):
    board = _board_context()
    control, evidence = _control(db_session), _evidence(db_session)
    policy = _policy_target(db_session)
    stale_payload = _payload(control, evidence, key="18f:stale-control")
    create_standards_mapping(db_session, board, **stale_payload)
    valid = create_standards_mapping(db_session, board, **{
        **_payload(policy, evidence, key="18f:valid-policy"),
        "target_type": "capability_autonomy_promotion_policy",
    })
    if transition == "deleted":
        db_session.delete(control)
    else:
        control.status = "paused"
        db_session.add(control)
    db_session.commit()

    assert [row.id for row in project_standards_mappings(db_session, board)] == [valid.id]
    with pytest.raises(InvalidReference, match="active global organization control"):
        create_standards_mapping(db_session, board, **{**stale_payload, "mapping_key": "18f:denied"})


def test_superseded_policy_is_omitted_without_hiding_valid_control_mapping(db_session: Session):
    board = _board_context()
    control, evidence = _control(db_session), _evidence(db_session)
    policy = _policy_target(db_session)
    stale_payload = {
        **_payload(policy, evidence, key="18f:stale-policy"),
        "target_type": "capability_autonomy_promotion_policy",
    }
    create_standards_mapping(db_session, board, **stale_payload)
    valid = create_standards_mapping(db_session, board, **_payload(control, evidence, key="18f:valid-control"))
    _policy(db_session, board, key="18f-v2", expected_policy_sequence=1)

    assert [row.id for row in project_standards_mappings(db_session, board)] == [valid.id]
    with pytest.raises(InvalidReference, match="superseded"):
        create_standards_mapping(db_session, board, **{**stale_payload, "mapping_key": "18f:denied"})


def test_other_tenant_cannot_create_global_control_mapping(db_session: Session):
    control, evidence = _control(db_session), _evidence(db_session, tenant="other")
    with pytest.raises(NotFound, match="not available to this tenant"):
        create_standards_mapping(db_session, _board_context("other"), **_payload(control, evidence))


def test_unavailable_tenant_target_is_omitted_and_creation_stays_strict(db_session: Session):
    board = _board_context()
    policy, evidence = _policy_target(db_session), _evidence(db_session)
    payload = {
        **_payload(policy, evidence),
        "target_type": "capability_autonomy_promotion_policy",
    }
    mapping = create_standards_mapping(db_session, board, **payload)
    # Model a stored mapping whose target is no longer available in its scope.
    # The projection must not resolve the policy through the other tenant.
    mapping.tenant_key = "other"
    db_session.add(mapping)
    db_session.commit()
    assert project_standards_mappings(db_session, _board_context("other")) == ()
    other_evidence = _evidence(db_session, tenant="other")
    with pytest.raises(NotFound):
        create_standards_mapping(db_session, _board_context("other"), **{
            **payload, "mapping_key": "18f:cross-target", "evidence_reference_ids": [other_evidence.id],
        })


def test_projection_does_not_hide_unknown_target_integrity_errors(db_session: Session, monkeypatch):
    board = _board_context()
    control, evidence = _control(db_session), _evidence(db_session)
    create_standards_mapping(db_session, board, **_payload(control, evidence))
    monkeypatch.setattr("app.services.organization_grc_standards_mapping._TARGETS", {})
    with pytest.raises(InvalidReference, match="not allowlisted"):
        project_standards_mappings(db_session, board)


def test_projection_does_not_hide_unknown_control_status_with_valid_policy_mapping(db_session: Session):
    board = _board_context()
    control, evidence = _control(db_session), _evidence(db_session)
    policy = _policy_target(db_session)
    create_standards_mapping(db_session, board, **_payload(control, evidence, key="18f:corrupt-control"))
    create_standards_mapping(db_session, board, **{
        **_payload(policy, evidence, key="18f:valid-policy"),
        "target_type": "capability_autonomy_promotion_policy",
    })
    control.status = "unknown-corrupt-status"
    db_session.add(control)
    db_session.commit()

    with pytest.raises(InvalidReference, match="unsupported status"):
        project_standards_mappings(db_session, board)
