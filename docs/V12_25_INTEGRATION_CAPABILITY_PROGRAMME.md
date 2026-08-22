# Global Mobility AIOS — V12.25 Integration Capability Programme

**Date:** 2026-08-22
**Status:** ACTIVE PROGRAMME DIRECTION / DOCUMENTATION-ONLY ENTRY
**Active branch:** `roadmap/global-mobility-aios-v12`
**Accepted runtime baseline:** K.1 COMPLETE / PASS / SEALED
**Next product milestone:** L — Live Organization
**Technology direction:** `TECHNOLOGY_RADAR_V1_3_2.md`
**Integration architecture:** `ENTERPRISE_INTEGRATION_ARCHITECTURE_V1.md`
**Capability radar:** `AIOS_INTEGRATION_CAPABILITY_RADAR_V1.md`

V12.25 adds a formal enterprise-integration track without changing the active product sequence or claiming production adoption of any new provider.

---

## 1. Why V12.25 exists

The project has reached the point where missing infrastructure can become a production risk even when the AI architecture is sound.

The project therefore needs to solve two problems simultaneously:

```text
avoid architecture/framework sprawl
        +
avoid neglecting essential production infrastructure
```

The permanent decision is:

> **Build mobility-specific intelligence and governance natively. Integrate mature commodity capability behind AIOS-owned contracts.**

---

## 2. Current accepted sequence

```text
I.1 capability autonomy profile                  SEALED
I.2 shadow autonomy evidence                     SEALED
I.3 promotion eligibility policy                 SEALED
I.4 qualified/temporal evidence evaluation       SEALED
J.1 Austria Agent Organization Runtime           SEALED
K.1 bounded specialist Execution/Coworker Runtime SEALED
L Live Organization                              NEXT
M Board Transparency Experience                  LATER
N Learning & Optimization                        LATER
```

The new integration programme runs in parallel. It does not reorder L/M/N.

---

## 3. V12.25 tracks

### Track P — Product / Live Organization

Primary next product work remains L.

L target:

```text
real Austria objective / owner
→ accepted WorkItems
→ current canonical ContextBundles
→ bounded specialist execution
→ durable specialist outputs
→ owner synthesis readiness
→ material owner synthesis result
→ persisted OrganizationActivity / decisions
→ blocked-work reason where applicable
→ runtime/tool lineage
→ Evidence / rule provenance where available
→ authority/autonomy state
→ latency / retries / governance telemetry
→ Cockpit read model backed only by persisted AIOS truth
```

### Track E — Enterprise Integration Foundation

```text
E0 Architecture + capability radar
E1 Observability + secrets + backup foundations
E2 Identity + Communications contracts
E3 E-signature + governed communications trial
E4 Accounting / ERP / payments — demand gated
```

Track E may support Track P but may not replace product proof with infrastructure work.

---

## 4. V12.25-E0 — Architecture and ownership — DOCUMENTED

E0 establishes:

- integration classes;
- port/adapter sovereignty model;
- data ownership matrix;
- identity-vs-authority separation;
- telemetry-vs-canonical-activity separation;
- secret/reference separation;
- communications/payment materiality path;
- ERP boundary;
- adoption lifecycle and scoring;
- integration security envelope.

Canonical records:

```text
docs/ENTERPRISE_INTEGRATION_ARCHITECTURE_V1.md
docs/AIOS_INTEGRATION_CAPABILITY_RADAR_V1.md
docs/TECHNOLOGY_RADAR_V1_3_2.md
```

E0 is documentation/direction only. It creates no runtime acceptance claim.

---

## 5. V12.25-E1 — Production foundation — NEXT PARALLEL PILOTS

E1 should be implemented in bounded sub-slices rather than as one platform rewrite.

### E1.1 — L telemetry correlation

Goal:

- use existing OpenTelemetry direction;
- correlate the first L organization cycle across request/objective, WorkItem, ContextBundle, AgentRun, OrganizationExecutionAttempt and durable output;
- preserve `OrganizationActivity` as canonical business/governance truth;
- capture latency/retry/runtime telemetry without Evidence/secret leakage.

Acceptance requires observable end-to-end correlation plus privacy/lineage tests.

### E1.2 — Secrets-manager pilot

Goal:

- define a minimal `SecretsPort` or equivalent configuration boundary only where proven necessary;
- pilot one non-production credential path;
- keep secret material out of ContextBundle, prompt, memory and activity;
- prove rotation/revocation/recovery behavior before broader adoption.

No production secret migration is pre-authorized.

