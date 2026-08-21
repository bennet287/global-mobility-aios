# Global Mobility AIOS — Technology Radar V1.3

**Date:** 2026-08-21
**Status:** ACTIVE CANDIDATE V1.3 — platform evolution / evaluation / controlled adoption track
**Accepted product baseline:** Phase 13.16.10 COMPLETE / PASS
**Active product stream:** Phase 13.17 IN PROGRESS / PAUSED BY EVALUATOR
**Accepted V1.3 baseline:** H.2.4 COMPLETE / PASS / SEALED
**Active Track C candidate:** H.2.2 runtime-health classification refinement — PRODUCTION PROOF PENDING
**Historical predecessor:** `TECHNOLOGY_RADAR_V1_2.md`

Technology Radar V1.3 preserves the Munder strategic-donor decision and adds Plasma AI as two separately evaluated controlled-adoption candidates: Plasma Wiki and Plasma Fractal.

The Radar remains an evidence-driven adoption system, not a dependency manifest.

> **External infrastructure provides capability. AIOS owns meaning and authority.**

---

## 1. Permanent adoption principles

Third-party infrastructure may parse, execute, retrieve, observe, scan, render, evaluate, optimize, coordinate, remember or connect, but may not become authoritative for:

- Global Mobility domain meaning;
- legal status;
- Evidence state;
- certification/publication state;
- human-review requirements;
- organizational authority;
- Mission/WorkItem semantics;
- semantic OrganizationActivity;
- canonical business outcomes.

Preferred pattern:

```text
AIOS domain / Organization OS
        ↓
AIOS-owned capability contract
        ↓
Context / Canonicalization / Governance / Execution boundaries
        ↓
external runtime / technology
```

Hard invariants:

```text
conversation != authority
message != decision
memory != Evidence
memory != VerifiedRule
provider event log != canonical AIOS Activity automatically
external runtime capability != organizational permission
```

---

## 2. Adoption lifecycle

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

`STRATEGIC DONOR`, `PILOT APPROVED` and `TRIAL` are not synonyms for production ADOPT.

Every external subsystem must earn its next state independently.

---

## 3. Current strategic fit and adoption state

### A+ — strongest strategic fit

| Technology | AIOS capability | Adoption state |
|---|---|---|
| Promptfoo | AI regression / adversarial / quality evaluation | PILOT COMPLETE / TRIAL-ELIGIBLE |
| OpenTelemetry | vendor-neutral engineering telemetry | PILOT COMPLETE / TRIAL-ELIGIBLE |
| ClamAV | untrusted-upload malware scanning / quarantine | PILOT COMPLETE / TRIAL-ELIGIBLE |
| Docling | document normalization / structured intelligence | PILOT IN PROGRESS |
| Presidio | Privacy Gateway / sensitive-data processing | QUEUED PILOT |
| urlwatch | official-source change monitoring | QUEUED PILOT |
| **Munder Difflin v0.4.4** | **Organization Fabric / Agent Runtime / Communication / Skills / Live Organization donor** | **STRATEGIC DONOR / CONTROLLED ADOPTION PROGRAMME** |
| **Plasma Wiki 1.2.0** | **Context-efficient project/organizational knowledge beneath Context Broker** | **PILOT APPROVED** |
| **Plasma Fractal 1.1.0** | **Recursive bounded work decomposition / hierarchical execution** | **PILOT APPROVED — SANDBOXED ENGINEERING ONLY** |
| OpenWorker | finished-work execution / tools-connectors-deliverables reference | REFERENCE / CONTROLLED RESEARCH |
| Temporal | durable timers / waits / retries / resumption | DEFERRED PILOT |
| OpenFGA | relationship authorization behind AIOS authority semantics | DEFERRED PILOT |

### A — specialist technologies

