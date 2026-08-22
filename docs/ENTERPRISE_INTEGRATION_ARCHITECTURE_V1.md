# Global Mobility AIOS — Enterprise Integration Architecture V1

**Date:** 2026-08-22
**Status:** ACTIVE ARCHITECTURE DIRECTION / NO PRODUCTION-ADOPTION CLAIM
**Active branch:** `roadmap/global-mobility-aios-v12`
**Parent architecture:** `GLOBAL_MOBILITY_AIOS_COMBINED_ARCHITECTURE_V1_1.md`
**Current product sequence:** I.1–I.4 SEALED → J.1 SEALED → K.1 SEALED → L Live Organization NEXT

> **External infrastructure provides capability. AIOS owns meaning, truth and authority.**

This document defines how Global Mobility AIOS may adopt enterprise infrastructure without allowing an identity provider, ERP, communications provider, payment processor, observability backend, secrets manager or other external system to become the AIOS system of organizational truth.

The purpose is not to build a generic ERP or accumulate integrations. The purpose is to make AIOS production-capable while preserving the constitutional architecture already proven through K.1.

---

## 1. Core decision

Global Mobility AIOS should use a **port / adapter / governed boundary** model for non-differentiating enterprise capabilities.

```text
AIOS domain / organization semantics
            ↓
AIOS-owned contract / port
            ↓
policy + authority + provenance boundary
            ↓
replaceable adapter
            ↓
external or open-source infrastructure
```

Permanent rule:

```text
CAN INTEGRATE != MAY SURRENDER AUTHORITY
```

An external system may execute a bounded capability. It may not redefine:

- Human Owner / Board sovereignty;
- `OrganizationPosition` identity;
- WorkItem or Mission meaning;
- Evidence, SourceSnapshots or VerifiedRules;
- canonical mobility/case state;
- Capability, Authority, Autonomy or Risk;
- Decision Readiness;
- Command Gateway authorization;
- Organizational Immune System policy;
- canonical Decision / Activity / Tool / Context lineage;
- autonomy promotion/demotion truth.

---

## 2. Integration classes

Every integration belongs to one of four classes.

| Class | Purpose | Examples | Canonical AIOS authority? |
|---|---|---|---|
| Infrastructure | Runtime/platform support | secrets, telemetry, backup, object storage | No |
| Identity / access support | Authenticate or federate identities | IdP / SSO | No — AIOS still authorizes |
| Operational execution | Perform bounded external work | email, e-signature, payments | No — AIOS authorizes intent/action |
| Enterprise back-office | Accounting/admin/resource operations | ERP/accounting/payroll | No — external ledger may be authoritative only for its own bounded accounting domain |

The integration class determines how strongly the Command Gateway, materiality model, audit lineage and human/Board authority floor apply.

---

## 3. Canonical integration fabric

Target architecture:

```text
                         HUMAN OWNER / BOARD
                                │
                         Global Mobility AIOS
                                │
                  Organization / Governance Runtime
                                │
               ┌────────────────┼────────────────┐
               │                │                │
          Domain Truth      Command Gateway   Transparency
               │                │                │
               └────────────────┼────────────────┘
                                │
                     Integration Contract Layer
                                │
       ┌────────────┬────────────┼───────────┬────────────┐
       │            │            │           │            │
 IdentityPort  SecretsPort  ObservabilityPort CommunicationPort BackupPort
       │            │            │           │            │
       ├────────────┼────────────┼───────────┼────────────┤
       │            │            │           │            │
 SignaturePort  AccountingPort PaymentPort ERPPort   future adapters
       │            │            │           │
       ▼            ▼            ▼           ▼
 replaceable external/open-source infrastructure
```

No adapter may expose a direct canonical database mutation path merely for convenience.

---

## 4. Identity and SSO boundary

Identity infrastructure answers:

> **Who authenticated?**

AIOS answers:

> **What may this principal access, decide, approve or execute in this tenant/case/organization context?**

Target flow:

```text
Identity Provider
      ↓
authenticated subject / claims
      ↓
AIOS Principal mapping
      ↓
tenant + role + position context
      ↓
AIOS authority / reserved-power evaluation
      ↓
allowed / blocked / escalated
```

Permanent invariant:

> **Identity Provider != Authority Provider.**

Candidate technologies may include Keycloak or Authentik, but no provider is adopted by this document.

Initial research criteria:

- OIDC / OAuth 2.x support;
- MFA and passkey capability;
- tenant/realm isolation;
- service-account controls;
- claim minimization;
- auditability;
- recovery/admin controls;
- migration/exportability;
- ability to keep final authorization in AIOS.

---

## 5. Secrets and credential architecture

