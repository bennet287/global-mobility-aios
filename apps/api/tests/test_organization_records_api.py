from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, func, select

from app.main import app
from app.models.domain import (
    AuditLog,
    Lead,
    LeadIntent,
    OrganizationActorType,
    OrganizationContribution,
)
from app.routers.organization_records import organization_command_context
from app.services.organization_activity import append_activity
from app.services.organization_command import OrganizationCommandContext
from app.services.organization_work import create_work_item


BASE = "/api/v1/organization"
NOW = datetime(2026, 8, 14, 10, 0, tzinfo=timezone.utc)


def _headers(role: str, user: str = "pytest-user") -> dict[str, str]:
    return {"X-GMAI-Role": role, "X-GMAI-User": user}


def _activity(key: str = "activity-1", **changes: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "activity_key": key,
        "stream_key": "stream-api",
        "activity_class": "operational",
        "activity_type": "api_verified",
        "title": "Verified API activity",
        "summary": "A bounded, authenticated activity command.",
        "source_object_type": "api_test",
        "source_object_id": key,
        "source_object_version": "v1",
        "occurred_at": NOW.isoformat(),
        "correlation_key": "correlation-api",
        "payload": {"safe": True},
    }
    payload.update(changes)
    return payload


def _work(key: str = "work-1", **changes: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "idempotency_key": key,
        "title": "Governed work",
        "objective": "Exercise the durable work lifecycle.",
        "department": "operations",
        "assigned_position_key": "operations_manager",
        "context": {"bounded": True},
    }
    payload.update(changes)
    return payload


def _decision(key: str = "decision-1", decision_type: str = "operational") -> dict[str, object]:
    return {
        "decision_key": key,
        "decision_type": decision_type,
        "title": "Governed decision",
        "question": "Should the validated outcome be accepted?",
        "recommendation": "Accept after human authority review.",
        "evidence": [{"kind": "test_fixture"}],
    }


def _approved_decision(client: TestClient, key: str = "decision-contribution") -> dict[str, object]:
    created = client.post(f"{BASE}/decisions/records", json=_decision(key))
    assert created.status_code == 201, created.text
    decision = created.json()
    outcome = client.post(
        f"{BASE}/decisions/records/{decision['id']}/outcome",
        json={"outcome": "approved", "reason": "Board verified the outcome."},
    )
    assert outcome.status_code == 200, outcome.text
    return outcome.json()


def _contribution(decision: dict[str, object], key: str = "contribution-1", **changes: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "contribution_key": key,
        "source_type": "executive_decision",
        "source_id": decision["id"],
        "source_version": decision["source_version"],
        "outcome_type": "approved_organizational_outcome",
        "verification_basis": "Terminal, human-attributed executive decision.",
        "contribution_type": "delivery",
        "title": "Validated delivery",
        "outcome_summary": "The governed outcome was delivered.",
        "department": "operations",
        "accountable_position_key": "board",
        "impact_kind": "delivery",
        "effective_at": NOW.isoformat(),
        "decision_id": decision["id"],
    }
    payload.update(changes)
    return payload


def _context(
    tenant: str,
    *,
    actor_id: str = "tenant-user",
    actor_type: OrganizationActorType = OrganizationActorType.human,
    role: str = "admin",
) -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key=tenant,
        actor_id=actor_id,
        actor_type=actor_type,
        authenticated_user_id=actor_id,
        role=role,
        department="operations",
        position_key="board" if role == "admin" else "organization_operator",
        authority_level="L4" if role == "admin" else "L2",
        request_id="pytest-request",
    )


def test_authentication_rbac_and_trusted_payload_boundary(raw_client: TestClient) -> None:
    # Matrix 1-7: authentication, reader GET, mutation RBAC, and spoof resistance.
    assert raw_client.get(f"{BASE}/activities").status_code == 401
    assert raw_client.get(f"{BASE}/activities", headers=_headers("read_only")).status_code == 200
    assert raw_client.post(
        f"{BASE}/activities", headers=_headers("read_only"), json=_activity()
    ).status_code == 403

    for field, value in (
        ("actor_id", "forged-human"),
        ("actor_type", "agent"),
        ("authority", "board"),
        ("role", "admin"),
        ("authority_level", "L4"),
        ("tenant_key", "other-tenant"),
    ):
        response = raw_client.post(
            f"{BASE}/activities",
            headers=_headers("operator", "trusted-operator"),
            json=_activity(f"spoof-{field}", **{field: value}),
        )
        assert response.status_code == 422, (field, response.text)


