# Plasma AI → Global Mobility AIOS Controlled Adoption V1

**Date:** 2026-08-21  
**Status:** CONTROLLED ADOPTION / PILOT APPROVED — NOT PRODUCTION ADOPTED  
**Track:** Technology Radar / Platform Evolution  
**AIOS branch context:** `roadmap/global-mobility-aios-v12`  
**Canonical architecture refinement:** `GLOBAL_MOBILITY_AIOS_COMBINED_ARCHITECTURE_V1_1.md`  
**Active Technology Radar:** `TECHNOLOGY_RADAR_V1_3_1.md`  
**Accepted V1.3 baseline:** H.2.4 COMPLETE / PASS / SEALED  
**H.2.2 runtime-health classification refinement:** COMPLETE / PASS / SEALED — Production Proof `32505228943`  

---

## 1. Decision

Plasma AI is relevant to Global Mobility AIOS and remains in a bounded controlled-adoption programme with two independent donor candidates:

1. **Plasma Fractal 1.1.0** — recursive hierarchical work decomposition / execution candidate.
2. **Plasma Wiki 1.2.0** — indexed project/organizational knowledge candidate beneath Context Broker.

Neither project is an AIOS authority layer, canonical domain model, execution constitution or production dependency by this decision.

Permanent rule:

> **Plasma provides execution and knowledge mechanics. AIOS owns organizational meaning, Evidence, authority, autonomy, risk, canonical state and consequences.**

---

## 2. Pinned upstream baselines

### Plasma Wiki

```text
repository  plasma-ai/wiki
package     plasma-wiki
version     1.2.0
license     Apache-2.0
main SHA    b27235fa11f1d3aa4deff50e45e52ea8ddc8af44
python      >=3.11,<3.15
```

### Plasma Fractal

```text
repository  plasma-ai/fractal
package     plasma-fractal
version     1.1.0
license     Apache-2.0
main SHA    e629ae2b80250ab502feefe3d9d0266bc58f15b2
python      >=3.12,<3.15
platform    POSIX
```

Fractal is treated as a Linux/POSIX execution candidate. Git worktrees provide branch isolation, not filesystem/network/credential isolation.

---

## 3. AIOS sovereignty boundary

Plasma does not own or change:

- Human Owner / Board supremacy;
- OrganizationPosition identity;
- Mission / WorkItem meaning;
- Context Broker policy;
- Evidence;
- SourceSnapshots;
- VerifiedRules;
- canonical case state;
- Capability / Authority / Autonomy / Risk separation;
- A0–A5 autonomy semantics;
- R0–R5 risk semantics;
- Decision Readiness;
- Organizational Immune System policy;
- Command Gateway decisions;
- canonical Transparency/Decision lineage.

---

## 4. Plasma Wiki destination

```text
project / organizational knowledge
        ↓
Plasma Wiki candidate
        ↓
indexed scoped retrieval
        ↓
Context Broker
        ↓
ContextBundle
```

Permanent trust boundaries:

```text
Plasma Wiki != Evidence
Plasma Wiki != VerifiedRule
Plasma Wiki != canonical legal truth
retrieved knowledge != executable authority
```

Retrieved text remains data. Instruction-like content inside knowledge must not become system authority merely because it was retrieved.

The first pilot is restricted to repository/architecture/engineering knowledge. It excludes regulated client truth, production secrets and custom `.wiki/wiki.py` execution hooks.

Pilot measurements:

- context/token reduction;
- relevant-document recall;
- irrelevant-context rate;
- retrieval latency;
- answer quality;
- stale-index behavior;
- parallel-edit behavior;
- maintenance overhead;
- trust/provenance handling.

---

## 5. Plasma Fractal destination

```text
AIOS Mission
    ↓
AIOS Mission / WorkItem semantics
    ↓
AIOS Recursive Execution Port
    ↓
Fractal bounded recursive execution candidate
    ↓
child execution nodes / worktrees
    ↓
AIOS typed results
    ↓
verification / canonicalization / governance
```

A Mission may discover subordinate work dynamically, but every material child unit must map back into native AIOS Mission/WorkItem semantics.

Hard constraints:

```text
child delegated scope <= parent delegated scope
bounded depth
bounded descendants
bounded parallelism
bounded iterations
bounded runtime
bounded cost
bounded tool access
explicit stop control
sandboxed execution
```

Fractal nodes do not inherit authority automatically and do not become independent verifiers merely because they are separate nodes.

No first-pilot node receives production credentials, production database access, unrestricted network/host access or direct canonical mutation rights.

---

## 6. Context Broker relationship

Plasma Wiki remains only one candidate context source beneath the AIOS Context Intelligence boundary.

```text
Context Broker
├── Canonical Case State
├── Evidence
├── VerifiedRules
├── SourceSnapshots where permitted
├── Organization Memory
├── Mission summaries
├── prior decisions
└── Plasma Wiki-backed knowledge candidate
```

