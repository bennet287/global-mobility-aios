# Global Mobility AIOS — Frozen V11 Product & Delivery Roadmap

**Roadmap generation:** V11.6 / frozen branch alignment  
**Date:** 2026-08-19  
**Branch:** `roadmap/global-mobility-aios-v11`  
**Branch role:** FROZEN PRODUCT / RUNTIME / ARCHITECTURE CHECKPOINT  
**V11 architecture checkpoint before final roadmap cleanup:** `dd2f2cd6e9e47179b1fd744ba3f56daf7c787449`  
**Accepted product baseline:** Phase 13.16.10 — COMPLETE / PASS at `b8393d0b6bdaf02c958bb151b4909b5b82fd0d09`  
**Human acceptance:** Phase 13.17 — IN PROGRESS / PAUSED BY EVALUATOR at the V11 checkpoint  
**Technology Radar snapshot:** Wave 1 PILOT COMPLETE / TRIAL-ELIGIBLE; Wave 2 IN PROGRESS with Docling started and Presidio queued  
**Architecture design present on V11:** [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md) — documentation/design direction only  
**Code migration head:** `0076_organization_position_active_identity`

<!-- CURRENT_MIGRATION_HEAD: 0076_organization_position_active_identity -->

This roadmap describes **V11 itself**. It is intentionally aligned with the V11 `README.md` and the product/runtime state preserved on this branch.

It does **not** contain the active V12 implementation roadmap. The detailed V1.3-A→V1.3-N implementation programme belongs to `roadmap/global-mobility-aios-v12`.

The earlier forward-looking V11.5 roadmap is retained only as historical evidence at [archive/ROADMAP_V11_5_HIGH_AUTONOMY_DIRECTION_2026-08-19.md](archive/ROADMAP_V11_5_HIGH_AUTONOMY_DIRECTION_2026-08-19.md).

---

## 1. V11 purpose

V11 is the preserved checkpoint representing the mature Phase 13 product foundation before active V1.3 runtime implementation moved onto V12.

It contains:

- the accepted global-mobility product foundation;
- the durable organization model already implemented through Phase 13;
- the accepted Cockpit / Board Room naming and role separation;
- Operations / Professional and My Mobility product surfaces;
- Evidence and provenance presentation;
- accepted responsive/accessibility integration through Phase 13.16.10;
- the owner-led Phase 13.17 human-acceptance checkpoint;
- Technology Radar pilot state existing at the branch boundary;
- the V1.3 architecture document as a design artifact created before the V12 branch split.

V11 is not the branch on which the new V1.3 control plane is to be implemented.

---

## 2. Product definition

Global Mobility AIOS on V11 is a **governed global mobility intelligence operating system** for the movement of people, talent, families, businesses, and capital across borders.

The product connects mobility intelligence, workflow and case orchestration, official-source Evidence, document intelligence, organization governance, human review, and controlled AI workers inside one auditable operating environment.

It is deliberately broader than:

- a visa chatbot;
- an immigration CRM;
- a study-abroad search site;
- a document uploader;
- a recommendation engine;
- a collection of disconnected AI agents.

The V11 product model is workflow-first, Evidence-backed, and human-governed.

---

## 3. North-star mobility lifecycle

V11 preserves the full product lifecycle described in the README:

```text
Dream / mobility goal
        ↓
Profile, constraints and consent
        ↓
Country + pathway discovery
        ↓
Eligibility, Evidence, risk, cost and timeline comparison
        ↓
Study / Work / Family / Business / Investment / Remote-work move
        ↓
Documents, reviews, submissions, appointments and authority decisions
        ↓
Post-arrival / graduate work / employment / business operation
        ↓
Renewal / change of status / family progression
        ↓
Permanent or long-term residence
        ↓
Citizenship / long-term global mobility strategy
```

The branch represents the product foundation that supports this connected lifecycle; it does not claim universal regulatory coverage or complete automation of every step.

---

## 4. Who V11 serves

### Mobility users