def test_activity_idempotency_actor_lists_filters_and_safe_errors(
    client: TestClient, db_session: Session
) -> None:
    # Matrix 12-16, 53-54, 57: service mutation, replay/conflict and safe output.
    payload = _activity()
    created = client.post(f"{BASE}/activities", json=payload)
    assert created.status_code == 201, created.text
    row = created.json()
    assert row["actor_id"] == "pytest-admin"
    assert row["actor_type"] == "human"

    audit_count = db_session.exec(select(func.count()).select_from(AuditLog)).one()
    replay = client.post(f"{BASE}/activities", json=payload)
    assert replay.status_code == 201
    assert replay.json()["id"] == row["id"]
    assert db_session.exec(select(func.count()).select_from(AuditLog)).one() == audit_count

    conflict = client.post(f"{BASE}/activities", json={**payload, "summary": "Changed semantics"})
    assert conflict.status_code == 409
    assert conflict.json() == {"detail": "Idempotency key conflicts with an existing command."}
    assert "traceback" not in conflict.text.lower()

    detail = client.get(f"{BASE}/activities/{row['id']}")
    listing = client.get(f"{BASE}/activities", params={"correlation_key": "correlation-api"})
    assert detail.status_code == 200
    assert [item["id"] for item in listing.json()["data"]] == [row["id"]]
    missing = client.get(f"{BASE}/activities/{uuid4()}")
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Organization resource not found."}


def test_tenant_isolation_is_non_disclosing_for_detail_mutation_and_filter(
    client: TestClient, db_session: Session
) -> None:
    # Matrix 8-11: every lookup/filter remains bound to authenticated tenant.
    other = _context("tenant-b")
    foreign_activity = append_activity(
        db_session,
        other,
        activity_key="foreign-activity",
        stream_key="foreign-stream",
        activity_class="operational",
        activity_type="foreign",
        title="Foreign activity",
        summary="Must not be disclosed.",
        source_object_type="api_test",
        source_object_id="foreign",
        occurred_at=NOW,
        correlation_key="shared-filter",
    )
    foreign_work = create_work_item(
        db_session,
        other,
        idempotency_key="foreign-work",
        title="Foreign work",
        objective="Tenant isolation",
        department="operations",
        authority_level="L4",
        assigned_position_key="board",
    )

    own = client.post(f"{BASE}/activities", json=_activity("own-activity", correlation_key="shared-filter"))
    assert own.status_code == 201
    assert client.get(f"{BASE}/activities/{own.json()['id']}").status_code == 200
    assert client.get(f"{BASE}/activities/{foreign_activity.id}").status_code == 404
    assert client.post(
        f"{BASE}/work-items/records/{foreign_work.id}/start", json={"reason": "probe"}
    ).status_code == 404
    filtered = client.get(f"{BASE}/activities", params={"correlation_key": "shared-filter"}).json()
    assert filtered["total"] == 1
    assert filtered["data"][0]["id"] == own.json()["id"]


