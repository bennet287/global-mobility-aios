# OpenFGA — AIOS Authorization Research

**State:** ASSESS / R2
**Reviewed pin:** `openfga/openfga@a7dfe8491dc7f9cd5905f4e9ae6c8e1d718c4bd9`
**License:** Apache-2.0
**Primary sources:** `https://openfga.dev/docs/modeling`, `https://openfga.dev/docs/use-cases/mcp-server-authorization`

## Fit

OpenFGA is the leading relationship/delegation candidate. Its documentation explicitly models agents as independently revocable principals and checks `can_call` for each MCP tool request. That maps well to organization/position/resource relationships while preserving AIOS as the source of canonical identity and grants.

Proposed use:

```text
AIOS canonical authority facts
→ versioned OpenFGA relationship projection
→ AuthorityEnginePort check
→ typed allow/deny receipt
→ Command Gateway final decision
```

## Risks

- relationship tuples can become stale or diverge from canonical AIOS state;
- contextual risk/evidence/autonomy conditions may not fit pure relationships cleanly;
- authorization-store availability becomes part of command availability;
- broad wildcard or inherited grants can hide privilege expansion;
- tuple writes and AIOS transactions require explicit consistency/reconciliation semantics.

## Required R3 tests

Use the five-action Austria employee fixture, then prove tenant isolation, direct and group delegation, expiry/revocation, stale projection denial, wildcard rejection, MCP per-tool checks, unavailable-provider fail-closed behavior and replay-stable decision receipts.

## Decision

Proceed only to an isolated comparison with OPA. Do not adopt or make OpenFGA canonical authority truth.