### E1.3 — Backup / restore proof

Goal:

- classify canonical/derived/cache/external state;
- establish PostgreSQL + object-storage backup policy;
- produce an isolated restore proof;
- verify migration/schema/canonical-state integrity after restoration;
- define initial RPO/RTO targets.

A backup file without restore evidence does not pass.

---

## 6. V12.25-E2 — Identity and communications contract

### E2.1 — Identity benchmark

Research Keycloak and Authentik-class candidates.

Required contract:

```text
IdP authenticates
AIOS maps principal
AIOS authorizes
```

No IdP may own Board authority, `OrganizationPosition`, capability authority, autonomy or material-action policy.

### E2.2 — Communications Gateway contract

Define:

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

---

## 7. V12.25-E3 — External professional execution

Demand/sequence gated.

Candidate work:

- EU DSS validation pilot;
- open-source signing-platform evaluation;
- exact AIOS document-version binding;
- governed communications trial;
- external-result reconciliation.

No government submission or other reserved action is authorized merely by completing E3.

---

## 8. V12.25-E4 — Commercial / ERP / payments

Explicitly demand gated.

### ERP/accounting

ERPNext/Odoo-class systems remain integration candidates, not AIOS core platforms.

Before a pilot:

- real invoicing/accounting demand must exist;
- master-system ownership must be defined;
- mobility case truth must remain AIOS-owned;
- no dual-master data model may be introduced casually.

### Payments

Before design advances:

- exact financial authority classes must be defined;
- amount/currency/beneficiary semantics must be typed;
- Board/human floors must be mapped;
- reconciliation and refund/compensation semantics must be specified.

---

## 9. Integration prioritization scorecard

Each candidate should be assessed on a 0–5 scale for:

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

A high score does not authorize adoption. It prioritizes research/pilot work.

High-risk capabilities additionally require materiality/authority mapping.

---

## 10. Required documentation for every adopted integration

Before production ADOPT:

- capability problem statement;
- architecture contract/port;
- selected implementation and version strategy;
- security/privacy assessment;
- data ownership declaration;
- credential model;
- retry/idempotency model;
- failure/recovery/compensation semantics;
- observability policy;
- test/benchmark evidence;
- deployment/backup plan;
- rollback/replacement plan;
- acceptance record;
- ROADMAP/CHANGELOG reconciliation.

---

## 11. Live Organization must remain the proving ground

The next integrations should be justified through actual L needs.

Example:

```text
L needs runtime latency / retries / cross-run correlation
→ OpenTelemetry E1.1 has a measurable product use
```

Not:

```text
observability product exists
→ integrate it
→ invent use later
```

This rule applies to every candidate.

---

## 12. CI / acceptance doctrine

Forward heavy proof runs should use the accepted Woodpecker direction once current repository wiring is confirmed.

Historical GitHub Actions proofs remain valid historical evidence and must not be relabeled.

For every new runtime slice:

```text
implementation
→ focused tests
→ migration/schema verification if affected
→ repository policy/diff hygiene
→ Woodpecker proof lanes
→ documentation reconciliation
→ acceptance only after observed PASS
```

Documentation-only commits do not inherit a runtime PASS automatically.

---

## 13. Non-goals

V12.25 does not authorize:

- full ERP implementation;
- payment execution;
- payroll;
- production IdP migration;
- autonomous outbound communications;
- automatic signing/submission;
- new generic agent frameworks;
- another organization datastore;
- observability data as canonical activity;
- secrets in AI context;
- external provider ownership of AIOS authority.

---

## 14. Success criteria

The programme succeeds if the project becomes more operationally mature without becoming more externally coupled.

Target effects:

```text
runtime traceability        ↑
credential hygiene          ↑
recoverability              ↑
integration replaceability  ↑
external-action auditability ↑
production readiness        ↑

provider lock-in            ↓
secret sprawl               ↓
mean diagnosis time         ↓
duplicate external actions  ↓
architecture duplication    ↓
```

---

## 15. Next implementation decision

The project should continue into **L Live Organization** and select only integration work that directly strengthens that proof.

Recommended immediate parallel ordering:

```text
1. L Live Organization core
2. E1.1 OpenTelemetry correlation for L
3. E1.3 backup / isolated restore proof
4. E1.2 secrets-manager bounded pilot
5. E2.1 identity benchmark
6. E2.2 Communications Gateway contract
```

ERP, payments and broad e-signature adoption remain later/demand-gated.

> **The Integration Radar is a production-maturity track, not a substitute for proving the AI organization.**