def test_contribution_source_policy_idempotency_and_append_only_correction(
    client: TestClient, db_session: Session
) -> None:
    # Matrix 17-23: narrow source adapter, replay/conflict, append-only corrections.
    decision = _approved_decision(client)
    payload = _contribution(decision)
    created = client.post(f"{BASE}/contributions", json=payload)
    assert created.status_code == 201, created.text
    contribution = created.json()

    audit_count = db_session.exec(select(func.count()).select_from(AuditLog)).one()
    replay = client.post(f"{BASE}/contributions", json=payload)
    assert replay.status_code == 201
    assert replay.json()["id"] == contribution["id"]
    assert db_session.exec(select(func.count()).select_from(AuditLog)).one() == audit_count
    conflict = client.post(f"{BASE}/contributions", json={**payload, "title": "Changed"})
    assert conflict.status_code == 409

    # D4 keeps both the sealed domain adapters and the deferred domain records out of
    # the generic authenticated Contribution command. Real domain emission must continue
    # to enter through its reviewed source-owned adapter rather than request-selected
    # source authority.
    rejected_source_types = (
        "agent_run",
        "workflow_run",
        "audit_log",
        "ui_interaction",
        "jurisdiction_source_certification",
        "initial_rule_assertion",
        "regulatory_change",
        "mobility_pathway_version",
        "jurisdiction_immigration_assessment",
        "reassessment_acceptance",
        "external_validation_run",
        "corporate_compliance_event",
        "mobility_timeline_milestone",
        "agency_submission",
        "authority_appointment",
        "eligibility_assessment",
        "pathway_comparison_assessment",
        "country_ranking_assessment",
        "external_validation_review",
        "external_validation_finding",
        "anything_else",
    )
    for source_type in rejected_source_types:
        rejected = client.post(
            f"{BASE}/contributions",
            json=_contribution(decision, f"rejected-{source_type}", source_type=source_type),
        )
        assert rejected.status_code == 422, (source_type, rejected.text)

    correction_payload = {
        "contribution_key": "contribution-1-retracted",
        "source_type": "executive_decision",
        "source_id": decision["id"],
        "source_version": decision["source_version"],
        "outcome_type": "approved_organizational_outcome",
        "verification_basis": "Human-authorized correction.",
        "record_kind": "retraction",
        "title": "Retracted delivery",
        "outcome_summary": "The prior outcome is retracted without mutation.",
        "effective_at": (NOW + timedelta(minutes=1)).isoformat(),
        "retraction_reason": "Corrected evidence changed the disposition.",
    }
    correction = client.post(
        f"{BASE}/contributions/{contribution['id']}/corrections", json=correction_payload
    )
    assert correction.status_code == 201, correction.text
    assert correction.json()["id"] != contribution["id"]
    assert correction.json()["supersedes_contribution_id"] == contribution["id"]
    original = db_session.get(OrganizationContribution, UUID(contribution["id"]))
    assert original is not None and original.record_kind.value == "outcome"


def test_work_item_lifecycle_is_service_only_and_does_not_emit_contribution(
    client: TestClient, db_session: Session
) -> None:
    # Matrix 24-29 and 55: explicit lifecycle commands, no PATCH bypass/emitter.
    created = client.post(f"{BASE}/work-items/records", json=_work())
    assert created.status_code == 201, created.text
    work_id = created.json()["id"]
    assert client.get(f"{BASE}/work-items/records/{work_id}").status_code == 200
    assert client.get(f"{BASE}/work-items/records").json()["total"] == 1

    premature = client.post(
        f"{BASE}/work-items/records/{work_id}/complete", json={"reason": "Too soon"}
    )
    assert premature.status_code == 409
    assert premature.json() == {"detail": "Organization resource cannot perform that transition."}
    started = client.post(
        f"{BASE}/work-items/records/{work_id}/start", json={"reason": "Authorized start"}
    )
    assert started.status_code == 200 and started.json()["status"] == "running"
    completed = client.post(
        f"{BASE}/work-items/records/{work_id}/complete", json={"reason": "Outcome recorded"}
    )
    assert completed.status_code == 200 and completed.json()["status"] == "completed"
    assert db_session.exec(select(func.count()).select_from(OrganizationContribution)).one() == 0
    assert client.patch(
        f"{BASE}/work-items/records/{work_id}", json={"status": "queued"}
    ).status_code == 405


def test_dependency_commands_and_authority(client: TestClient, raw_client: TestClient) -> None:
    # Matrix 30-34: create/self/cross-tenant are service guarded; waiver is human-admin only.
    first = client.post(f"{BASE}/work-items/records", json=_work("dep-work-1")).json()
    second = client.post(f"{BASE}/work-items/records", json=_work("dep-work-2")).json()
    self_edge = client.post(
        f"{BASE}/work-item-dependencies",
        json={
            "dependency_key": "self-edge",
            "work_item_id": first["id"],
            "depends_on_work_item_id": first["id"],
            "dependency_type": "blocks",
        },
    )
    assert self_edge.status_code == 409
    dependency = client.post(
        f"{BASE}/work-item-dependencies",
        json={
            "dependency_key": "dependency-1",
            "work_item_id": first["id"],
            "depends_on_work_item_id": second["id"],
            "dependency_type": "requires",
        },
    )
    assert dependency.status_code == 201, dependency.text
    denied = raw_client.post(
        f"{BASE}/work-item-dependencies/{dependency.json()['id']}/waive",
        headers=_headers("operator"),
        json={"reason": "Operator cannot waive"},
    )
    assert denied.status_code == 403

    decision = _approved_decision(client, "dependency-decision")
    contribution = client.post(
        f"{BASE}/contributions", json=_contribution(decision, "dependency-contribution")
    ).json()
    satisfied = client.post(
        f"{BASE}/work-item-dependencies/{dependency.json()['id']}/satisfy",
        json={"contribution_id": contribution["id"], "reason": "Authoritative outcome exists"},
    )
    assert satisfied.status_code == 200 and satisfied.json()["status"] == "satisfied"


