from __future__ import annotations

from a2a.utils import TransportProtocol

from labs.r3.interoperability.network_a2a import (
    NetworkExecutorCounters,
    network_agent_card,
)


def test_network_card_advertises_exact_transport_and_no_authority() -> None:
    card = network_agent_card(
        protocol_binding=TransportProtocol.JSONRPC,
        url="http://127.0.0.1:8000/a2a",
    )

    assert card.supported_interfaces[0].protocol_binding == TransportProtocol.JSONRPC
    assert card.supported_interfaces[0].protocol_version == "1.0"
    assert all(
        "authority" not in skill.id.lower()
        for skill in card.skills
    )


def test_network_executor_counters_start_at_zero() -> None:
    counters = NetworkExecutorCounters()

    assert counters.executions == 0
    assert counters.cancellations == 0
