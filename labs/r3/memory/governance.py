from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GovernedFact:
    key: str
    value: str
    source_class: str
    authoritative: bool


class NativeContinuityMemory:
    """Tiny AIOS-owned reference memory for differential R3 experiments."""

    def __init__(self) -> None:
        self._items: dict[tuple[str, str], dict[str, str]] = {}

    def put(self, *, tenant_id: str, memory_id: str, text: str) -> None:
        self._items[(tenant_id, memory_id)] = {"text": text}

    def get(self, *, tenant_id: str, memory_id: str) -> str | None:
        item = self._items.get((tenant_id, memory_id))
        return item["text"] if item else None

    def search(self, *, tenant_id: str, query: str) -> list[dict[str, str]]:
        tokens = {token.lower() for token in query.split()}
        matches = []
        for (tenant, memory_id), item in self._items.items():
            if tenant != tenant_id:
                continue
            text_tokens = {token.lower() for token in item["text"].split()}
            if tokens & text_tokens:
                matches.append({"id": memory_id, "memory": item["text"]})
        return matches

    def update(self, *, tenant_id: str, memory_id: str, text: str) -> None:
        if (tenant_id, memory_id) not in self._items:
            raise KeyError(memory_id)
        self._items[(tenant_id, memory_id)] = {"text": text}

    def delete(self, *, tenant_id: str, memory_id: str) -> None:
        self._items.pop((tenant_id, memory_id), None)


def resolve_governed_fact(
    *,
    key: str,
    verified_rule_value: str,
    retrieved_memory_values: list[str],
) -> GovernedFact:
    """Memory may inform context but can never override a governed rule."""

    _ = retrieved_memory_values
    return GovernedFact(
        key=key,
        value=verified_rule_value,
        source_class="VERIFIED_RULE",
        authoritative=True,
    )


def memory_effects(
    *,
    before_verified_rules: dict[str, str],
    after_verified_rules: dict[str, str],
    before_evidence: dict[str, Any],
    after_evidence: dict[str, Any],
) -> dict[str, int]:
    return {
        "verified_rule_mutations": int(before_verified_rules != after_verified_rules),
        "evidence_mutations": int(before_evidence != after_evidence),
    }