def test_dependency_rejects_foreign_tenant_target(
    client: TestClient, db_session: Session
) -> None:
    local = client.post(f"{BASE}/work-items/records", json=_work("local-dependency-work")).json()
    foreign = create_work_item(
        db_session,
        _context("tenant-b"),
        idempotency_key="foreign-dependency-work",
        title="Foreign",
        objective="No cross-tenant edges",
        department="operations",
        authority_level="L4",
        assigned_position_key="board",
    )
    response = client.post(
        f"{BASE}/work-item-dependencies",
        json={
            "dependency_key": "foreign-edge",
            "work_item_id": local["id"],
            "depends_on_work_item_id": str(foreign.id),
            "dependency_type": "blocks",
        },
    )
    assert response.status_code == 404


def test_blocker_commands_authority_and_no_delete(client: TestClient, raw_client: TestClient) -> None:
    # Matrix 35-38: open/resolve, admin waiver boundary, and no delete transition.
    work = client.post(f"{BASE}/work-items/records", json=_work("blocker-work")).json()
    payload = {
        "blocker_key": "blocker-1",
        "blocker_type": "dependency",
        "severity": "high",
        "title": "A governed blocker",
        "description": "Requires an explicit resolution command.",
        "work_item_id": work["id"],
    }
    blocker = client.post(f"{BASE}/blockers", json=payload)
    assert blocker.status_code == 201, blocker.text
    assert client.get(f"{BASE}/blockers/{blocker.json()['id']}").status_code == 200
    denied = raw_client.post(
        f"{BASE}/blockers/{blocker.json()['id']}/waive",
        headers=_headers("operator"),
        json={"reason": "Operator waiver"},
    )
    assert denied.status_code == 403
    resolved = client.post(
        f"{BASE}/blockers/{blocker.json()['id']}/resolve",
        json={"reason": "Dependency resolved"},
    )
    assert resolved.status_code == 200 and resolved.json()["status"] == "resolved"
    predecessor = client.post(f"{BASE}/blockers", json={**payload, "blocker_key": "blocker-2"})
    replacement = client.post(
        f"{BASE}/blockers/{predecessor.json()['id']}/supersede",
        json={**payload, "blocker_key": "blocker-2-replacement", "title": "Replacement blocker"},
    )
    assert replacement.status_code == 201
    assert replacement.json()["supersedes_blocker_id"] == predecessor.json()["id"]
    assert client.get(f"{BASE}/blockers/{predecessor.json()['id']}").json()["status"] == "superseded"
    assert client.delete(f"{BASE}/blockers/{blocker.json()['id']}").status_code == 405


