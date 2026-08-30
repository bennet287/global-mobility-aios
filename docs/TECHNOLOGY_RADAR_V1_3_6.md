# Global Mobility AIOS — Technology Radar V1.3.6

**Date:** 2026-08-30
**Status:** ACTIVE CANONICAL RADAR / AGGRESSIVE EXECUTION MODE / TRANCHE 1 R3 QUEUE AUTHORIZED
**Supersedes for active radar direction:** `TECHNOLOGY_RADAR_V1_3_5.md`
**Research baseline:** `a9e52c28af05893a2ed6397b6bf6ba26df2f55a5`
**Current milestone:** L — IMPLEMENTED / ACCEPTANCE PENDING
**Milestone effect:** none; M remains NOT STARTED

V1.3.6 turns the radar from a growing technology inventory into a reproducible engineering research and elimination programme. It records common methods, exact upstream pins, weighted scorecards, hard blockers, AIOS-specific test scenarios and architecture outputs, then forces credible candidates rapidly into bounded proof or out of the active queue.

```text
Technology Radar = research + architecture + controlled experiments
Technology Radar != production adoption
Technology Radar != Milestone M
Research prototype != canonical AIOS implementation
High score without timely proof = candidate expiry, not indefinite ASSESS
```

## 1. Aggressive operating doctrine

The radar optimizes for learning velocity, decisive elimination and early architectural leverage:

```text
DISCOVER FAST
PIN EXACTLY
TEST THE HARDEST BOUNDARY FIRST
RUN LEADING CANDIDATES IN PARALLEL
PROMOTE, HOLD WITH A NAMED TRIGGER, OR KILL
REVISIT ONLY WHEN EVIDENCE OR PRODUCT NEED CHANGES
```

Aggressive means aggressive against uncertainty and shelfware. It does not mean bypassing authority, security, evidence, licensing or production-acceptance gates.

Execution rules:

- an R2 candidate scoring 85 or higher with no hard blocker enters the next R3 wave automatically;
- at most two candidates solving the same problem advance, and they use identical fixtures;
- R0–R2 should finish within five working days per bounded question;
- an R3 lab should finish within ten working days of entering the active queue;
- an R3 decision record is due within two working days after evidence capture;
- a candidate without an owner, exact pin, fixture, cleanup plan or measurable differentiator is removed from the active queue;
- every active candidate receives a decision expiry date; expired evidence cannot support promotion;
- failed candidates are recorded explicitly and not kept alive through vague “future evaluation” language.

