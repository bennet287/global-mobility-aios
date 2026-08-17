from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    AgencySubmission,
    ApplicationAuthorityChecklistItem,
    ApplicationRecord,
    AuditLog,
    AuthorityAppointment,
    ClientPortalAccessGrant,
    DocumentRecord,
    DocumentRequirementAssessment,
    ExternalAgency,
    ExternalAgencyAssignment,
    MobilityPathway,
    MobilityPathwayVersion,
    MobilityTimeline,
    MobilityTimelineMilestone,
    PathwayComparisonAssessment,
    Profile,
    now_utc,
)
from app.services.client_portal import issue_client_portal_grant
from tests.conftest import create_lead


def _portal_profile(
    session: Session,
    lead_id: UUID,
    *,
    version: int = 1,
    supersedes_profile_id: UUID | None = None,
) -> Profile:
    profile = Profile(
        lead_id=lead_id,
        profile_version=version,
        lifecycle_status="active",
        supersedes_profile_id=supersedes_profile_id,
        target_country="Germany",
        completeness_score=90,
        readiness_stage="review",
        consent_status="granted",
    )
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


def _persist_portal_plan_graph(
    session: Session,
    lead_id: UUID,
    profile: Profile,
    *,
    key: str,
    created_at: datetime,
    simulation: bool = False,
    version_status: str = "published",
) -> dict[str, object]:
    pathway = MobilityPathway(
        pathway_key=key,
        name=f"{key.replace('-', ' ').title()} Pathway",
        country="Germany",
        domain="work",
        catalogue_status=(
            "draft"
            if version_status == "draft"
            else "active"
        ),
        created_by="pytest",
    )
    session.add(pathway)
    session.flush()

    published = version_status != "draft"
    version = MobilityPathwayVersion(
        pathway_id=pathway.id,
        version_number=1,
        lifecycle_status=version_status,
        costs_json=json.dumps(
            {
                "currency": "EUR",
                "government_fee": 120,
                "minimum_funds_eur": 5000,
            }
        ),
        processing_time_json=json.dumps(
            {
                "minimum_weeks": 4,
                "maximum_weeks": 12,
            }
        ),
        risks_json=json.dumps(
            ["Qualification recognition may be required"]
        ),
        human_review_required=True,
        approved_by=(
            "pytest-pathway-reviewer"
            if published
            else None
        ),
        published_at=created_at if published else None,
        created_by="pytest",
        created_at=created_at,
        updated_at=created_at,
    )
    session.add(version)
    session.flush()

    cost_summary = {
        "currency": "EUR",
        "one_time_total": 120.0,
        "minimum_funds": 5000.0,
        "estimated_total_status": "not_established",
        "government_application_fee": 120.0,
        "government_application_fee_scope":
            "official authority application fee only",
    }
    risk_summary = {
        "level": "medium",
        "score": 0.45,
        "declared_risks": [
            "Qualification recognition may be required"
        ],
        "evidence_risks": [],
        "regulatory_risks": [
            "Authority processing remains external"
        ],
    }
    comparison = PathwayComparisonAssessment(
        lead_id=lead_id,
        profile_id=profile.id,
        profile_version=profile.profile_version,
        primary_pathway_id=pathway.id,
        primary_pathway_version_id=version.id,
        status="ready_for_review",
        comparison_json=json.dumps(
            {
                "consent_status": "granted",
                "simulation": simulation,
                "primary": {
                    "processing_evidence_status":
                        "established"
                },
                "alternatives": [],
            }
        ),
        cost_summary_json=json.dumps(cost_summary),
        risk_summary_json=json.dumps(risk_summary),
        alternative_pathways_json="[]",
        missing_evidence_json="[]",
        summary=(
            "Evidence-backed route retained for human review."
        ),
        human_review_required=True,
        generated_by="pytest",
        created_at=created_at,
    )
    session.add(comparison)
    session.flush()

    timeline = MobilityTimeline(
        lead_id=lead_id,
        profile_id=profile.id,
        profile_version=profile.profile_version,
        comparison_assessment_id=comparison.id,
        primary_pathway_id=pathway.id,
        primary_pathway_version_id=version.id,
        title=f"{pathway.name} mobility timeline",
        status="active",
        current_stage_key="evidence_collection",
        generated_by="pytest",
        activated_by="pytest-human-operator",
        activated_at=created_at,
        created_at=created_at,
        updated_at=created_at,
    )
    session.add(timeline)
    session.flush()

    first = MobilityTimelineMilestone(
        timeline_id=timeline.id,
        stage_order=1,
        stage_key="profile_readiness",
        title="Profile readiness",
        status="completed",
        due_at=created_at + timedelta(days=7),
        requires_human_approval=False,
        completed_at=created_at,
        created_at=created_at,
        updated_at=created_at,
    )
    second = MobilityTimelineMilestone(
        timeline_id=timeline.id,
        stage_order=2,
        stage_key="evidence_collection",
        title="Evidence collection",
        status="blocked",
        due_at=created_at + timedelta(days=14),
        requires_human_approval=True,
        created_at=created_at,
        updated_at=created_at,
    )
    session.add_all([first, second])
    session.commit()

    return {
        "pathway": pathway,
        "version": version,
        "comparison": comparison,
        "timeline": timeline,
    }