The current project already interacts with database credentials, CI/OAuth secrets, external tunnels and future model/provider credentials. `.env` files remain acceptable for bounded local development, but they are not the production destination.

Target:

```text
AIOS configuration
      ↓
secret reference
      ↓
SecretsPort
      ↓
secret backend
      ↓
shortest-necessary runtime injection
```

Permanent rules:

```text
secret != agent memory
secret != prompt context
secret != OrganizationActivity
secret != Decision rationale
secret != repository content
```

Candidate direction: OpenBao-class secret management behind an AIOS-owned contract.

Required capabilities before adoption:

- encrypted storage;
- scoped machine identity;
- rotation;
- revocation;
- audit trail;
- environment isolation;
- no secret material in normal application logs;
- safe backup/recovery;
- replaceability.

---

## 6. Observability and Live Organization

Observability is the first integration capability directly aligned with **L — Live Organization**.

AIOS already needs to reconstruct business/governance truth. Engineering telemetry serves a different purpose.

```text
canonical AIOS Activity / Decision Lineage
                !=
engineering telemetry / trace data
```

Both can share correlation identifiers without becoming the same data model.

Target correlation:

```text
HTTP / trigger
    ↓
Mission / objective
    ↓
WorkItem
    ↓
ContextBundle
    ↓
AgentRun
    ↓
OrganizationExecutionAttempt
    ↓
OrganizationalActionOutput
    ↓
Command Gateway / canonical effect

correlated by stable trace identifiers where appropriate
```

Candidate telemetry dimensions:

- trace/span IDs;
- tenant/case-safe correlation IDs;
- WorkItem ID;
- AgentRun ID;
- execution-attempt ID;
- runtime/provider class;
- latency;
- retries;
- token/compute cost;
- tool calls;
- verification latency;
- Command Gateway outcome;
- incident/circuit correlation.

OpenTelemetry is already the preferred vendor-neutral telemetry foundation. A backend such as Langfuse and/or a conventional trace/metrics/log stack may be evaluated behind it.

Permanently forbidden:

- storing unrestricted Evidence/documents in telemetry by default;
- treating telemetry as canonical Activity;
- allowing an observability vendor to define organizational semantics;
- exposing secrets or protected personal data in spans/logs.

---

## 7. Backup and disaster recovery

Global Mobility AIOS must classify state by recovery requirement.

```text
CANONICAL
→ must be recoverable and restore-tested

DERIVED
→ may be rebuilt from canonical sources

CACHE
→ may be discarded

EXTERNAL
→ must be reconciled with external provider state after recovery
```

Initial targets:

- PostgreSQL point-in-time / scheduled backup strategy;
- MinIO/S3-compatible object backup/versioning strategy;
- encryption at rest and in transit;
- off-host/off-machine copy;
- documented RPO/RTO targets;
- restore tests rather than backup-file existence only;
- migration-aware recovery procedure;
- secrets recovery kept separate from ordinary data backup;
- explicit Qdrant/retrieval rebuild vs backup policy.

Candidate tooling may include pgBackRest/WAL-G-class PostgreSQL tooling and Restic-class encrypted backup tooling. Selection remains evidence-driven.

---

## 8. Communications Gateway

AI employees must not directly own arbitrary SMTP/SMS/messaging credentials or bypass AIOS authority.

Target:

```text
AI Employee / professional workflow
        ↓
CommunicationIntent
        ↓
materiality + risk + authority + policy
        ↓
Command Gateway where material
        ↓
CommunicationPort
        ↓
provider adapter
        ↓
email / portal / SMS / messaging channel
        ↓
delivery result / external event
        ↓
AIOS reconciliation + lineage
```

Communications are consequence-sensitive. Client-facing or authority-facing messages may require stronger autonomy/human-review floors than internal notifications.

Required semantics:

- recipient identity;
- tenant/case scope;
- message purpose/class;
- content provenance;
- approval/review state where required;
- idempotency;
- delivery provider/message ID;
- retry policy;
- correction/compensation semantics;
- retention/privacy classification.

The gateway must support future provider replacement without changing organizational authority.

---

## 9. Electronic signature

E-signature is an execution capability, not canonical mobility truth.

Target:

```text
AIOS document version
      ↓
validation / required review
      ↓
signature intent
      ↓
authority / signer identity / policy
      ↓
SignaturePort
      ↓
external signature service
      ↓
signed artifact + provider evidence
      ↓
AIOS verification / provenance / locked version relationship
```

Research candidates include EU DSS for validation and open-source signing platforms such as Documenso/DocuSeal-class systems. No production provider is selected here.

A signature provider may attest that a signing transaction occurred. It does not automatically determine that the underlying mobility claim or document content is legally correct.

---

## 10. Accounting, ERP and commercial operations

