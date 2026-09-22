# Phase 16 Candidate Evaluation — System-1 Decisions and AX Orchestration

**Date:** 2026-09-23
**Base:** `9ca583cb3a38c2cee33d2558ada9995106758cd9`
**Purpose:** bounded architectural decision record for Jev, Laya, and Google AX.
**Production authority:** AIOS deterministic policy and canonical state remain authoritative.

## Decision

This evaluation does **not** promote any external candidate directly into production.

| Candidate | Decision | Why |
| --- | --- | --- |
| **Jev** | **HOLD — benchmark candidate** | Strong fit for low-latency typed decisions, but it is an external/closed API. We do not yet have reproducible AIOS workload results, calibrated thresholds, or provider-cost evidence sufficient for production authority. |
| **Laya** | **HOLD — preferred self-hosted System-1 candidate for a controlled benchmark** | Apache-2.0, local/self-hostable, typed decisions and probabilities. Its own published README explicitly says the base model is near chance on its typed-decision benchmark without task-specific fine-tuning and that probabilities require application-specific calibration. Therefore it is a candidate for specialization, not a drop-in production decision engine. |
| **Google AX** | **DEFER — execution-substrate candidate, not AIOS orchestrator** | AX provides declarative Tasks, Workspaces, Gateways and Models plus sandboxing and suspend/resume. It overlaps strongly with future AIOS runtime infrastructure, but it introduces Kubernetes/Agent Substrate dependencies and is explicitly still v1alpha1/under active breaking-change development. It must not become canonical AIOS organizational state or authority. |

## What we actually established

### 1. System-1 decision engines

AIOS already has deterministic governance and must keep it.

The correct future boundary is:

```
AIOS canonical state
    ↓
deterministic policy / eligibility / safety gates
    ↓
optional System-1 recommendation
    ↓
AIOS deterministic validation
    ↓
action or exception
```

A System-1 probability is evidence. It is never permission, authority, truth, or an execution grant.

Candidate workloads for a later benchmark:

- retry / stop / escalate;
- work routing;
- competency preflight: READY / GAP / NOT_SUITABLE;
- routine human-exception classification;
- provider/model routing.

Required benchmark metrics:

- decision accuracy;
- calibration / ECE;
- false-allow rate;
- false-stop rate;
- unnecessary human escalation;
- p50/p95 latency;
- measured inference cost;
- disagreement with deterministic policy;
- behavior under missing/ambiguous input.

The benchmark must use representative AIOS cases, not vendor benchmark numbers.

### 2. Laya-specific conclusion

Laya is technically attractive because it is self-hostable and exposes typed `choice`, `score`, and probability-style outputs. Its published repository reports very fast inference and provides an Apache-2.0 license.

However, its own limitations are decisive for our current stage:

- zero-shot typed-decision performance is reported as near chance on its benchmark;
- its strongest typed-decision result comes from a fine-tuned checkpoint;
- its README reports that calibration materially changes ECE;
- multilingual performance varies substantially by language.

Therefore:

**Do not install Laya as a generic AIOS dependency.**

If the benchmark later demonstrates value, the first production form should be a narrowly scoped, task-specific decision adapter with application-calibrated thresholds and deterministic fallback.

### 3. Jev-specific conclusion

Jev's product concept is directly relevant: fast typed/probabilistic decisions rather than text generation.

However, AIOS cannot infer production superiority from vendor or third-party benchmark claims. A fair comparison requires the same AIOS fixtures, same decision questions, same acceptance labels, same latency measurement method, and measured cost.

Therefore:

**Jev remains a benchmark candidate, not a production dependency.**

If Jev wins a specific workload, that result must still be wrapped by AIOS policy and must remain replaceable.

### 4. AX-specific conclusion

AX is materially different from Jev/Laya.

AX is an **execution substrate/orchestrator candidate**, not a decision model.

Its primitives map conceptually as:

```
AX Task      → isolated execution unit
AX Workspace → prepared code/tool environment
AX Gateway   → network boundary
AX Model     → model configuration
```

This maps well to future AIOS runtime infrastructure, especially for:

- isolated agent execution;
- suspend/resume;
- reusable workspaces;
- controlled network egress;
- high-density agent workloads;
- long-lived agents that spend much of their lifetime idle.

But AIOS must retain:

- OrganizationAgent identity;
- AgentRun execution evidence;
- work assignment;
- authority;
- permissions;
- credentials;
- budget/economic truth;
- outcome attribution;
- audit lineage.

AX can provide execution infrastructure underneath those boundaries. It cannot replace them.

## Why we are not integrating AX now

The current AIOS Phase 16 work still needs canonical:

- runtime timeout/cancellation behavior;
- hard runtime budget boundaries;
- actual cost metering;
- circuit-breaker semantics;
- runtime reconciliation.

Introducing AX before those contracts exist would invert the architecture: infrastructure would begin dictating application semantics.

The correct sequence is:

```
canonical AIOS runtime contracts
        ↓
bounded execution abstraction
        ↓
substrate compatibility test
        ↓
AX/Agent Substrate benchmark
        ↓
adopt only if it measurably reduces complexity/cost/risk
```

## Final selection

For now:

**Production decision engine:** existing deterministic AIOS logic.

**System-1 research candidate:** Laya first for self-hosted controlled evaluation; Jev remains a parallel external benchmark candidate.

**Execution substrate:** existing AIOS runtime remains authoritative; AX is a deferred substrate evaluation.

This is deliberately a **hold/defer decision, not a rejection**. The candidates are useful enough to keep in the evaluation ledger, but none has earned production authority merely by existing or publishing strong benchmark claims.

## Non-negotiable boundary

> **External model/runtime capability may improve AIOS execution; it never becomes AIOS organizational truth or authority.**

The eventual promotion path is:

**TEST → EVALUATE → SHADOW → GOVERN → PROMOTE → MEASURE → REVOKE IF EVIDENCE REGRESSES.**

No candidate receives authority, budget, credentials, permissions, autonomy, assignment or external execution rights from this document.
