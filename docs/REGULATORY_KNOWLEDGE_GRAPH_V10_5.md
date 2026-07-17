# Regulatory Knowledge Graph v10.5

## Outcome

The platform now maintains a provenance-preserving regulatory knowledge graph
as a relational projection of human-published verified rules. It is not an
independent source of truth and it cannot be written by crawlers, classifiers,
models, or client-assessment workflows.

PostgreSQL remains the appropriate store for this phase. A dedicated graph
database remains deferred until measured traversal requirements justify the
Phase 13 Neo4j capability.

## Projection boundary

```text
immutable official-source snapshot
  -> detected regulatory change
  -> accepted classification proposal
  -> human-approved regulatory change
  -> human-published verified rule
  -> transactional graph node/edge projection
```

A rule is eligible only when it has a human publisher and publication time,
resolves to a human-reviewed published change, and has consistent jurisdiction,
official-source, and immutable-snapshot provenance.

## Graph entities

The v1 projection creates typed nodes for:

- jurisdiction;
- regulatory domain;
- regulatory authority, when registered;
- official source;
- immutable source snapshot;
- reviewed regulatory change; and
- verified rule.

It creates explicit relations such as `HAS_PUBLISHED_RULE`,
`DERIVED_FROM_CHANGE`, `EVIDENCED_BY_SNAPSHOT`, `CAPTURED_FROM_SOURCE`,
`GOVERNED_BY_AUTHORITY`, and `SUPERSEDES`.

Every edge stores the exact verified-rule ID, source-snapshot ID,
regulatory-change ID, projection version, effective window, and active/history
state. No provenance is inferred from labels or free text.

## Lifecycle

- Rule publication projects the graph in the same database transaction.
- Repeated publication calls are idempotent and repair a missing projection.
- Supersession deactivates the old rule's edges without deleting them and adds
  the new rule's provenance path.
- Retirement deactivates graph edges and recalculates node activity while
  preserving historical nodes and edges.
- Operator synchronization backfills or repairs projections from eligible
  published rules only; unpublished records are ignored.
- Graph projection and deactivation actions are audited.

The graph does not update pathway versions or client assessments. Phase 10A
v10.6 now consumes graph/rule lifecycle events into a separate immutable,
review-gated pathway impact ledger; it still cannot rewrite criteria or
reassess clients automatically. See
`docs/PATHWAY_REGULATORY_IMPACT_LINKS_V10_6.md`.

## API

- `GET /api/v1/regulatory-intelligence/knowledge-graph`
  - filters: `jurisdiction_id`, `verified_rule_id`, `active`, `limit`
  - returns typed nodes, provenance-complete edges, integrity flags, and counts
- `POST /api/v1/regulatory-intelligence/knowledge-graph/sync`
  - derives projections only from eligible human-published verified rules

There is deliberately no generic node or edge mutation endpoint.

## Operator workspace

The Regulatory Intelligence workspace includes a graph tab with node/rule/edge
counts, human-publication and provenance-integrity gates, relationship flows,
and exact rule/change/snapshot identifiers. Operators can request a controlled
sync from existing published rules.

## Migration and rollback

Migration `0021_regulatory_knowledge_graph` creates the node and edge projection
tables. Downgrade drops edges before nodes and does not modify verified rules,
regulatory changes, snapshots, sources, authorities, or jurisdictions.
