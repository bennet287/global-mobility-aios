from __future__ import annotations

from app.services.regulatory_machine_verification import evaluate_catalog_differential


def _program(program_id: str, name: str, *, active: bool = True) -> dict:
    return {
        "program_id": program_id,
        "name": name,
        "status": "active" if active else "retired",
        "active": active,
        "summary": "",
        "effective_date": None,
    }


def test_new_program_is_verified_from_snapshot_catalog_delta() -> None:
    result = evaluate_catalog_differential(
        change_type="new_program",
        previous_catalog=[_program("study", "Study Visa")],
        current_catalog=[
            _program("study", "Study Visa"),
            _program("talent", "Global Talent Visa"),
        ],
        missing_means_retired=False,
    )

    assert result.valid is True
    assert result.added_program_ids == ("talent",)
    assert result.reasons == ()


def test_program_retirement_is_verified_from_explicit_inactive_transition() -> None:
    result = evaluate_catalog_differential(
        change_type="program_removed",
        previous_catalog=[_program("legacy", "Legacy Route")],
        current_catalog=[_program("legacy", "Legacy Route", active=False)],
        missing_means_retired=False,
    )

    assert result.valid is True
    assert result.deactivated_program_ids == ("legacy",)
    assert result.removed_program_ids == ()


def test_program_absence_only_counts_when_source_contract_declares_retirement_semantics() -> None:
    unresolved = evaluate_catalog_differential(
        change_type="program_removed",
        previous_catalog=[_program("legacy", "Legacy Route")],
        current_catalog=[_program("study", "Study Visa")],
        missing_means_retired=False,
    )
    verified = evaluate_catalog_differential(
        change_type="program_removed",
        previous_catalog=[_program("legacy", "Legacy Route")],
        current_catalog=[_program("study", "Study Visa")],
        missing_means_retired=True,
    )

    assert unresolved.valid is False
    assert "program_absence_not_semantically_retired" in unresolved.reasons
    assert verified.valid is True
    assert verified.removed_program_ids == ("legacy",)


def test_duplicate_program_identity_blocks_machine_verification() -> None:
    result = evaluate_catalog_differential(
        change_type="new_program",
        previous_catalog=[_program("study", "Study Visa")],
        current_catalog=[
            _program("talent", "Global Talent Visa"),
            _program("talent", "Duplicate Talent Visa"),
        ],
        missing_means_retired=False,
    )

    assert result.valid is False
    assert "program_catalog_duplicate_identity" in result.reasons


def test_unsupported_interpretive_change_type_cannot_be_machine_verified() -> None:
    result = evaluate_catalog_differential(
        change_type="rule_change",
        previous_catalog=[_program("study", "Study Visa")],
        current_catalog=[_program("study", "Study Visa")],
        missing_means_retired=False,
    )

    assert result.valid is False
    assert result.reasons == ("unsupported_machine_verification_change_type",)
