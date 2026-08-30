# Global Mobility AIOS — Technology Radar V1.3.6

**Date:** 2026-08-30
**Status:** ACTIVE CANONICAL RADAR / DEEP-EVIDENCE EXECUTION MODE
**Supersedes for active radar direction:** `TECHNOLOGY_RADAR_V1_3_5.md`
**Research baseline:** `a9e52c28af05893a2ed6397b6bf6ba26df2f55a5`
**Current milestone:** L — IMPLEMENTED / ACCEPTANCE PENDING
**Milestone effect:** none; M remains NOT STARTED

V1.3.6 is now an end-to-end technology evidence programme rather than an
inventory, architecture scorecard or R3-only lab queue.

```text
Technology Radar
  = discover
  + understand
  + architecture prove
  + lab prove
  + shadow prove
  + integration prove
  + scoped adoption
  + continuous verification
  + retirement

Radar != product necessity
Radar != production authority
Radar != canonical truth
```

Canonical supporting documents:

- `technology-radar/V1_3_6_RESEARCH_METHOD.md`
- `technology-radar/V1_3_6_SCORECARD.md`
- `technology-radar/V1_3_6_DEEP_VALIDATION_BLUEPRINT.md`

## 1. Permanent boundaries

```text
CAN DO != MAY DO
SKILL != CAPABILITY
CAPABILITY != AUTHORITY
AUTHORITY != AUTONOMY
MEMORY != EVIDENCE
SANDBOX ISOLATION != EXECUTION AUTHORITY
AGENT FRAMEWORK STATE != ORGANIZATION TRUTH
TELEMETRY != CANONICAL ORGANIZATION ACTIVITY
UI INTENT != COMMAND AUTHORIZATION
EXTERNAL AGENT CLAIM != TRUST OR AUTHORITY
MODEL OUTPUT != HUMAN APPROVAL
R3 PASS != PRODUCTION ADOPTION
```

## 2. Canonical maturity and evidence depth

```text
R0 DISCOVER
R1 UNDERSTAND
R2 ARCHITECTURE PROVE
R3 LAB PROVE
R4 SHADOW PROVE
R5 INTEGRATION PROVE
R6 ADOPT
R7 CONTINUOUSLY VERIFY
R8 RETIRE / REPLACE
```

Tracked separately:

```text
T0 contract/mock
T1 real component
T2 native feature depth
T3 stateful lifecycle
T4 adversarial/security
T5 chaos/failure/recovery
T6 concurrency/scale/property
T7 cross-component integration
T8 historical replay/restore/retirement
```

A large T0/T1 count cannot masquerade as deep R3 proof.

## 3. Whole-Radar question set

```text
What does an AI employee know?                  Skill Registry
What may it do?                                 Authority Engine
How does it reach tools?                        MCP
How does it cooperate with external agents?     A2A
How is execution isolated?                      Sandbox
How does it remember without inventing truth?   Memory/context
How does long-running work survive failure?     Durable orchestration
How are secrets controlled?                     SecretsPort/OpenBao
How is behavior observed?                       OpenTelemetry/Langfuse/Phoenix
How are boundaries attacked/evaluated?          Inspect/Promptfoo/garak
How does the Human Owner interact safely?        Cockpit + governed UI
How are technologies replaced/retired?          R8 exit proof
```

## 4. Candidate map

### Authority

| Candidate | Architecture Score | Current evidence |
|---|---:|---|
| OpenFGA | 88 | T1 real 120-case correctness PASS; T5 partial; native-feature depth pending |
| OPA | 86 | T1 real 120-case correctness PASS; T5 partial; policy lifecycle pending |
| Cedar | 82 | T0 PASS; real CLI T1 rerun pending after serialization repair |
| SpiceDB | 84 | R2 challenger; no deep empirical evidence yet |

### Interoperability

| Candidate | Architecture Score | Current evidence |
|---|---:|---|
| MCP 2026-07-28 | 87 | R2 design; hostile-server deep lab required |
| A2A 1.0 | 82 | R2 design; trust/task/artifact deep lab required |

### Security/evaluation

| Candidate | Architecture Score | Current evidence |
|---|---:|---|
| Inspect AI | 87 | R2 only for V1.3.6 |
| Promptfoo | 86 | research + historical pilot context; V1.3.6 target lane pending |
| garak | 78 | R2 challenger |
| Native security corpus | n/a | 18-category T0 smoke; not 18 resisted attacks |