def test_portal_grant_is_hashed_scoped_and_audited(client, raw_client, db_session: Session) -> None:
    lead = create_lead(db_session, name="Portal Client", target_country="Austria")
    document = DocumentRecord(
        lead_id=lead.id,
        document_type="passport",
        filename="passport.pdf",
        status="verified",
    )
    application = ApplicationRecord(
        lead_id=lead.id,
        domain="visa",
        target_country="Austria",
        status="preparation",
    )
    db_session.add(document)
    db_session.add(application)
    db_session.commit()

    issued = client.post(
        "/api/v1/client-portal/grants",
        json={
            "lead_id": str(lead.id),
            "label": "Primary client access",
            "expires_in_days": 14,
        },
    )
    assert issued.status_code == 201, issued.text
    payload = issued.json()
    token = payload["token"]
    assert token.startswith("gmai_portal_")
    assert payload["portal_path"] == f"/portal?token={token}"

    grant = db_session.get(ClientPortalAccessGrant, UUID(payload["grant"]["id"]))
    assert grant is not None
    assert grant.token_hash == hashlib.sha256(token.encode("utf-8")).hexdigest()
    assert token not in grant.token_hash

    dashboard = raw_client.get(
        "/api/v1/public/client-portal/dashboard",
        headers={"X-GMAI-Portal-Token": token},
    )
    assert dashboard.status_code == 200, dashboard.text
    data = dashboard.json()
    assert data["client_name"] == "Portal Client"
    assert data["target_country"] == "Austria"
    assert data["application_stage"] == "preparation"
    assert data["documents"][0]["filename"] == "passport.pdf"
    assert "email" not in data
    assert "eligibility" not in data
    assert "follow_ups" not in data

    db_session.refresh(grant)
    assert grant.access_count == 1
    assert grant.last_accessed_at is not None
    actions = {
        row.action
        for row in db_session.exec(
            select(AuditLog).where(AuditLog.entity_id == str(grant.id))
        ).all()
    }
    assert {"client_portal_grant_created", "client_portal_accessed"} <= actions


def test_portal_token_cannot_cross_lead_scope_and_revocation_is_immediate(
    client,
    raw_client,
    db_session: Session,
) -> None:
    first = create_lead(db_session, name="First Portal Client")
    second = create_lead(db_session, name="Second Portal Client")
    grant, token = issue_client_portal_grant(
        db_session,
        first.id,
        actor="pytest-operator",
    )

    cross_scope = raw_client.get(
        f"/api/v1/public/return/{second.id}",
        headers={"X-GMAI-Portal-Token": token},
    )
    assert cross_scope.status_code == 404

    revoked = client.post(
        f"/api/v1/client-portal/grants/{grant.id}/revoke",
        json={"reason": "Client requested access closure."},
    )
    assert revoked.status_code == 200, revoked.text
    assert revoked.json()["status"] == "revoked"

    denied = raw_client.get(
        "/api/v1/public/client-portal/dashboard",
        headers={"X-GMAI-Portal-Token": token},
    )
    assert denied.status_code == 404


