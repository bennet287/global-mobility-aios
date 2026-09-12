from __future__ import annotations

from sqlmodel import select

from app.models.domain import (
    AuditLog,
    Jurisdiction,
    MobilityPathway,
    OfficialSource,
    RegulatoryChange,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from app.services.audit_log import record_audit
from app.services.regulatory_freshness_guard import FRESHNESS_ACTION, FRESHNESS_VERSION
from app.services.regulatory_promotion_authorization import (
    AUTHORIZATION_ACTION,
    AUTHORIZATION_VERSION,
    assess_machine_promotion_authorization,
    generate_machine_promotion_authorization_envelopes,
)
from app.services.regulatory_promotion_policy import PROMOTION_ACTION, PROMOTION_POLICY_VERSION
from app.services.regulatory_rule_compiler import COMPILER_ACTION, COMPILER_VERSION


def _seed_authorization_lineage(
    db_session,
    *,
    freshness_status: str = "fresh",
    quarantine_required: bool = False,
    shadow_revoked: bool = False,
    promotion_compiler_id_override: str | None = None,
):
    jurisdiction = Jurisdiction(code="AT-RIA71", name="Austria RI.A7.1")
    db_session.add(jurisdiction)
    db_session.flush()

    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        country="Austria",
        domain="work",
        name="Austrian immigration authority RI.A7.1",
        url="https://example.gv.at/ria71/programs",
    )
    db_session.add(source)
    db_session.flush()

    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="d" * 64,
        status="changed",
        parser_version="structured-program-catalog-v1",
        metadata_json="{}",
    )
    db_session.add(snapshot)
    db_session.flush()

    change = RegulatoryChange(
        jurisdiction_id=jurisdiction.id,
        official_source_id=source.id,
        current_snapshot_id=snapshot.id,
        domain="work",
        change_type="new_program",
        title="New deterministic route",
        summary="Certified deterministic candidate.",
        materiality="medium",
        status="pending_review",
        detected_at=now_utc(),
    )
    db_session.add(change)
    db_session.flush()

    candidate_key = f"{jurisdiction.id}:{source.id}:talent"
    compiler = record_audit(
        db_session,
        action=COMPILER_ACTION,
        entity_type="regulatory_change",
        entity_id=change.id,
        after_state={
            "regulatory_change_id": str(change.id),
            "compiler_version": COMPILER_VERSION,
            "discovery_audit_id": "pytest-discovery",
            "source_snapshot_id": str(snapshot.id),
            "source_snapshot_content_hash": snapshot.content_hash,
            "candidates": [
                {
                    "candidate_key": candidate_key,
                    "program_id": "talent",
                    "name": "Global Talent Route",
                    "status": "active",
                    "summary": "Official structured programme description.",
                    "effective_date": "2026-10-01",
                    "compile_status": "typed_candidate",
                    "typed_rules": [
                        {
                            "rule_key": "minimum_salary",
                            "field": "employment.salary_monthly_gross",
                            "operator": "gte",
                            "value_type": "currency_amount",
                            "value": {"amount": "4000.00", "currency": "EUR"},
                            "unit": None,
                            "currency": "EUR",
                            "effective_from": "2026-10-01",
                            "effective_to": None,
                            "source_text": "Monthly gross salary must be at least EUR 4,000.",
                            "deterministic": True,
                            "publication_allowed": False,
                            "canonical_write_allowed": False,
                        }
                    ],
                    "reasons": [],
                    "pathway_create_allowed": False,
                    "publication_allowed": False,
                    "canonical_write_allowed": False,
                }
            ],
            "candidate_only": True,
            "verified_rule_write_allowed": False,
            "pathway_write_allowed": False,
            "publication_allowed": False,
            "canonical_write_allowed": False,
            "reasons": [],
        },
        actor="pytest-compiler",
        source=COMPILER_VERSION,
    )
    db_session.flush()

    promotion = record_audit(
        db_session,
        action=PROMOTION_ACTION,
        entity_type="regulatory_change",
        entity_id=change.id,
        after_state={
            "regulatory_change_id": str(change.id),
            "promotion_policy_version": PROMOTION_POLICY_VERSION,
            "shadow_mode": True,
            "compiler_audit_id": promotion_compiler_id_override or str(compiler.id),
            "discovery_audit_id": "pytest-discovery",
            "source_snapshot_id": str(snapshot.id),
            "source_snapshot_content_hash": snapshot.content_hash,
            "candidates": [
                {
                    "candidate_key": candidate_key,
                    "program_id": "talent",
                    "outcome": "shadow_eligible",
                    "shadow_promotion_eligible": True,
                    "reasons": [],
                    "typed_rule_keys": ["minimum_salary"],
                    "publication_allowed": False,
                    "pathway_write_allowed": False,
                    "verified_rule_write_allowed": False,
                    "canonical_write_allowed": False,
                }
            ],
            "publication_writes_allowed": False,
            "pathway_writes_allowed": False,
            "verified_rule_writes_allowed": False,
            "canonical_write_allowed": False,
            "reasons": [],
        },
        actor="pytest-promotion",
        source=PROMOTION_POLICY_VERSION,
    )
    db_session.flush()

    freshness = record_audit(
        db_session,
        action=FRESHNESS_ACTION,
        entity_type="regulatory_change",
        entity_id=change.id,
        after_state={
            "regulatory_change_id": str(change.id),
            "freshness_version": FRESHNESS_VERSION,
            "promotion_audit_id": str(promotion.id),
            "source_snapshot_id": str(snapshot.id),
            "source_snapshot_content_hash": snapshot.content_hash,
            "latest_snapshot_id": str(snapshot.id),
            "latest_snapshot_content_hash": snapshot.content_hash,
            "source_active": True,
            "freshness_status": freshness_status,
            "quarantine_required": quarantine_required,
            "shadow_eligibility_revoked": shadow_revoked,
            "rollback_reference_snapshot_id": str(snapshot.id),
            "rollback_reference_snapshot_content_hash": snapshot.content_hash,
            "canonical_write_allowed": False,
            "reasons": [] if not quarantine_required else ["newer_snapshot_content_drift"],
        },
        actor="pytest-freshness",
        source=FRESHNESS_VERSION,
    )
    db_session.commit()
    return change, snapshot, compiler, promotion, freshness


