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
from app.services.regulatory_program_discovery import DISCOVERY_ACTION, DISCOVERY_VERSION
from app.services.regulatory_promotion_policy import (
    PROMOTION_ACTION,
    assess_regulatory_shadow_promotion,
    run_shadow_promotion_policy,
)
from app.services.regulatory_rule_compiler import COMPILER_ACTION, COMPILER_VERSION


def _seed_shadow_candidate(
    db_session,
    *,
    compile_status: str = "typed_candidate",
    candidate_reasons: list[str] | None = None,
    possible_existing_pathway_ids: list[str] | None = None,
):
    jurisdiction = Jurisdiction(code="AT-RIA7", name="Austria RI.A7")
    db_session.add(jurisdiction)
    db_session.flush()

    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        country="Austria",
        domain="work",
        name="Austrian immigration authority RI.A7",
        url="https://example.gv.at/ria7/programs",
    )
    db_session.add(source)
    db_session.flush()

    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="c" * 64,
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
    discovery = record_audit(
        db_session,
        action=DISCOVERY_ACTION,
        entity_type="regulatory_change",
        entity_id=change.id,
        after_state={
            "regulatory_change_id": str(change.id),
            "discovery_version": DISCOVERY_VERSION,
            "source_snapshot_id": str(snapshot.id),
            "source_snapshot_content_hash": snapshot.content_hash,
            "verification_audit_id": "pytest-verification",
            "watchdog_audit_id": "pytest-watchdog",
            "candidates": [
                {
                    "candidate_key": candidate_key,
                    "program_id": "talent",
                    "name": "Global Talent Route",
                    "summary": "Official structured programme description.",
                    "effective_date": "2026-10-01",
                    "status": "active",
                    "active": True,
                    "possible_existing_pathway_ids": possible_existing_pathway_ids or [],
                    "candidate_only": True,
                    "publication_allowed": False,
                    "pathway_create_allowed": False,
                    "canonical_write_allowed": False,
                }
            ],
            "fanout_limited": False,
            "candidate_only": True,
            "publication_allowed": False,
            "pathway_create_allowed": False,
            "canonical_write_allowed": False,
            "reasons": [],
        },
        actor="pytest-discovery",
        source=DISCOVERY_VERSION,
    )
    db_session.flush()

    typed_rules = []
    if compile_status == "typed_candidate":
        typed_rules = [
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
        ]

    compiler = record_audit(
        db_session,
        action=COMPILER_ACTION,
        entity_type="regulatory_change",
        entity_id=change.id,
        after_state={
            "regulatory_change_id": str(change.id),
            "compiler_version": COMPILER_VERSION,
            "discovery_audit_id": str(discovery.id),
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
                    "compile_status": compile_status,
                    "typed_rules": typed_rules,
                    "reasons": candidate_reasons or [],
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
    db_session.commit()
    return change, discovery, compiler


def test_ri_a7_clean_deterministic_candidate_is_shadow_eligible_only(db_session) -> None:
    change, discovery, compiler = _seed_shadow_candidate(db_session)

    packet = assess_regulatory_shadow_promotion(db_session, change)

    assert packet.shadow_mode is True
    assert packet.compiler_audit_id == str(compiler.id)
    assert packet.discovery_audit_id == str(discovery.id)
    assert packet.publication_writes_allowed is False
    assert packet.pathway_writes_allowed is False
    assert packet.verified_rule_writes_allowed is False
    assert packet.canonical_write_allowed is False
    assert len(packet.candidates) == 1
    candidate = packet.candidates[0]
    assert candidate.outcome == "shadow_eligible"
    assert candidate.shadow_promotion_eligible is True
    assert candidate.reasons == ()
    assert candidate.typed_rule_keys == ("minimum_salary",)
    assert candidate.publication_allowed is False
    assert candidate.canonical_write_allowed is False


def test_ri_a7_existing_pathway_signal_is_quarantined(db_session) -> None:
    change, _, _ = _seed_shadow_candidate(
        db_session,
        possible_existing_pathway_ids=["11111111-1111-1111-1111-111111111111"],
    )

    packet = assess_regulatory_shadow_promotion(db_session, change)

    candidate = packet.candidates[0]
    assert candidate.outcome == "quarantined"
    assert candidate.shadow_promotion_eligible is False
    assert "possible_existing_pathway_requires_lineage_resolution" in candidate.reasons


def test_ri_a7_incomplete_or_quarantined_compile_cannot_be_shadow_eligible(db_session) -> None:
    change, _, _ = _seed_shadow_candidate(
        db_session,
        compile_status="quarantined",
        candidate_reasons=["typed_rule_operator_unsupported"],
    )

    packet = assess_regulatory_shadow_promotion(db_session, change)

    candidate = packet.candidates[0]
    assert candidate.shadow_promotion_eligible is False
    assert "candidate_not_fully_typed" in candidate.reasons
    assert "typed_rules_missing" in candidate.reasons
    assert "compiler_candidate_has_exceptions" in candidate.reasons


def test_ri_a7_batch_is_idempotent_and_never_writes_canonical_truth(db_session) -> None:
    change, _, _ = _seed_shadow_candidate(db_session)
    before_rules = len(db_session.exec(select(VerifiedRule)).all())
    before_pathways = len(db_session.exec(select(MobilityPathway)).all())

    first = run_shadow_promotion_policy(db_session)
    second = run_shadow_promotion_policy(db_session)

    audits = db_session.exec(
        select(AuditLog)
        .where(AuditLog.action == PROMOTION_ACTION)
        .where(AuditLog.entity_type == "regulatory_change")
        .where(AuditLog.entity_id == str(change.id))
    ).all()

    assert first["shadow_mode"] is True
    assert first["shadow_eligible_candidates"] == 1
    assert first["quarantined_candidates"] == 0
    assert first["publication_writes"] == 0
    assert first["pathway_writes"] == 0
    assert first["verified_rule_writes"] == 0
    assert first["canonical_writes"] == 0
    assert first["audit_writes"] == 1
    assert second["audit_writes"] == 0
    assert len(audits) == 1
    assert len(db_session.exec(select(VerifiedRule)).all()) == before_rules == 0
    assert len(db_session.exec(select(MobilityPathway)).all()) == before_pathways == 0

    db_session.refresh(change)
    assert change.status == "pending_review"
    assert change.reviewed_at is None
    assert change.published_at is None
