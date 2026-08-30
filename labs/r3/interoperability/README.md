# R3 Deep Interoperability Lane

## MCP

This lane uses the real MCP Python SDK v2.1.1 with in-memory protocol transport.
It does not add MCP to product dependencies.

Install the isolated lab dependency:

```powershell
python -m pip install -r labs/r3/interoperability/requirements.txt
```

Run:

```powershell
python -m pytest labs/r3/interoperability/tests -q

python -m labs.r3.interoperability.run_mcp_deep `
  --run-id mcp-deep-20260830-001 `
  --output labs/r3/interoperability/results/mcp-deep-20260830-001.json

python -m labs.r3.common.verify_results labs/r3/interoperability/results/*.json
```

Deep coverage includes real client/server negotiation, tool listing, filtered
discovery, per-call authority, denial before provider contact, malicious metadata,
untrusted provider results, server identity mismatch and idempotent replay.

Streamable HTTP/network reconnect remains a later transport-depth experiment.


## A2A 1.0 / Python SDK 1.1.3

The A2A deep fixture uses real SDK AgentCard/AgentSkill types,
DefaultRequestHandlerV2, InMemoryTaskStore and task/artifact lifecycle. It is
handler-level isolated proof; network JSON-RPC/gRPC, streaming subscription and
cancel/resume remain explicit later depth.

Because the A2A SDK has its own dependency floor, prefer an isolated lab
environment if the main development environment is pinned to an older httpx.

```powershell
python -m pytest labs/r3/interoperability/tests/test_a2a_deep.py -q

python -m labs.r3.interoperability.run_a2a_deep `
  --run-id a2a-deep-20260830-001 `
  --output labs/r3/interoperability/results/a2a-deep-20260830-001.json

python -m labs.r3.common.verify_results labs/r3/interoperability/results/*.json
```

The gateway treats Agent Cards, skills, task status and artifacts as untrusted
remote observations. Skill inflation, fake owner approval, card version changes,
cross-tenant requests and privileged local-action requests cannot grant local
authority or create canonical WorkItems/effects.
