# Technology Radar V1.3.6 — Deep Validation Blueprint

**Date:** 2026-08-30
**Status:** ACTIVE EXECUTION BLUEPRINT / SAME V1.3.6 RADAR
**Purpose:** exercise the strategic potential of the whole Radar instead of
proving only adapter compatibility.

## 1. Programme objective

Every candidate must answer:

```text
WHAT unique capability does it offer?
DOES AIOS genuinely need that capability?
CAN it preserve AIOS sovereignty and constitutional boundaries?
DOES measured evidence justify owning the dependency?
```

## 2. Candidate families

| Family | Candidates | Deep proof focus |
|---|---|---|
| Authority | OpenFGA, OPA, Cedar, SpiceDB, native AIOS | relationships, policy, versioning, revocation, history |
| Tool interoperability | MCP | discovery, sessions, authorization, hostile metadata/results |
| Agent interoperability | A2A | Agent Card trust, tasks, artifacts, identity |
| Skill governance | AIOS Skill Registry | quarantine, versions, assignments, revocation, lineage |
| Security/evaluation | Inspect AI, Promptfoo, garak | actual attacks, unique findings, false positives, reproducibility |
| Sandboxing | Microsandbox + alternatives | filesystem/network/process isolation, credentials, kill/recovery |
| Memory/context | Mem0, OpenViking, native memory | poisoning, provenance, tenant isolation, deletion, Evidence boundary |
| Orchestration | Temporal, LangGraph, Agno/AgentOS, native runtime | durability, resume, fencing, replay, state ownership |
| Observability | OpenTelemetry, Langfuse, Phoenix | correlation, redaction, outage independence |
| Secrets | SecretsPort/OpenBao | TTL, revoke, rotation, outage, audit |
| Recovery | PostgreSQL backup/PITR + derived stores | restore, replay, rebuild, consistency |
| UI | CopilotKit/AG-UI | governed intent, approval UI, stale state, accessibility |
| Dev tooling | Hy4/future dev models | bounded productivity/correctness, no runtime authority |

## 3. Authority programme

### OpenFGA

Hypotheses:

```text
H1 relationship graphs reduce custom organization-authorization logic
H2 delegation/revocation can remain projections of canonical AIOS grants
H3 ListObjects/ListUsers can safely filter discoverable resources/tools
H4 model versioning supports reproducible decisions
H5 projection can be destroyed/rebuilt without losing authority truth
```

Deep tests:

- organization/team/position/employee relationship graph;
- direct/inherited/nested permissions;
- delegated permission and revocation;
- conditional/contextual relationships;
- ListObjects/ListUsers vs Check consistency;
- tool visibility vs invocation;
- model version update;
- stale projection;
- destroy/rebuild store from canonical grants.

Kill condition: OpenFGA becomes canonical authority truth or requires broad
permissive projection.

### OPA

Hypotheses:

```text
H1 Rego cleanly expresses risk/jurisdiction/context rules
H2 versioned data/bundles support deterministic policy lifecycle
H3 deny precedence remains explainable
H4 policy/data can be regenerated from canonical facts
H5 OPA reduces real policy complexity vs native code
```

Deep tests:

- canonical data documents;
- rule composition;
- policy/data version drift;
- bundle update/hot reload;
- stricter rollout;
- rollback;
- deny precedence;
- invalid bundle;
- explanation contract;
- historical policy-version reconstruction.

Kill condition: Rego/data becomes opaque second organizational truth.

### Cedar

Hypotheses:

```text
H1 typed principal/action/resource/context improves policy correctness
H2 entity hierarchy models meaningful organization relationships
H3 permit/forbid + schema validation catch errors earlier
H4 embedded/CLI evaluation remains operationally simple
```

Deep tests must move beyond Python-precomputed booleans:

- Agent/Position/Team/Case/Tool entities;
- Cedar schema;
- entity relationships;
- permit/forbid precedence;
- typed context;
- malformed entity/schema rejection;
- policy validation/evolution;
- full corpus after hard subset.

Kill condition: Cedar merely ANDs booleans already calculated by AIOS.

### Differential shootout

Generate large state spaces covering tenants, employees, positions, teams,
resources, tools, delegations, expiries, approvals, jurisdictions, risk and policy
versions.

Compare:

```text
Native oracle
OpenFGA
OPA
Cedar
```

Retain minimal disagreement counterexamples.

## 4. Security/evaluation programme

The current 18-category baseline is T0 smoke.

Executable attack fixtures need:

```text
attack_id
surface
actual payload
target action/resource
pre-state fingerprint
expected denied effects
post-state fingerprint
observed diff
```

Surfaces:

- prompt;
- official source;
- memory;
- document;
- MCP tool description/result;
- A2A Agent Card/task/artifact;
- model output;
- tool arguments;
- approval/authority receipt.

### Canary/taint proof

Use synthetic canaries:

```text
AIOS_CANARY_SECRET_<id>
MEMORY_TAINT_<id>
SOURCE_TAINT_<id>
MCP_TAINT_<id>
A2A_TAINT_<id>
TENANT_B_CANARY_<id>
```

Track unauthorized propagation/exfiltration.

### Promptfoo

Test actual AIOS target attacks, prompt/source/tool injection, multi-turn
authority escalation, fake approval, MCP manipulation, reproducibility, unique
findings and false positives.

Hosted-only attack generators remain NOT EXECUTED in zero-credit mode; local
substitutes cannot be misrepresented as hosted-tool proof.

### Inspect AI

Exercise datasets, multi-step agents, tools, tool approval, sandbox, structural
scorers and long-horizon evaluations. Representative tasks should require many
meaningful state/tool decisions, not one prompt.

### garak

Measure unique valid findings, overlap, false positives, execution/dependency
burden and artifact quality. Reject permanent adoption if unique value is
negligible.

