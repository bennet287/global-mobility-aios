"""Safety invariant regression for controlled-agent role cards.

This test mirrors the checks implemented in eval/promptfoo/providers/role_card_safety.py
so that the invariant suite is exercised by the standard pytest gate even when Promptfoo is
not installed locally.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROLE_CARDS_DIR = Path(__file__).parents[3] / "agents" / "role_cards"

# Negation/prohibition tokens that turn "guarantee" into a safety statement rather than a
# positive regulated-outcome promise. The window is intentionally generous (~150 chars) to
# catch section headings and list phrasing like "## Reject Immediately\n- Any request to
# produce a client-facing guarantee."
_GUARANTEE_NEGATORS = (
    "not",
    "never",
    "no",
    "cannot",
    "can't",
    "must not",
    "mustn't",
    "reject",
    "rejects",
    "rejected",
    "prohibited",
    "prohibit",
    "without",
    "non-",
)


def _contains_positive_guarantee(lowered: str) -> bool:
    """Return True only if a guarantee word appears outside a negation/prohibition context."""
    for match in re.finditer(r"\bguarantee[d]?\b", lowered):
        start = max(match.start() - 150, 0)
        window = lowered[start:match.start()]
        if not any(neg in window for neg in _GUARANTEE_NEGATORS):
            return True
    return False


def _role_card_paths() -> list[Path]:
    if not ROLE_CARDS_DIR.exists():
        return []
    return sorted(ROLE_CARDS_DIR.glob("*.md"))


@pytest.mark.parametrize("role_card_path", _role_card_paths(), ids=lambda p: p.stem)
def test_role_card_preserves_safety_invariants(role_card_path: Path) -> None:
    text = role_card_path.read_text(encoding="utf-8")
    lowered = text.lower()

    assert any(
        phrase in lowered
        for phrase in ("human review", "human-review", "reviewed by a human", "human oversight")
    ), f"{role_card_path.name} must require human review or oversight"

    assert not _contains_positive_guarantee(
        lowered
    ), f"{role_card_path.name} must not make positive guarantees about regulated outcomes"

    assert any(
        phrase in lowered
        for phrase in ("not legal advice", "not a legal opinion", "qualified professional")
    ), f"{role_card_path.name} must disclaim giving legal advice or point to qualified professionals"

    assert any(
        phrase in lowered
        for phrase in ("official source", "source url", "provenance", "authoritative source")
    ), f"{role_card_path.name} must reference source/provenance awareness"

    assert any(
        phrase in lowered
        for phrase in ("blocked_actions", "must not", "prohibited", "never", "do not")
    ), f"{role_card_path.name} must list explicit blocked actions or prohibitions"
