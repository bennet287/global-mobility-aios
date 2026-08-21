# Global Mobility AIOS — Canonical Combined Architecture V1.1

**Date:** 2026-08-21  
**Status:** CANONICAL ACTIVE ARCHITECTURE REFINEMENT — DOCUMENTATION / DIRECTION ONLY  
**Active implementation branch:** `roadmap/global-mobility-aios-v12`  
**Refines:** `GLOBAL_MOBILITY_AIOS_FINAL_COMBINED_ARCHITECTURE_V1.md`  
**Preserves constitutional source:** `HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md`  
**Runtime effect of this document:** none by itself  

> **Global Mobility AIOS is a governed, evidence-grounded, transparent and cost-intelligent high-autonomy digital organization that coordinates persistent AI employees to perform global-mobility work through dynamic Missions, purpose-scoped context, earned capability-specific autonomy, risk-tiered verification, governed execution and Human Owner / Board sovereignty.**

This record freezes the combined architecture after reconciling the existing V1.3 high-autonomy organization, Munder Difflin donor programme, Plasma Wiki/Fractal controlled adoption, context-compression strategy, model routing and AI economics.

It is a refinement of direction, not a claim that every component described here is already implemented.

---

## 1. Permanent architectural ownership

External frameworks and providers may supply capability. They do not own AIOS meaning, truth or authority.

```text
Munder Difflin
Plasma Wiki
Plasma Fractal
LLMLingua-2
local/open models
hosted/frontier models
future execution runtimes
        ↓
AIOS-owned ports / adapters
        ↓
GLOBAL MOBILITY AIOS
```

AIOS alone owns the canonical semantics of:

- Human Owner / Board sovereignty;
- organizational identity and `OrganizationPosition`;
- Mission and WorkItem meaning;
- Evidence and SourceSnapshots;
- VerifiedRules and governed facts;
- canonical mobility/case state;
- Capability, Authority, Autonomy and Risk;
- A0–A5 autonomy semantics;
- R0–R5 consequence/risk semantics;
- Decision Readiness;
- materiality;
- Command Gateway decisions;
- Organizational Immune System policy;
- incident and recovery meaning;
- Decision / Activity / Tool / Context lineage;
- learning and promotion governance.

Permanent rule:

> **External infrastructure provides capability. AIOS owns meaning, truth and authority.**

---

## 2. Canonical high-level architecture

```text
                     HUMAN OWNER / BOARD
                       SUPREME AUTHORITY
                              │
                   GLOBAL MOBILITY AIOS
                         COCKPIT
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
     Organization        Transparency        Board Room
          │
        AI CEO
          │
   ORGANIZATION RUNTIME
          │
Persistent Employees
Missions / WorkItems / Squads
          │
     ┌────┴──────────────────────────────┐
     │                                   │
CONTEXT INTELLIGENCE              EXECUTION FABRIC
     │                                   │
Context Broker                       Runtime Ports
     │                                   │
├── Evidence                     ├── AIOS Native
├── VerifiedRules                ├── Munder-derived
├── Memory                       ├── Plasma Fractal
├── Knowledge                    └── other adapters
│   └── Plasma Wiki
│
└── ContextCompressionPort
    └── LLMLingua-2
        SELECTED PRIMARY PILOT
     │
Context integrity
     │
ContextBundle
     │
Model Router
     │
deterministic / local / hosted / frontier
     │
AgentRun
     │
Typed Proposed Intent
     │
Canonicalization
     │
Evidence / Readiness /
Verification / Policy
     │
Immune-System restrictive preflight
     │
Command Gateway
     │
ALLOW / BLOCK / ESCALATE
     │
Canonical State
     │
Activity / Decision / Tool /
Context / Cost Lineage
     │
Outcome
     │
Learning + Performance
```

This diagram is conceptual. The Immune System is not merely one serial box; it is cross-cutting around context, runtime, governance, canonical state, incidents and recovery.

---

## 3. Organizational Immune System — restriction only

The Immune System never grants authority, autonomy or permission.

It may:

- observe;
- classify;
- detect contradictions or anomalies;
- restrict scope;
- open a circuit;
- quarantine a bounded capability where policy exists;
- downgrade an already-existing autonomy allowance once a canonical autonomy contract exists;
- block;
- escalate;
- require recovery evidence.

It may not:

- create authority;
- increase authority;
- promote autonomy;
- waive Board-reserved powers;
- convert model confidence into permission;
- create canonical truth from a warning or score.

Cross-cutting destination:

```text
ORGANIZATIONAL IMMUNE SYSTEM

Context integrity
Compression integrity
Runtime health
Model health
Evidence integrity
Contradictions
Recurrence / anomaly detection
Circuit breakers
Budget / rate protection
Blast-radius restriction
Incident detection
Root-cause classification
Recovery monitoring

RESTRICTION ONLY
NEVER AUTHORITY GRANT
```

Permanent invariant:

> **The Immune System may restrict or stop. It never manufactures permission.**

---

## 4. Context Intelligence

The Context Broker becomes a first-class Context Intelligence subsystem.

Responsibilities include:

- purpose-scoped access;
- employee/position context;
- tenant/case/Mission scope;
- Evidence retrieval;
- VerifiedRule retrieval;
- SourceSnapshot references where permitted;
- organizational memory retrieval;
- project/knowledge retrieval;
- relevance ranking;
- freshness/version checks;
- contradiction visibility;
- sensitivity/privacy constraints;
- deduplication;
- token efficiency;
- compression eligibility;
- context lineage.

The Context Broker does not create legal or domain truth.

Permanent rule:

> **More relevant truth, not more tokens.**

---

## 5. LLMLingua-2 — selected primary compression pilot

LLMLingua-2 is selected as the primary pilot behind an AIOS-owned abstraction:

```text
Context Broker
      ↓
ContextCompressionPort
      ↓
LLMLingua2Adapter
```

It is not described as inherently safe. Semantic compression is lossy and must earn its use under an explicit integrity contract.

Canonical doctrine:

> **Compression output is derived context, not source truth.**

> **Compression may reduce representation. It may not reduce governance meaning.**

> **No compression is preferable to unsafe compression.**

### 5.1 Protected context

The initial policy for material R3–R5 work is zero semantic compression for governance-critical material, including:

- authority constraints;
- autonomy constraints;
- risk classification;
- mandatory Evidence;
- critical VerifiedRules;
- contradictions;
- exact dates;
- monetary values;
- identifiers and version pins;
- policy constraints;
- material-action parameters;
- source identifiers;
- Board-reserved conditions.

Compressible material may include verbose conversation history, repeated collaboration, duplicated retrieval, large historical narratives and bulky tool output when integrity policy permits.

### 5.2 Compression lineage

A compressed execution context should eventually preserve:

```text
original context references/hash
compressor family + revision
compression policy version
parameters
protected-span hashes
original token count
compressed token count
ContextBundle version/hash
compression decision / reason
```

The Flight Recorder must be able to reconstruct what representation changed before an AgentRun.

---

## 6. Plasma Wiki — organizational knowledge, not truth

Plasma Wiki is a controlled candidate beneath Context Broker for indexed organizational/project knowledge.

```text
Organizational / project knowledge
        ↓
Plasma Wiki candidate
        ↓
scoped indexed retrieval
        ↓
Context Broker
        ↓
ContextBundle
```

It is not:

- Evidence;
- a VerifiedRule store;
- a certified CaseFact store;
- canonical legal truth;
- an instruction-authority channel.

Permanent knowledge-security invariant:

> **Retrieved knowledge is data, not executable authority.**

Knowledge records should eventually carry provenance, trust and sensitivity metadata. Untrusted retrieved text must remain untrusted data even when it contains instruction-like language.

Custom `.wiki/wiki.py` execution hooks remain excluded from the first pilot.

---

## 7. Plasma Fractal — recursive execution donor

Plasma Fractal is a controlled donor/pilot for recursive Mission decomposition and hierarchical bounded execution.

Destination:

