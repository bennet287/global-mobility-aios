from __future__ import annotations

from app.services.regulatory_autonomy import evaluate_regulatory_autonomy_gates


def test_structured_certified_program_change_can_enter_machine_verification() -> None:
    eligible, reasons = evaluate_regulatory_autonomy_gates(
        change_status="pending_review",
        change_type="new_program",
        materiality="high",
        source_active=True,
        source_authority_consistent=True,
        certification_approved=True,
        certification_covers_domain=True,
        snapshot_provenance_valid=True,
        structured_program_evidence=True,
        deterministic_evidence_present=True,
    )

    assert eligible is True
    assert reasons == []


def test_critical_change_stays_on_human_exception_path() -> None:
    eligible, reasons = evaluate_regulatory_autonomy_gates(
        change_status="pending_review",
        change_type="new_program",
        materiality="critical",
        source_active=True,
        source_authority_consistent=True,
        certification_approved=True,
        certification_covers_domain=True,
        snapshot_provenance_valid=True,
        structured_program_evidence=True,
        deterministic_evidence_present=True,
    )

    assert eligible is False
    assert "critical_or_unknown_materiality" in reasons


def test_unstructured_rule_change_requires_exception_review() -> None:
    eligible, reasons = evaluate_regulatory_autonomy_gates(
        change_status="pending_review",
        change_type="rule_change",
        materiality="medium",
        source_active=True,
        source_authority_consistent=True,
        certification_approved=True,
        certification_covers_domain=True,
        snapshot_provenance_valid=True,
        structured_program_evidence=False,
        deterministic_evidence_present=True,
    )

    assert eligible is False
    assert "change_type_requires_interpretation" in reasons
    assert "structured_program_evidence_missing" in reasons


def test_uncertified_source_cannot_enter_machine_verification() -> None:
    eligible, reasons = evaluate_regulatory_autonomy_gates(
        change_status="pending_review",
        change_type="program_removed",
        materiality="medium",
        source_active=True,
        source_authority_consistent=True,
        certification_approved=False,
        certification_covers_domain=False,
        snapshot_provenance_valid=True,
        structured_program_evidence=True,
        deterministic_evidence_present=True,
    )

    assert eligible is False
    assert "approved_source_certification_missing" in reasons


def test_machine_verification_routing_never_grants_canonical_write_authority() -> None:
    eligible, reasons = evaluate_regulatory_autonomy_gates(
        change_status="pending_review",
        change_type="new_program",
        materiality="low",
        source_active=True,
        source_authority_consistent=True,
        certification_approved=True,
        certification_covers_domain=True,
        snapshot_provenance_valid=True,
        structured_program_evidence=True,
        deterministic_evidence_present=True,
    )

    assert eligible is True
    assert reasons == []
    # RI.A1 only routes evidence. Publication remains governed by the existing
    # regulatory-change approval / VerifiedRule publication boundary.
