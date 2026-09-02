from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = ROOT / "scripts" / "prepare_austria_source_certification_review_handoff.py"
SPEC = importlib.util.spec_from_file_location(
    "prepare_austria_source_certification_review_handoff",
    SCRIPT_PATH,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _pack() -> dict[str, object]:
    return {
        "pack_version": "source_certification_structured_evidence_v1",
        "evidence_pack_sha256": "a" * 64,
        "certification_id": "11111111-1111-1111-1111-111111111111",
        "certification_status": "pending_review",
        "proposed_by": "austria-live-acceptance-operator",
        "jurisdiction": {
            "id": "22222222-2222-2222-2222-222222222222",
            "code": "AT",
            "name": "Austria",
        },
        "source_snapshot": {
            "id": "33333333-3333-3333-3333-333333333333",
            "content_hash": "b" * 64,
        },
        "structured_projection": {
            "year": 2026,
            "scope": "national",
            "entry_count": 2,
            "entry_set_sha256": "c" * 64,
            "extraction_version": "austria_migration_shortage_v1",
            "source_snapshot_content_hash": "b" * 64,
        },
        "structured_entries": [
            {
                "source_ordinal": 1,
                "occupation_group": "One",
                "occupation_aliases": ["Alias one"],
                "entry_sha256": "d" * 64,
            },
            {
                "source_ordinal": 2,
                "occupation_group": "Two",
                "occupation_aliases": ["Alias two"],
                "entry_sha256": "e" * 64,
            },
        ],
        "review_checklist": ["Compare every structured row."],
    }


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def _completed_return(pack: dict[str, object]) -> dict[str, object]:
    template = MODULE.build_return_template(pack)
    template.update(
        {
            "reviewer_identity": "independent-human-reviewer",
            "reviewer_role": "reviewer",
            "reviewer_reference": "external-review-record-2026-08-25",
            "reviewer_credential_reference": "credential-reference-2026-08-25",
            "review_completed_at": "2026-08-25T14:30:00+02:00",
            "decision": "approved",
            "notes": "Personally compared the immutable source snapshot with every structured row.",
            "independent_human_attestation": True,
            "attestations": {
                "official_source_and_snapshot_confirmed": True,
                "every_structured_entry_compared": True,
                "year_scope_counts_and_hashes_confirmed": True,
                "non_eligibility_boundary_understood": True,
                "reviewer_is_independent_from_proposer": True,
            },
        }
    )
    return template


def test_handoff_packet_pins_exact_review_identity(tmp_path: Path) -> None:
    path = tmp_path / "pack.json"
    pack = _pack()
    _write_json(path, pack)

    loaded = MODULE.load_review_pack(path)
    packet = MODULE.build_handoff_packet(loaded)

    assert packet["certification_id"] == pack["certification_id"]
    assert packet["evidence_pack_sha256"] == "a" * 64
    assert packet["source_snapshot_id"] == "33333333-3333-3333-3333-333333333333"
    assert packet["submission_contract"]["independent_human_attestation_required"] is True
    assert packet["review_pack"] == pack


def test_valid_return_compiles_exact_service_arguments() -> None:
    pack = _pack()
    returned = _completed_return(pack)

    report = MODULE.validate_return(pack, returned)

    assert report["structurally_ready_for_submission"] is True
    assert report["external_identity_and_credentials_verified_by_this_tool"] is False
    assert report["service_arguments"] == {
        "certification_id": "11111111-1111-1111-1111-111111111111",
        "decision": "approved",
        "notes": "Personally compared the immutable source snapshot with every structured row.",
        "actor": "independent-human-reviewer",
        "reviewer_role": "reviewer",
        "evidence_pack_sha256": "a" * 64,
        "source_snapshot_id": "33333333-3333-3333-3333-333333333333",
        "independent_human_attestation": True,
    }


def test_return_rejects_proposer_self_review() -> None:
    pack = _pack()
    returned = _completed_return(pack)
    returned["reviewer_identity"] = pack["proposed_by"]

    with pytest.raises(ValueError, match="different from the proposer"):
        MODULE.validate_return(pack, returned)


def test_return_rejects_changed_hash_and_missing_attestation() -> None:
    pack = _pack()
    changed_hash = _completed_return(pack)
    changed_hash["evidence_pack_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="evidence_pack_sha256"):
        MODULE.validate_return(pack, changed_hash)

    missing_attestation = _completed_return(pack)
    missing_attestation["attestations"]["every_structured_entry_compared"] = False
    with pytest.raises(ValueError, match="all reviewer attestations must be true"):
        MODULE.validate_return(pack, missing_attestation)
