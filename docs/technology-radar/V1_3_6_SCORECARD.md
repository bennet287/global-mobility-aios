# Technology Radar V1.3.6 — Deep Evidence Scorecard

**Date:** 2026-08-30
**Status:** ARCHITECTURE SCORES PRESERVED / EMPIRICAL DEPTH RECLASSIFIED / NO ADOPTION DECISION
**Method:** `V1_3_6_RESEARCH_METHOD.md`
**Blueprint:** `V1_3_6_DEEP_VALIDATION_BLUEPRINT.md`

## 1. Why this changed

The earlier scorecard used one weighted R2 number. That remains useful for
architecture potential but is too easy to read as proof.

V1.3.6 now tracks:

```text
Architecture Score
Security Score
Operational Score
Empirical Score

Confidence = LOW | MEDIUM | HIGH

Evidence coverage:
  feature
  security
  failure
  lifecycle
  integration
```

No composite score may hide a sovereignty failure.

## 2. Architecture Score

The original R2 weights remain unchanged:

| Dimension | Weight |
|---|---:|
| AIOS architectural fit | 20 |
| sovereignty / replaceability | 15 |
| security architecture | 15 |
| authority compatibility | 10 |
| evidence compatibility | 10 |
| enterprise maturity | 8 |
| interoperability | 7 |
| self-host/data control | 5 |
| operational simplicity | 4 |
| licensing | 3 |
| cost | 3 |
| **Total** | **100** |

Architecture Score answers "how promising is the design fit?" It does not answer
"has it been proven?"

## 3. Independent score classes

**Security Score** comes from threat modeling, tenant/delegation/secret controls,
real adversarial testing, fail-closed behavior, supply-chain posture and
reproduced findings.

**Operational Score** comes from deployment, upgrades, latency, availability,
recovery, observability, backup, operator burden, resources and cost.

**Empirical Score** comes only from executed evidence. T0 contributes little;
native feature, lifecycle, adversarial, chaos, concurrency, integration and replay
evidence progressively contribute more.

Until T0–T8 result contracts are automated, use tier/coverage labels instead of
inventing empirical numbers.

## 4. Current Architecture Scores

| Candidate | Architecture Score | R2 state |
|---|---:|---|
| OpenFGA | 88 | ASSESS |
| OPA | 86 | ASSESS |
| Cedar | 82 | RESEARCH challenger |
| SpiceDB | 84 | ASSESS challenger |
| MCP 2026-07-28 | 87 | ASSESS |
| A2A 1.0 | 82 | RESEARCH |
| Inspect AI | 87 | ASSESS |
| Promptfoo | 86 | TRIAL-ELIGIBLE / RED TEAM R2 |
| garak | 78 | RESEARCH |

## 5. Current empirical-depth board

| Candidate/lane | T0 | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|
| OpenFGA | PASS | PASS — real 120-case corpus | PENDING | PENDING | PENDING | PARTIAL PASS | PENDING | PENDING | PENDING | MEDIUM |
| OPA | PASS | PASS — real 120-case corpus | PENDING | PENDING | PENDING | PARTIAL PASS | PENDING | PENDING | PENDING | MEDIUM |
| Cedar | PASS | IN PROGRESS — real CLI rerun pending after serialization repair | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | LOW |
| SpiceDB | R2 only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | LOW |
| MCP | design/contract only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | LOW |
| A2A | R2 only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | LOW |
| Security native baseline | PASS — category smoke | NOT REAL ATTACK PROOF | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | LOW |
| Inspect AI | R2 only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | LOW |
| Promptfoo | research + historical pilot context | PENDING for V1.3.6 target | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | LOW |
| garak | R2 only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | LOW |
| Skill Registry | architecture only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | LOW |

## 6. Evidence coverage

Each candidate eventually reports measured:

```text
Feature coverage
Security coverage
Failure coverage
Lifecycle coverage
Integration coverage
```

The denominator is strategically relevant features/tests in the candidate Feature
Exploitation Matrix, not every vendor feature.

Until automated, use `PENDING_MEASURED` rather than subjective percentages.

## 7. Hard blockers

A candidate is HOLD/REJECT for the proposed role if evidence shows:

- external state must become canonical AIOS truth;
- skill/capability discovery grants authority;
- material action bypasses Command Gateway;
- memory/telemetry/security finding becomes Evidence automatically;
- privileged execution fails open;
- tenant isolation is ambiguous;
- secrets escape governed storage;
- candidate cannot be replaced/rebuilt without losing canonical meaning;
- license/data obligations are incompatible.

A 99/100 architecture score cannot override a blocker.

## 8. Feature Exploitation Matrix

Every active candidate must maintain:

| Feature | AIOS hypothesis | Test tier | Unique value expected | Result | Evidence ref |
|---|---|---|---|---|---|
| feature | measurable claim | T2/T3/etc | what native AIOS lacks | pending/pass/fail | artifact |

Major strategic features cannot remain untested beyond R3 without explicit
exclusion rationale.

## 9. Competitive shootouts

Authority:

```text
OpenFGA vs OPA vs Cedar vs Native AIOS
```

Security:

```text
Inspect AI vs Promptfoo vs garak vs Native attack corpus
```

Memory:

```text
Mem0 vs OpenViking vs Native memory
```

Orchestration:

```text
Temporal vs LangGraph vs Agno/AgentOS vs Native WorkItem runtime
```

Every shootout includes a "do we need this dependency?" result.

## 10. Promotion rules

**R2 → R3:** high Architecture Score may prioritize testing, but Feature
Hypotheses and Feature Exploitation Matrix are mandatory.

**R3 → R4:** relevant T1/T2 plus lifecycle/security/failure tiers appropriate to
the component, no hard blocker, and measurable unique value.

**R4 → R5:** shadow evidence, acceptable false-allow/deny behavior, operational
evidence and integration/rollback design.

**R5 → R6:** replaceability, security/license/operations/recovery proof and
explicitly scoped adoption.

## 11. Current decision posture

Current R2 rankings still prioritize work, but V1.3.6 no longer allows "R3
verified" language based only on T0/T1 breadth.

The next scorecard revision must be driven by machine-readable deep-validation
evidence.