def test_expired_portal_grant_is_denied(client, raw_client, db_session: Session) -> None:
    lead = create_lead(db_session, name="Expired Portal Client")
    grant, token = issue_client_portal_grant(
        db_session,
        lead.id,
        actor="pytest-operator",
    )
    grant.expires_at = now_utc() - timedelta(minutes=1)
    db_session.add(grant)
    db_session.commit()

    denied = raw_client.get(
        "/api/v1/public/client-portal/dashboard",
        headers={"X-GMAI-Portal-Token": token},
    )
    assert denied.status_code == 404
    db_session.refresh(grant)
    assert grant.status == "expired"


def test_portal_grant_issuance_requires_operator_auth(raw_client, db_session: Session) -> None:
    lead = create_lead(db_session, name="Protected Portal Client")
    response = raw_client.post(
        "/api/v1/client-portal/grants",
        json={"lead_id": str(lead.id), "expires_in_days": 30},
    )
    assert response.status_code == 401


def test_portal_dashboard_exposes_agency_workflows(
    client, raw_client, db_session: Session
) -> None:
    lead = create_lead(db_session, name="Agency Workflow Client", target_country="Germany")
    application = ApplicationRecord(
        lead_id=lead.id,
        domain="visa",
        target_country="Germany",
        status="preparation",
    )
    db_session.add(application)
    db_session.commit()
    db_session.refresh(application)

    agency = ExternalAgency(
        name="Partner Agency",
        status="active",
        created_by="pytest",
        updated_by="pytest",
    )
    db_session.add(agency)
    db_session.commit()
    db_session.refresh(agency)

    scheduled_at = datetime(2026, 8, 15, 10, 0, 0, tzinfo=timezone.utc)
    submitted_at = datetime(2026, 8, 10, 14, 0, 0, tzinfo=timezone.utc)

    appointment = AuthorityAppointment(
        application_id=application.id,
        appointment_type="interview",
        authority_name="German Consulate Mumbai",
        location="Mumbai",
        scheduled_at=scheduled_at,
        timezone="Asia/Kolkata",
        status="scheduled",
        reference_number="APT-001",
        created_by="pytest",
        updated_by="pytest",
    )
    submission = AgencySubmission(
        application_id=application.id,
        authority_name="German Consulate Mumbai",
        submission_channel="online",
        submitted_at=submitted_at,
        status="submitted",
        reference_number="SUB-001",
        created_by="pytest",
        updated_by="pytest",
    )
    assignment = ExternalAgencyAssignment(
        application_id=application.id,
        external_agency_id=agency.id,
        status="assigned",
        sla_due_at=datetime.now(timezone.utc) + timedelta(days=3),
        sla_status="on_track",
        created_by="pytest",
        updated_by="pytest",
    )
    checklist_item = ApplicationAuthorityChecklistItem(
        application_id=application.id,
        authority_name="German Consulate Mumbai",
        item_key="passport_copy",
        item_label="Copy of passport",
        category="document",
        is_required=True,
        status="pending",
        created_by="pytest",
        updated_by="pytest",
    )
    db_session.add_all([appointment, submission, assignment, checklist_item])
    db_session.commit()

    grant, token = issue_client_portal_grant(
        db_session, lead.id, actor="pytest-operator"
    )
    dashboard = raw_client.get(
        "/api/v1/public/client-portal/dashboard",
        headers={"X-GMAI-Portal-Token": token},
    )
    assert dashboard.status_code == 200, dashboard.text
    data = dashboard.json()

    assert len(data["appointments"]) == 1
    assert data["appointments"][0]["authority_name"] == "German Consulate Mumbai"
    assert data["appointments"][0]["appointment_type"] == "interview"
    assert data["appointments"][0]["reference_number"] == "APT-001"

    assert len(data["submissions"]) == 1
    assert data["submissions"][0]["status"] == "submitted"
    assert data["submissions"][0]["reference_number"] == "SUB-001"

    assert len(data["external_agency_assignments"]) == 1
    assert data["external_agency_assignments"][0]["agency_name"] == "Partner Agency"
    assert data["external_agency_assignments"][0]["status"] == "assigned"
    assert data["external_agency_assignments"][0]["sla_status"] == "on_track"
    assert data["external_agency_assignments"][0]["sla_due_at"] is not None

    assert len(data["authority_checklist"]) == 1
    assert data["authority_checklist"][0]["item_label"] == "Copy of passport"
    assert data["authority_checklist"][0]["is_required"] is True

    # Internal-only fields are never exposed to the portal.
    for section in ("appointments", "submissions", "external_agency_assignments", "authority_checklist"):
        assert data[section][0]
        assert "notes" not in data[section][0]
        assert "created_by" not in data[section][0]
        assert "updated_by" not in data[section][0]


