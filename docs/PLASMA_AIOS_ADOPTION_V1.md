# Plasma AI → Global Mobility AIOS Controlled Adoption V1

**Date:** 2026-08-21
**Status:** CONTROLLED ADOPTION / PILOT APPROVED — NOT PRODUCTION ADOPTED
**Track:** Technology Radar / Platform Evolution
**AIOS branch context:** `roadmap/global-mobility-aios-v12`
**Accepted V1.3 baseline at assessment:** H.2.4 COMPLETE / PASS / SEALED
**Active safety candidate at assessment:** H.2.2 runtime-health classification refinement — IMPLEMENTED / PRODUCTION PROOF PENDING

---

## 1. Decision

Plasma AI is relevant to Global Mobility AIOS and should enter a bounded controlled-adoption programme now.

The programme has two independent donor candidates:

1. **Plasma Fractal** — recursive hierarchical agent execution and work decomposition.
2. **Plasma Wiki** — indexed hierarchical project/organizational knowledge for context-efficient agent retrieval.

Neither project becomes an AIOS authority layer, canonical domain model, execution constitution or production dependency by this decision.

Permanent rule:

> **Plasma provides execution and knowledge mechanics. AIOS owns organizational meaning, Evidence, authority, autonomy, risk, canonical state and consequences.**

---

## 2. Upstream baselines inspected

### Plasma Fractal

```text
repository  plasma-ai/fractal
package     plasma-fractal
version     1.1.0
license     Apache-2.0
python      >=3.12,<3.15
main SHA    e629ae2b80250ab502feefe3d9d0266bc58f15b2
```

Fractal describes itself as hierarchical agent loops with recursive self-organization. Its current package depends on `plasma-wiki>=1,<2`, Rich, Textual and Typer.

Important platform constraint:

```text
Operating System :: POSIX
```

The current implementation uses POSIX mechanisms including `fcntl`, shell scripts and `tmux`. It should therefore be treated as a Linux/POSIX execution candidate, not a native Windows runtime dependency.

### Plasma Wiki

```text
repository  plasma-ai/wiki
package     plasma-wiki
version     1.2.0
license     Apache-2.0
python      >=3.11,<3.15
main SHA    b27235fa11f1d3aa4deff50e45e52ea8ddc8af44
```

Wiki stores project knowledge as plain Markdown with deterministic `_index.md` structures and CLI-managed indexing/cross-links.

Its architecture is directly relevant to the AIOS Context Broker doctrine:

> **More relevant truth, not more tokens.**

---

## 3. Architectural fit

Plasma and Munder solve different useful parts of the future AIOS Organization Fabric.

```text
                         GLOBAL MOBILITY AIOS
                                  │
                       owns meaning + authority
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
       Munder                  Plasma                 AIOS-native
          │                       │                       │
 communication              recursive work             Evidence
 presence                   decomposition               VerifiedRules
 skills                     hierarchical loops          authority
 triggers                   worktrees                   A0–A5 autonomy
 telemetry                  indexed knowledge           R0–R5 risk
 live-scene mechanics       context efficiency          Context Broker
                                                       Command Gateway
                                                       Transparency
                                                       Immune System
```

Munder remains strongest as a horizontal organization/runtime donor.

Plasma Fractal is strongest as a recursive execution/decomposition donor.

Plasma Wiki is strongest as a context-efficient organizational/project-knowledge donor.

---

## 4. Plasma Fractal destination

Fractal must not become the AIOS organization model.

Target relationship:

```text
AIOS Mission
    ↓
AIOS Mission / WorkItem semantics
    ↓
AIOS Runtime Adapter
    ↓
Fractal recursive execution candidate
    ↓
child execution nodes / worktrees
    ↓
AIOS typed results
    ↓
Canonicalization / Governance / Immune System
    ↓
Command Gateway when a material effect is proposed
```

High-value Fractal concepts:

- recursive task decomposition;
- parent/child work trees;
- bounded depth and descendant counts;
- iteration limits;
- time limits;
- cost limits;
- per-node worktrees;
- agent/model attribution;
- operator steering;
- merge/completion mechanics;
- hierarchical execution visibility.

### Explicit non-adoption

Fractal nodes do not receive implicit AIOS authority because they can run commands.

The following remain prohibited unless explicitly mediated through AIOS contracts:

- production database writes;
- arbitrary production filesystem access;
- unrestricted network access;
- production credentials;
- government submissions;
- client/employer communications with material consequences;
- canonical Evidence or VerifiedRule mutation;
- authority/autonomy mutation;
- canonical case-state mutation.