def test_ri_a71_clean_lineage_is_evidence_ready_but_execution_disabled(db_session) -> None:
    change, snapshot, compiler, promotion, freshness = _seed_authorization_lineage(db_session)

    envelope = assess_machine_promotion_authorization(db_session, change)

    assert envelope.authorization_version == AUTHORIZATION_VERSION
    assert envelope.authorization_state == "evidence_ready_authority_missing"
    assert envelope.evidence_ready is True
    assert envelope.execution_authority is False
    assert envelope.human_publication_contract_required is True
    assert envelope.compiler_audit_id == str(compiler.id)
    assert envelope.promotion_audit_id == str(promotion.id)
    assert envelope.freshness_audit_id == str(freshness.id)
    assert envelope.source_snapshot_id == str(snapshot.id)
    assert envelope.reasons == ()
    assert len(envelope.intended_rule_mutations) == 1
    mutation = envelope.intended_rule_mutations[0]
    assert mutation.rule_key == "minimum_salary"
    assert mutation.intended_operation == "create_verified_rule_candidate"
    assert mutation.execution_allowed is False
    assert envelope.verified_rule_writes_allowed is False
    assert envelope.publication_writes_allowed is False
    assert envelope.canonical_write_allowed is False


def test_ri_a71_freshness_quarantine_blocks_evidence_readiness(db_session) -> None:
    change, _, _, _, _ = _seed_authorization_lineage(
        db_session,
        freshness_status="quarantined",
        quarantine_required=True,
        shadow_revoked=True,
    )

    envelope = assess_machine_promotion_authorization(db_session, change)

    assert envelope.authorization_state == "quarantined"
    assert envelope.evidence_ready is False
    assert envelope.execution_authority is False
    assert "freshness_quarantine_required" in envelope.reasons
    assert "shadow_eligibility_revoked" in envelope.reasons
    assert "freshness_not_clear" in envelope.reasons


def test_ri_a71_lineage_mismatch_is_fail_closed(db_session) -> None:
    change, _, _, _, _ = _seed_authorization_lineage(
        db_session,
        promotion_compiler_id_override="stale-compiler-audit",
    )

    envelope = assess_machine_promotion_authorization(db_session, change)

    assert envelope.authorization_state == "quarantined"
    assert envelope.evidence_ready is False
    assert "promotion_compiler_lineage_mismatch" in envelope.reasons
    assert envelope.execution_authority is False


def test_ri_a71_batch_is_idempotent_and_never_writes_canonical_truth(db_session) -> None:
    change, _, _, _, _ = _seed_authorization_lineage(db_session)
    before_rules = len(db_session.exec(select(VerifiedRule)).all())
    before_pathways = len(db_session.exec(select(MobilityPathway)).all())

    first = generate_machine_promotion_authorization_envelopes(db_session)
    second = generate_machine_promotion_authorization_envelopes(db_session)

    audits = db_session.exec(
        select(AuditLog)
        .where(AuditLog.action == AUTHORIZATION_ACTION)
        .where(AuditLog.entity_type == "regulatory_change")
        .where(AuditLog.entity_id == str(change.id))
    ).all()

    assert first["execution_authority"] is False
    assert first["evidence_ready"] == 1
    assert first["quarantined"] == 0
    assert first["verified_rule_writes"] == 0
    assert first["pathway_writes"] == 0
    assert first["publication_writes"] == 0
    assert first["canonical_writes"] == 0
    assert first["audit_writes"] == 1
    assert second["audit_writes"] == 0
    assert len(audits) == 1
    assert len(db_session.exec(select(VerifiedRule)).all()) == before_rules == 0
    assert len(db_session.exec(select(MobilityPathway)).all()) == before_pathways == 0

    db_session.refresh(change)
    assert change.status == "pending_review"
    assert change.reviewed_at is None
    assert change.reviewed_by is None
    assert change.published_at is None
