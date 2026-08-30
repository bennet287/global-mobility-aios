# SpiceDB — AIOS Authorization Research

**State:** ASSESS / R2
**Reviewed pin:** `authzed/spicedb@1ba6b9714f0a1af73d20033c63977d963f2a9a84`
**License:** Apache-2.0
**Primary sources:** `https://authzed.com/docs/spicedb/concepts/relationships`, `https://authzed.com/docs/spicedb/concepts/schema`

## Fit

SpiceDB provides Zanzibar-style relationship-based authorization with explicit schema, relationships, graph traversal and consistency controls. It is credible for large organization/resource graphs and agent authorization.

## Risks

- it introduces a second authorization datastore whose relationship freshness must be reconciled with AIOS;
- consistency tokens and read-after-write semantics become part of command correctness;
- relationship writes across AIOS PostgreSQL and SpiceDB need an outbox/reconciliation design rather than unsafe dual writes;
- contextual risk/evidence/autonomy policy may require caveats or a separate layer;
- self-hosted operations are heavier than an embedded decision library.

## R3 trigger

Evaluate only when relationship scale, permission lookup or consistency requirements exceed the OpenFGA/OPA comparison. Test stale relationships, tenant graph isolation, consistency tokens, reconciliation failure and explicit deny behavior.

## Decision

Retain as relationship-engine challenger; no current integration.
