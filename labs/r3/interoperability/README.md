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