```text
AIOS Mission
    ↓
AIOS Mission / WorkItem contract
    ↓
AIOS Recursive Execution Port
    ↓
Fractal-backed bounded decomposition
    ↓
child execution nodes
    ↓
AIOS typed results
    ↓
verification / canonicalization / governance
```

A Mission may discover that additional subordinate work is required. That subordinate work must map back into native AIOS Mission/WorkItem semantics rather than becoming hidden framework state.

Hard constraints:

- child delegated scope <= parent delegated scope;
- child work cannot manufacture authority;
- bounded depth;
- bounded descendant count;
- bounded parallelism;
- bounded iterations;
- bounded runtime;
- bounded cost;
- bounded tools/connectors;
- explicit stop control;
- sandboxed execution where required;
- no production secrets in the engineering pilot;
- Git worktrees are not security sandboxes.

A Fractal child or sibling is not automatically an independent verifier. AIOS verification-independence rules remain authoritative.

---

## 8. Munder Difflin — Organization Fabric donor

Munder Difflin v0.4.4 remains the strategic donor/reference for horizontal organization/runtime mechanics such as:

- communication and routing;
- presence;
- persistent runtime mechanics;
- Skills;
- triggers;
- schedules/heartbeats;
- provider abstraction;
- telemetry/transcripts;
- cost/token signals;
- worktree/IDE mechanics;
- live-organization concepts.

Adoption method remains:

```text
reference implementation
      ↓
study
      ↓
DIRECT REUSE / PORT / ADAPT /
REIMPLEMENT / REJECT
      ↓
AIOS-native capability
```

Munder does not become the organization or canonical state store.

---

## 9. Model Router and AIOS Mobility Model Benchmark

Model routing is capability-qualified, not confidence-qualified.

Permanent invariant:

> **A model earns capability eligibility through measured evaluation, not self-reported confidence.**

The future AIOS Mobility Model Benchmark should measure capabilities such as:

- official-source research;
- source grounding;
- Austrian/German/EU mobility reasoning;
- eligibility;
- Evidence extraction/assessment;
- contradiction detection;
- regulatory interpretation;
- document reasoning;
- structured-output reliability;
- tool use;
- professional/client explanation.

A model/runtime combination may be eligible for one capability and prohibited for another.

Routing flow:

```text
capability + context + risk
        ↓
eligible runtime/model set
        ↓
quality history
privacy
latency
runtime health
availability
cost
        ↓
selected execution path
```

Regulatory truth continues to originate from the governed source chain:

```text
Official Source
      ↓
SourceSnapshot
      ↓
Governed Evidence / VerifiedRule
      ↓
eligible model synthesis
```

A model is never the regulatory source merely because it is strong or local.

---

## 10. Quality Floor Doctrine

Permanent doctrine:

> **Minimize total governed outcome cost subject to a non-negotiable quality and constitutional floor.**

Cost optimization never overrides:

- authority;
- risk;
- required quality;
- Evidence requirements;
- verification requirements;
- privacy/sensitivity;
- SLA/latency requirements;
- reliability;
- Board-reserved rules.

A cheaper execution path is acceptable only if it has already earned the required capability quality.

---

## 11. AI Economics / Cost Governor

The Cost Governor is an explicit architectural component, but not an authorization layer.

Destination responsibilities:

- Model Router economics;
- context-compression economics;
- prompt/context caching;
- semantic caching where safe;
- token accounting;
- AgentRun cost;
- Mission cost;
- department cost;
- provider cost;
- local compute/GPU cost;
- verification cost;
- retry/failure cost;
- human-intervention cost;
- latency/SLA penalty;
- quality-adjusted cost;
- budget anomaly detection.

Target business metric:

> **€ / successful governed outcome**

Budget pressure may reroute, defer, restrict or escalate. It may not silently lower the required quality.

---

## 12. Persistent employee != model

The organizational employee abstraction persists independently of any one inference provider/model.

