# Global Mobility AIOS — Technology Radar V1.3.2

**Date:** 2026-08-22
**Status:** ACTIVE CANONICAL RADAR REVISION
**Supersedes for active radar direction:** `TECHNOLOGY_RADAR_V1_3_1.md`
**Architecture references:** `GLOBAL_MOBILITY_AIOS_COMBINED_ARCHITECTURE_V1_1.md`, `ENTERPRISE_INTEGRATION_ARCHITECTURE_V1.md`
**Integration radar:** `AIOS_INTEGRATION_CAPABILITY_RADAR_V1.md`
**Accepted organization/runtime baseline:** I.1–I.4 COMPLETE / PASS / SEALED; J.1 COMPLETE / PASS / SEALED; K.1 COMPLETE / PASS / SEALED
**Next product increment:** L — Live Organization
**Forward CI direction:** self-hosted Woodpecker parity proven; historical GitHub Actions evidence remains historical evidence

Technology Radar V1.3.2 preserves the evidence-driven adoption model and adds a formal enterprise integration/capability-gap programme.

> **External infrastructure provides capability. AIOS owns meaning, truth and authority.**

> **No new major framework by default; no missing commodity infrastructure by neglect.**

---

## 1. Adoption lifecycle

```text
REFERENCE
  ↓
RESEARCH
  ↓
BENCHMARK
  ↓
PILOT
  ↓
TRIAL
  ↓
ADOPT
```

Additional governance states:

```text
WATCH
DEFER
REJECT
STRATEGIC DONOR
```

No state below `ADOPT` is a production-adoption claim.

---

## 2. Current strategic set

### Organization / runtime / context

| Technology | AIOS capability | State |
|---|---|---|
| Munder Difflin v0.4.4 | Organization Fabric / runtime / communication / Skills donor | STRATEGIC DONOR / CONTROLLED ADOPTION |
| Plasma Wiki 1.2.0 | Context-efficient project/organizational knowledge beneath Context Broker | PINNED DONOR PRESENT / PILOT APPROVED |
| Plasma Fractal 1.1.0 | Recursive bounded Mission decomposition / hierarchical execution | PINNED DONOR PRESENT / PILOT APPROVED — SANDBOXED ENGINEERING ONLY |
| LLMLingua-2 | Context/token compression behind `ContextCompressionPort` | SELECTED PRIMARY PILOT |
| Local/open models | economical inference | BENCHMARK THROUGH MODEL ROUTER |
| Hosted/frontier APIs | difficult/high-risk reasoning | SELECTIVE ESCALATION RESOURCE |

The Plasma vendor source import is now present in the V12 repository. Vendoring remains distinct from production adoption.

### Existing platform candidates

| Technology | Intended capability | State |
|---|---|---|
| Promptfoo | AI regression/adversarial evaluation | PILOT COMPLETE / TRIAL-ELIGIBLE |
| OpenTelemetry | vendor-neutral engineering telemetry | PILOT COMPLETE / TRIAL-ELIGIBLE; PRIORITY FOR L |
| ClamAV | upload malware scanning/quarantine | PILOT COMPLETE / TRIAL-ELIGIBLE |
| Docling | document normalization/structured intelligence | PILOT IN PROGRESS |
| Presidio | privacy/sensitive-data processing | QUEUED PILOT |
| urlwatch | official-source change monitoring | QUEUED PILOT |
| pgvector | governed semantic retrieval | BENCHMARK |
| Qdrant | semantic retrieval alternative/current platform capability | BENCHMARK AGAINST PGVECTOR |
| Pydantic AI | typed runtime candidate | RESEARCH / PILOT CANDIDATE; NO NEED PROVEN FOR K.1 |
| Langfuse | LLM/agent observability behind OpenTelemetry | RESEARCH / PILOT CANDIDATE |
| Temporal | durable waits/retries/resumption | DEFERRED PILOT / GAP-TRIGGERED |
| OpenFGA | relationship authorization beneath AIOS semantics | DEFERRED PILOT |
| DSPy | offline AI-program optimization | RESEARCH |
| EU DSS | electronic-signature validation | RESEARCH |

### New enterprise-integration capability candidates