def test_portal_device_binding_binds_on_first_access_and_rejects_mismatched_device(
    client, raw_client, db_session: Session
) -> None:
    lead = create_lead(db_session, name="Device Bound Client")
    grant, token = issue_client_portal_grant(
        db_session,
        lead.id,
        actor="pytest-operator",
    )
    assert grant.device_fingerprint is None

    # First access binds the device fingerprint.
    first = raw_client.get(
        "/api/v1/public/client-portal/dashboard",
        headers={
            "X-GMAI-Portal-Token": token,
            "X-GMAI-Portal-Device": "device-alpha",
            "User-Agent": "pytest-first-device",
        },
    )
    assert first.status_code == 200, first.text
    db_session.refresh(grant)
    assert grant.device_fingerprint == "device-alpha"
    assert grant.user_agent == "pytest-first-device"
    actions = {
        row.action
        for row in db_session.exec(
            select(AuditLog).where(AuditLog.entity_id == str(grant.id))
        ).all()
    }
    assert "client_portal_device_bound" in actions

    # Second access with the same fingerprint succeeds.
    second = raw_client.get(
        "/api/v1/public/client-portal/dashboard",
        headers={
            "X-GMAI-Portal-Token": token,
            "X-GMAI-Portal-Device": "device-alpha",
        },
    )
    assert second.status_code == 200, second.text
    db_session.refresh(grant)
    assert grant.access_count == 2

    # Access with a different fingerprint returns 403 and signals a new-grant request.
    mismatch = raw_client.get(
        "/api/v1/public/client-portal/dashboard",
        headers={
            "X-GMAI-Portal-Token": token,
            "X-GMAI-Portal-Device": "device-beta",
        },
    )
    assert mismatch.status_code == 403, mismatch.text
    data = mismatch.json()
    assert data.get("action") == "request_new_grant"

    # Access without a device header after binding is also rejected.
    missing = raw_client.get(
        "/api/v1/public/client-portal/dashboard",
        headers={"X-GMAI-Portal-Token": token},
    )
    assert missing.status_code == 403, missing.text


def test_portal_grant_read_exposes_device_fields_after_binding(
    client, raw_client, db_session: Session
) -> None:
    lead = create_lead(db_session, name="Device Read Client")
    grant, token = issue_client_portal_grant(
        db_session,
        lead.id,
        actor="pytest-operator",
    )
    raw_client.get(
        "/api/v1/public/client-portal/dashboard",
        headers={
            "X-GMAI-Portal-Token": token,
            "X-GMAI-Portal-Device": "device-read",
        },
    )

    listed = client.get("/api/v1/client-portal/grants")
    assert listed.status_code == 200, listed.text
    items = listed.json()
    matching = [item for item in items if item["id"] == str(grant.id)]
    assert len(matching) == 1
    assert matching[0]["device_fingerprint"] == "device-read"
    assert matching[0]["access_count"] >= 1


