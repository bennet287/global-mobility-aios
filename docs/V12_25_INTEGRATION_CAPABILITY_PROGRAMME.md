# Global Mobility AIOS — V12.25 Integration Capability Programme

**Date:** 2026-08-22
**Status:** ACTIVE CAPABILITY REFERENCE / SUBORDINATE TO MASTER ROADMAP
**Active branch:** `roadmap/global-mobility-aios-v12`
**Accepted runtime baseline:** K.1 COMPLETE / PASS / SEALED
**Current product milestone:** L — Live Organization
**Master scheduling authority:** `ROADMAP.md`
**Technology direction:** `TECHNOLOGY_RADAR_V1_3_2.md`
**Integration architecture:** `ENTERPRISE_INTEGRATION_ARCHITECTURE_V1.md`
**Capability radar:** `AIOS_INTEGRATION_CAPABILITY_RADAR_V1.md`

This document defines integration capability boundaries and proof expectations. It does **not** independently schedule implementation.

If this document uses terms such as E1, E2, pilot, research or candidate, those terms describe capability grouping/evidence posture only. `ROADMAP.md` determines whether the work is PRIMARY, REQUIRED ENABLEMENT, SUPPORTING PARALLEL or DEFERRED / DEMAND-GATED.

---

## 1. Why this programme exists

Global Mobility AIOS must solve two production risks at the same time:

```text
avoid architecture/framework sprawl
        +
avoid neglecting essential production infrastructure
```

Permanent doctrine:

> **Build mobility-specific intelligence and governance natively. Integrate mature commodity capability behind AIOS-owned contracts.**

The governing trigger is product necessity:

```text
product need
→ architectural gap
→ native vs integration vs donor decision
→ bounded contract
→ implementation when ROADMAP.md activates the dependency
```

Not:

```text
useful technology exists
→ integrate it
→ invent the need later
```

---

## 2. Product sequence remains authoritative

The accepted organization sequence remains:

```text
I.1 capability autonomy profile                   SEALED
I.2 shadow autonomy evidence                      SEALED
I.3 promotion eligibility policy                  SEALED
I.4 qualified/temporal evidence evaluation        SEALED
J.1 Austria Agent Organization Runtime            SEALED
K.1 bounded specialist Execution/Coworker Runtime SEALED
L Live Organization                               CURRENT
M Board Transparency Experience                   NEXT AFTER L ACCEPTANCE
N Learning & Optimization                         THEN
```

Integration work may strengthen those milestones but may not replace their proof.

---

## 3. Integration capability groups

These groups are a taxonomy, not a standalone delivery sequence.

### E0 — Architecture / ownership

Defines:

- integration classes;
- port/adapter sovereignty;
- data ownership;
- identity-vs-authority separation;
- telemetry-vs-canonical-Activity separation;
- secret/reference separation;
- communications/payment materiality boundaries;
- ERP boundary;
- adoption lifecycle and scoring;
- integration security envelope.

Canonical records:

```text
docs/ENTERPRISE_INTEGRATION_ARCHITECTURE_V1.md
docs/AIOS_INTEGRATION_CAPABILITY_RADAR_V1.md
docs/TECHNOLOGY_RADAR_V1_3_2.md
```

E0 is architecture/direction only and creates no runtime acceptance claim.

### E1 — Production foundations

#### E1.1 — Runtime observability / correlation

Capability need:

- correlate a real organization cycle across request/objective, WorkItem, ContextBundle, AgentRun, OrganizationExecutionAttempt, durable output and canonical effect where applicable;
- diagnose latency, retries and provider/runtime failure;
- preserve privacy and lineage boundaries.

Permanent distinction:

```text
engineering telemetry != canonical OrganizationActivity
```

OpenTelemetry is the current preferred/trial-eligible implementation direction because an optional vendor-neutral pilot exists. The product requirement is operational correlation, not OpenTelemetry by constitutional decree.

For current scheduling classification, see `ROADMAP.md`.

#### E1.2 — Secrets-management boundary

Capability need when a real credential lifecycle requires it:

- AIOS-owned secrets port/configuration boundary;
- secret material excluded from ContextBundle, prompt, memory and Activity;
- rotation/revocation/recovery proof;
- minimum provider coupling.

Permanent rule:

```text
secret != prompt
secret != ContextBundle
secret != memory
secret != OrganizationActivity
```

OpenBao-class infrastructure remains a candidate, not an automatically scheduled dependency.

#### E1.3 — Backup / isolated restore

Capability need:

- classify canonical/derived/cache/external state;
- protect PostgreSQL + object-storage state as applicable;
- restore into an isolated environment;
- verify migration/schema/canonical-state integrity after restoration;
- define RPO/RTO targets appropriate to the deployment.

Permanent rule:

```text
backup created != recovery proven
```

Backup/restore becomes a release blocker when the actual deployment/recoverability dependency requires it, not merely because backup tooling is available.

### E2 — Identity + communications

#### Identity

Candidate capability:

- benchmark Keycloak / Authentik-class IdPs when a multi-user/deployment authentication need reaches the active product path.

Required contract:

```text
IdP authenticates
AIOS maps principal
AIOS authorizes
```

No IdP may own Board authority, `OrganizationPosition`, capability authority, autonomy or material-action policy.

#### Communications Gateway

When governed outbound communications become an active product dependency, define:

- `CommunicationIntent` semantics;
- tenant/case/recipient scope;
- message class/materiality;
- review/approval floors;
- idempotency;
- provider delivery identifiers;
- retries;
- compensation/correction;
- privacy/retention;
- Command Gateway mapping.

Provider selection remains secondary to contract correctness.

### E3 — E-signature / governed professional execution

Demand/dependency gated.

Candidate capability work includes:

- EU DSS validation;
- signing-platform evaluation;
- exact AIOS document-version binding;
- governed communications trial;
- external-result reconciliation.

No government submission or other reserved action is authorized merely by implementing E3 infrastructure.

### E4 — Commercial / ERP / payments

Demand gated.

#### ERP/accounting

ERPNext/Odoo-class systems remain integration candidates, not AIOS core platforms.

Before activation:

- real invoicing/accounting demand must exist;
- master-system ownership must be defined;
- mobility case truth must remain AIOS-owned;
- dual-master models must be avoided unless explicitly justified.

#### Payments

Before activation:

- exact financial authority classes must exist;
- amount/currency/beneficiary semantics must be typed;
- Board/human floors must be mapped;
- reconciliation and refund/compensation semantics must be specified.

---

## 4. Integration sovereignty rules

Permanent rules:

> **Identity providers authenticate; AIOS authorizes.**

> **Telemetry observes AIOS truth; it does not become AIOS truth.**

> **Secrets may be injected into runtimes; they may not become context or memory.**

> **External execution requires governed intent, provenance, idempotency and recovery semantics.**

> **ERP/accounting may own bounded back-office ledgers; it never owns mobility truth or Board authority.**

> **No integration may bypass the Command Gateway for a material action.**

---

## 5. Candidate prioritization scorecard

When `ROADMAP.md` identifies a capability gap that may require integration, candidate solutions may be assessed on a 0–5 scale for:

```text
necessity
outcome benefit
security/privacy fit
maturity
operational burden (inverse)
portability
cost efficiency
AIOS sovereignty fit
integration complexity (inverse)
replacement ease
```

A high score does not authorize adoption or scheduling. It informs the build/integrate/adapt decision for an already-demonstrated need.

High-risk capabilities additionally require materiality/authority mapping.

---

## 6. Required evidence for production ADOPT

Before production adoption of an integration, prove as applicable:

- capability problem statement linked to an active roadmap dependency;
- architecture contract/port;
- selected implementation and version strategy;
- security/privacy assessment;
- data ownership declaration;
- credential model;
- retry/idempotency model;
- failure/recovery/compensation semantics;
- observability policy;
- test/benchmark evidence;
- deployment/backup expectations;
- rollback/replacement plan;
- acceptance record;
- ROADMAP/CHANGELOG reconciliation.

---

## 7. Live Organization as the current proving ground

Current L needs may pull integration capability forward only where the need is concrete.

Valid example:

```text
L needs cross-run latency/retry/runtime diagnosis
→ observability/correlation is an active capability gap
→ evaluate/use the existing OpenTelemetry direction
```

Invalid example:

```text
observability product exists
→ integrate it
→ invent a product use later
```

This rule applies to every candidate.

---

## 8. CI / acceptance doctrine

For every activated runtime/integration slice:

```text
implementation
→ focused tests
→ migration/schema verification if affected
→ security/privacy/authority checks if affected
→ repository policy / complete PR diff hygiene
→ Woodpecker proof lanes
→ documentation reconciliation
→ acceptance only after observed PASS
```

Historical GitHub Actions evidence remains historical evidence and must not be relabeled as Woodpecker proof.

Documentation-only commits do not inherit runtime acceptance automatically.

---

## 9. Non-goals

This programme does not independently authorize:

- full ERP implementation;
- payment execution;
- payroll;
- production IdP migration;
- autonomous outbound communications;
- automatic signing/submission;
- new generic agent frameworks;
- another organization datastore;
- observability data as canonical Activity;
- secrets in AI context;
- external provider ownership of AIOS authority;
- implementation merely because a candidate is listed in a Radar.

---

## 10. Success criteria

The programme succeeds if activated integrations improve product and production outcomes without increasing external ownership of AIOS semantics.

Desired effects:

```text
runtime traceability         ↑
credential hygiene           ↑
recoverability               ↑
integration replaceability   ↑
external-action auditability ↑
production readiness         ↑

provider lock-in             ↓
secret sprawl                ↓
mean diagnosis time          ↓
duplicate external actions   ↓
architecture duplication     ↓
```

---

## 11. Scheduling authority

This document intentionally has **no independent implementation queue**.

The active classification and timing for observability, backup, secrets, identity, communications, e-signature, ERP and payments are defined in `ROADMAP.md`.

When product necessity changes, update `ROADMAP.md` first, then reconcile this capability reference and the relevant Radar/architecture records.

> **The Integration Radar and programme help choose and govern capability. They do not choose what the product builds next.**
