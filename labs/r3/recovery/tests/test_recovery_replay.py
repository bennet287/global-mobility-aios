from __future__ import annotations

from labs.r3.recovery.recovery_lab import reconstruct_at


EVENTS = [
    {
        "sequence": 1,
        "occurred_at": "2026-08-30 18:00:00+00",
        "status_after": "OPEN",
        "authority_after": "RETAINED",
    },
    {
        "sequence": 2,
        "occurred_at": "2026-08-30 18:05:00+00",
        "status_after": "IN_PROGRESS",
        "authority_after": "RETAINED",
    },
    {
        "sequence": 3,
        "occurred_at": "2026-08-30 18:10:00+00",
        "status_after": "HUMAN_REVIEW_REQUIRED",
        "authority_after": "RETAINED",
    },
]


def test_reconstruct_at_respects_cutoff() -> None:
    assert reconstruct_at(EVENTS, "2026-08-30 18:07:00+00") == {
        "status": "IN_PROGRESS",
        "authority": "RETAINED",
    }


def test_reconstruct_at_before_first_event_is_absent() -> None:
    assert reconstruct_at(EVENTS, "2026-08-30 17:59:59+00") == {
        "status": "ABSENT",
        "authority": "ABSENT",
    }


def test_reconstruct_at_uses_latest_sequence_at_or_before_cutoff() -> None:
    assert reconstruct_at(EVENTS, "2026-08-30 18:10:00+00") == {
        "status": "HUMAN_REVIEW_REQUIRED",
        "authority": "RETAINED",
    }