def test_human_action_request_read_preserves_dependency_source_provenance(
    client: TestClient,
) -> None:
    downstream = client.post(
        f"{BASE}/work-items/records",
        json=_work("har-provenance-downstream"),
    ).json()
    upstream = client.post(
        f"{BASE}/work-items/records",
        json=_work("har-provenance-upstream"),
    ).json()
    dependency = client.post(
        f"{BASE}/work-item-dependencies",
        json={
            "dependency_key": "har-provenance-dependency",
            "work_item_id": downstream["id"],
            "depends_on_work_item_id": upstream["id"],
            "dependency_type": "requires",
        },
    )
    assert dependency.status_code == 201, dependency.text
    dependency_row = dependency.json()

    payload = {
        "request_key": "har-provenance-request",
        "request_type": "review",
        "title": "Dependency provenance review",
        "instructions": "Review the exact dependency edge without losing source provenance.",
        "required_role": "reviewer",
        "priority": "high",
        "work_item_id": downstream["id"],
        "source_object_type": "organization_work_item_dependency",
        "source_object_id": dependency_row["id"],
        "source_object_version": "v1",
    }
    created = client.post(f"{BASE}/human-action-requests", json=payload)
    assert created.status_code == 201, created.text

    created_row = created.json()
    assert created_row["work_item_id"] == downstream["id"]
    assert created_row["source_object_type"] == "organization_work_item_dependency"
    assert created_row["source_object_id"] == dependency_row["id"]
    assert created_row["source_object_version"] == "v1"

    detail = client.get(f"{BASE}/human-action-requests/{created_row['id']}")
    assert detail.status_code == 200, detail.text
    detail_row = detail.json()
    assert detail_row["source_object_type"] == "organization_work_item_dependency"
    assert detail_row["source_object_id"] == dependency_row["id"]
    assert detail_row["source_object_version"] == "v1"

    listing = client.get(f"{BASE}/human-action-requests", params={"page_size": 100})
    assert listing.status_code == 200, listing.text
    listed = next(item for item in listing.json()["data"] if item["id"] == created_row["id"])
    assert listed["source_object_type"] == "organization_work_item_dependency"
    assert listed["source_object_id"] == dependency_row["id"]
    assert listed["source_object_version"] == "v1"


def test_human_action_request_completion_is_human_only_idempotent_and_not_contribution(
    client: TestClient, db_session: Session
) -> None:
    # Matrix 39-45: governed request/action, human-only context, replay and no emitter.
    work = client.post(f"{BASE}/work-items/records", json=_work("human-action-work")).json()
    request_payload = {
        "request_key": "human-request-1",
        "request_type": "attestation",
        "title": "Human attestation required",
        "instructions": "Review and attest the bounded outcome.",
        "required_role": "admin",
        "assigned_human_id": "pytest-admin",
        "work_item_id": work["id"],
    }
    request = client.post(f"{BASE}/human-action-requests", json=request_payload)
    assert request.status_code == 201, request.text
    completion_payload = {
        "action_key": "human-action-1",
        "action_type": "attested",
        "outcome": "Attested by the authenticated internal human.",
        "occurred_at": NOW.isoformat(),
        "reason": "Reviewed evidence",
        "completion_notes": "Bounded API test",
    }
    completed = client.post(
        f"{BASE}/human-action-requests/{request.json()['id']}/complete", json=completion_payload
    )
    assert completed.status_code == 200, completed.text
    action_id = completed.json()["action"]["id"]
    assert completed.json()["action"]["human_actor_id"] == "pytest-admin"
    assert client.get(f"{BASE}/human-actions/{action_id}").status_code == 200
    assert client.get(f"{BASE}/human-actions").json()["total"] == 1
    audit_count = db_session.exec(select(func.count()).select_from(AuditLog)).one()
    replay = client.post(
        f"{BASE}/human-action-requests/{request.json()['id']}/complete", json=completion_payload
    )
    assert replay.status_code == 200 and replay.json()["action"]["id"] == action_id
    assert db_session.exec(select(func.count()).select_from(AuditLog)).one() == audit_count
    assert db_session.exec(select(func.count()).select_from(OrganizationContribution)).one() == 0


@pytest.mark.parametrize(
    "actor_type", [OrganizationActorType.agent, OrganizationActorType.worker, OrganizationActorType.system, OrganizationActorType.external_human]
)
def test_non_human_trusted_context_cannot_complete_human_action(
    client: TestClient, actor_type: OrganizationActorType
) -> None:
    # Dependency overrides simulate a future trusted machine identity provider;
    # request-body identity fields remain impossible regardless.
    work = client.post(f"{BASE}/work-items/records", json=_work(f"human-denied-{actor_type.value}")).json()
    request = client.post(
        f"{BASE}/human-action-requests",
        json={
            "request_key": f"request-denied-{actor_type.value}",
            "request_type": "review",
            "title": "Internal human review",
            "instructions": "Only a human may complete this.",
            "required_role": "admin",
            "work_item_id": work["id"],
        },
    ).json()
    app.dependency_overrides[organization_command_context] = lambda: _context(
        "default", actor_id=f"trusted-{actor_type.value}", actor_type=actor_type
    )
    try:
        response = client.post(
            f"{BASE}/human-action-requests/{request['id']}/complete",
            json={
                "action_key": f"action-denied-{actor_type.value}",
                "action_type": "reviewed",
                "outcome": "Attempted machine completion",
                "occurred_at": NOW.isoformat(),
            },
        )
    finally:
        app.dependency_overrides.pop(organization_command_context, None)
    assert response.status_code == 403
    assert response.json() == {"detail": "Organization action is not permitted."}


