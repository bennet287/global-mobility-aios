# R3 Interoperability Lane

This lane tests governed MCP-style tool discovery/invocation and A2A-style remote
agent discovery/delegation. The lab uses synthetic providers and JSON-RPC-shaped
messages; protocol declarations remain untrusted until AIOS validates them.

```text
AUTHORIZED DISCOVERY + AUTHORIZED INVOCATION
AGENT CARD != IDENTITY
SKILL CLAIM != AUTHORITY
REMOTE HUMAN-APPROVAL CLAIM != APPROVAL
```

The fixture deliberately keeps its gateway and trust semantics AIOS-owned. It is
not yet an SDK-conformance claim for MCP 2026-07-28 or A2A 1.0.

Run:

```bash
python -m pytest labs/r3/interoperability/tests -q
python -m labs.r3.interoperability.run_fixture --output .test-tmp/interoperability-results.json
```
