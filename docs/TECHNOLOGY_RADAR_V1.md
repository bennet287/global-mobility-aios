# Global Mobility AIOS — Technology Radar V1

**Status:** FROZEN V1 — architecture/evaluation checkpoint only
**Date:** 2026-08-17
**Product baseline:** Phase 13.16.5 COMPLETE / PASS
**Next product slice:** Phase 13.16.6 — Owner decision and escalation inbox
**Runtime impact:** none

This Radar records how Global Mobility AIOS evaluates external/open-source technology without
allowing frameworks to become the product's domain architecture.

> **AIOS Semantic Sovereignty Principle:** Third-party infrastructure may implement, accelerate,
> observe, execute, retrieve, parse, scan, render, evaluate, or enforce an AIOS-defined
> capability, but it must never become authoritative for AIOS domain meaning, legal status,
> evidence status, certification state, human-review requirements, publication state,
> organizational authority, or business outcome semantics.

The Radar is not a dependency manifest. A listed technology is not automatically installed,
production-approved, or allowed to own AIOS state.

## 1. V1 classifications

| Classification | Technologies |
|---|---|
| **ADOPT / EARLY PILOT** | Docling, Presidio, urlwatch, Promptfoo, OpenTelemetry, ClamAV |
| **PILOT / BENCHMARK** | PaddleOCR, Unlimited-OCR, pgvector, Qdrant, Pydantic AI, Langfuse, Gotenberg, Typst |
| **STRATEGIC PILOT** | Temporal, OpenFGA |
| **RESEARCH** | DSPy, EU DSS, Fides, OpenLineage |
| **NARROW / CONDITIONAL** | OPA, OpenFeature |
| **BENCHMARK ONLY** | Haystack, MarkItDown |

`ADOPT / EARLY PILOT` means approved to enter a bounded pilot when the corresponding product need
exists. It does **not** mean already deployed or production-authoritative.

## 2. Placement and ownership

| Technology | Intended AIOS placement | May provide | Must not own |
|---|---|---|---|
| Docling | Document normalization adapter | parsing, layout, tables, reading order | durable evidence/document semantics |
| Presidio | Privacy Gateway | PII detection/transformation | privacy purpose, disclosure authority |
| urlwatch | Regulatory monitoring adapter | change detection/diffs | VerifiedRule/legal publication |
| Promptfoo | AI safety/evaluation gate | regression/red-team tests | production authority |
| OpenTelemetry | Neutral telemetry contract | traces/metrics/spans | Activity or evidence provenance |
| ClamAV | Upload quarantine service | malware scanning | authenticity/evidence approval |
| PaddleOCR | OCR provider candidate | OCR/document extraction | evidence truth |
| Unlimited-OCR | OCR/VLM candidate | OCR/VLM extraction | evidence truth |
| pgvector | Retrieval candidate | semantic retrieval in PostgreSQL | legal truth/certification |
| Qdrant | Retrieval candidate | dedicated vector retrieval | legal truth/certification |
| Pydantic AI | Typed production agent-runtime candidate | typed model/tool execution | deterministic domain logic/authority |
| Langfuse | Optional OTel-backed LLM observability | traces/evals/engineering analytics | business audit/legal provenance |
| Gotenberg | PDF conversion/rendering | HTML/Office/PDF conversion | report truth/approval |
| Typst | Premium report renderer | typeset professional reports | report truth/approval |
| Temporal | Durable execution infrastructure | timers/retries/signals/resumption | WorkItem/business semantics |
| OpenFGA | Relationship authorization provider | ReBAC evaluation | domain/legal truth |
| DSPy | Offline AI optimization | experimentation/optimization | production authority |
| EU DSS | EU signature adapter candidate | cryptographic signature validation | legal acceptance of contents |
| Fides | Privacy-governance research | privacy inventory/governance | AIOS domain semantics |
| OpenLineage | Processing-lineage candidate | job/run/dataset lineage | Activity/evidence provenance |
| OPA | System-policy gate | AIOS-defined policy evaluation | immigration/legal eligibility |
| OpenFeature | Feature rollout contract | flag abstraction | authorization/business approval |
| Haystack | Benchmark-only RAG alternative | retrieval/orchestration patterns | default AIOS runtime architecture |
| MarkItDown | Benchmark-only converter | lightweight text/Markdown conversion | durable document representation |

