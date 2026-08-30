from __future__ import annotations

import json
from pathlib import Path

from labs.r3.reconciliation.reconcile_programme import _clean, _matches_group


MANIFEST = Path(__file__).resolve().parents[1] / "execution_manifest.v2.json"


def test_manifest_pins_all_six_physical_branches_and_ten_logical_lanes() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert set(manifest["physical_branches"]) == {
        "authority", "security", "skills", "interoperability", "infrastructure", "runtime"
    }
    assert set(manifest["logical_lanes"]) == {
        "authority", "security", "skills", "interoperability", "observability",
        "secrets", "recovery", "sandbox", "memory", "orchestration"
    }
    assert manifest["grand_trial"]["required_lane_count"] == 10
    assert manifest["production_adoption"] is False


def test_marker_groups_match_candidate_or_experiment() -> None:
    item = {
        "candidate": "postgresql-native-wal-pitr",
        "experiment": "t5-t8-native-wal-pitr",
    }
    assert _matches_group(item, ["native-wal-pitr"])
    assert not _matches_group(item, ["openbao"])


def test_clean_rejects_mixed_head_blocked_and_effectful_results() -> None:
    base = {
        "git_sha": "abc",
        "execution_blocked": False,
        "failures": 0,
        "critical_failures": 0,
        "unauthorized_canonical_effects": 0,
    }
    assert _clean(base, "abc") == (True, [])

    mixed = {**base, "git_sha": "def"}
    assert "git_sha_mismatch" in _clean(mixed, "abc")[1]

    blocked = {**base, "execution_blocked": True}
    assert "execution_blocked" in _clean(blocked, "abc")[1]

    effectful = {**base, "unauthorized_canonical_effects": 1}
    assert "unauthorized_canonical_effects" in _clean(effectful, "abc")[1]


def test_manifest_requires_native_and_external_security_evidence() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    groups = manifest["logical_lanes"]["security"]["required_evidence_groups"]
    assert set(groups) == {"native_state_diff", "external_frameworks"}


def test_manifest_requires_logical_and_native_wal_recovery() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    groups = manifest["logical_lanes"]["recovery"]["required_evidence_groups"]
    assert set(groups) == {"logical_restore_and_replay", "native_wal_pitr"}