Students, graduates, professionals, job seekers, remote workers, families, founders, investors, HNWIs, and people planning long-term settlement or citizenship.

### Professionals / operators

Mobility advisers, case operators, compliance reviewers, Evidence researchers, source reviewers, and regulated-domain reviewers.

### Employers / corporate mobility

Employee mobility, sponsor requirements, dependants, work/residence workflows, compliance calendars, case portfolios, and relocation operations.

### Business / investment / family-office contexts

Entrepreneurship, startup pathways, business relocation, investment-migration context, HNWI/family-office mobility, and tax-residency issue mapping remain Evidence- and review-gated.

### Partners / agencies / authority workflows

V11 includes foundations for partner APIs, agency operations, appointments, submissions, authority assignments, and checklists where authorization permits.

A workflow existing in the product never implies legal authority to submit, approve, certify, or make a binding decision.

---

## 5. V11 organizational operating model

V11 already contains a durable organization model rather than treating AI work as disposable chat sessions.

The README checkpoint records:

- **61 active OrganizationPosition identities**;
- **9 L3 executive roles** beneath the CEO;
- **26 operational domains**;
- **59 positions downstream of the CEO**;
- zero duplicate active position keys after active-identity reconciliation;
- capability-only positions remaining non-executable until authorized;
- preserved Human Board and CEO governance;
- bounded executive delegation rather than title-based authority.

Accepted migration head:

```text
0076_organization_position_active_identity
```

The implemented V11 organization concepts include:

```text
OrganizationPosition
OrganizationalWorkItem
OrganizationBlocker
OrganizationWorkItemDependency
OrganizationHumanActionRequest
OrganizationContribution
OrganizationActivity
Organization Observatory
```

---

## 6. Human experiences on V11

### Global Mobility AIOS Cockpit

The **Cockpit** is the top-level Human Owner / Board control surface.

It provides organization-wide awareness, health, friction, attention signals, and governed intervention without making the Owner a routine task operator.

### Board Room

**Board Room is a module inside Cockpit**, reserved for genuinely Board-level authority, decisions, escalations, and control.

It is not the name of the entire Owner surface.

### Department workspaces

Accepted organizational workspaces expose executive ownership, positions, work, blockers, dependencies, HumanActionRequests, Contributions, and durable Activity without creating mutation shortcuts.

### Cross-department friction

V11 includes the accepted cross-department friction surface for blockers, dependencies, human-action indicators, escalation, overdue state, durable Activity, and deep links to affected departments.

### Operations

The Professional / Operator shell is the high-information-density workspace for case operations, Evidence, provenance, review, authority workflow, and specialist work.

### My Mobility

The mobility-user experience is goal- and journey-centered around profile, pathways, eligibility, documents, actions, deadlines, costs, risks, Evidence, and longer-term progression.

---

## 7. Truth, Evidence, and safety model

The V11 safety rule remains:

> **Regulated or consequential claims must be grounded in Evidence and the required review state. Model output alone is never authoritative.**

V11 must not silently convert:

```text
model suggestion → VerifiedRule
memory → Evidence
draft → published decision
capability position → executable authority
pending certification → approved source
incomplete Evidence → legal certainty
visible UI control → backend authority
```

Important permanent distinctions retained by the V11 checkpoint include:

```text
conversation != authority
memory != Evidence
memory != VerifiedRule
provider event != canonical AIOS Activity automatically
capability != authority
```

Backend authorization remains authoritative.

---

## 8. Accepted Phase 13 delivery state

