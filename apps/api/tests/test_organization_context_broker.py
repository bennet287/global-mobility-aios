from __future__ import annotations

from dataclasses import fields
from datetime import timedelta
from uuid import uuid4

import pytest
from sqlmodel import Session

from app.models.domain import OrganizationPosition, OrganizationalWorkItem, now_utc
from app.services.organization_command import TenantMismatch, canonical_json
from app.services.organization_context_broker import (
    CONTEXT_BUNDLE_SCHEMA_VERSION,
    ContextBundle,
    ContextIdentityUnavailable,
    ContextIntegrityError,
    ContextPurpose,
    ContextScopeDenied,
    build_work_item_context_bundle,
)


def _position(
    session: Session,
    *,
    position_key: str = "mobility_operations_lead",
    status: str = "active",
    contract_json: str = "{}",
) -> OrganizationPosition:
    row = OrganizationPosition(
        position_key=position_key,
        title="Global Mobility Operations Lead",
        department="Operations",
        reports_to_position_key="coo",
        role_card_name="mobility_operations_lead",
        authority_level="L2",
        contract_json=contract_json,
        status=status,
        version=3,
        created_by="pytest",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _work(
    session: Session,
    *,
    tenant_key: str = "tenant-a",
    assigned_position_key: str = "mobility_operations_lead",
    context_json: str = "{}",
    source_object_type: str | None = None,
    source_object_id: str | None = None,
    source_object_version: str | None = None,
) -> OrganizationalWorkItem:
    row = OrganizationalWorkItem(
        idempotency_key=f"context-work-{uuid4()}",
        tenant_key=tenant_key,
        title="Assess mobility case readiness",
        objective="Prepare bounded case context for the assigned employee.",
        department="Operations",
        authority_level="L2",
        assigned_position_key=assigned_position_key,
        risk_level="routine",
        context_json=context_json,
        source_object_type=source_object_type,
        source_object_id=source_object_id,
        source_object_version=source_object_version,
        created_by="pytest",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def test_builds_deterministic_provider_neutral_context_bundle(db_session: Session) -> None:
    _position(db_session, contract_json='{"can_delegate":false,"scope":"case"}')
    work = _work(
        db_session,
        context_json='{"country":"Austria","question":"readiness"}',
        source_object_type="mobility_case",
        source_object_id="case-123",
        source_object_version="v7",
    )

    first = build_work_item_context_bundle(
        db_session,
        tenant_key="tenant-a",
        position_key="mobility_operations_lead",
        work_item_id=work.id,
    )
    second = build_work_item_context_bundle(
        db_session,
        tenant_key="tenant-a",
        position_key="mobility_operations_lead",
        work_item_id=work.id,
    )

    assert first.schema_version == CONTEXT_BUNDLE_SCHEMA_VERSION
    assert first.purpose is ContextPurpose.WORK_EXECUTION
    assert first.position.position_key == "mobility_operations_lead"
    assert first.position.position_version == 3
    assert first.position.contract_json == '{"can_delegate":false,"scope":"case"}'
    assert first.work_item.working_context_json == '{"country":"Austria","question":"readiness"}'
    assert first.context_hash == second.context_hash
    assert first.generated_at <= second.generated_at
    assert first.canonical_references[-1].kind == "mobility_case"
    assert first.canonical_references[-1].identifier == "case-123"
    assert first.canonical_references[-1].version == "v7"

    field_names = {item.name for item in fields(ContextBundle)}
    assert "provider" not in field_names
    assert "model" not in field_names
    assert "session_id" not in field_names
    assert "runtime_id" not in field_names


def test_context_hash_changes_when_canonical_work_context_changes(db_session: Session) -> None:
    _position(db_session)
    work = _work(db_session, context_json='{"stage":"initial"}')
    first = build_work_item_context_bundle(
        db_session,
        tenant_key="tenant-a",
        position_key="mobility_operations_lead",
        work_item_id=work.id,
    )

    work.context_json = canonical_json({"stage": "updated"})
    work.updated_at = now_utc() + timedelta(seconds=1)
    db_session.add(work)
    db_session.commit()

    second = build_work_item_context_bundle(
        db_session,
        tenant_key="tenant-a",
        position_key="mobility_operations_lead",
        work_item_id=work.id,
    )
    assert first.context_hash != second.context_hash
    assert second.work_item.working_context_json == '{"stage":"updated"}'


def test_inactive_position_fails_closed(db_session: Session) -> None:
    _position(db_session, status="suspended")
    work = _work(db_session)

    with pytest.raises(ContextIdentityUnavailable):
        build_work_item_context_bundle(
            db_session,
            tenant_key="tenant-a",
            position_key="mobility_operations_lead",
            work_item_id=work.id,
        )


def test_tenant_mismatch_remains_non_disclosing_command_boundary(db_session: Session) -> None:
    _position(db_session)
    work = _work(db_session, tenant_key="tenant-b")

    with pytest.raises(TenantMismatch):
        build_work_item_context_bundle(
            db_session,
            tenant_key="tenant-a",
            position_key="mobility_operations_lead",
            work_item_id=work.id,
        )


def test_assignment_scope_mismatch_fails_closed(db_session: Session) -> None:
    _position(db_session)
    work = _work(db_session, assigned_position_key="case_operations_specialist")

    with pytest.raises(ContextScopeDenied):
        build_work_item_context_bundle(
            db_session,
            tenant_key="tenant-a",
            position_key="mobility_operations_lead",
            work_item_id=work.id,
        )


def test_malformed_working_context_fails_closed(db_session: Session) -> None:
    _position(db_session)
    work = _work(db_session, context_json="{not-json")

    with pytest.raises(ContextIntegrityError):
        build_work_item_context_bundle(
            db_session,
            tenant_key="tenant-a",
            position_key="mobility_operations_lead",
            work_item_id=work.id,
        )


def test_working_context_cannot_promote_itself_to_evidence_tools_or_runtime_authority(
    db_session: Session,
) -> None:
    _position(db_session)
    work = _work(
        db_session,
        context_json=canonical_json(
            {
                "evidence_refs": ["self-declared-evidence"],
                "verified_rule_refs": ["self-declared-rule"],
                "allowed_tools": ["shell", "browser"],
                "provider": "self-selected-provider",
                "model": "self-selected-model",
            }
        ),
    )

    bundle = build_work_item_context_bundle(
        db_session,
        tenant_key="tenant-a",
        position_key="mobility_operations_lead",
        work_item_id=work.id,
        purpose=ContextPurpose.RESEARCH,
    )

    assert bundle.evidence_refs == ()
    assert bundle.verified_rule_refs == ()
    assert bundle.source_snapshot_refs == ()
    assert bundle.allowed_tools == ()
    assert bundle.policy_version is None
    # The values remain visible only as untrusted working context. They are not
    # promoted into authority-bearing ContextBundle fields.
    assert "self-declared-evidence" in bundle.work_item.working_context_json
    assert "self-selected-provider" in bundle.work_item.working_context_json


def test_malformed_position_contract_and_incomplete_source_reference_fail_closed(
    db_session: Session,
) -> None:
    position = _position(db_session, contract_json="[not-an-object]")
    work = _work(db_session)
    with pytest.raises(ContextIntegrityError):
        build_work_item_context_bundle(
            db_session,
            tenant_key="tenant-a",
            position_key=position.position_key,
            work_item_id=work.id,
        )

    position.contract_json = "{}"
    db_session.add(position)
    db_session.commit()
    work.source_object_type = "mobility_case"
    work.source_object_id = None
    db_session.add(work)
    db_session.commit()

    with pytest.raises(ContextIntegrityError):
        build_work_item_context_bundle(
            db_session,
            tenant_key="tenant-a",
            position_key=position.position_key,
            work_item_id=work.id,
        )