License/maturity metadata must be reverified against canonical projects immediately before an
implementation decision.

## 3. Responsibility boundaries

### Documents

```text
Untrusted upload
  ↓
type/size validation + hash + quarantine
  ↓
ClamAV adapter
  ↓
Docling/parser adapter
  ↓
OCRProvider adapter
  ├─ PaddleOCR
  ├─ Unlimited-OCR
  └─ future provider
  ↓
future AIOSDocumentArtifact
  ↓
Presidio/Privacy Gateway derivative
  ↓
Governed AIOS Evidence Objects
```

Provider-native document JSON is adapter output, not the permanent AIOS format.

### Regulatory monitoring

```text
official source
  ↓
monitoring adapter
  ↓
new immutable snapshot
  ↓
RegulatoryChange candidate
  ↓
AI triage
  ↓
human/source review
  ↓
VerifiedRule
  ↓
certification
```

A detected source change never automatically becomes legal truth.

### Durable execution

```text
AIOS domain truth
WorkItem / Blocker / Dependency / HumanActionRequest /
ExecutiveDecision / Contribution / Activity
        ↓
future Temporal adapter
timers / retries / signals / waits / resumption
```

Temporal history is infrastructure execution history, not AIOS business semantics.

### Authorization and policy

```text
OpenFGA → WHO may do WHAT to WHICH resource?
OPA     → under WHICH AIOS-defined system conditions is the operation allowed?
AIOS    → what does the legal/business/domain state actually mean?
```

### AI runtime

```text
Pydantic AI → typed production runtime candidate
DSPy        → offline optimization/research
```

### Telemetry and provenance

Keep four layers separate:

1. **Engineering trace** — OpenTelemetry / optional Langfuse.
2. **Processing lineage** — OpenLineage candidate.
3. **Organizational semantic history** — OrganizationActivity.
4. **Evidence/legal provenance** — AIOS evidence/source/certification model.

No layer may silently substitute for another.

## 4. Platform-evolution waves

### Wave 0 — architecture only — CURRENT

- Technology Radar V1
- adoption principles
- provider-neutral adapter ADR
- benchmark contracts
- ownership/prohibition rules

No dependencies, containers, migrations, feature flags, placeholder runtime interfaces, or
database changes.

### Wave 1 — low-blast-radius safety

- Promptfoo
- OpenTelemetry
- ClamAV ingestion boundary

### Wave 2 — document/privacy intelligence

- Docling
- PaddleOCR vs Unlimited-OCR benchmark
- Presidio Privacy Gateway

### Wave 3 — regulatory monitoring

- urlwatch or equivalent source-monitor adapter
- change candidate only; never auto-VerifiedRule

### Wave 4 — retrieval and AI runtime

- pgvector vs Qdrant benchmark
- Pydantic AI pilot
- DSPy offline research
- Langfuse behind OpenTelemetry

Target: one primary retrieval architecture unless a real workload justifies a split.

### Wave 5 — organization infrastructure

- Temporal
- OpenFGA

Only after current organization semantics are stable enough that infrastructure cannot define
unresolved business semantics.

### Wave 6 — professional output

- Gotenberg
- Typst
- EU DSS research/pilot

OPA, OpenFeature, Fides, OpenLineage, Haystack, and MarkItDown remain demand-triggered.

## 5. Standard candidate-evaluation contract

Every candidate must be evaluated on:

### Domain correctness
- preserves AIOS semantics;
- does not force framework state into domain records;
- provider output remains distinguishable from authoritative AIOS state.

### Safety/governance
- cannot bypass authorization, evidence, certification, publication, or human-review gates;
- supports least privilege;
- failures cannot silently become successful business transitions.

### Technical quality
- accuracy/recall where applicable;
- latency/throughput;
- determinism;
- failure behavior;
- observability;
- CPU/GPU/memory;
- upgrade/reproducibility.

### Operational fit
- self-hosting/deployment;
- backup/restore;
- disaster recovery;
- data residency;
- tenancy;
- security updates;
- monitoring and supportability.