def test_portal_grant_list_without_device_binding_shows_null_fields(
    client, db_session: Session
) -> None:
    lead = create_lead(db_session, name="Unbound Device Client")
    grant, _token = issue_client_portal_grant(
        db_session,
        lead.id,
        actor="pytest-operator",
    )
    assert grant.device_fingerprint is None

    listed = client.get("/api/v1/client-portal/grants")
    assert listed.status_code == 200, listed.text
    matching = [item for item in listed.json() if item["id"] == str(grant.id)]
    assert len(matching) == 1
    assert matching[0]["device_fingerprint"] is None
    assert matching[0]["device_label"] is None
    assert matching[0]["user_agent"] is None
def test_portal_exposes_only_human_activated_pinned_mobility_plan(
    raw_client,
    db_session: Session,
) -> None:
    lead = create_lead(
        db_session,
        name="Reviewed Plan Client",
        target_country="Germany",
    )
    profile = _portal_profile(
        db_session,
        lead.id,
    )
    base = datetime(
        2026,
        8,
        17,
        8,
        0,
        tzinfo=timezone.utc,
    )
    graph = _persist_portal_plan_graph(
        db_session,
        lead.id,
        profile,
        key="reviewed-client-route",
        created_at=base,
    )

    approved = DocumentRequirementAssessment(
        assessment_key="portal-reviewed-evidence",
        lead_id=lead.id,
        pathway_id=graph["pathway"].id,
        pathway_version_id=graph["version"].id,
        profile_id=profile.id,
        profile_version=profile.profile_version,
        requirement_source="published_pathway_version",
        result_status="needs_documents",
        review_status="approved",
        required_count=4,
        satisfied_count=2,
        missing_count=2,
        inconsistency_count=0,
        requirements_json="[]",
        findings_json="[]",
        source_snapshot_json="{}",
        document_snapshot_json="[]",
        summary="Reviewed document requirement coverage.",
        human_review_required=True,
        generated_by="pytest",
        reviewed_by="pytest-document-reviewer",
        reviewed_at=base + timedelta(minutes=10),
        review_notes="Reviewed against the pinned pathway.",
        created_at=base,
        updated_at=base + timedelta(minutes=10),
    )
    newer_pending = DocumentRequirementAssessment(
        assessment_key="portal-newer-pending-evidence",
        lead_id=lead.id,
        pathway_id=graph["pathway"].id,
        pathway_version_id=graph["version"].id,
        profile_id=profile.id,
        profile_version=profile.profile_version,
        requirement_source="published_pathway_version",
        result_status="complete",
        review_status="pending",
        required_count=4,
        satisfied_count=4,
        missing_count=0,
        inconsistency_count=0,
        requirements_json="[]",
        findings_json="[]",
        source_snapshot_json="{}",
        document_snapshot_json="[]",
        summary="Newer assessment still awaiting human review.",
        human_review_required=True,
        generated_by="pytest",
        created_at=base + timedelta(minutes=20),
        updated_at=base + timedelta(minutes=20),
    )
    db_session.add_all([approved, newer_pending])
    db_session.commit()

    _grant, token = issue_client_portal_grant(
        db_session,
        lead.id,
        actor="pytest-operator",
    )
    response = raw_client.get(
        "/api/v1/public/client-portal/dashboard",
        headers={"X-GMAI-Portal-Token": token},
    )
    assert response.status_code == 200, response.text

    data = response.json()
    plan = data["mobility_plan"]
    assert plan is not None
    assert plan["pathway_name"] == (
        "Reviewed Client Route Pathway"
    )
    assert plan["plan_status"] == "active"
    assert plan["profile_version"] == 1
    assert plan["processing_evidence_status"] == "established"
    assert plan["cost"]["currency"] == "EUR"
    assert (
        plan["cost"]["government_application_fee"]
        == 120.0
    )
    assert plan["cost"]["minimum_funds"] == 5000.0
    assert (
        plan["cost"]["estimated_total_status"]
        == "not_established"
    )
    assert plan["risk"] == {
        "level": "medium",
        "declared_count": 1,
        "evidence_count": 0,
        "regulatory_count": 1,
    }
    assert plan["journey"][0]["state"] == "complete"
    assert plan["journey"][1]["state"] == "attention"

    evidence = data["evidence_summary"]
    assert evidence is not None
    assert evidence["review_status"] == "approved"
    assert evidence["required_count"] == 4
    assert evidence["satisfied_count"] == 2
    assert evidence["missing_count"] == 2
    assert evidence["inconsistency_count"] == 0

    serialized = json.dumps(data)
    for internal_field in (
        "verified_rule_ids",
        "source_snapshot_ids",
        "review_notes",
        "approved_by",
        "owner_role",
        "blockers",
        "findings_json",
        "source_snapshot_json",
        "document_snapshot_json",
    ):
        assert internal_field not in serialized


