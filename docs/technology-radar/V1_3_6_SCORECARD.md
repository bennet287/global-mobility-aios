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

This board now separates historical evidence from current deep implementation.
`IMPLEMENTED / RUN PENDING` is not a pass.

| Candidate/lane | Current implementation depth | Executed evidence posture | Confidence |
|---|---|---|---|
| OpenFGA | T1/T2/T3/T6/T8 harnesses, relationship graph, ListObjects, revocation, model versioning, rebuild, temporal conditions | historical 120-case correctness evidence exists on an earlier authority checkpoint; new deep/current-head runs pending | MEDIUM |
| OPA | T1/T2/T3/T4/T6/T8 harnesses, canonical data, hot update/rollback, signed bundles, tamper rejection | historical 120-case correctness evidence exists on an earlier authority checkpoint; bundle/deep/current-head runs pending | MEDIUM |
| Cedar | real CLI, typed entities, schema validation, hierarchy, permit/forbid | real-CLI execution must be rerun on current typed implementation | LOW |
| SpiceDB | real service challenger, schema, nested permissions, revocation | implementation only; execution pending | LOW |
| MCP | real SDK, authority-filtered discovery, per-call authorization, replay, Streamable HTTP | implementation only; execution pending | LOW |
| A2A | real SDK, Agent Card trust, task/artifact lifecycle, identity/version boundaries, network transport | implementation only; execution pending | LOW |
| Security native | 36-payload state-diff/canary target plus historical category baseline | historical 18/18 category baseline PASS; deep current evidence pending | MEDIUM-LOW |
| Inspect AI / Promptfoo / garak | external-tool adapters wired against the governed attack target | execution pending | LOW |
| Skill Registry | quarantine, review, immutable activation, tenant/position assignment, manifests, version/revocation lineage | execution pending | LOW |
| Microsandbox | microVM, no-network execution, filesystem/timeout/metrics, volumes, snapshots, concurrency | execution pending | LOW |
| Native memory / Mem0 / OpenViking | governance reference, local-only adapters, poisoning and tenant stress | execution pending; external candidates may be BLOCKED if local services are absent | LOW |
| Native / Temporal / LangGraph / Agno orchestration | common durable lifecycle, HITL, retry/resume/checkpoint experiments | execution pending | LOW |
| OpenTelemetry | SDK trace boundary plus real Collector chaos harness | execution pending | LOW |
| Langfuse / Phoenix | self-hosted/local-only secondary observability harnesses | execution pending; BLOCKED if local services are absent | LOW |
| OpenBao | KV v2, ACL/TTL/revocation/rotation/audit plus persistence depth | execution pending | LOW |
| PostgreSQL recovery | logical restore, event replay and native WAL-PITR fixture | execution pending | LOW |
| AG-UI | real protocol event models, protected state filtering, tool/interrupt/revision boundaries | execution pending | LOW |
| CopilotKit | isolated v2 runtime, info/SSE/middleware/factory/A2UI boundary | execution pending | LOW |
| Development-model benchmark | provider-neutral task packet + Microsandbox evaluator | BLOCKED until a real candidate output is supplied; non-blocking for runtime R4 | LOW |
| Grand Integration Trial | eleven mandatory runtime lanes + fingerprint/failure/sovereignty gates | execution pending until lane artifacts exist | LOW |

No candidate receives current-head empirical credit merely because its lab exists.

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
OpenFGA vs OPA vs Cedar vs SpiceDB vs Native AIOS
```

Security:

```text
Inspect AI vs Promptfoo vs garak vs Native state-diff attack target
```

Memory:

```text
Mem0 vs OpenViking vs Native continuity memory
```

Orchestration:

```text
Temporal vs LangGraph vs Agno vs Native WorkItem semantics
```

Observability:

```text
OpenTelemetry baseline vs Langfuse vs Phoenix
```

Governed UI:

```text
AG-UI protocol boundary vs CopilotKit runtime boundary vs Native Cockpit state contract
```

Development-model tooling is evaluated separately because it is not an AIOS
runtime dependency. Its result cannot unblock a failed runtime sovereignty lane.

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

The R3 **implementation surface is complete enough to execute the programme**, but
the evidence surface is not reconciled. The authoritative implementation snapshot
is `labs/r3/programme_inventory.v1.json`.

The runtime Grand Integration Trial now requires eleven evidence lanes:

```text
authority
interoperability
security
skills
sandbox
observability
secrets
recovery
memory
orchestration
ui
```

A lane artifact is unacceptable when it is missing, execution-blocked, failed,
has critical failures, reports unauthorized canonical effects, or lacks its
result fingerprint.

Development-model tooling is intentionally outside the eleven runtime gates. It
measures developer productivity/correctness and cannot compensate for runtime
security or sovereignty failures.

Current programme posture:

```text
R3 implementation surface     IMPLEMENTED
R3 current-head execution     PENDING
R3 evidence reconciliation    PENDING
Grand Integration Trial       PENDING
R4 decision eligibility       NOT YET ELIGIBLE
Production adoption           NOT AUTHORIZED
Austria professional review   NOT SATISFIED BY THIS RADAR
Milestone M                   NOT AUTHORIZED BY THIS RADAR
```

The next scorecard change must come from actual machine-readable result artifacts,
not from another architecture-only reassessment.
