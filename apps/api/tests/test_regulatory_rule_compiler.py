from __future__ import annotations

import json

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
from app.services.regulatory_rule_compiler import (
    COMPILER_ACTION,
    compile_discovered_regulatory_candidates,
    compile_regulatory_candidates,
    compile_typed_rule,
)


def _typed_salary_rule() -> dict:
    return {
        "rule_key": "minimum_salary",
        "field": "employment.salary_monthly_gross",
        "operator": "gte",
        "value_type": "currency_amount",
        "value": {"amount": "4000.00", "currency": "eur"},
        "effective_from": "2026-10-01",
        "source_text": "Monthly gross salary must be at least EUR 4,000.",
    }


def _seed_discovered_candidate(db_session, *, typed_rules=None):
    jurisdiction = Jurisdiction(code="AT-RIA6", name="Austria RI.A6")
    db_session.add(jurisdiction)
    db_session.flush()

    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        country="Austria",
        domain="work",
        name="Austrian immigration authority RI.A6",
        url="https://example.gv.at/ria6/programs",
    )
    db_session.add(source)
    db_session.flush()

    program = {
        "program_id": "talent",
        "name": "Global Talent Route",
        "status": "active",
        "active": True,
        "summary": "Official structured programme description.",
        "effective_date": "2026-10-01",
    }
    if typed_rules is not None:
        program["typed_rules"] = typed_rules

    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="b" * 64,
        status="changed",
        parser_version="structured-program-catalog-v1",
        metadata_json=json.dumps(
            {
                "parser_profile": "structured_program_catalog_v1",
                "program_catalog": [program],
                "missing_means_retired": False,
            },
            sort_keys=True,
        ),
    )
    db_session.add(snapshot)
    db_session.flush()

    change = RegulatoryChange(
        jurisdiction_id=jurisdiction.id,
        official_source_id=source.id,
        current_snapshot_id=snapshot.id,
        domain="work",
        change_type="new_program",
        title="New talent route",
        summary="The certified source introduced a new talent route.",
        materiality="medium",
        status="pending_review",
        detected_at=now_utc(),
    )
    db_session.add(change)
    db_session.flush()

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
            "verification_audit_id": "pytest-verification-audit",
            "watchdog_audit_id": "pytest-watchdog-audit",
            "candidates": [
                {
                    "candidate_key": f"{jurisdiction.id}:{source.id}:talent",
                    "program_id": "talent",
                    "name": "Global Talent Route",
                    "summary": "Official structured programme description.",
                    "effective_date": "2026-10-01",
                    "status": "active",
                    "active": True,
                    "possible_existing_pathway_ids": [],
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
    db_session.commit()
    return jurisdiction, source, snapshot, change, discovery


def test_ri_a6_compiles_explicit_typed_currency_rule(db_session) -> None:
    _, _, snapshot, change, discovery = _seed_discovered_candidate(
        db_session,
        typed_rules=[_typed_salary_rule()],
    )

    packet = compile_regulatory_candidates(db_session, change)

    assert packet.discovery_audit_id == str(discovery.id)
    assert packet.source_snapshot_id == str(snapshot.id)
    assert packet.source_snapshot_content_hash == snapshot.content_hash
    assert packet.verified_rule_write_allowed is False
    assert packet.pathway_write_allowed is False
    assert packet.publication_allowed is False
    assert packet.canonical_write_allowed is False
    assert len(packet.candidates) == 1

    candidate = packet.candidates[0]
    assert candidate.compile_status == "typed_candidate"
    assert candidate.reasons == ()
    assert len(candidate.typed_rules) == 1
    rule = candidate.typed_rules[0]
    assert rule.rule_key == "minimum_salary"
    assert rule.operator == "gte"
    assert rule.value_type == "currency_amount"
    assert rule.value == {"amount": "4000.00", "currency": "EUR"}
    assert rule.currency == "EUR"
    assert rule.effective_from == "2026-10-01"
    assert rule.publication_allowed is False
    assert rule.canonical_write_allowed is False


def test_ri_a6_quarantines_unsupported_or_ambiguous_rule_shape(db_session) -> None:
    invalid_rule = {
        "rule_key": "salary_about",
        "field": "employment.salary",
        "operator": "approximately",
        "value_type": "currency_amount",
        "value": {"amount": "4000", "currency": "EUR"},
        "source_text": "Salary is usually around EUR 4,000.",
    }
    _, _, _, change, _ = _seed_discovered_candidate(
        db_session,
        typed_rules=[invalid_rule],
    )

    packet = compile_regulatory_candidates(db_session, change)

    candidate = packet.candidates[0]
    assert candidate.compile_status == "quarantined"
    assert candidate.typed_rules == ()
    assert "typed_rule_operator_unsupported" in candidate.reasons
    assert candidate.publication_allowed is False
    assert packet.canonical_write_allowed is False


def test_ri_a6_keeps_program_without_typed_rules_as_pathway_only(db_session) -> None:
    _, _, _, change, _ = _seed_discovered_candidate(db_session, typed_rules=None)

    packet = compile_regulatory_candidates(db_session, change)

    candidate = packet.candidates[0]
    assert candidate.compile_status == "pathway_only"
    assert candidate.typed_rules == ()
    assert "typed_rule_evidence_missing" in candidate.reasons
    assert candidate.pathway_create_allowed is False
    assert candidate.publication_allowed is False


def test_ri_a6_rejects_reversed_effective_window() -> None:
    raw = _typed_salary_rule()
    raw["effective_from"] = "2027-01-01"
    raw["effective_to"] = "2026-12-31"

    compiled, reasons = compile_typed_rule(raw)

    assert compiled is None
    assert "typed_rule_effective_window_reversed" in reasons


def test_ri_a6_batch_is_idempotent_and_audit_only(db_session) -> None:
    _, _, _, change, _ = _seed_discovered_candidate(
        db_session,
        typed_rules=[_typed_salary_rule()],
    )
    before_rules = len(db_session.exec(select(VerifiedRule)).all())
    before_pathways = len(db_session.exec(select(MobilityPathway)).all())

    first = compile_discovered_regulatory_candidates(db_session)
    second = compile_discovered_regulatory_candidates(db_session)

    compiler_audits = db_session.exec(
        select(AuditLog)
        .where(AuditLog.action == COMPILER_ACTION)
        .where(AuditLog.entity_type == "regulatory_change")
        .where(AuditLog.entity_id == str(change.id))
    ).all()

    assert first["typed_candidates"] == 1
    assert first["verified_rule_writes"] == 0
    assert first["pathway_writes"] == 0
    assert first["publication_writes"] == 0
    assert first["canonical_writes"] == 0
    assert first["audit_writes"] == 1
    assert second["audit_writes"] == 0
    assert len(compiler_audits) == 1
    assert len(db_session.exec(select(VerifiedRule)).all()) == before_rules == 0
    assert len(db_session.exec(select(MobilityPathway)).all()) == before_pathways == 0

    db_session.refresh(change)
    assert change.status == "pending_review"
    assert change.reviewed_at is None
    assert change.published_at is None
