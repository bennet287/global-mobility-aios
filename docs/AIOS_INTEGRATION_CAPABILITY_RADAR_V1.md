# Global Mobility AIOS — Integration & Capability Radar V1

**Date:** 2026-08-22
**Status:** ACTIVE CAPABILITY-GAP / INTEGRATION GOVERNANCE RADAR
**Architecture contract:** `ENTERPRISE_INTEGRATION_ARCHITECTURE_V1.md`
**Technology parent:** `TECHNOLOGY_RADAR_V1_3_1.md`
**Current product boundary:** K.1 COMPLETE / PASS / SEALED; L Live Organization NEXT

This radar exists so the project does not depend on ad-hoc user discovery of necessary infrastructure and does not overcorrect by building commodity enterprise capability internally.

The radar is capability-first, not technology-first.

---

## 1. Decision doctrine

For every material new capability:

```text
Need exists?
  ├── NO  → do not add technology
  └── YES
       ↓
Is this capability a Global Mobility AIOS differentiator?
  ├── YES → prefer AIOS-native implementation / domain contract
  └── NO
       ↓
Does mature infrastructure exist?
  ├── YES → integrate behind AIOS-owned port / adapter
  └── NO  → implement smallest bounded capability or defer
```

Permanent rule:

> **No new major framework by default; no missing commodity infrastructure by neglect.**

---

## 2. Radar states

| State | Meaning |
|---|---|
| ADOPT | Accepted production infrastructure/capability |
| TRIAL | Production-like bounded evaluation permitted |
| PILOT | Controlled technical evaluation |
| BENCHMARK | Compare candidates against measured AIOS requirements |
| RESEARCH | Requirements/candidate analysis only |
| WATCH | Relevant, but demand/timing not sufficient |
| DEFER | Deliberately postponed |
| REJECT | Incompatible or unnecessary under current architecture |
| STRATEGIC DONOR | Source/reference for ideas, not platform ownership |

No state below ADOPT is a production adoption claim.

---

## 3. Priority matrix

| Capability | Need | Current decision | Timing | AIOS-owned boundary |
|---|---:|---|---|---|
| Vendor-neutral telemetry | Critical | OpenTelemetry TRIAL-ELIGIBLE | L NOW | `ObservabilityPort` / correlation contract |
| AI/agent observability backend | High | Langfuse RESEARCH/PILOT CANDIDATE | L NOW | behind OTel / no canonical truth ownership |
| Secrets management | Critical | OpenBao-class RESEARCH → PILOT | NOW | `SecretsPort` |
| Backup / restore / DR | Critical | pgBackRest/WAL-G/Restic-class RESEARCH | NOW | recovery contract |
| Identity / SSO | Critical before broader users | Keycloak / Authentik RESEARCH | DESIGN NOW | `IdentityPort`; AIOS authorization retained |
| Communications gateway | Critical before external agent work | architecture approved / provider-neutral RESEARCH | DESIGN NOW; execute later | `CommunicationPort` |
| E-signature | High for filing/document flows | EU DSS RESEARCH + signing-platform WATCH | BEFORE MATERIAL FILING | `SignaturePort` |
| Accounting / invoicing | Medium-high when commercial | ERPNext/Odoo/accounting WATCH | DEMAND-GATED | `AccountingPort` |
| ERP | Medium later | DEFER as core; WATCH as external subsystem | DEMAND-GATED | `ERPPort` |
| Payments | High only when commercial execution starts | DEFER provider selection | DEMAND-GATED | `PaymentPort` + Command Gateway |
| Feature flags/config rollout | Medium | Unleash-class WATCH | AFTER LIVE ORG NEED | configuration boundary |
| Relationship authorization | Medium | OpenFGA DEFERRED PILOT | AFTER identity/tenancy needs | advisory/relationship engine beneath AIOS authorization |
| Durable workflow waits | Medium | Temporal DEFERRED PILOT | GAP-TRIGGERED | execution adapter only |
| Malware scanning | Critical uploads | ClamAV PILOT COMPLETE / TRIAL-ELIGIBLE | CONTINUE | document-ingress control |
| Document normalization | High | Docling PILOT IN PROGRESS | CONTINUE | Document Intelligence adapter |
| Sensitive-data processing | High | Presidio QUEUED PILOT | CONTINUE | privacy processing adapter |
| Source-change monitoring | High | urlwatch QUEUED PILOT | CONTINUE | regulatory monitoring adapter |
| Semantic retrieval | High | pgvector vs Qdrant BENCHMARK | CONTINUE | Context/Retrieval port |
| Prompt/AI regression | High | Promptfoo PILOT COMPLETE / TRIAL-ELIGIBLE | CONTINUE | evaluation infrastructure |
| Context compression | Economic | LLMLingua-2 SELECTED PRIMARY PILOT | AFTER integrity benchmark | `ContextCompressionPort` |
| Major generic agent framework | Low current need | REJECT BY DEFAULT | GAP-TRIGGERED ONLY | AIOS native organization/runtime remains canonical |