| Capability | Candidates / class | State |
|---|---|---|
| Secrets management | OpenBao-class | RESEARCH NOW → bounded PILOT |
| Identity / SSO | Keycloak / Authentik-class | RESEARCH NOW |
| PostgreSQL backup / PITR | pgBackRest / WAL-G-class | RESEARCH NOW |
| Encrypted backup / restore | Restic-class | RESEARCH NOW |
| Observability backend | Langfuse and/or conventional OTel-compatible backend | RESEARCH / PILOT CANDIDATE |
| Communications | provider-neutral email/portal/SMS adapters | CONTRACT DESIGN NOW; PROVIDER DEFERRED |
| Open-source e-signing | Documenso / DocuSeal-class | RESEARCH / WATCH |
| ERP/accounting | ERPNext / Odoo / accounting integration | WATCH / DEFER |
| Payments | provider-neutral payment port | DEFER PROVIDER SELECTION |
| Feature flags | Unleash-class | WATCH |

---

## 3. Capability-first adoption rule

```text
Capability gap?
  ├── no → do not add technology
  └── yes
       ↓
Global Mobility differentiator?
  ├── yes → build/extend AIOS-native domain capability
  └── no
       ↓
Mature infrastructure available?
  ├── yes → integrate behind AIOS-owned port
  └── no → smallest bounded implementation or defer
```

This prevents two opposite failures:

- building every commodity capability internally;
- turning AIOS into a collection of externally-owned frameworks.

---

## 4. Current L interaction

The next product milestone remains L — Live Organization.

Technology work may support L but may not replace it.

Priority integration contribution to L:

```text
real persisted Austria organization cycle
        ↓
canonical AIOS Activity / execution truth
        +
OpenTelemetry correlation
        ↓
latency / retries / runtime/tool telemetry
        ↓
Cockpit / transparency read model
```

Permanent distinction:

```text
engineering telemetry != canonical AIOS Activity
```

L should prove organization behavior using persisted AIOS truth; observability provides correlated operational evidence.

---

## 5. Secrets decision

Production AIOS should not rely indefinitely on flat `.env` files for growing provider credentials.

Target:

```text
AIOS config
→ secret reference
→ SecretsPort
→ secret backend
→ runtime injection
```

Permanent rules:

```text
secret != prompt
secret != ContextBundle
secret != memory
secret != OrganizationActivity
secret != repository content
```

OpenBao-class infrastructure enters RESEARCH NOW. First pilot must be bounded to non-production credentials and must test retrieval, scope, rotation/revocation and recovery.

---

## 6. Identity / SSO decision

Keycloak and Authentik-class systems enter RESEARCH NOW.

Permanent rule:

> **Identity Provider != Authority Provider.**

An IdP may authenticate a human/service identity. AIOS remains authoritative for tenant, role, `OrganizationPosition`, reserved powers, capability authority, autonomy and material-action permission.

No production identity migration is authorized by this radar.

---

## 7. Backup / DR decision

Backup infrastructure is now a production-foundation priority.

Canonical classification:

```text
CANONICAL → restore-tested backup required
DERIVED   → may be rebuilt
CACHE     → may be discarded
EXTERNAL  → reconciliation required
```

Research now:

- PostgreSQL PITR/scheduled backup via pgBackRest/WAL-G-class tooling;
- encrypted off-host backup via Restic-class tooling;
- MinIO/S3 versioning/replication strategy;
- isolated restore proof;
- RPO/RTO definition.

A backup file existing is not acceptance. Restore must be demonstrated.

---

## 8. Communications decision

A provider-neutral `CommunicationPort` / Communications Gateway is architecturally approved for design.

```text
CommunicationIntent
→ risk/materiality/authority/review
→ Command Gateway where material
→ CommunicationPort
→ provider
→ delivery result
→ reconciliation / lineage
```

No current stage authorizes autonomous client/authority-facing communication merely because the gateway contract exists.

---

## 9. E-signature decision

EU DSS remains a research candidate for electronic-signature validation.

Documenso/DocuSeal-class signing platforms may be evaluated as execution providers behind a `SignaturePort`.

Permanent distinction:

```text
signature transaction evidence
!=
substantive legal correctness of document content
```

E-signature remains P1, before material filing workflows but after L foundation.

---

## 10. ERP / accounting decision

The project should not implement or adopt a full ERP as the AIOS core.

