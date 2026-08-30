# R3 Interoperability Evidence — Governed Fixture Pass

**Date:** 2026-08-30

**Status:** AIOS-OWNED MCP/A2A FIXTURE PASS / SDK CONFORMANCE PENDING

**Technical candidate:** `0889aaad41ea3cf3574619ac7c8064ddcabc7611`

The exact-candidate fixture passed 23/23 synthetic scenarios with zero critical
failures and zero unauthorized canonical effects.

Proven in this slice:

- different AI employees receive authority-filtered tool catalogs;
- dangerous tool-description text cannot make a tool discoverable;
- invocation is re-authorized and exact replay avoids a second provider call;
- unknown tools/arguments, credentials, cross-tenant resources and missing
  authority are denied before provider contact;
- provider output cannot grant authority or claim human approval;
- Agent Cards require a synthetic trust anchor and changes require review;
- advertised A2A skills do not grant authority;
- cross-tenant tasks, executable artifacts and privileged local-tool requests
  are denied;
- exact A2A replay succeeds and conflicting replay is denied.

Machine result:

```text
interoperability-20260830-002.json
embedded result SHA-256:
22c44f35aa29d09aa13ff34d428bf4df4da5a236c75689d25416aa04d4b9befd
```

Limitations:

- this is an AIOS-owned gateway/trust fixture, not an official MCP SDK or A2A
  SDK conformance run;
- no remote network service, OAuth flow, request-routing header, elicitation or
  multi-round-trip protocol implementation was exercised;
- tool provider state and A2A task state remain in-memory synthetic fixtures;
- no product runtime adapter, credential, external action or production authority
  was introduced.

Disposition:

```text
CONTINUE_R3_WITH_SPECIFIC_GAP

trigger:
run the same invariants through pinned official MCP/A2A SDK transports and
malicious loopback servers.
```
