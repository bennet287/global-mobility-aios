#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


HANDOFF_CONTRACT_VERSION = "austria-source-certification-review-handoff.v1"
RETURN_TEMPLATE_CONTRACT_VERSION = "austria-source-certification-review-return.v1"
EXPECTED_PACK_VERSION = "source_certification_structured_evidence_v1"
EXPECTED_JURISDICTION_CODE = "AT"
EXPECTED_YEAR = 2026
EXPECTED_SCOPE = "national"


def _json(value: object) -> str:
    return json.dumps(value, default=str, indent=2, sort_keys=True, ensure_ascii=False)


def _require_mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Unable to read {label}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON: {exc}") from exc
    return _require_mapping(raw, label)


def load_review_pack(path: Path) -> dict[str, Any]:
    pack = _load_json(path, "review pack")
    if pack.get("pack_version") != EXPECTED_PACK_VERSION:
        raise ValueError(
            f"review pack must use {EXPECTED_PACK_VERSION}"
        )
    if pack.get("certification_status") != "pending_review":
        raise ValueError("source certification must still be pending_review")

    certification_id = _require_text(pack.get("certification_id"), "certification_id")
    proposer = _require_text(pack.get("proposed_by"), "proposed_by")
    evidence_hash = _require_text(pack.get("evidence_pack_sha256"), "evidence_pack_sha256")
    if len(evidence_hash) != 64 or any(char not in "0123456789abcdefABCDEF" for char in evidence_hash):
        raise ValueError("evidence_pack_sha256 must be a 64-character hexadecimal SHA-256")

    jurisdiction = _require_mapping(pack.get("jurisdiction"), "jurisdiction")
    if str(jurisdiction.get("code", "")).strip().upper() != EXPECTED_JURISDICTION_CODE:
        raise ValueError("review pack must be for Austria (AT)")

    snapshot = _require_mapping(pack.get("source_snapshot"), "source_snapshot")
    _require_text(snapshot.get("id"), "source_snapshot.id")
    _require_text(snapshot.get("content_hash"), "source_snapshot.content_hash")

    projection = _require_mapping(pack.get("structured_projection"), "structured_projection")
    if projection.get("year") != EXPECTED_YEAR:
        raise ValueError(f"structured projection must be for {EXPECTED_YEAR}")
    if projection.get("scope") != EXPECTED_SCOPE:
        raise ValueError(f"structured projection must use {EXPECTED_SCOPE} scope")

    entries = pack.get("structured_entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("structured_entries must be a non-empty array")
    entry_count = projection.get("entry_count")
    if not isinstance(entry_count, int) or entry_count != len(entries):
        raise ValueError("structured projection entry_count must equal structured_entries length")

    ordinals = [entry.get("source_ordinal") for entry in entries if isinstance(entry, dict)]
    if ordinals != list(range(1, len(entries) + 1)):
        raise ValueError("structured entries must have contiguous source ordinals from 1")

    # Touch required identity fields so malformed handoff packs fail before export.
    _ = certification_id, proposer
    return pack


def build_handoff_packet(pack: dict[str, Any]) -> dict[str, Any]:
    snapshot = _require_mapping(pack["source_snapshot"], "source_snapshot")
    projection = _require_mapping(pack["structured_projection"], "structured_projection")
    return {
        "contract_version": HANDOFF_CONTRACT_VERSION,
        "purpose": (
            "Independent human review of the governed Austria primary source certification. "
            "This is source-governance review, not the separate L professional-review benchmark tranche."
        ),
        "certification_id": pack["certification_id"],
        "certification_status": pack["certification_status"],
        "proposed_by": pack["proposed_by"],
        "evidence_pack_sha256": pack["evidence_pack_sha256"],
        "pack_version": pack["pack_version"],
        "source_snapshot_id": snapshot["id"],
        "source_snapshot_content_hash": snapshot.get("content_hash"),
        "structured_projection": projection,
        "review_checklist": pack.get("review_checklist", []),
        "reviewer_requirements": [
            "The reviewer must be a genuine separate human and must not be the proposer.",
            "The reviewer must personally compare the immutable source text with every structured row.",
            "The reviewer must confirm the exact evidence-pack SHA-256 in this packet.",
            "Approval or rejection both require independent-human attestation.",
            "A source-certification decision does not publish a pathway or establish individual eligibility.",
            "Do not fabricate reviewer identity, credential, or external-review references.",
        ],
        "submission_contract": {
            "decision_values": ["approved", "rejected"],
            "required_service_arguments": [
                "certification_id",
                "decision",
                "notes",
                "actor",
                "reviewer_role",
                "evidence_pack_sha256",
                "source_snapshot_id",
                "independent_human_attestation",
            ],
            "reviewer_role_values": ["reviewer", "admin"],
            "evidence_pack_sha256": pack["evidence_pack_sha256"],
            "source_snapshot_id": snapshot["id"],
            "independent_human_attestation_required": True,
        },
        "review_pack": pack,
    }


def build_return_template(pack: dict[str, Any]) -> dict[str, Any]:
    snapshot = _require_mapping(pack["source_snapshot"], "source_snapshot")
    return {
        "contract_version": RETURN_TEMPLATE_CONTRACT_VERSION,
        "certification_id": pack["certification_id"],
        "source_snapshot_id": snapshot["id"],
        "evidence_pack_sha256": pack["evidence_pack_sha256"],
        "pack_version": pack["pack_version"],
        "proposed_by": pack["proposed_by"],
        "reviewer_identity": None,
        "reviewer_role": "reviewer",
        "reviewer_reference": None,
        "reviewer_credential_reference": None,
        "review_completed_at": None,
        "decision": None,
        "notes": None,
        "independent_human_attestation": None,
        "attestations": {
            "official_source_and_snapshot_confirmed": None,
            "every_structured_entry_compared": None,
            "year_scope_counts_and_hashes_confirmed": None,
            "non_eligibility_boundary_understood": None,
            "reviewer_is_independent_from_proposer": None,
        },
    }


def validate_return(pack: dict[str, Any], returned: dict[str, Any]) -> dict[str, Any]:
    if returned.get("contract_version") != RETURN_TEMPLATE_CONTRACT_VERSION:
        raise ValueError(
            f"review return must use {RETURN_TEMPLATE_CONTRACT_VERSION}"
        )
    snapshot = _require_mapping(pack["source_snapshot"], "source_snapshot")

    expected_pairs = {
        "certification_id": pack["certification_id"],
        "source_snapshot_id": snapshot["id"],
        "evidence_pack_sha256": pack["evidence_pack_sha256"],
        "pack_version": pack["pack_version"],
        "proposed_by": pack["proposed_by"],
    }
    for field, expected in expected_pairs.items():
        if returned.get(field) != expected:
            raise ValueError(f"review return {field} does not match the pinned review pack")

    reviewer_identity = _require_text(returned.get("reviewer_identity"), "reviewer_identity")
    proposer = _require_text(pack.get("proposed_by"), "proposed_by")
    if reviewer_identity.casefold() == proposer.casefold():
        raise ValueError("reviewer_identity must be different from the proposer")

    reviewer_role = _require_text(returned.get("reviewer_role"), "reviewer_role").lower()
    if reviewer_role not in {"reviewer", "admin"}:
        raise ValueError("reviewer_role must be reviewer or admin")

    decision = _require_text(returned.get("decision"), "decision").lower()
    if decision not in {"approved", "rejected"}:
        raise ValueError("decision must be approved or rejected")
    notes = _require_text(returned.get("notes"), "notes")

    if returned.get("independent_human_attestation") is not True:
        raise ValueError("independent_human_attestation must be true")

    attestations = _require_mapping(returned.get("attestations"), "attestations")
    required_attestations = [
        "official_source_and_snapshot_confirmed",
        "every_structured_entry_compared",
        "year_scope_counts_and_hashes_confirmed",
        "non_eligibility_boundary_understood",
        "reviewer_is_independent_from_proposer",
    ]
    incomplete = [name for name in required_attestations if attestations.get(name) is not True]
    if incomplete:
        raise ValueError(
            "all reviewer attestations must be true; incomplete: " + ", ".join(incomplete)
        )

    reviewer_reference = _require_text(returned.get("reviewer_reference"), "reviewer_reference")
    reviewer_credential_reference = _require_text(
        returned.get("reviewer_credential_reference"),
        "reviewer_credential_reference",
    )
    review_completed_at = _require_text(returned.get("review_completed_at"), "review_completed_at")

    service_arguments = {
        "certification_id": pack["certification_id"],
        "decision": decision,
        "notes": notes,
        "actor": reviewer_identity,
        "reviewer_role": reviewer_role,
        "evidence_pack_sha256": pack["evidence_pack_sha256"],
        "source_snapshot_id": snapshot["id"],
        "independent_human_attestation": True,
    }
    return {
        "contract_version": HANDOFF_CONTRACT_VERSION,
        "mode": "validate-return",
        "structurally_ready_for_submission": True,
        "certification_id": pack["certification_id"],
        "decision": decision,
        "reviewer_identity": reviewer_identity,
        "reviewer_role": reviewer_role,
        "reviewer_reference": reviewer_reference,
        "reviewer_credential_reference": reviewer_credential_reference,
        "review_completed_at": review_completed_at,
        "evidence_pack_sha256": pack["evidence_pack_sha256"],
        "source_snapshot_id": snapshot["id"],
        "service_arguments": service_arguments,
        "external_identity_and_credentials_verified_by_this_tool": False,
        "acceptance_boundary": (
            "Structural validation does not prove that the reviewer identity, independence, credentials, "
            "or external references are genuine. Those must be verified outside this tool before submission."
        ),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare or validate an independent-human Austria source-certification review handoff. "
            "This tool never submits or approves a certification and never writes gmai.db."
        )
    )
    parser.add_argument("--review-pack", type=Path, required=True)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--prepare-packet", action="store_true")
    modes.add_argument("--prepare-return-template", action="store_true")
    modes.add_argument("--validate-return", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def _emit(payload: dict[str, Any], output: Path | None) -> None:
    rendered = _json(payload) + "\n"
    if output is None:
        print(rendered, end="")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(
        _json(
            {
                "status": "prepared",
                "output": str(output),
                "contract_version": payload.get("contract_version"),
                "certification_id": payload.get("certification_id"),
                "evidence_pack_sha256": payload.get("evidence_pack_sha256"),
            }
        )
    )


def main() -> int:
    args = _parse_args()
    try:
        pack = load_review_pack(args.review_pack)
        if args.prepare_packet:
            _emit(build_handoff_packet(pack), args.output)
            return 0
        if args.prepare_return_template:
            _emit(build_return_template(pack), args.output)
            return 0

        returned = _load_json(args.validate_return, "review return")
        report = validate_return(pack, returned)
        print(_json(report))
        return 0
    except (ValueError, KeyError) as exc:
        print(
            _json(
                {
                    "contract_version": HANDOFF_CONTRACT_VERSION,
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