def test_decision_authority_outcome_and_supersession(
    client: TestClient, raw_client: TestClient, db_session: Session
) -> None:
    # Matrix 46-48, 56: operator cannot forge Board authority; original stays immutable.
    denied = raw_client.post(
        f"{BASE}/decisions/records",
        headers=_headers("operator", "ordinary-operator"),
        json=_decision("forged-board", "board_reserved"),
    )
    assert denied.status_code == 403
    original = _approved_decision(client, "board-authorized")
    superseded = client.post(
        f"{BASE}/decisions/records/{original['id']}/supersede",
        json={
            "new_decision_key": "board-authorized-v2",
            "title": "Replacement decision",
            "question": "Should the revised outcome be accepted?",
            "recommendation": "Review the revised evidence.",
            "reason": "New evidence requires a new append-only version.",
        },
    )
    assert superseded.status_code == 201, superseded.text
    assert superseded.json()["supersedes_decision_id"] == original["id"]
    persisted_original = client.get(f"{BASE}/decisions/records/{original['id']}").json()
    assert persisted_original["status"] == "approved"
    assert persisted_original["supersedes_decision_id"] is None


def test_record_reference_validation_and_tenant_safe_owner(
    client: TestClient, db_session: Session
) -> None:
    # Matrix 49-52: allowlisted/existent target plus exactly-one tenant-safe owner.
    lead = Lead(
        full_name="Reference Target",
        email="reference.target@example.com",
        intent=LeadIntent.visa,
        target_country="Austria",
        source="pytest",
    )
    db_session.add(lead)
    db_session.commit()
    db_session.refresh(lead)
    work = client.post(f"{BASE}/work-items/records", json=_work("reference-work")).json()
    payload = {
        "reference_key": "reference-1",
        "reference_role": "evidence",
        "target_type": "lead",
        "target_id": str(lead.id),
        "work_item_id": work["id"],
        "label": "Validated lead evidence",
    }
    accepted = client.post(f"{BASE}/record-references", json=payload)
    assert accepted.status_code == 201, accepted.text
    assert client.get(f"{BASE}/record-references/{accepted.json()['id']}").status_code == 200
    assert client.get(f"{BASE}/record-references").json()["total"] == 1

    invalid_type = client.post(
        f"{BASE}/record-references", json={**payload, "reference_key": "bad-type", "target_type": "work_item"}
    )
    assert invalid_type.status_code == 422
    nonexistent = client.post(
        f"{BASE}/record-references",
        json={**payload, "reference_key": "missing-target", "target_id": str(uuid4())},
    )
    assert nonexistent.status_code == 422

    foreign_owner = create_work_item(
        db_session,
        _context("tenant-b"),
        idempotency_key="foreign-reference-owner",
        title="Foreign reference owner",
        objective="Must not be disclosed",
        department="operations",
        authority_level="L4",
        assigned_position_key="board",
    )
    wrong_tenant = client.post(
        f"{BASE}/record-references",
        json={**payload, "reference_key": "foreign-owner", "work_item_id": str(foreign_owner.id)},
    )
    assert wrong_tenant.status_code == 404


def test_pagination_is_bounded_stable_and_tenant_scoped(
    client: TestClient, db_session: Session
) -> None:
    # Matrix 58-60: maximum size, deterministic newest-first order and tenant scope.
    for index in range(3):
        response = client.post(
            f"{BASE}/activities",
            json=_activity(
                f"page-{index}",
                occurred_at=(NOW + timedelta(minutes=index)).isoformat(),
                correlation_key="page-scope",
            ),
        )
        assert response.status_code == 201
    append_activity(
        db_session,
        _context("tenant-b"),
        activity_key="foreign-page",
        stream_key="foreign-page-stream",
        activity_class="operational",
        activity_type="page_test",
        title="Foreign page row",
        summary="Must remain tenant-scoped.",
        source_object_type="api_test",
        source_object_id="foreign-page",
        occurred_at=NOW + timedelta(hours=1),
        correlation_key="page-scope",
    )
    first = client.get(
        f"{BASE}/activities", params={"page": 1, "page_size": 2, "correlation_key": "page-scope"}
    ).json()
    second = client.get(
        f"{BASE}/activities", params={"page": 2, "page_size": 2, "correlation_key": "page-scope"}
    ).json()
    assert first["total"] == 3 and first["total_pages"] == 2
    assert [row["activity_key"] for row in first["data"]] == ["page-2", "page-1"]
    assert {row["id"] for row in first["data"]}.isdisjoint({row["id"] for row in second["data"]})
    assert client.get(f"{BASE}/activities", params={"page_size": 201}).status_code == 422


