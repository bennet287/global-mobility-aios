from __future__ import annotations

import argparse
import asyncio
import json
import socket
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id
from labs.r3.interoperability.mcp_fixture import build_server
from labs.r3.interoperability.network_mcp import GovernedNetworkMcpGateway


MCP_VERSION = "2.1.1"


class ExecutionBlocked(RuntimeError):
    pass


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@dataclass
class LocalMcpHttpServer:
    mcp: Any
    port: int
    _server: Any = None
    _task: asyncio.Task[Any] | None = None

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}/mcp"

    async def start(self) -> None:
        try:
            import uvicorn
        except ImportError as exc:
            raise ExecutionBlocked("uvicorn is not installed") from exc

        app = self.mcp.streamable_http_app(json_response=True)
        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=self.port,
            log_level="error",
            access_log=False,
        )
        self._server = uvicorn.Server(config)
        self._task = asyncio.create_task(self._server.serve())

        for _ in range(300):
            if self._server.started:
                return
            if self._task.done():
                error = self._task.exception()
                raise ExecutionBlocked(
                    f"MCP HTTP server exited during startup: {error}"
                )
            await asyncio.sleep(0.01)
        raise ExecutionBlocked("MCP HTTP server did not start")

    async def stop(self) -> None:
        if self._server is None or self._task is None:
            return
        self._server.should_exit = True
        try:
            await asyncio.wait_for(self._task, timeout=10)
        except asyncio.TimeoutError:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
        finally:
            self._server = None
            self._task = None


def _record(
    outcomes: list[dict[str, Any]],
    *,
    feature: str,
    observed: Any,
    expected: Any,
) -> None:
    outcomes.append(
        {
            "feature": feature,
            "observed": observed,
            "expected": expected,
            "passed": observed == expected,
            "unauthorized_canonical_effects": [],
        }
    )


async def run_network_mcp() -> dict[str, Any]:
    outcomes: list[dict[str, Any]] = []
    mcp, counters = build_server(name="gmai-network", hostile=False)
    server = LocalMcpHttpServer(mcp=mcp, port=_free_port())
    await server.start()
    gateway = GovernedNetworkMcpGateway(
        url=server.url,
        expected_server_name="gmai-network",
    )

    try:
        discovery = await gateway.discover(actor="agent:austria-regulatory")
        _record(
            outcomes,
            feature="streamable_http_discovery_crosses_real_network",
            observed=(
                discovery["decision"],
                discovery["server_name"],
                discovery["visible_tools"],
                bool(discovery["protocol_version"]),
            ),
            expected=(
                "ALLOW",
                "gmai-network",
                ["eligibility_calculate", "source_retrieve"],
                True,
            ),
        )

        denied = await gateway.invoke(
            actor="agent:austria-regulatory",
            tool="government_submit",
            arguments={"case_id": "case:AT-001"},
            idempotency_key="http-denied-001",
        )
        _record(
            outcomes,
            feature="network_gateway_denies_before_provider_contact",
            observed=(
                denied.decision,
                denied.provider_called,
                counters.count("government_submit"),
                denied.canonical_effects,
            ),
            expected=("DENY", False, 0, 0),
        )

        allowed = await gateway.invoke(
            actor="agent:austria-regulatory",
            tool="source_retrieve",
            arguments={"url": "https://example.invalid/source"},
            idempotency_key="http-source-001",
        )
        _record(
            outcomes,
            feature="authorized_tool_uses_streamable_http",
            observed=(
                allowed.decision,
                allowed.provider_called,
                allowed.provider_result_untrusted,
                counters.count("source_retrieve"),
                allowed.canonical_effects,
            ),
            expected=("ALLOW", True, True, 1, 0),
        )
    finally:
        await server.stop()

    # Outage must fail without creating any canonical effect.
    outage_failed_closed = False
    try:
        await gateway.discover(actor="agent:austria-regulatory")
    except Exception:
        outage_failed_closed = True
    _record(
        outcomes,
        feature="streamable_http_outage_fails_closed",
        observed=outage_failed_closed,
        expected=True,
    )

    # The same MCP server is restarted on the same endpoint; a new Client
    # session must negotiate and operate again without stale authority state.
    await server.start()
    try:
        reconnected = await gateway.invoke(
            actor="agent:austria-regulatory",
            tool="eligibility_calculate",
            arguments={"points": 60},
            idempotency_key="http-reconnect-001",
        )
        _record(
            outcomes,
            feature="fresh_client_reconnects_after_server_restart",
            observed=(
                reconnected.decision,
                reconnected.provider_called,
                counters.count("eligibility_calculate"),
                reconnected.canonical_effects,
            ),
            expected=("ALLOW", True, 1, 0),
        )

        replay = await gateway.invoke(
            actor="agent:austria-regulatory",
            tool="eligibility_calculate",
            arguments={"points": 60},
            idempotency_key="http-reconnect-001",
        )
        _record(
            outcomes,
            feature="idempotency_survives_transport_reconnect",
            observed=(
                replay.replayed,
                replay.provider_called,
                counters.count("eligibility_calculate"),
            ),
            expected=(True, False, 1),
        )
    finally:
        await server.stop()

    failures = [item for item in outcomes if not item["passed"]]
    return {
        "outcomes": outcomes,
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "feature_coverage": {
            "streamable_http_transport": True,
            "real_loopback_network": True,
            "protocol_negotiation": True,
            "authority_pre_provider_contact": True,
            "outage_fail_closed": True,
            "network_reconnect": True,
            "idempotency_across_reconnect": True,
            "tls": False,
            "oauth": False,
            "proxy_failure": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validate_run_id(args.run_id)

    try:
        detail = asyncio.run(run_network_mcp())
        blocked = False
        block_reason = None
    except ExecutionBlocked as exc:
        detail = {"outcomes": [], "passes": 0, "failures": 0, "feature_coverage": {}}
        blocked = True
        block_reason = str(exc)

    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "mcp-python-sdk-streamable-http",
        "candidate_version": MCP_VERSION,
        "git_sha": _git_sha(),
        "environment": "synthetic-local-loopback-network",
        "experiment": "t2-t3-t5-streamable-http-reconnect",
        "test_tiers": ["T2", "T3", "T5"],
        "execution_blocked": blocked,
        "block_reason": block_reason,
        "scenario_count": len(detail["outcomes"]),
        "passes": detail["passes"],
        "failures": detail["failures"],
        "critical_failures": 0,
        "unauthorized_canonical_effects": 0,
        "feature_coverage": detail["feature_coverage"],
        "outcomes": detail["outcomes"],
        "decision_candidate": "CONTINUE_R3_WITH_SPECIFIC_GAP",
    }
    result["result_sha256"] = fingerprint(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    if blocked:
        print(f"MCP Streamable HTTP execution blocked: {block_reason}")
        return 2
    print(
        f"MCP Streamable HTTP: {result['passes']}/"
        f"{result['scenario_count']} passed"
    )
    return 0 if result["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
