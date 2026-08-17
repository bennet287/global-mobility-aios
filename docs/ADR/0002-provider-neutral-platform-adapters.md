# ADR 0002 — Provider-Neutral Platform Adapters

- **Status:** Accepted
- **Date:** 2026-08-17
- **Scope:** Future third-party/open-source platform integrations
- **Runtime change:** None

## Context

Global Mobility AIOS has credible external candidates for document parsing/OCR, privacy, malware
scanning, regulatory monitoring, semantic retrieval, durable workflow execution, AI
observability/evaluation, relationship authorization, policy evaluation, document rendering,
signature validation and processing lineage.

Those mechanisms are mostly commodity infrastructure. The product differentiates through mobility
reasoning, evidence governance, certification state, human review, organization governance,
durable business semantics, legal-safety boundaries and role-appropriate experiences.

Direct provider imports throughout domain services risk making framework-specific concepts become
AIOS business truth.

## Decision

Future integrations should follow:

```text
AIOS domain/service
  ↓
AIOS-owned capability contract
  ↓
AIOS adapter
  ↓
external provider/framework/service
```

The contract is expressed in AIOS terms. The adapter translates provider concepts at the edge.

### Timing decision

Technology Radar V1 is documentation-only. We will **not** add speculative empty interfaces merely
to reserve names such as `DocumentNormalizer`, `OCRProvider`, `AITraceSink`,
`SemanticRetriever`, `AuthorizationProvider`, or `DurableWorkflowEngine`.

A runtime contract is introduced only when a real implementation needs it.

## Semantic sovereignty examples

- Docling may parse; AIOS owns durable document/evidence representation.
- Presidio may detect/transform PII; AIOS owns purpose/access semantics.
- urlwatch may detect changes; AIOS owns RegulatoryChange/VerifiedRule transitions.
- pgvector/Qdrant may retrieve; AIOS owns evidence truth/certification.
- Temporal may execute waits/retries; AIOS owns WorkItem/business semantics.
- OpenFGA may evaluate relationships; AIOS owns organization/authority semantics.
- OPA may evaluate system policy; AIOS owns legal/business domain truth.
- Langfuse may show traces; AIOS owns Activity/audit semantics.
- Gotenberg/Typst may render; AIOS owns report facts/approval.
- EU DSS may validate cryptographic signatures; AIOS owns legal/evidentiary interpretation.

## Consequences

### Positive

- provider replacement remains possible;
- external tools cannot silently redefine domain state;
- alternatives can be benchmarked behind one meaning;
- exit cost becomes measurable;
- evidence/audit semantics remain stable;
- security review has a bounded integration surface.

### Costs

- adapter code adds overhead;
- not every provider-specific feature is exposed immediately;
- capability boundaries require deliberate design;
- premature generic adapters remain a risk.

## Guardrails

1. No adapter before a real integration.
2. Authoritative IDs/states remain AIOS-owned.
3. External IDs are mappings/traceability only.
4. Derived provider data should be rebuildable where practical.
5. Provider success cannot itself commit an authoritative AIOS transition.
6. Backend authorization remains authoritative.
7. Human-review/evidence/certification gates remain AIOS-owned.
8. Integration failure must be observable and cannot silently become business success.
9. Provider objects are translated at the integration edge.
10. Material adoption updates ROADMAP and CHANGELOG.

## Alternatives rejected

### Direct framework imports throughout domain code
Rejected because of coupling and exit cost.

### Build all commodity infrastructure ourselves
Rejected because AIOS should own differentiating semantics, not recreate mature infrastructure
without a concrete reason.

### Create all generic interfaces now
Rejected because Wave 0 must not create speculative abstractions.

### Adopt one end-to-end AI framework
Rejected as a default because parsing, privacy, execution, authorization, retrieval,
observability and regulated truth have different failure/ownership boundaries.

## Related documents

- `docs/TECHNOLOGY_RADAR_V1.md`
- `docs/THIRD_PARTY_PLATFORM_ADOPTION_PRINCIPLES.md`