```text
AI Employee
├── identity
├── OrganizationPosition
├── department / manager
├── responsibilities / expertise
├── capabilities
├── authority
├── autonomy
├── risk permissions
├── Missions / WorkItems
├── memory / relationships
├── tools
├── runtime eligibility
├── model eligibility
├── performance / quality history
├── incident history
├── cost history
└── learning history
```

An Austria specialist can use different eligible models across time or even inside one Mission. The employee's organizational identity remains stable.

---

## 13. Dynamic Mission Squads

Complex Missions may create temporary cross-functional squads from persistent employees.

```text
Mission
  ↓
required capabilities
  ↓
Mission Squad
  ├── mobility specialist
  ├── Evidence specialist
  ├── document specialist
  ├── regulatory specialist
  └── independent verifier where required
  ↓
Mission Lead
```

Munder-derived communication may support collaboration. Plasma-style recursive decomposition may discover additional bounded work. AIOS governance defines what every participant may do.

---

## 14. Transparency / Flight Recorder

Consequential organizational behavior should eventually be reconstructable end-to-end:

```text
Mission
→ WorkItem
→ employee
→ ContextBundle
→ knowledge retrieval
→ compression decision
→ model/runtime selection
→ conversation
→ tool action
→ Evidence / VerifiedRule
→ recommendation
→ verification
→ Decision Readiness
→ authority decision
→ Command Gateway
→ canonical effect
→ outcome
```

New lineage dimensions include:

- original context references/hash;
- compression method/revision/policy;
- before/after token counts;
- protected context;
- model/runtime selected;
- why it was eligible/selected;
- estimated/actual cost;
- quality outcome.

Board visibility does not imply Board interruption.

---

## 15. Earned Autonomy boundary

Autonomy remains capability + context specific.

```text
A0  Prohibited
A1  Human executes
A2  AI prepares; approval required
A3  Autonomous with mandatory review
A4  Autonomous with monitoring + valid recovery controls
A5  Fully autonomous within bounded authority
```

Permanent invariants:

- agents cannot promote themselves;
- authority != autonomy != risk;
- Board ceilings remain supreme;
- promotion requires measured evidence;
- downgrade may be faster than promotion;
- recursive child work never inherits broader authority/autonomy automatically.

The current repository has canonical `OrganizationPosition.authority_level` but does not yet have an equally explicit canonical capability-specific autonomy profile. V1.3-I must create that truth before the Immune System attempts dynamic autonomy downgrade.

---

## 16. H → I transition

The accepted H-stage now has enough bounded measurement + restrict-only behavior to close the **H.2 safety/measurement foundation** without pretending the entire future Immune System is complete.

Accepted foundations include:

- H.1 canonical-lineage validation and aggregate circuit;
- H.2.1 verifier-disagreement recurrence restriction;
- H.2.2 trusted runtime-health attribution;
- H.2.2 runtime failure classification / provider-egress provenance;
- H.2.3 pre-egress revision-conflict attribution;
- H.2.4 post-producer revision-race attribution.

No additional H.2 control is justified merely because unused incident vocabulary exists.

The next architectural stage is:

```text
V1.3-I.1
Capability-Specific Autonomy Profile
+
Autonomy Evidence Foundation
```

I.1 begins with canonical measurement/governance truth. It does not begin with automatic promotion.

---

## 17. Technology strategy — stop adding major frameworks

The current external technology strategy is sufficient:

| Technology | AIOS role | Current architectural position |
|---|---|---|
| Munder Difflin v0.4.4 | organization/runtime donor | STRATEGIC DONOR / CONTROLLED ADOPTION |
| Plasma Wiki 1.2.0 | organizational/project knowledge | PILOT APPROVED |
| Plasma Fractal 1.1.0 | recursive Mission execution | PILOT APPROVED — SANDBOXED ENGINEERING ONLY |
| LLMLingua-2 | context/token compression | SELECTED PRIMARY PILOT |
| Local/open models | economical inference | BENCHMARK THROUGH MODEL ROUTER |
| Frontier APIs | difficult/high-risk reasoning | SELECTIVE ESCALATION RESOURCE |

Do not add another major agent framework merely because it is interesting. New technology must close a measured gap that the current stack cannot address cleanly.