AIOS should **not** become a general-purpose ERP.

AIOS should own mobility/business semantics such as:

- client/corporate mobility case state;
- Evidence and regulated conclusions;
- WorkItems and organizational execution;
- authority and approvals;
- mobility-specific cost/readiness data;
- canonical operational lineage.

A back-office system may own bounded administrative/accounting semantics such as:

- invoice ledger;
- accounting journal;
- payroll;
- procurement;
- tax bookkeeping;
- inventory/assets if ever relevant.

Target:

```text
AIOS Commercial / Enterprise Operations
              ↓
AccountingPort / ERPPort
              ↓
ERPNext / Odoo / accounting provider candidate
```

Current decision:

> **ERPNext/Odoo are WATCH / DEFER integration candidates, not AIOS core dependencies.**

Commercial operations should be introduced only when real billing/accounting/resource demand exists.

---

## 11. Payments and financial execution

No agent may directly charge, transfer or refund money merely because a payment SDK is available.

Target:

```text
financial intent
    ↓
amount / currency / beneficiary / purpose
    ↓
budget + authority + materiality + fraud/risk checks
    ↓
Command Gateway / required human authority
    ↓
PaymentPort
    ↓
provider
    ↓
external payment result
    ↓
reconciliation / append-only lineage
```

A future payment provider is an executor. AIOS remains responsible for whether the transaction was organizationally authorized.

---

## 12. Integration security envelope

Every production adapter should eventually declare:

```text
integration_id
capability
provider/adapter version
allowed tenants/scopes
authorized action classes
credential reference
network destination policy
data classification
idempotency semantics
timeout/retry policy
rate/budget limits
recovery semantics
observability policy
kill-switch/circuit policy
```

High-consequence adapters should support:

- explicit allowlists;
- least-privilege credentials;
- rate limits;
- blast-radius bounds;
- circuit breakers;
- deterministic idempotency;
- auditable external IDs;
- reconciliation;
- compensation where possible;
- Human/Board override.

---

## 13. Adoption decision framework

Every proposed integration must answer:

```text
What capability gap exists?
        ↓
Is it strategically differentiating?
        ├── YES → prefer AIOS-native domain capability
        └── NO
             ↓
Does mature infrastructure exist?
        ├── YES → evaluate integration behind AIOS-owned port
        └── NO  → defer or build minimal bounded capability
```

Score each candidate on:

- necessity;
- domain differentiation;
- maturity;
- security/privacy;
- licensing and maintenance sustainability;
- operational burden;
- integration complexity;
- performance;
- cost;
- data portability;
- vendor lock-in;
- replacement difficulty;
- AIOS sovereignty impact;
- measurable outcome benefit.

Possible states:

```text
REFERENCE
RESEARCH
BENCHMARK
PILOT
TRIAL
ADOPT
WATCH
DEFER
REJECT
```

---

## 14. Sequencing relative to L / M / N

The integration programme must not derail the product sequence.

```text
CURRENT
  K.1 bounded specialist execution — SEALED
        ↓
  L Live Organization — NEXT
        ↓
  M Board Transparency Experience
        ↓
  N Learning & Optimization
```

Parallel integration sequence:

```text
P0 NOW
  Observability correlation for L
  Secrets architecture research/pilot
  Backup/restore architecture + proof plan

P0/P1 DESIGN NOW
  Identity/SSO contract
  Communications Gateway contract

P1 BEFORE MATERIAL EXTERNAL WORK
  e-signature adapter
  governed communications execution

P1/P2 WHEN COMMERCIAL DEMAND EXISTS
  accounting / ERP integration
  payments / commercial operations
```

L must remain a real persisted AIOS organization proof. Integration work may support L but may not replace it with infrastructure work.

---

## 15. Current non-claims

This document does **not** claim that AIOS has production-adopted:

- Keycloak or Authentik;
- OpenBao;
- Langfuse or any observability backend;
- pgBackRest, WAL-G or Restic;
- an email/SMS/messaging provider;
- Documenso, DocuSeal or another e-signature platform;
- ERPNext or Odoo;
- a payment provider.

It establishes the architecture and sequencing contract under which those capabilities may be researched, piloted and adopted.

---

## 16. Permanent rules

> **Integrate commodity capability; build differentiating mobility intelligence.**

> **Authentication may be external. Authorization remains AIOS-governed.**

> **Telemetry observes AIOS truth; it does not become AIOS truth.**

> **Secrets may be injected into runtimes; they may not become context or memory.**

> **External execution requires governed intent, provenance and recovery semantics.**

> **ERP/accounting systems may own bounded back-office ledgers; they never own mobility truth or Board authority.**

> **No integration may bypass the Command Gateway for a material action.**
