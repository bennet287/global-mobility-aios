from __future__ import annotations

import asyncio

from labs.r3.interoperability.governed_mcp import GovernedMcpGateway
from labs.r3.interoperability.mcp_fixture import build_server
from labs.r3.interoperability.run_mcp_deep import run_deep_mcp


def test_real_mcp_deep_reference_run_is_clean() -> None:
    result = asyncio.run(run_deep_mcp())

    assert result["failures"] == 0
    assert result["passes"] == len(result["outcomes"])
    assert result["feature_coverage"]["real_sdk_client_server"] is True
    assert result["feature_coverage"]["per_call_authorization"] is True


def test_dangerous_tool_is_denied_before_server_function() -> None:
    async def run() -> tuple[str, bool, int]:
        server, counters = build_server(name="gmai-test")
        gateway = GovernedMcpGateway(
            server=server,
            expected_server_name="gmai-test",
        )
        result = await gateway.invoke(
            actor="agent:austria-regulatory",
            tool="government_submit",
            arguments={"case_id": "case:AT-001"},
            idempotency_key="deny-001",
        )
        return result.decision, result.provider_called, counters.count(
            "government_submit"
        )

    assert asyncio.run(run()) == ("DENY", False, 0)


def test_hostile_tool_metadata_does_not_expand_visible_catalog() -> None:
    async def run() -> tuple[list[str], list[str]]:
        server, _ = build_server(name="gmai-hostile", hostile=True)
        gateway = GovernedMcpGateway(
            server=server,
            expected_server_name="gmai-hostile",
        )
        result = await gateway.discover(actor="agent:austria-regulatory")
        return result["provider_tools"], result["visible_tools"]

    provider, visible = asyncio.run(run())
    assert "government_submit" in provider
    assert "government_submit" not in visible
    assert visible == ["eligibility_calculate", "source_retrieve"]
