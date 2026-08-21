# V1.3 Plasma Controlled Adoption Roadmap — 2026-08-21

**Status:** TRACK B PILOT PROGRAMME — APPROVED TO START  
**Production authority effect:** NONE  
**Accepted V1.3 baseline:** H.2.4 COMPLETE / PASS / SEALED  
**Active Track C candidate:** H.2.2 runtime-health classification refinement — PRODUCTION PROOF PENDING

---

## Purpose

This record places Plasma AI into the current V12 delivery sequence without disturbing the accepted High-Autonomy Organization dependency order.

Plasma adoption runs in **Track B — Technology Radar / Platform Evolution** while V1.3-H continues its bounded safety/measurement programme in Track C.

No Plasma pilot is allowed to pre-authorize Earned Autonomy, production recursive execution, new provider-health policy, new material-action authority or canonical state mutation.

---

## Current repository checkpoint

At the time this programme is created:

```text
V1.3-A       COMPLETE / PASS / SEALED
V1.3-B       COMPLETE / PASS / SEALED
V1.3-C       COMPLETE / PASS / SEALED through C.4
V1.3-D       COMPLETE / PASS / SEALED through D.3
V1.3-E       COMPLETE / PASS / SEALED through E.2
V1.3-F       COMPLETE / PASS / SEALED through F.1
V1.3-G       COMPLETE / PASS / SEALED through G.5
V1.3-H.1     COMPLETE / PASS / SEALED
V1.3-H.2.1   COMPLETE / PASS / SEALED
V1.3-H.2.2   COMPLETE / PASS / SEALED
V1.3-H.2.3   COMPLETE / PASS / SEALED
V1.3-H.2.4   COMPLETE / PASS / SEALED

H.2.2 runtime-health classification refinement
              IMPLEMENTED / PRODUCTION PROOF PENDING

V1.3-I Earned Autonomy
              NOT STARTED
```

Latest accepted Production Proof at programme creation:

```text
run 32500438187
4 / 4 jobs PASS
```

This programme does not change those acceptance states.

---

## Plasma programme sequence

### P0 — Architecture and security assessment

**State:** COMPLETE for initial controlled-adoption decision.

Outputs:

- `docs/PLASMA_AIOS_ADOPTION_V1.md`
- Technology Radar V1.3 classification
- pinned upstream versions and inspected main revisions
- explicit AIOS semantic/authority boundary
- Fractal sandbox requirement
- Wiki trust-hook restriction

### P1 — Plasma Wiki project-knowledge pilot

**State:** APPROVED / NOT STARTED

Scope:

- architecture knowledge;
- engineering knowledge;
- repository policy;
- accepted V1.3 programme knowledge;
- Technology Radar knowledge.

Forbidden in P1:

- client data;
- secrets;
- authoritative Evidence;
- authoritative VerifiedRules;
- production CaseFacts;
- credentials.

Measurements:

- token/context reduction;
- retrieval quality;
- relevance rate;
- latency;
- maintenance overhead;
- stale-index behavior;
- parallel-edit behavior.

### P2 — Fractal sandboxed engineering pilot

**State:** APPROVED / NOT STARTED

Scope:

- Linux/POSIX sandbox;
- no production credentials;
- no production database;
- bounded recursive depth;
- bounded child count;
- bounded iterations;
- bounded wall-clock time;
- bounded cost;
- explicit operator stop.

First target Mission:

> Analyse the accepted Context Broker/runtime implementation and identify missing contracts and proof gaps without modifying authoritative production state.

Measurements:

- decomposition quality;
- final-result quality;
- duplicate work;
- worktree/merge conflicts;
- runtime failures;
- context usage;
- cost;
- latency;
- operator interventions;
- trace completeness.

### P3 — AIOS adapter design

**State:** BLOCKED ON P1/P2 EVIDENCE

Only if pilot evidence is favorable.

Design surfaces may include:

```text
AIOS RecursiveExecutionPort
AIOS KnowledgeIndexPort
FractalExecutionAdapter
PlasmaWikiKnowledgeAdapter
```

Adapter design must preserve:

```text
Context Broker
Capability / Authority / Autonomy / Risk
Materiality Registry
Transparency Layer
Organizational Immune System
Command Gateway
Canonical AIOS state
```

### P4 — Trial implementation

**State:** NOT AUTHORIZED

Requires explicit pilot acceptance.

May include a non-production engineering-only runtime adapter and a repository-knowledge adapter behind feature flags.

### P5 — Production mobility trial

**State:** NOT AUTHORIZED

Requires separately accepted runtime, security, observability, sandbox, authority and recovery contracts.

No government-facing or client-consequential action enters P5 by implication.

---

## Relationship to Munder

Plasma does not replace Munder.

```text
Munder donor
→ horizontal Organization Fabric
  communication / presence / Skills / triggers / telemetry / live organization mechanics

Plasma Fractal donor
→ recursive decomposition / hierarchical execution / bounded worktree agents

Plasma Wiki donor
→ indexed project/organizational knowledge for Context Broker support
```

Where Munder and Plasma overlap, AIOS should benchmark the implementations rather than maintain duplicated production subsystems.

---

## Dependency rule

The programme must preserve the current constitutional sequence:

> **Governance before unrestricted execution. Transparency before increased autonomy. Production proof before additional safety architecture.**

Plasma Track B pilots can run in parallel only because they remain isolated and non-authoritative.

Production integration cannot jump ahead of AIOS contracts simply because upstream code already works.

---

## Exit decision

Each component exits the pilot independently as one of:

```text
ADOPT
TRIAL
HOLD
REJECT
```

Plasma Wiki may advance even if Fractal does not, and vice versa.

The decision must be based on measured value and bounded risk, not framework enthusiasm.