---

## 4. P0 — Observability for L Live Organization

### Why now

L requires real persisted organization state plus latency, retries, runtime/tool lineage and governance telemetry. Engineering observability therefore directly increases the proof quality of L without changing organizational truth.

### Target

```text
AIOS canonical event / run IDs
        ↓
OpenTelemetry instrumentation
        ↓
trace / metric / log export
        ↓
replaceable observability backend
```

### Mandatory boundaries

- no unrestricted Evidence/document payloads in spans;
- no secrets in telemetry;
- tenant-safe correlation;
- telemetry failure must not mutate domain truth;
- `OrganizationActivity` remains canonical organizational activity;
- a trace may link to a material action but cannot authorize it.

### Acceptance evidence for advancement

- one L workflow traceable end-to-end;
- stable WorkItem / AgentRun / execution-attempt correlation;
- measurable latency and retry data;
- no protected-content leakage in sampled telemetry;
- observability backend can be replaced without changing domain behavior.

---

## 5. P0 — Secrets management

### Problem

Provider growth increases secret sprawl: databases, CI, tunnels, model APIs, communications, signing, payments and future enterprise integrations.

### Direction

Research OpenBao-class secret storage and runtime injection.

### Required properties

- non-repository secret storage;
- scoped machine/workload identity;
- short-lived credentials where possible;
- rotation and revocation;
- auditability;
- dev/test/prod separation;
- no secrets in prompt/context/memory/activity;
- recovery strategy;
- minimal operational burden.

### Advancement gate

Pilot only one non-production credential path first. Production adoption requires rotation/recovery proof, not only successful secret retrieval.

---

## 6. P0 — Backup / restore / disaster recovery

### Why now

The project has meaningful canonical PostgreSQL state, object storage, migrations, Evidence assets and increasing runtime history. Backup must mature before Live Organization becomes operationally important.

### Candidate classes

- PostgreSQL: pgBackRest / WAL-G-class tooling;
- encrypted file/object backup: Restic-class tooling;
- MinIO/S3 native versioning/replication where appropriate.

### Required proof

```text
backup created
    !=
recovery proven
```

Acceptance requires a bounded restore exercise into an isolated environment and verification of schema/migration/canonical-state integrity.

---

## 7. P0/P1 — Identity / SSO

### Direction

Evaluate Keycloak and Authentik-class OIDC identity providers.

### AIOS boundary

```text
IdP authenticates
AIOS authorizes
```

The IdP may provide subject identity, MFA, session and federation. AIOS must keep tenant, position, authority, Board power and material-action authorization semantics.

### Required benchmark dimensions

- OIDC compatibility;
- MFA/passkeys;
- operational complexity;
- backup/recovery;
- claim minimization;
- service identities;
- tenant isolation;
- auditability;
- export/migration;
- security-maintenance cadence.

No production selection is made by this radar.

---

## 8. P0/P1 — Communications Gateway

### Direction

Define the provider-neutral gateway before choosing mail/SMS/messaging vendors.

```text
CommunicationIntent
→ authority / risk / review
→ idempotency
→ CommunicationPort
→ provider
→ delivery result
→ reconciliation / lineage
```

### Required future capability

- email;
- portal notifications;
- optional SMS/messaging where justified;
- templates without bypassing Evidence/provenance;
- delivery reconciliation;
- correction/compensation path;
- per-channel privacy/retention policy;
- provider failover without changing authority.

No client/authority-facing autonomous sending is authorized by this radar.

---

## 9. P1 — Electronic signature

Current relevant technology already on the parent radar: EU DSS for validation.

Additional signing-platform category: Documenso/DocuSeal-class open-source systems may be researched.

Selection criteria:

- signer identity and authentication;
- signed artifact integrity;
- audit evidence;
- timestamp/signature validation;
- EU workflow suitability;
- API integration;
- self-hostability / portability;
- retention/export;
- ability to bind provider transaction to exact AIOS document version.

Signature success never certifies the substantive legal correctness of the document.

---

## 10. P1/P2 — Enterprise Operations / ERP

The project needs ERP-like enterprise operations over time, but a general ERP must not become the AIOS core.

### Native AIOS responsibilities

- mobility cases;
- corporate mobility programmes;
- WorkItems;
- Evidence;
- authority;
- organizational execution;
- readiness and risk;
- mobility-specific cost/timeline state;
- decision lineage.

### External/back-office responsibilities when needed

- accounting journal;
- invoices;
- payroll;
- procurement;
- tax bookkeeping;
- generic asset/inventory administration.