| Technology | Intended capability | Adoption state |
|---|---|---|
| pgvector | governed semantic retrieval | BENCHMARK |
| Qdrant | dedicated semantic retrieval alternative | BENCHMARK AGAINST PGVECTOR |
| Pydantic AI | typed production agent runtime | RESEARCH / PILOT CANDIDATE |
| Langfuse | LLM/agent observability behind OpenTelemetry | RESEARCH / PILOT CANDIDATE |
| PaddleOCR | specialist OCR / extraction | GAP-TRIGGERED BENCHMARK |
| Unlimited-OCR | advanced OCR/VLM extraction | GAP-TRIGGERED BENCHMARK |
| DSPy | offline AI-program optimization | RESEARCH |
| Gotenberg | PDF/document conversion | QUEUED WHEN OUTPUT NEED EXISTS |
| Typst | premium professional report generation | QUEUED WHEN OUTPUT NEED EXISTS |
| EU DSS | EU electronic-signature validation | RESEARCH |

Conditional/fallback candidates remain Fides, OpenLineage, OPA, OpenFeature, Haystack and MarkItDown.

---

## 4. Munder Difflin strategic donor

Munder Difflin v0.4.4 remains the frozen donor baseline already vendored into the AIOS repository.

Canonical record:

`docs/MUNDER_DIFFLIN_AIOS_ADOPTION_V1.md`

High-value donor areas remain:

- Hive communication/routing;
- persistent runtime mechanics;
- provider abstraction;
- PTY/CLI execution;
- Skills;
- task coordination;
- circuit breakers;
- triggers/schedules/heartbeats;
- webhooks/integration patterns;
- memory mechanics;
- transcripts/telemetry;
- cost/token signals;
- graph/live-scene mechanics;
- Git worktrees/IDE concepts;
- voice/realtime concepts.

Rejected assumptions remain:

- file/SQLite state as authoritative AIOS truth;
- GOD-style unlimited implicit authority;
- direct material mutation bypassing Command Gateway;
- provider-owned organization semantics;
- retro pixel-office presentation as final AIOS product design.

---

## 5. Plasma controlled-adoption decision

Canonical record:

`docs/PLASMA_AIOS_ADOPTION_V1.md`

Delivery record:

`docs/V1_3_PLASMA_CONTROLLED_ADOPTION_ROADMAP_2026-08-21.md`

Plasma is split into two independent candidates rather than treated as one platform dependency.

### 5.1 Plasma Wiki

Inspected baseline:

```text
package   plasma-wiki 1.2.0
license   Apache-2.0
python    >=3.11,<3.15
main SHA  b27235fa11f1d3aa4deff50e45e52ea8ddc8af44
```

Candidate destination:

```text
project / organizational knowledge
        ↓
Plasma Wiki
        ↓
indexed scoped retrieval
        ↓
AIOS Context Broker
        ↓
ContextBundle
```

Wiki is not Evidence, not a VerifiedRule store and not canonical legal truth.

The first pilot is restricted to repository/architecture/engineering knowledge.

Custom `.wiki/wiki.py` hooks are executable code and are excluded from the first pilot.

### 5.2 Plasma Fractal

Inspected baseline:

```text
package   plasma-fractal 1.1.0
license   Apache-2.0
python    >=3.12,<3.15
main SHA  e629ae2b80250ab502feefe3d9d0266bc58f15b2
platform  POSIX
```

Candidate destination:

```text
AIOS Mission / WorkItem
        ↓
AIOS Recursive Execution Port
        ↓
Fractal bounded recursive execution
        ↓
AIOS typed results
```

Fractal is not allowed to become the source of AIOS authority, autonomy, risk or canonical state.

The first pilot must be engineering-only and sandboxed on Linux/POSIX.

Git worktrees are branch isolation, not security isolation.

---

## 6. Combined Munder + Plasma destination map