## 2. Permanent boundaries

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
```

## 3. Tranche 1 question set

```text
What does an AI employee know how to do?  → Skill Registry
What may it do now?                        → Authority Engine
How does it access tools/remote agents?    → MCP/A2A Gateways
How are those boundaries attacked/proven? → Red Team Lab
```

Memory, sandbox, durable execution/orchestration and observability remain subsequent research. Their infrastructure choices should sit beneath the governance model defined here rather than define it.

## 4. Research outputs

### Method and scoring

- `technology-radar/V1_3_6_RESEARCH_METHOD.md`
- `technology-radar/V1_3_6_SCORECARD.md`

The method introduces R0–R6 maturity, identical AIOS test fixtures, exact source pins, weighted scoring and hard constitutional blockers. Tranche 1 stops at R2; no isolated lab was executed.

### Skill Registry

- `technology-radar/skills/AIOS_SKILL_REGISTRY_RESEARCH.md`
- `architecture/AIOS_SKILL_REGISTRY_BLUEPRINT.md`

Decision: canonical registry must be AIOS-native. External skills enter through content-addressed quarantine/review, and A2A may receive only a safe outbound projection. A skill or assignment never grants tools or authority.

### Authority Engine

- `technology-radar/authorization/OPENFGA.md`
- `technology-radar/authorization/OPA.md`
- `technology-radar/authorization/CEDAR.md`
- `technology-radar/authorization/SPICEDB.md`
- `architecture/AIOS_AUTHORITY_ENGINE_BLUEPRINT.md`

| Candidate | R2 score | Decision |
|---|---:|---|
| OpenFGA | 88 | ASSESS; leading relationship/delegation candidate |
| OPA | 86 | ASSESS; leading general policy-decision candidate |
| SpiceDB | 84 | ASSESS challenger for large relationship graphs |
| Cedar | 82 | RESEARCH challenger for typed contextual policy |

Recommendation: a future isolated OpenFGA-vs-OPA lab using the same five-action Austria fixture. Do not compose multiple engines unless the lab proves a necessary hybrid.

### MCP/A2A interoperability

- `technology-radar/interoperability/MCP.md`
- `technology-radar/interoperability/A2A.md`
- `architecture/AIOS_INTEROPERABILITY_BLUEPRINT.md`

MCP 2026-07-28 is ASSESS/R2 for governed tools/data. A2A 1.0 is RESEARCH/R2 for independent-agent interoperability. Tool catalogs, Agent Cards, AgentSkill declarations, task state and artifacts are attributed untrusted provider data until AIOS validates and accepts them.

```text
MCP → tools/data through McpGatewayPort
A2A → external agents through A2AGatewayPort
```

Both remain behind AIOS identity, skill, capability, authority, data-egress, Command Gateway, idempotency and reconciliation controls.

### Cybersecurity and Red Team Lab

- `technology-radar/security/AIOS_CYBERSECURITY_SKILL_REGISTRY.md`
- `technology-radar/security/INSPECT_AI.md`
- `technology-radar/security/PROMPTFOO.md`
- `technology-radar/security/GARAK.md`
- `architecture/AIOS_RED_TEAM_LAB_BLUEPRINT.md`

| Candidate | R2 score | Proposed role |
|---|---:|---|
| Inspect AI | 87 | structured evaluation-lab foundation |
| Promptfoo | 86 | application/agent/MCP attack generator; existing pilot remains trial-eligible |
| garak | 78 | independent model/system scanner challenger |

Tool output creates an observation only. An accepted finding requires exact reproduction, defensive-owner review, remediation and independent retest.

## 5. LangGraph truth reconciliation

The repository already contains:

- optional `langgraph>=0.2` dependency declaration;
- a non-production intake graph skeleton;
- historical architecture/workflow direction.

Therefore the accurate active classification is:

```text
OPTIONAL SKELETON PRESENT
NOT USED BY ACCEPTED J/K/L ORGANIZATION RUNTIME
NOT A PRODUCTION-ADOPTED CONTROL PLANE
FUTURE RuntimePort FIT REQUIRES MEASURED NEED + R3 PROOF
```

V1.3.5's phrase “may later evaluate” was incomplete repository truth. V1.3.6 corrects the active classification without rewriting the historical V1.3.5 record.

## 6. R3 execution queue

```text
V1.3.6 Tranche 1 research/architecture  COMPLETE at R2
R3 Wave A                              AUTHORIZED / READY TO IMPLEMENT
production dependencies                NONE ADDED
runtime/schema/authority change         NONE
L acceptance effect                    NONE
M implementation                       NOT STARTED
```

### Wave A — execute first

| Lane | Candidates | Hard question | Required outcome |
|---|---|---|---|
| Authority | OpenFGA vs OPA | can AIOS express employee/resource/delegation decisions without moving canonical authority out of AIOS? | one winner, bounded hybrid proof, or reject both |
| Interoperability | MCP | can a malicious or over-broad tool catalog remain discoverable while invocation fails before provider contact? | gateway contract evidence or HOLD |
| Adversarial evaluation | Inspect AI + Promptfoo | can attacks against authority, evidence and tool boundaries be reproduced without findings becoming truth? | complementary role proof or remove one |

Wave A is authorized for isolated synthetic labs under the research method. It does not require another radar-scheduling decision. Implementation still must declare the exact environment, network/credential scope, owner, artifacts and cleanup before execution.

### Wave B — start when a Wave A lane frees

```text
A2A gateway trust-boundary fixture
Cedar or SpiceDB challenger only if Wave A exposes a concrete gap
AIOS Skill Registry quarantine/signature/activation fixture
OpenTelemetry trace-correlation pilot
backup/PITR restore proof
SecretsPort/OpenBao isolated pilot
```

Wave B uses a pull system: no more than three R3 lanes run concurrently, but completed or killed work is replaced immediately. Backup/restore and secrets proofs take priority over optional framework comparisons because they close production-readiness risks.

### Promotion and kill rules

An R3 candidate advances only when it:

- passes positive and negative AIOS contract fixtures;
- fails closed under outage, stale policy, revocation and malformed input;
- preserves tenant, authority, evidence and canonical-state boundaries;
- has acceptable measured latency and operational burden;
- has a compatible license, replacement path and bounded blast radius.

Fail any constitutional blocker: `REJECT`. Fail the core use case twice after one bounded correction: `HOLD` or `REJECT`. Pass R3: produce an R4 pilot proposal within two working days; do not silently install it in production.

## 7. Subsequent execution backlog

```text
sandbox/isolation comparison             NEXT QUEUE
Temporal/durable execution               NEXT QUEUE
memory architecture and Mem0/OpenViking  NEXT QUEUE
LangGraph/Agno orchestration fit          TRIGGERED ONLY BY PROVEN GAP
OpenTelemetry observability              WAVE B PRIORITY
Langfuse/Phoenix comparison               AFTER OTEL BASELINE
backup/PITR + restore                     WAVE B PRIORITY
SecretsPort/OpenBao                       WAVE B PRIORITY
final cross-tranche scorecard             CONTINUOUSLY UPDATED
```

The queue advances automatically within these bounds. Product necessity and `ROADMAP.md` remain scheduling authority for changing priorities, expanding scope or moving any candidate into production.

## 8. Current L truth

```text
L runtime acceptance evidence       COMPLETE / ACCEPTED
AI domain corroboration harness     IMPLEMENTED / RESULT PENDING
independent professional review     PENDING
final exact-current-head proof      PENDING
L overall                           IMPLEMENTED / ACCEPTANCE PENDING
M                                   NOT STARTED
```

V1.3.6 is supporting research only and cannot substitute for either remaining L acceptance gate.
