from __future__ import annotations

import pytest

from labs.r3.interoperability.mcp_fixture import build_server
from labs.r3.interoperability.network_mcp import GovernedNetworkMcpGateway


@pytest.mark.asyncio
async def test_network_gateway_denies_without_opening_transport() -> None:
    gateway = GovernedNetworkMcpGateway(
        url="http://127.0.0.1:1/mcp",
        expected_server_name="never-contacted",
    )

    result = await gateway.invoke(
        actor="agent:austria-regulatory",
        tool="government_submit",
        arguments={"case_id": "synthetic"},
        idempotency_key="deny-without-network",
    )

    assert result.decision == "DENY"
    assert result.provider_called is False
    assert result.canonical_effects == 0


def test_mcp_server_exposes_streamable_http_asgi_app() -> None:
    server, _ = build_server(name="gmai-test", hostile=False)
    app = server.streamable_http_app(json_response=True)

    assert callable(app)
    assert server.session_manager is not None