| Programme / slice | V11 state |
|---|---|
| Phases 1–9 | Complete — core platform, Truth Engine, profiles, pathways, timelines, document intelligence |
| Phase 10 software | Complete — self-updating intelligence foundation, registry workflows, dashboards, ranking, planning |
| Phase 10B Evidence operations | Ongoing programme — jurisdiction Evidence onboarding, independent review, publication, freshness |
| Phase 11 | Complete — corporate, business, wealth, investment, family-office, tax/treaty mobility |
| Phase 12 | Complete / stabilized — portals, partner APIs, governed automation, agency/government workflow foundations |
| Phase 13.0–13.15 | Complete / PASS where gated — AI organization governance, runtime and correctness foundation |
| Phase 13.16.0 | CLOSED / PASS — design and information architecture |
| Phase 13.16.1 | COMPLETE / PASS — durable Contribution & Activity model |
| Phase 13.16.2 | COMPLETE / PASS — premium role shells/navigation/preserved-SQLite reconciliation |
| Phase 13.16.3 | COMPLETE / PASS — Unified Owner Control Center |
| Phase 13.16.4 | COMPLETE / PASS — Department workspaces |
| Phase 13.16.5 | COMPLETE / PASS — cross-department blocker/dependency view |
| Phase 13.16.6 | COMPLETE / PASS — Owner decision/escalation inbox |
| Phase 13.16.7 | COMPLETE / PASS — Mobility User experience |
| Phase 13.16.8 | COMPLETE / PASS — Professional / Operator workspace |
| Phase 13.16.9 | COMPLETE / PASS — Evidence / provenance presentation |
| **Phase 13.16.10** | **COMPLETE / PASS — integrated responsive/accessibility role experience** |
| **Phase 13.17** | **IN PROGRESS / PAUSED BY EVALUATOR — owner-led human acceptance** |
| Phase 14 | NOT STARTED / demand-gated |

This table represents V11's delivered/accepted product position.

---

## 9. Latest accepted V11 runtime evidence

The latest accepted runtime evidence carried into the V11 architecture checkpoint is:

```text
API regression                873 passed / 5 skipped / 0 failed
Next.js production build      41 / 41 pages
Design foundation             28 / 28 passed
Alembic head                  0076_organization_position_active_identity
```

The preserved `gmai.db` remained unchanged across the documentation-only architecture checkpoint.

These results are historical accepted evidence. This final roadmap cleanup does not rerun them and does not claim new CI/runtime PASS evidence.

---

## 10. Phase 13.17 on V11

Phase 13.17 remains an **owner-led human-acceptance checkpoint** in the V11 history.

At the branch boundary it was:

```text
IN PROGRESS / PAUSED BY EVALUATOR
```

Known unresolved themes included:

- click-through traceability;
- plain-language Evidence/governance concepts;
- powerful-control semantics;
- diagnosis/routing;
- blocker/dependency direction;
- role-context navigation;
- icon + text navigation;
- Professional next-action clarity;
- pathway/context-alignment terminology.

The resume point remained Professional Task 2.

A documentation change does not resolve those findings. Any continuation/correction after the branch split belongs on V12 or a V12 descendant unless explicitly backported.

---

## 11. Technology Radar snapshot preserved on V11

At the V11 checkpoint:

| Technology | State |
|---|---|
| Promptfoo | PILOT COMPLETE / TRIAL-ELIGIBLE |
| OpenTelemetry | PILOT COMPLETE / TRIAL-ELIGIBLE |
| ClamAV | PILOT COMPLETE / TRIAL-ELIGIBLE |
| Docling | PILOT IN PROGRESS |
| Presidio | QUEUED PILOT |
| urlwatch | QUEUED PILOT |
| Munder Difflin | REFERENCE / CONTROLLED RESEARCH / EXPERIMENTAL |
| OpenWorker | REFERENCE / CONTROLLED RESEARCH |
| Temporal | DEFERRED PILOT |
| OpenFGA | DEFERRED PILOT |

Technology Radar state is preserved as branch history. New experiments/adoption decisions belong to V12.

---

## 12. V1.3 architecture document on V11

V11 contains [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md) because that architecture was designed and documented **before V12 was branched**.

That does not make V11 the V12 implementation roadmap.

On V11, V1.3 should be understood as:

```text
architecture/design checkpoint
NOT runtime implementation
NOT completion claim
NOT V12 delivery sequencing
```

The V1.3 document records important direction such as:

- Human Owner / Board supremacy;
- Board by exception;
- Board Transparency / Decision Lineage;
- persistent AI employees;
- Context Broker;
- deterministic canonicalization;
- Command Gateway mutation boundary;
- earned capability-specific autonomy;
- risk-tiered verification;
- Organizational Immune System;
- consequence-aware recovery;
- performance/scalability doctrine;
- AIOS Semantic Sovereignty.

The actual staged implementation programme for those concepts is owned by the V12 roadmap.

---

## 13. What V11 intentionally does not contain

The active V11 roadmap intentionally does **not** define or schedule:

```text
V1.3-A Constitutional Contracts
V1.3-B Governance Kernel
V1.3-C Transparency Foundation
V1.3-D Context & Agent Identity
V1.3-E First Governed Vertical Workflow
V1.3-F Decision Readiness
V1.3-G Independent Verification
V1.3-H Organizational Immune System
V1.3-I Earned Autonomy
V1.3-J Agent Organization Runtime
V1.3-K Execution / Coworker Runtime
V1.3-L Live Organization
V1.3-M Board Transparency Experience
V1.3-N Learning & Optimization
```

Those are **V12 implementation roadmap items**.

V11 preserves the design checkpoint from which that programme was derived, not the active delivery plan itself.

---

## 14. V11 branch boundary

The relationship is:

```text
V11 product/runtime checkpoint
        │
        ├── README.md            → V11 product definition/current state
        ├── docs/ROADMAP.md      → frozen V11 product/delivery roadmap
        ├── docs/CHANGELOG.md    → V11 history
        └── V1.3 architecture   → design artifact created on V11
                 │
                 └──────────────→ V12 active implementation line
```

The V12 branch was originally created from V11 at:

```text
dd2f2cd6e9e47179b1fd744ba3f56daf7c787449
```

V11 receives no normal new product/runtime implementation after the split. This roadmap correction is final documentation housekeeping requested by the Human Owner so the branch describes itself accurately.

---

## 15. Repository discipline at the V11 boundary

V11 remains a reference/recovery branch.

Therefore:

- do not implement new V1.3 runtime functionality on V11;
- do not advance Technology Radar experiments on V11;
- do not continue Phase 13.17 fixes on V11 unless explicitly backported;
- do not change migrations or preserved database state on V11;
- use V12 for active development;
- use V11 for historical comparison, recovery, and understanding the pre-V12 product/runtime state.

---

## 16. Canonical V11 documents

Start with:

- [`../README.md`](../README.md) — V11 repository/product overview;
- [`ROADMAP.md`](ROADMAP.md) — this frozen V11 roadmap;
- [`CHANGELOG.md`](CHANGELOG.md) — V11 history;
- [`GLOBAL_MOBILITY_AIOS_VISION_V1.md`](GLOBAL_MOBILITY_AIOS_VISION_V1.md) — product vision;
- [`AI_ORGANIZATION_GOVERNANCE_V13_0.md`](AI_ORGANIZATION_GOVERNANCE_V13_0.md) — implemented governance direction;
- [`HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md`](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md) — V1.3 architecture/design checkpoint;
- [`TECHNOLOGY_RADAR_V1_1.md`](TECHNOLOGY_RADAR_V1_1.md) — Radar state at the branch boundary;
- [`archive/ROADMAP_V11_5_HIGH_AUTONOMY_DIRECTION_2026-08-19.md`](archive/ROADMAP_V11_5_HIGH_AUTONOMY_DIRECTION_2026-08-19.md) — historical forward-looking V11.5 roadmap that seeded V12 planning.

---

## 17. Final V11 direction

V11's role is now intentionally simple:

> **Preserve the accepted Global Mobility AIOS product and organization foundation through Phase 13.16.10, preserve Phase 13.17's owner-led acceptance state, preserve the Technology Radar snapshot, and preserve the V1.3 architecture design checkpoint without carrying the active V12 implementation roadmap.**

The branch remains evidence of what existed and what had been designed at the V11/V12 boundary.

Active implementation continues on V12.