Current decision:

```text
ERPNext / Odoo
→ WATCH / DEFER
→ future back-office integration candidates
```

AIOS remains canonical for mobility cases, Evidence, organizational execution, WorkItems, authority and decision lineage.

A future ERP/accounting system may own bounded ledgers such as invoices/accounting/payroll/procurement.

Every shared field must have one declared master system; dual-master synchronization is prohibited by default.

---

## 11. Payments decision

Payment provider selection is deferred.

Future architecture requires:

```text
financial intent
→ exact amount/currency/beneficiary
→ authority/budget/risk/fraud controls
→ Command Gateway / required Human or Board gate
→ PaymentPort
→ provider
→ reconciliation
```

No agent receives direct payment authority from possession of an SDK or API key.

---

## 12. Munder boundary

Munder remains a donor/reference, not the AIOS organization.

Useful donor areas continue to include communication/routing, presence, runtime mechanics, Skills, schedules/triggers/heartbeats, provider abstraction, telemetry/transcripts, cost/token signals and live-organization concepts.

Rejected assumptions remain:

- file/SQLite state as authoritative production truth;
- unlimited implicit authority;
- direct material mutation bypassing AIOS governance;
- provider-owned organization semantics;
- donor UI as final product identity.

K.1 materially strengthens the decision to prefer the native runtime: the bounded specialist execution path was accepted without another agent framework.

---

## 13. Plasma boundary

### Wiki

```text
Wiki != Evidence
Wiki != VerifiedRule
Wiki != canonical legal truth
retrieved knowledge != executable instruction
```

### Fractal

Hard gates remain:

- native Mission/WorkItem meaning stays canonical;
- child scope cannot exceed parent scope;
- no automatic authority inheritance;
- no automatic verifier independence;
- bounded recursion/parallelism/time/cost;
- no direct canonical mutation.

Pinned vendor source presence does not equal adoption.

---

## 14. LLMLingua-2 decision

LLMLingua-2 remains the selected primary pilot behind:

```text
Context Broker
→ ContextCompressionPort
→ LLMLingua2Adapter
```

Compression remains derived context, never source truth. Initial R3–R5 protected context retains zero semantic compression for governance-critical material.

No production adoption claim is added by V1.3.2.

---

## 15. Model Router / AI Economics

Permanent rule:

> **A model earns capability eligibility through measured evaluation, not self-reported confidence.**

Cost remains subordinate to quality, authority, risk, Evidence, verification, privacy, SLA and reliability floors.

Target economic metric:

> **€ / successful governed outcome**

Integration economics should additionally measure maintenance burden, replacement cost, external-service dependency and incident cost.

---

## 16. Integration security / sovereignty

No external technology may become authoritative for:

- Global Mobility domain meaning;
- Evidence / VerifiedRules;
- canonical mobility state;
- organizational identity;
- authority/autonomy/risk;
- WorkItem/Mission semantics;
- Decision Readiness;
- Immune-System policy;
- Command Gateway decisions;
- Board authority;
- canonical Transparency/Decision lineage.

Each production adapter should eventually declare scope, credential reference, allowed actions, data classification, idempotency, timeout/retry, recovery semantics, rate/budget limits, observability policy and kill-switch/circuit behavior.

---

## 17. Parallel technology waves

```text
Wave E0 — NOW
  enterprise integration architecture
  capability/integration inventory
  ownership matrix

Wave E1 — alongside L
  OpenTelemetry correlation
  secrets-manager bounded pilot
  backup + isolated restore proof

Wave E2
  IdentityPort benchmark
  Communications Gateway contract

Wave E3
  e-signature validation/signing pilot
  governed communications trial

Wave E4 — demand gated
  accounting / ERP adapter benchmark
  payment adapter design
```

No wave automatically authorizes the next.

---

## 18. No-new-framework default

> **Do not add another major agent framework unless a measured architectural gap cannot be addressed cleanly by AIOS + the current donor/adapter set.**

At the same time, the Technology Radar must proactively identify necessary infrastructure gaps instead of waiting for them to be discovered ad hoc.

---

## 19. Permanent sovereignty rule

> **Adopt commodity capability aggressively when evidence supports it. Build differentiating mobility intelligence natively. Never surrender the constitution.**