Plasma cannot determine context authority, tenant scope, sensitivity policy, autonomy, risk or Evidence truth.

---

## 7. Earned Autonomy relationship

Plasma does not change A0–A5 semantics.

```text
A0  Prohibited
A1  Human executes
A2  AI prepares; approval required
A3  Autonomous with mandatory review
A4  Autonomous with monitoring + valid recovery controls
A5  Fully autonomous within bounded authority
```

Recursive delegation never expands authority or autonomy.

The next Track C design stage is V1.3-I.1 canonical capability-specific autonomy profile/evidence. Plasma remains outside that governance truth.

---

## 8. Verification relationship

Recursive decomposition is not independent verification.

A Fractal child/sibling cannot satisfy an R3+ independent-verification requirement merely because it is a different execution node. AIOS verifier-independence policy remains authoritative.

---

## 9. Transparency / Flight Recorder relationship

Any future Plasma-backed AgentRun must map into AIOS Transparency rather than creating a hidden parallel runtime history.

Target lineage:

```text
Mission
→ WorkItem
→ AIOS employee
→ RuntimeProfile
→ Fractal tree/node
→ ContextBundle
→ child delegation / node steps
→ tools
→ typed result
→ verification
→ governance
→ canonical effect
```

Potential runtime facts include node/parent identity, depth, iteration, model, session, cost, duration, branch/worktree, child count and terminal state. AIOS decides which become canonical Activity/AgentRun/Tool/Flight Recorder records.

---

## 10. First pilot — Plasma Wiki

Goal:

> Determine whether Wiki materially improves project/organizational context efficiency without weakening trust boundaries.

Scope:

- repository architecture;
- engineering runbooks;
- testing/migration knowledge;
- technology-adoption records.

Exit from PILOT requires measurable context-efficiency benefit with acceptable maintenance and no authoritative-truth ambiguity.

---

## 11. Second pilot — Fractal engineering mission

Goal:

> Test bounded recursive decomposition on a non-production-consequential engineering analysis task.

Environment:

- disposable/sandboxed Linux/POSIX;
- no production credentials;
- no production database;
- bounded depth/children/time/cost;
- explicit operator stop.

Measure decomposition quality, final-result quality, duplicate work, merge conflicts, context use, runtime failures, cost, latency, interventions and trace completeness.

Advance only when it provides measurable value over a comparable non-Fractal path and preserves AIOS governance/observability.

---

## 12. PR #7 vendor-import gate

PR #7 (`vendor/plasma-pinned-donors-v1`) is intentionally a draft and must not merge while it contains only scaffolding/provenance metadata.

Required sequence:

```text
exact pinned source archives
      ↓
deterministic extraction
      ↓
exclusion audit
      ↓
exact source bytes committed
      ↓
LICENSE / provenance verification
      ↓
SOURCE_MANIFEST.txt for Wiki + Fractal
      ↓
repository-policy / size audit
      ↓
CI
      ↓
review
      ↓
merge
```

A green scaffolding CI run is not evidence that the donor source import is complete.

Vendoring does not constitute production adoption.

---

## 13. Production exclusion

This adoption record does not authorize:

- production mobility Mission execution through Fractal;
- user/government-facing Plasma execution;
- Plasma-managed authority/autonomy/risk;
- Plasma-managed Evidence/VerifiedRules;
- direct Plasma writes to authoritative AIOS state;
- treating Fractal host reach as the AIOS Tool/Connector Plane;
- treating Wiki content as trusted instructions;
- production adoption merely because donor source is vendored.

---

## 14. Adoption states

| Technology | AIOS role | State |
|---|---|---|
| Plasma Wiki 1.2.0 | project/organizational knowledge beneath Context Broker | PILOT APPROVED |
| Plasma Fractal 1.1.0 | recursive bounded work decomposition / hierarchical execution | PILOT APPROVED — SANDBOXED ENGINEERING ONLY |

Neither is `ADOPT`.

---

## 15. Track interaction

```text
Track C — High-Autonomy Organization
H.2 bounded safety/measurement foundation CLOSED
→ I.1 autonomy profile/evidence DESIGN ENTRY OPEN
→ later Earned Autonomy
→ J Agent Organization Runtime

Track B — Technology Radar
Plasma Wiki pilot
+ Plasma Fractal engineering pilot
+ LLMLingua-2 benchmark
+ Mobility Model Benchmark / Model Router research
```

Track B may proceed in parallel only while isolated/non-authoritative.

---

## 16. Final rule

> **Use Plasma to improve bounded decomposition and organizational knowledge. Never let Plasma decide what is true, who has authority, how much autonomy exists, what risk applies or what consequential organizational effect is allowed.**