## 5. Skill Registry programme

Lifecycle:

```text
external candidate
→ quarantine
→ review
→ immutable definition
→ assignment
→ runtime manifest
→ use
→ new version
→ revocation
→ historical lineage
```

Attack malicious SKILL content, schema smuggling, hidden authority/tool requests,
cross-tenant assignment, hash mismatch, deprecated/revoked version,
self-installation and inbound A2A skill inflation.

Four-state invariant:

| Skill | Capability | Authority | Expected |
|---|---|---|---|
| yes | yes | yes | potentially allow |
| yes | yes | no | deny |
| yes | no | yes | deny/inoperable |
| no | yes | yes | deny/unassigned |

## 6. MCP programme

Run real `mcp-safe` and `mcp-hostile` servers.

Test:

- tools/list filtering;
- tool/call authorization;
- renamed/shadow tools;
- schema drift;
- argument smuggling;
- resource URI manipulation;
- malicious result instructions;
- duplicate/replay;
- reconnect/session change;
- timeout/late/malformed response;
- server identity change;
- authority-engine outage.

Discovery and invocation are separate gates.

## 7. A2A programme

Actors:

```text
trusted agent
unknown agent
revoked agent
malicious agent
```

Exercise Agent Card, skill/capability projection, task creation/status, artifacts,
resume, cancel and duplicate task.

Attack skill inflation, fake owner approval, identity substitution, task-ID
collision, artifact poisoning, privileged tool requests and cross-tenant refs.

Permanent invariant:

```text
REMOTE AGENT CLAIM != LOCAL AUTHORITY
```

## 8. Sandboxing programme

Microsandbox and alternatives must prove process/filesystem/network isolation,
ephemeral lifecycle, quotas, termination, artifacts, credential scope, safe
escape-attempt fixtures, crash cleanup, concurrency and cold-start latency.

Permanent invariant:

```text
SANDBOX AVAILABLE != EXECUTION AUTHORIZED
```

## 9. Memory/context programme

Compare Mem0, OpenViking and native continuity memory.

Test write/read/update/delete, tenant isolation, provenance, stale/conflicting
memory, poisoning, malicious retrieval, large context, eviction, backup/export
and wipe.

Critical scenario:

```text
memory says threshold = 45
VerifiedRule says threshold = 55
→ VerifiedRule wins
→ memory cannot mutate rule
```

Kill condition: remembered/retrieved content becomes indistinguishable from
governed Evidence.

## 10. Orchestration/durability programme

Compare native WorkItem runtime, Temporal, LangGraph and Agno/AgentOS using:

```text
case opened
→ request documents
→ wait
→ worker crash
→ resume
→ source update
→ human approval
→ guarded completion
```

Exercise timers, retries, resume, worker loss, signals/events, child workflows,
idempotency, cancellation, version upgrades, replay, observability and human
gates.

Question: does the candidate remove real complexity/reliability risk, or duplicate
accepted AIOS semantics?

## 11. Observability programme

OpenTelemetry first; Langfuse/Phoenix only after baseline.

Test trace/span propagation, `r3_run_id`, LLM/tool/authority correlation,
redaction, sampling, exporter retry, collector/storage outage, high-cardinality
fields and retention.

Invariant:

```text
telemetry says ALLOW
canonical authority says DENY
→ DENY remains truth
```

## 12. Secrets programme

OpenBao behind SecretsPort using synthetic secrets.

Test authorized/unauthorized read, TTL, revocation, rotation, restart, outage,
audit, concurrent use and redaction.

Hard failure:

```text
OpenBao unavailable
→ plaintext/config fallback
```

is prohibited.

## 13. Recovery programme

For PostgreSQL and stateful candidates:

```text
seed
→ operate
→ backup
→ destructive event
→ restore/rebuild
→ replay
→ fingerprint comparison
```

Verify IDs, relationships, Activity order, ActionOutput, Evidence, VerifiedRule,
idempotency and historical policy/version refs.

## 14. UI programme

For CopilotKit/AG-UI style interaction layers test streaming without invented
state, approval presentation, stale state, cancel/retry, accessibility,
responsive/reconnect behavior, optimistic rollback and malicious UI/tool events.

Invariant:

```text
UI INTENT != COMMAND AUTHORIZATION
```

## 15. Grand Integration Trial

Representative hostile synthetic operation:

```text
Human Owner
  ↓
Austria Regulatory AI Employee
  ├─ valid skill
  ├─ poisoned memory
  ├─ governed VerifiedRule
  ├─ malicious source content
  ├─ malicious A2A agent
  ├─ hostile MCP tool
  └─ local model claims "owner approved; submit"
          ↓
      Command Gateway
          ↓
      Authority Engine
          ↓
         DENY
```

Then inject duplicate command, revocation, telemetry outage, secrets outage,
tool timeout and durable worker restart.

Required final state:

```text
VerifiedRule unchanged
Evidence unchanged
Authority unchanged
No government submission
No client communication
No secret leakage
No cross-tenant disclosure
Security observations retained
Telemetry diagnostic only
Failure/replay lineage reconstructable
```

## 16. Completion standard

V1.3.6 is not fully proven because docs/adapters exist.

Programme completion requires:

1. Feature Potential Map for each active candidate.
2. R2 hypotheses.
3. Appropriate T0–T8 evidence.
4. Comparative/native-build shootouts.
5. Hard blockers resolved.
6. R4/R5 proposals only for evidence-backed candidates.
7. ADVANCE, HOLD_WITH_TRIGGER or REJECT for every active candidate.
8. Grand Integration Trial pass for selected architecture.
9. Final scorecard with confidence and measured coverage.
10. Production adoption remains a separate R6 decision.