### Exit cost
- can be removed without rewriting domain services;
- external IDs are mapped, not semantic primary keys;
- data export/rebuild path exists;
- alternative providers can be benchmarked behind the same AIOS meaning.

Exit cost is a first-class selection criterion.

## 6. OCR/document benchmark

Use an AIOS mobility corpus including:

- passports and residence cards;
- degrees and transcripts;
- employment letters, payslips and contracts;
- government PDFs;
- German and multilingual documents;
- tables;
- stamps/signatures;
- rotated/poor scans;
- mixed digital/scanned PDFs;
- long guidance documents.

Measure:

- text accuracy;
- layout fidelity;
- table accuracy;
- reading order;
- page provenance/coordinates;
- multilingual quality;
- hallucination/repetition rate;
- latency/throughput;
- GPU requirements and CPU fallback;
- memory/deployment complexity;
- data residency;
- determinism;
- failure observability;
- provider/version traceability.

Benchmark the **AIOS adapter output**, not only provider demos.

## 7. Retrieval benchmark — pgvector vs Qdrant

Evaluate:

- semantic recall/precision;
- jurisdiction filters;
- effective-date filters;
- certification-state filters;
- tenant isolation;
- hybrid search needs;
- indexing/update cost;
- deletion semantics;
- backup/restore;
- replication/recovery;
- metadata filtering;
- realistic corpus latency;
- memory/storage;
- operational burden;
- observability;
- migration/exit cost.

> Vector similarity retrieves candidate evidence. It does not establish legal truth, eligibility,
> certification, or publication state.

## 8. AI safety regression direction

A future Promptfoo suite should include invariants such as:

- missing binding job offer remains blocking when required;
- unknown province/region does not fabricate regional eligibility;
- pending certification is not described as approved;
- draft pathway state is not presented as production-ready;
- unresolved qualification mapping is not called recognized;
- prompt injection inside uploaded content cannot alter authorization/evidence state;
- model output cannot bypass human review;
- retrieved text cannot automatically become a VerifiedRule.

This complements pytest, migration/database contracts, repo policy, authorization tests, frontend
regressions, runtime smoke, and external-human acceptance.

## 9. Privacy Gateway direction

Presidio is a detection/transformation candidate, not the privacy authority.

```text
governed original
  ↓
AIOS privacy policy
  ↓
PII detection/transformation
  ↓
AI-safe derivative
```

AIOS decides purpose, recipient/tool, minimum necessary fields, transformation, retention,
re-identification permission, and required human review.

## 10. Professional output direction

- **Gotenberg:** commodity HTML/Office/PDF conversion.
- **Typst:** selected premium reports such as Mobility Assessments, Board briefings, evidence
  registers, risk registers, employer packs, source-provenance appendices and case chronologies.
- **EU DSS:** preferred initial research path for EU signature validation.

Cryptographic signature validity is not the same as legal/evidentiary acceptance.

## 11. Adoption gate

Before any Radar candidate enters runtime:

1. A concrete problem exists.
2. AIOS semantics are defined independently of the framework.
3. Integration boundary is documented.
4. Permitted/prohibited ownership is explicit.
5. Security/license/dependency review is complete.
6. Sensitive-data and residency impact are known.
7. Acceptance benchmark is defined before implementation.
8. Rollback and exit strategy are documented.
9. Change is delivered as a bounded repository slice.
10. ROADMAP and CHANGELOG record the result.

## 12. Rejection criteria

Reject/remove a candidate if it:

- requires framework-specific domain semantics;
- becomes the only authoritative provenance/audit copy;
- weakens evidence/certification/human-review gates;
- creates unacceptable data-residency or security risk;
- adds disproportionate operational burden;
- cannot be safely observed/failed/retried;
- cannot be replaced without a domain rewrite;
- duplicates another selected technology without demonstrated need.

## 13. Relationship to the product roadmap

```text
13.16.5 Cross-department dependencies and blocker view
COMPLETE / PASS
        ↓
Technology Radar V1
docs-only architecture checkpoint
        ↓
13.16.6 Owner decision and escalation inbox
UNLOCKED / NOT STARTED
```

No Radar technology is required merely to start 13.16.6.