Current state:

```text
ERPNext / Odoo
→ WATCH / DEFER
→ integration candidate only
→ no implementation before real commercial/back-office demand
```

Before adoption, define synchronization ownership for every shared field. Avoid dual-master state.

---

## 11. P1/P2 — Payments

Payment execution is a future R4/R5-class capability depending on amount/purpose and cannot be treated as ordinary API integration.

Required architecture:

- financial intent;
- exact amount/currency/beneficiary;
- budget and authority checks;
- fraud/risk policy;
- idempotency;
- human/Board floor where required;
- provider transaction ID;
- reconciliation;
- refund/compensation semantics;
- append-only financial action lineage.

Provider selection is deliberately deferred.

---

## 12. Data ownership matrix

| Data / meaning | Canonical owner |
|---|---|
| Mobility case state | AIOS |
| Evidence / VerifiedRules | AIOS |
| OrganizationPosition / authority | AIOS |
| WorkItem / Mission semantics | AIOS |
| AgentRun / execution provenance | AIOS |
| Board decision / material authorization | AIOS |
| Authentication session | Identity provider may own session; AIOS maps identity |
| Secret material | Secrets backend |
| Engineering trace/log storage | Observability backend |
| Invoice/accounting journal | Future accounting/ERP system may own its bounded ledger |
| External payment transaction | Payment provider owns network transaction; AIOS owns authorization/reconciliation record |
| Signature transaction | Signature provider owns signing transaction evidence; AIOS owns document/version/provenance relationship |
| Email/SMS delivery | Provider owns delivery transport state; AIOS owns communication intent/authorization/reconciliation |

---

## 13. Integration acceptance template

No technology advances to ADOPT without recording:

```text
capability gap
candidate(s)
AIOS-owned port / contract
data ownership
security/privacy analysis
license/maintenance analysis
failure modes
retry/idempotency
recovery/compensation
cost/operational burden
benchmark/pilot evidence
rollback/replacement plan
acceptance decision
```

High-risk adapters additionally require Command Gateway/materiality mapping and authority/autonomy policy mapping.

---

## 14. Parallel execution programme

### Product track — do not interrupt

```text
L Live Organization
→ M Board Transparency Experience
→ N Learning & Optimization
```

### Integration track

```text
Wave E0 — architecture / inventory
  integration ownership model
  secrets inventory
  backup classification
  telemetry correlation contract

Wave E1 — production-foundation pilots
  OpenTelemetry correlation for L
  secrets-manager bounded pilot
  backup + isolated restore proof

Wave E2 — human/communication foundation
  IdentityPort benchmark
  CommunicationPort contract

Wave E3 — external professional execution
  e-signature validation/signing pilot
  governed communication trial

Wave E4 — commercial operations
  accounting/ERP adapter benchmark
  payment adapter design
```

Each wave is independently acceptance-gated. No wave automatically authorizes the next.

---

## 15. What should not be built now

Do not divert L into:

- a full ERP implementation;
- payroll;
- payment execution;
- broad SSO migration;
- arbitrary outbound communication;
- a new generic workflow engine;
- a second agent framework;
- a giant integration abstraction before the first real adapters exist.

Build only the smallest ports required by proven use cases.

---

## 16. Outcome metrics

The integration programme succeeds only if it improves measurable operation.

Track:

- incidents caused/prevented;
- credential exposure events;
- restore success/time;
- trace completeness;
- mean time to diagnose runtime failures;
- integration availability;
- retries/duplicate external actions;
- provider-specific coupling;
- replacement effort;
- human interventions;
- external-action reconciliation completeness;
- cost per successful governed outcome.

---

## 17. Current decision summary

```text
ADOPTED / EXISTING FOUNDATION
  PostgreSQL
  MinIO/S3-compatible storage
  Redis
  Qdrant (current platform; semantic benchmark still applies)
  Woodpecker self-hosted CI direction

TRIAL-ELIGIBLE / CONTINUE
  OpenTelemetry
  ClamAV
  Promptfoo

PILOT / BENCHMARK
  Docling
  LLMLingua-2
  pgvector vs Qdrant

RESEARCH NOW
  OpenBao-class secrets
  backup/DR toolchain
  Keycloak vs Authentik
  Langfuse / observability backend
  Communications Gateway contract

RESEARCH / WATCH
  EU DSS + signing platform
  ERPNext / Odoo
  feature flags

DEFER
  payment provider
  broad ERP adoption
  Temporal unless durable-wait gap is measured
  OpenFGA until relationship-authorization need justifies it

REJECT BY DEFAULT
  new generic agent framework without measured architectural gap
```

> **The project should proactively discover missing infrastructure, but every integration must remain subordinate to AIOS constitutional semantics and measurable product need.**
