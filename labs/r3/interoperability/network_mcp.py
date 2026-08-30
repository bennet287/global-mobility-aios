from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mcp import Client

from labs.r3.interoperability.governed_mcp import McpAuthority


@dataclass(frozen=True)
class NetworkGatewayResult:
    decision: str
    reason_class: str
    provider_called: bool
    replayed: bool
    tool: str
    protocol_version: str | None
    server_name: str | None
    provider_result_present: bool
    provider_result_untrusted: bool
    canonical_effects: int


class GovernedNetworkMcpGateway:
    """Governed MCP boundary over real Streamable HTTP transport."""

    def __init__(
        self,
        *,
        url: str,
        expected_server_name: str,
        authority: McpAuthority | None = None,
    ) -> None:
        self._url = url
        self._expected_server_name = expected_server_name
        self._authority = authority or McpAuthority()
        self._replay_cache: dict[str, NetworkGatewayResult] = {}

    @staticmethod
    def _identity(client: Client) -> tuple[str | None, str | None]:
        info = getattr(client, "server_info", None)
        name = getattr(info, "name", None)
        protocol = getattr(client, "protocol_version", None)
        return name, str(protocol) if protocol is not None else None

    async def discover(self, *, actor: str) -> dict[str, Any]:
        async with Client(self._url) as client:
            server_name, protocol = self._identity(client)
            if server_name != self._expected_server_name:
                return {
                    "decision": "DENY",
                    "reason_class": "MCP_SERVER_IDENTITY_MISMATCH",
                    "server_name": server_name,
                    "protocol_version": protocol,
                    "provider_tools": [],
                    "visible_tools": [],
                }

            page = await client.list_tools()
            provider_tools = sorted(tool.name for tool in page.tools)
            visible = sorted(
                tool
                for tool in provider_tools
                if self._authority.discoverable(actor=actor, tool=tool)
            )
            return {
                "decision": "ALLOW",
                "reason_class": "AUTHORIZED_DISCOVERY",
                "server_name": server_name,
                "protocol_version": protocol,
                "provider_tools": provider_tools,
                "visible_tools": visible,
            }

    async def invoke(
        self,
        *,
        actor: str,
        tool: str,
        arguments: dict[str, Any],
        idempotency_key: str,
    ) -> NetworkGatewayResult:
        replay = self._replay_cache.get(idempotency_key)
        if replay is not None:
            return NetworkGatewayResult(
                **{
                    **replay.__dict__,
                    "provider_called": False,
                    "replayed": True,
                }
            )

        # Local authority is evaluated before any network connection is opened.
        if not self._authority.callable(actor=actor, tool=tool):
            result = NetworkGatewayResult(
                decision="DENY",
                reason_class="MCP_TOOL_AUTHORITY_MISSING",
                provider_called=False,
                replayed=False,
                tool=tool,
                protocol_version=None,
                server_name=None,
                provider_result_present=False,
                provider_result_untrusted=True,
                canonical_effects=0,
            )
            self._replay_cache[idempotency_key] = result
            return result

        async with Client(self._url) as client:
            server_name, protocol = self._identity(client)
            if server_name != self._expected_server_name:
                result = NetworkGatewayResult(
                    decision="DENY",
                    reason_class="MCP_SERVER_IDENTITY_MISMATCH",
                    provider_called=False,
                    replayed=False,
                    tool=tool,
                    protocol_version=protocol,
                    server_name=server_name,
                    provider_result_present=False,
                    provider_result_untrusted=True,
                    canonical_effects=0,
                )
                self._replay_cache[idempotency_key] = result
                return result

            response = await client.call_tool(tool, arguments)
            result = NetworkGatewayResult(
                decision="ALLOW",
                reason_class=(
                    "MCP_PROVIDER_ERROR"
                    if getattr(response, "is_error", False)
                    else "AUTHORIZED_TOOL_RESULT_UNTRUSTED"
                ),
                provider_called=True,
                replayed=False,
                tool=tool,
                protocol_version=protocol,
                server_name=server_name,
                provider_result_present=bool(
                    getattr(response, "structured_content", None)
                    or getattr(response, "content", None)
                ),
                provider_result_untrusted=True,
                canonical_effects=0,
            )
            self._replay_cache[idempotency_key] = result
            return result