### Subsequent candidates

```text
Microsandbox                  sandbox/isolation
Mem0                         lower-truth continuity memory
OpenViking                   context/memory donor
Temporal                     durable execution challenger
LangGraph                    bounded execution-graph donor
Agno/AgentOS                 agent-platform donor
OpenTelemetry                observability baseline
Langfuse/Phoenix             observability/eval comparison after OTEL
SecretsPort/OpenBao          secrets control
CopilotKit/AG-UI             governed Cockpit interaction candidate
Hy4/future dev models        bounded development tooling
```

None is production-adopted merely because it appears here.

## 5. Deep-evidence correction

Earlier V1.3.6 language overemphasized "R3 PASS" and test counts.

Current truth:

```text
Contracts/mocks                           T0
Real OpenFGA/OPA 120-case runs           T1
Authority chaos                          partial T5
Cedar real CLI                           T1 in progress
Security 18-category native baseline     T0 smoke only

Still needed:
T2 native feature depth
T3 lifecycle
T4 real adversarial execution
T5 broader failure where relevant
T6 property/concurrency/differential
T7 cross-stack integration
T8 replay/rebuild/retirement
```

This does not invalidate existing work. It makes its evidence meaning precise.

## 6. Feature-first research

Every active candidate now needs:

```text
Feature Potential Map
Feature Exploitation Matrix
Anti-Fit Matrix
Native-build comparison
Feature hypotheses
Kill criteria
Exit strategy
```

The Radar deliberately tests the features that made the candidate interesting.

## 7. Security proof rule

A category label returning a canned denial is not an attack.

Security proof must derive effects from state:

```text
before state
→ real adversarial payload
→ real target
→ after state
→ canonical effect diff
```

Primary metrics:

```text
unauthorized ActionOutputs           0
unauthorized external actions        0
unauthorized authority grants        0
unauthorized VerifiedRule mutation   0
unauthorized Evidence mutation       0
cross-tenant disclosure              0
secret exfiltration                  0
```

## 8. Competitive and native shootouts

```text
Authority:
OpenFGA vs OPA vs Cedar vs Native AIOS

Security:
Inspect vs Promptfoo vs garak vs Native attack corpus

Memory:
Mem0 vs OpenViking vs Native memory

Orchestration:
Temporal vs LangGraph vs Agno vs Native WorkItem runtime
```

A working candidate may be rejected if native AIOS is simpler/stronger.

## 9. Grand Integration Trial

Final proof combines selected architecture under one hostile synthetic mobility
operation.

Inject poisoned memory, malicious source/MCP/A2A content, fake owner approval,
model hallucinated authority, revocation, duplicate command, provider/tool
timeout, telemetry outage, secret request and safe durable-runtime disruption.

Required:

```text
Human/Board sovereignty preserved
Authority preserved
Tenant boundary preserved
Evidence/VerifiedRule truth preserved
No unauthorized external action
No unauthorized canonical mutation
No secret leak
Replay truthful
Failure preserved
Decision lineage reconstructable
```

## 10. Execution priority

Immediate Authority closure remains useful, but it is one layer inside the deeper
programme.

```text
Authority T1 closure
  ├─ real Cedar
  ├─ exact-current-head OpenFGA/OPA
  └─ evidence rollup

then deepen:
  ├─ Authority T2/T3/T6 native-feature shootout
  ├─ Security real attacks T1–T4
  ├─ Skill Registry lifecycle
  ├─ MCP hostile server
  ├─ A2A trust lifecycle
  ├─ OTel / secrets / recovery
  └─ Grand Integration Trial
```

## 11. Adoption discipline

R4 shadow, R5 integration, R6 scoped adoption, R7 continuous verification and R8
retirement are explicit gates.

No candidate jumps from a lab to production.

## 12. Current milestone truth

```text
L runtime acceptance evidence       COMPLETE / ACCEPTED
AI domain corroboration harness     IMPLEMENTED / RESULT PENDING
Independent professional review     PENDING
Final exact-current-head proof      PENDING
L overall                           IMPLEMENTED / ACCEPTANCE PENDING
M                                   NOT STARTED
```

Radar work cannot substitute for L acceptance or silently start M.