---

## 5. Fractal security boundary

Fractal's own security model makes clear that Git worktrees isolate Git branches, not the host filesystem, network or credentials available to the process.

Therefore the first AIOS Fractal pilot must run only in a disposable/sandboxed Linux or POSIX environment with no production secrets.

Required boundary:

```text
Fractal node
    ↓
Sandbox
    ↓
AIOS Runtime Adapter
    ↓
Capability Registry
    ↓
Authority
    ↓
A0–A5 Autonomy
    ↓
R0–R5 Risk
    ↓
Typed output / proposed intent
    ↓
Command Gateway for material effects
```

Git worktree isolation alone is insufficient.

---

## 6. Plasma Wiki destination

Plasma Wiki is a candidate implementation/reference for repository knowledge and organizational memory retrieval beneath the Context Broker.

Target relationship:

```text
Project / Organizational Knowledge
        ↓
Plasma Wiki candidate
        ↓
indexed map / scoped retrieval
        ↓
Context Broker
        ↓
ContextBundle
        ↓
AgentRun
```

Permanent trust boundary:

```text
Plasma Wiki
    ≠ Evidence
    ≠ VerifiedRule
    ≠ certified CaseFact
    ≠ canonical legal truth
```

A Wiki page may inform or contextualize an employee. It cannot certify a regulatory rule or consequential fact.

The existing authoritative chain remains:

```text
Official Source
    ↓
SourceSnapshot
    ↓
Governed Evidence
    ↓
Review / verification
    ↓
VerifiedRule / canonical fact
```

---

## 7. Wiki hook security boundary

Plasma Wiki supports a `.wiki/wiki.py` customization hook which executes Python code with the user's privileges after the wiki is trusted.

AIOS must therefore treat custom Wiki hooks as executable code, not inert content.

Pilot rule:

- no custom `.wiki/wiki.py` hook in the first pilot;
- no `wiki trust` for external/unreviewed content;
- any future hook requires code review, sandboxing and explicit adoption evidence.

---

## 8. Relationship to Context Broker

Plasma Wiki does not replace the Context Broker.

The Context Broker remains responsible for:

- employee identity;
- OrganizationPosition;
- authority context;
- capability-specific autonomy;
- Mission/WorkItem context;
- tenant scope;
- case scope;
- Evidence selection;
- VerifiedRule selection;
- sensitivity constraints;
- allowed tools/connectors;
- risk tier;
- policy version;
- effective context version/hash.

Wiki may contribute only one controlled context source among several.

```text
Context Broker
├── Canonical Case State
├── Evidence
├── VerifiedRules
├── SourceSnapshots where permitted
├── Organization Memory
├── Mission summaries
├── prior decisions
└── Plasma Wiki-backed project knowledge candidate
```

---

## 9. Relationship to Earned Autonomy

Plasma does not change A0–A5 semantics.

```text
A0  Prohibited
A1  Human executes
A2  AI prepares; approval required
A3  Autonomous with mandatory review
A4  Autonomous with monitoring + valid recovery
A5  Fully autonomous bounded operation
```

Recursive decomposition does not inherit authority automatically.

If a parent AIOS employee delegates a subtask to a Fractal child node, the child receives only the capability/authority/autonomy scope explicitly granted for that WorkItem.

```text
parent authority
   ≠ automatically inherited authority
```

Child scope must be equal to or narrower than the delegating scope.

---

## 10. Relationship to risk-tiered verification

Fractal's ability to generate multiple workers must not be confused with independent verification.

A sibling or child node is not automatically an independent verifier.

AIOS R0–R5 verification rules remain authoritative.

For R3+ work, verifier independence must still satisfy the AIOS verification contract, including model/provider/runtime independence where required.

---

## 11. Relationship to Transparency and Flight Recorder

Any future Plasma-backed AgentRun must map into AIOS Transparency rather than creating a parallel hidden runtime history.

Target lineage:

```text
Mission
→ WorkItem
→ AIOS employee
→ RuntimeProfile
→ Fractal tree/node
→ ContextBundle
→ node steps / child delegation
→ tools
→ typed result
→ verification
→ governance
→ canonical effect
```

Useful Plasma telemetry may include:

- node identity;
- parent identity;
- depth;
- iteration;
- model;
- session;
- cost;
- duration;
- branch/worktree;
- child count;
- terminal state.

AIOS remains responsible for deciding which runtime facts become canonical `OrganizationActivity`, `AgentRun`, `ToolActionRecord` or Flight Recorder records.

---

## 12. First pilot — Plasma Wiki

### Goal