---

## 18. Plasma PR #7 boundary

PR #7 remains a draft vendor-import PR and must not be merged while it contains only scaffolding/provenance metadata.

Required sequence before merge:

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

Target pinned donors remain:

```text
Plasma Wiki    1.2.0 @ b27235fa11f1d3aa4deff50e45e52ea8ddc8af44
Plasma Fractal 1.1.0 @ e629ae2b80250ab502feefe3d9d0266bc58f15b2
license        Apache-2.0
```

Vendoring does not constitute production adoption.

---

## 19. Canonical invariants

The following are frozen architectural rules:

1. Human Owner / Board is supreme authority.
2. Board by exception. Transparency by default.
3. Capability != Authority != Autonomy != Risk.
4. CAN DO != MAY DO.
5. Memory != Truth.
6. Conversation != authority.
7. External runtime != AIOS organization.
8. Scores route; deterministic gates authorize.
9. Agents may be wrong while reasoning; canonical AIOS truth may not become wrong silently.
10. Context should contain more relevant truth, not merely more tokens.
11. Compression output is derived context, not source truth.
12. Compression may reduce representation, never governance meaning.
13. Retrieved knowledge is data, not executable authority.
14. Quality has a floor; cost does not override it.
15. Use the cheapest path already proven capable of satisfying required quality.
16. Paid frontier intelligence is an escalation resource, not a universal default.
17. A model earns capability eligibility through measured evaluation, not self-reported confidence.
18. External frameworks provide capability; AIOS owns meaning and authority.
19. Git/worktree isolation is not security isolation.
20. Autonomy is earned capability by capability.
21. Child delegation may narrow parent scope but never expand it.
22. Governance cost scales with consequence, uncertainty and novelty.
23. Material organizational effects cross governed boundaries.
24. The Immune System may restrict or stop; it never creates permission.
25. Every consequential decision should eventually be reconstructable.
26. Quality first. Cost intelligence second. Premium compute only where it produces measurable additional value.

---

## 20. Delivery sequence

Canonical sequence from this refinement:

```text
H.2 safety/measurement foundation
      ↓
close H.2 as bounded foundation
      ↓
V1.3-I Earned Autonomy
  └── I.1 capability-specific autonomy profile + evidence
      ↓
V1.3-J Agent Organization Runtime
  ├── Munder-derived organization mechanics
  └── Plasma Fractal controlled runtime pilot
      ↓
V1.3-K Execution / Coworker Runtime
      ↓
V1.3-L Live Organization
      ↓
V1.3-M Board Transparency Experience
      ↓
V1.3-N Learning & Optimization
```

Parallel Technology Radar evidence may continue without destabilizing Track C:

```text
Plasma Wiki pilot
Plasma Fractal engineering pilot
LLMLingua-2 benchmark
local-model / Mobility Model Benchmark
Model Router research
```

---

## 21. End-to-end benchmark north star

A future Austrian Mobility Mission should exercise the whole organization:

```text
Goal
→ Mission
→ AI CEO
→ Mission Squad
→ bounded recursive decomposition
→ organization communication
→ Context Broker
→ organizational knowledge
→ Evidence retrieval
→ compression where eligible
→ Model Router
→ specialist reasoning
→ independent verification
→ Decision Readiness
→ restrictive Immune checks
→ Command Gateway
→ Board only where required
→ canonical outcome
→ decision lineage
→ learning
```

Measure at least:

- professional outcome quality;
- Evidence grounding;
- critical error rate;
- context tokens;
- compression ratio;
- model/runtime cost;
- total governed outcome cost;
- latency;
- collaboration quality;
- verification disagreement;
- human interventions;
- Board interventions;
- autonomous completion;
- trace completeness.

---

## 22. Final direction

The project is no longer short of architecture.

Its next competitive advantage will come from proving that this organization works end-to-end with high professional quality, governed autonomy, bounded cost and reconstructable decisions.

> **Build the organization. Measure it. Govern it. Let autonomy be earned from evidence.**
