from __future__ import annotations

from labs.r3.memory.governance import (
    NativeContinuityMemory,
    resolve_governed_fact,
)


def test_native_memory_is_tenant_scoped() -> None:
    memory = NativeContinuityMemory()
    memory.put(
        tenant_id="tenant:alpha",
        memory_id="m1",
        text="Austria threshold 45",
    )

    assert memory.get(tenant_id="tenant:alpha", memory_id="m1") is not None
    assert memory.get(tenant_id="tenant:beta", memory_id="m1") is None


def test_memory_never_overrides_verified_rule() -> None:
    result = resolve_governed_fact(
        key="at.rwr.threshold",
        verified_rule_value="55",
        retrieved_memory_values=["Austria threshold 45"],
    )

    assert result.value == "55"
    assert result.source_class == "VERIFIED_RULE"
    assert result.authoritative is True