```text
Munder Hive / router
→ Organizational Communication Fabric

Munder Skills
→ Capability Registry runtime

Munder providers / CLI mechanics
→ Agent Runtime Fabric donor

Munder triggers / scheduling / heartbeat
→ Event Nervous System donor

Munder telemetry / transcripts
→ Transparency + Flight Recorder + AI Economics donor

Munder live-scene mechanics
→ Living Organization donor

Plasma Wiki
→ indexed project/organizational knowledge candidate beneath Context Broker

Plasma Fractal
→ recursive Mission decomposition / hierarchical bounded execution candidate
```

Overlap is benchmarked rather than duplicated blindly.

---

## 7. AIOS sovereignty boundary

No Munder or Plasma runtime receives unrestricted context or unrestricted production writes.

```text
Persistent AIOS Employee
        ↓
Context Broker
        ↓
ContextBundle
        ↓
AIOS Runtime / Execution Port
        ↓
Munder / Plasma / other external capability
        ↓
reasoning / decomposition / tools
        ↓
Typed AIOS result or intent
        ↓
Canonicalization
        ↓
Organizational Immune System
        ↓
Authority / Autonomy / Risk / Policy
        ↓
Command Gateway
        ↓
Canonical AIOS state
```

---

## 8. Earned Autonomy boundary

External runtimes never assign A0–A5 autonomy.

Autonomy remains capability-specific and governed by AIOS.

Recursive child work must receive an explicit delegated scope that is equal to or narrower than the parent scope.

```text
parent can delegate work
parent cannot manufacture new authority
```

---

## 9. Risk and verification boundary

Recursive decomposition is not independent verification.

A Fractal child or sibling node cannot automatically satisfy an R3+ independent-verification requirement merely because it is a different node.

AIOS verification independence rules remain authoritative.

---

## 10. Current delivery interaction

At this Radar revision:

```text
accepted V1.3 baseline   H.2.4 COMPLETE / PASS / SEALED
active Track C candidate H.2.2 runtime-health classification refinement
candidate state          IMPLEMENTED / PRODUCTION PROOF PENDING
Earned Autonomy          NOT STARTED
```

Therefore:

- Track C must finish the exact Production Proof required for its current candidate;
- Plasma Track B pilots may start in parallel only because they are isolated and non-authoritative;
- Plasma does not pre-authorize any later H.2 control;
- Plasma does not pre-authorize V1.3-I Earned Autonomy;
- production Fractal mobility execution remains blocked on later explicit acceptance.

---

## 11. Pilot gates

### Plasma Wiki pilot

Measure:

- context/token reduction;
- relevant-document recall;
- irrelevant-context rate;
- retrieval latency;
- agent output quality;
- stale-index behavior;
- parallel-edit behavior;
- maintenance burden.

### Fractal engineering pilot

Measure:

- decomposition quality;
- final-result quality;
- duplicate work;
- worktree/merge conflict rate;
- context usage;
- runtime failures;
- cost;
- latency;
- operator interventions;
- trace completeness.

Environment requirements:

```text
sandboxed Linux/POSIX
no production credentials
no production database
bounded depth
bounded descendants
bounded iterations
bounded time
bounded cost
explicit stop control
```

---

## 12. Advancement criteria

A Plasma component may move from PILOT to TRIAL only when evidence demonstrates measurable value and all applicable boundaries remain intact:

- semantic sovereignty;
- Human Owner / Board supremacy;
- tenant isolation;
- Context Broker mediation;
- sensitivity/privacy isolation;
- Capability/Authority/Autonomy/Risk separation;
- sandboxing;
- bounded resource use;
- deterministic failure behavior;
- traceability;
- no direct canonical mutation;
- replacement strategy;
- repository-policy compliance;
- Production Proof once AIOS runtime code is introduced.

---

## 13. Final Radar rule

> **Adopt external technology aggressively when it demonstrably accelerates AIOS, but never surrender domain meaning, Evidence, authority, autonomy, risk, canonical truth, governance, Command Gateway control or Board transparency.**

For Plasma specifically:

> **Use Wiki to improve context efficiency and Fractal to test bounded recursive execution. Do not let either become the organization itself.**