def test_portal_skips_newer_simulation_and_draft_plan_state(
    raw_client,
    db_session: Session,
) -> None:
    lead = create_lead(
        db_session,
        name="Safe Selection Client",
        target_country="Germany",
    )
    profile = _portal_profile(
        db_session,
        lead.id,
    )
    base = datetime(
        2026,
        8,
        17,
        7,
        0,
        tzinfo=timezone.utc,
    )

    valid = _persist_portal_plan_graph(
        db_session,
        lead.id,
        profile,
        key="safe-reviewed-route",
        created_at=base,
    )
    _persist_portal_plan_graph(
        db_session,
        lead.id,
        profile,
        key="newer-simulation-route",
        created_at=base + timedelta(hours=1),
        simulation=True,
    )
    _persist_portal_plan_graph(
        db_session,
        lead.id,
        profile,
        key="newer-draft-route",
        created_at=base + timedelta(hours=2),
        version_status="draft",
    )

    _grant, token = issue_client_portal_grant(
        db_session,
        lead.id,
        actor="pytest-operator",
    )
    response = raw_client.get(
        "/api/v1/public/client-portal/dashboard",
        headers={"X-GMAI-Portal-Token": token},
    )
    assert response.status_code == 200, response.text

    plan = response.json()["mobility_plan"]
    assert plan is not None
    assert plan["timeline_id"] == str(valid["timeline"].id)
    assert plan["pathway_name"] == "Safe Reviewed Route Pathway"

    serialized = json.dumps(plan).lower()
    assert "simulation" not in serialized
    assert "newer simulation route" not in serialized
    assert "newer draft route" not in serialized


def test_portal_suppresses_plan_when_current_profile_version_changes(
    raw_client,
    db_session: Session,
) -> None:
    lead = create_lead(
        db_session,
        name="Stale Plan Client",
        target_country="Germany",
    )
    profile_v1 = _portal_profile(
        db_session,
        lead.id,
    )
    base = datetime(
        2026,
        8,
        17,
        6,
        0,
        tzinfo=timezone.utc,
    )
    _persist_portal_plan_graph(
        db_session,
        lead.id,
        profile_v1,
        key="stale-profile-route",
        created_at=base,
    )

    _portal_profile(
        db_session,
        lead.id,
        version=2,
        supersedes_profile_id=profile_v1.id,
    )

    _grant, token = issue_client_portal_grant(
        db_session,
        lead.id,
        actor="pytest-operator",
    )
    response = raw_client.get(
        "/api/v1/public/client-portal/dashboard",
        headers={"X-GMAI-Portal-Token": token},
    )
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["mobility_plan"] is None
    assert data["evidence_summary"] is None
def test_client_portal_cors_preflight_allows_portal_headers(
    raw_client,
) -> None:
    response = raw_client.options(
        "/api/v1/public/client-portal/dashboard",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": (
                "x-gmai-portal-device,"
                "x-gmai-portal-token"
            ),
        },
    )

    assert response.status_code == 200, response.text
    assert (
        response.headers.get(
            "access-control-allow-origin"
        )
        == "http://localhost:3000"
    )

    allowed = {
        value.strip().lower()
        for value in response.headers.get(
            "access-control-allow-headers",
            "",
        ).split(",")
        if value.strip()
    }

    assert {
        "x-gmai-portal-device",
        "x-gmai-portal-token",
    }.issubset(allowed)