Determine whether Plasma Wiki materially improves Context Broker/project-knowledge efficiency without weakening canonical truth boundaries.

### Scope

Use repository/architecture knowledge only.

Do not place regulated mobility truth, client data or secrets into the pilot Wiki.

Candidate knowledge:

```text
architecture/
  autonomy
  context-broker
  command-gateway
  transparency
  immune-system

engineering/
  testing
  migrations
  repository-policy
  production-proof

technology/
  munder
  plasma
```

### Measurements

- context tokens loaded;
- relevant-document recall;
- irrelevant context rate;
- retrieval latency;
- agent answer quality;
- stale-index behavior;
- parallel-edit conflict behavior;
- maintenance overhead.

### Exit criteria

Advance from PILOT to TRIAL only if it demonstrates useful context reduction with no authoritative-truth ambiguity and acceptable maintenance burden.

---

## 13. Second pilot — Fractal engineering mission

### Goal

Test recursive decomposition against a real but non-production-consequential AIOS engineering analysis task.

Recommended first mission:

> Analyse the accepted Context Broker/runtime architecture and identify missing implementation or acceptance contracts without modifying production state.

Candidate decomposition:

```text
Engineering Mission
        ↓
Lead node
        ├── API/runtime analysis
        ├── tests/acceptance analysis
        ├── architecture/documentation analysis
        └── integration-risk analysis
        ↓
consolidated recommendation
```

### Environment

- disposable/sandboxed Linux/POSIX host;
- no production credentials;
- no production database;
- read-only or isolated repository copy initially;
- bounded cost/time/depth/child count;
- explicit operator stop path.

### Measurements

- result quality;
- decomposition quality;
- duplicate work;
- merge conflicts;
- context usage;
- time;
- cost;
- tool/runtime errors;
- operator interventions;
- child-node usefulness;
- trace completeness.

### Exit criteria

Advance only when the pilot demonstrates a measurable advantage over a comparable non-Fractal execution path and preserves AIOS observability and governance boundaries.

---

## 14. Production exclusion

This adoption decision does **not** authorize:

- production mobility Mission execution through Fractal;
- user-facing or government-facing execution through Fractal;
- Plasma-managed authority;
- Plasma-managed A0–A5 autonomy;
- Plasma-managed R0–R5 risk;
- Plasma-managed canonical Evidence or VerifiedRules;
- direct Plasma writes to authoritative AIOS state;
- use of Fractal's host reach as a substitute for the AIOS Tool/Connector Plane.

Those require separately accepted implementation slices.

---

## 15. Adoption states

Current classification:

| Technology | AIOS role | State |
|---|---|---|
| Plasma Wiki 1.2.0 | Context-efficient project/organizational knowledge candidate | PILOT APPROVED |
| Plasma Fractal 1.1.0 | Recursive bounded execution/decomposition candidate | PILOT APPROVED — SANDBOXED ENGINEERING ONLY |

Neither is `ADOPT`.

---

## 16. Interaction with current V1.3 progress

The current V1.3 accepted baseline is H.2.4. The H.2.2 runtime-health classification refinement is implemented but still awaiting Production Proof.

Therefore Plasma work must not displace the active H-stage acceptance sequence.

Track relationship:

```text
Track C — High-Autonomy Organization
H.2.2 refinement Production Proof
→ later bounded H-stage choices
→ Earned Autonomy

Track B — Technology Radar
Plasma Wiki pilot
+ sandboxed Fractal engineering pilot

No production authority crossover
```

A Track B pilot may run in parallel because it is isolated and non-authoritative. Production Fractal execution is deferred until the required AIOS runtime, authority, sandbox and Transparency contracts are accepted.

---

## 17. Adoption gate

Before any Plasma subsystem advances beyond PILOT/TRIAL, require applicable evidence for:

- semantic sovereignty;
- tenant isolation;
- Context Broker mediation;
- sensitivity/privacy isolation;
- Capability/Authority/Autonomy/Risk separation;
- explicit child-delegation scope;
- sandbox isolation;
- no direct canonical mutation;
- deterministic failure behavior;
- time/cost/depth/child limits;
- idempotency where effects exist;
- traceability;
- Flight Recorder integration where material;
- replacement/rollback strategy;
- focused tests;
- Production Proof when runtime code enters AIOS;
- repository-policy compliance.

---

## 18. Final rule

> **Use Plasma to make AIOS employees better at decomposing complex work and loading only relevant organizational knowledge. Never let Plasma decide what is true, who has authority, how much autonomy exists, or what consequential organizational effect is allowed.**