def test_openapi_and_phase_architecture_boundaries() -> None:
    # Matrix 61-64 plus schema/OpenAPI contract checks. E1 permits only the
    # bounded GET-only Observatory read surface defined by the reconciliation contract.
    schema = app.openapi()
    paths = schema["paths"]
    organization_paths = [path for path in paths if path.startswith(BASE)]

    allowed_observatory_paths = {
        f"{BASE}/observatory/summary",
        f"{BASE}/observatory/departments",
        f"{BASE}/observatory/contribution-reconciliation",
    }
    observatory_paths = {
        path for path in organization_paths if path.startswith(f"{BASE}/observatory")
    }
    assert observatory_paths == allowed_observatory_paths

    http_methods = {"get", "post", "put", "patch", "delete"}
    for path in allowed_observatory_paths:
        assert {method for method in paths[path] if method in http_methods} == {"get"}

    # Keep the pre-E1 prohibition everywhere except the explicitly approved E1 summary.
    forbidden_suffixes = ("/observatory", "/dashboard", "/metrics")
    assert not any(path.endswith(forbidden_suffixes) for path in organization_paths)
    assert not any(
        path.endswith("/summary") and path not in allowed_observatory_paths
        for path in organization_paths
    )

    operation_ids = [
        operation["operationId"]
        for path in paths.values()
        for operation in path.values()
        if isinstance(operation, dict) and "operationId" in operation
    ]
    assert len(operation_ids) == len(set(operation_ids))
    trusted_fields = {"actor_id", "actor_type", "authenticated_user_id", "role", "authority", "authority_level", "tenant_key"}
    for name in (
        "ActivityCreate",
        "ContributionCreate",
        "app__schemas_organization_records__WorkItemCreate",
        "BlockerCreate",
        "HumanActionRequestCreate",
        "HumanActionCreate",
        "DecisionCreate",
        "ReferenceCreate",
    ):
        properties = set(schema["components"]["schemas"][name].get("properties", {}))
        assert properties.isdisjoint(trusted_fields), (name, properties & trusted_fields)
    assert "source_version" in schema["components"]["schemas"]["DecisionRead"]["properties"]
    assert "record_fingerprint" not in schema["components"]["schemas"]["DecisionRead"]["properties"]

    repo_root = Path(__file__).resolve().parents[3]
    migration_names = {path.name for path in (repo_root / "apps/api/alembic/versions").glob("*.py")}
    assert "0075_legacy_schema_reconciliation.py" in migration_names
    assert "0076_organization_position_active_identity.py" in migration_names
    assert "0077_canonical_eligibility_assessment_revision.py" in migration_names
    assert "0078_capability_autonomy_profile_foundation.py" in migration_names
    assert "0079_capability_autonomy_evidence_profile_foundation.py" in migration_names
    assert "0080_capability_autonomy_promotion_policy_foundation.py" in migration_names
    assert "0081_capability_autonomy_evidence_evaluation_policy.py" in migration_names
    assert "0082_organization_execution_heartbeat_lease.py" in migration_names
    assert not any(
        name[:4].isdigit() and int(name[:4]) > 82
        for name in migration_names
    )
    migration_text = (repo_root / "apps/api/alembic/versions/0074_durable_contribution_activity_model.py").read_text(encoding="utf-8")
    assert 'revision = "0074_durable_contribution_activity_model"' in migration_text
    router_text = (repo_root / "apps/api/app/routers/organization_records.py").read_text(encoding="utf-8")
    assert "app.services.organization_contribution" in router_text
    for emitter_module in ("eligibility", "pathway", "external_validation", "workflow"):
        assert f"app.services.{emitter_module}" not in router_text