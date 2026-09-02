# Global Mobility AIOS — V1.3 K.1 Bounded Specialist Execution Acceptance

**Date:** 2026-08-22  
**Status:** COMPLETE / PASS / SEALED  
**Technical candidate:** `9a7df63511e45f6a0945ae933929522314a04ec3`  
**V12 Production Proof:** `32582805820` — 4/4 PASS  
**Repository Policy Check:** `32582805835` — PASS  
**Woodpecker push proof:** pipeline `#17` — 4/4 PASS  
**Woodpecker pull-request proof:** pipeline `#18` — 4/4 PASS  
**Parent programme:** V12.24 Outcome Evidence + Live Organization Programme

## 1. Accepted scope

K.1 converts the accepted J.1 Austria organization topology into bounded, durable specialist execution using native AIOS primitives. It does not add a second mission/orchestration system, new agent framework, new database table or migration.

Accepted path:

```text
J.1 Austria mobility objective
→ specialist OrganizationalWorkItem
→ current canonical ContextBundle
→ provider-neutral EmployeeRuntimeBinding revalidation
→ OrganizationExecutionAttempt
→ existing controlled-agent runner / AgentRun
→ one stable current-work OrganizationalActionOutput
→ WorkItem completion
→ owner synthesis readiness only when both specialist outputs remain current and provenance-valid
```

The two persistent specialist positions remain:

```text
pathway_operations_specialist
regulatory_intelligence_analyst
```

The pathway specialist executes through the existing `operations_coordination_agent`; the regulatory specialist executes through the existing `business_intelligence_agent`. Controlled-agent identity is a technical execution primitive, not organizational identity or authority.

## 2. Durable execution and replay contract

For each required specialist, K.1 persists and validates the existing native execution lineage:

```text
OrganizationalWorkItem
ContextBundle
EmployeeRuntimeBinding
OrganizationExecutionAttempt
AgentRun
OrganizationalActionOutput
OrganizationActivity
```

A successful exact replay checks the stable specialist output before invoking the controlled agent. Exact replay therefore returns the already accepted current-work output and its existing AgentRun/execution-attempt lineage rather than creating an uncontrolled duplicate.

Accepted replay properties:

- one durable current-work output per required specialist;
- exact replay does not create a second current-work output;
- exact replay does not create a second AgentRun;
- exact replay does not create a second OrganizationExecutionAttempt;
- cross-session PostgreSQL replay preserves the same durable identifiers;
- provider/model changes cannot masquerade as exact replay provenance.

## 3. Fail-closed provenance and readiness

K.1 strengthens J.1 owner-synthesis readiness. WorkItem completion alone is no longer sufficient.

The readiness gate requires current evidence for both specialists and validates the exact relationship among:

```text
root objective WorkItem
specialist child WorkItem
persistent employee position
current ContextBundle hash
EmployeeRuntimeBinding/runtime profile provenance
execution attempt + execution token
AgentRun
current-work OrganizationalActionOutput
completed WorkItem fingerprint
no-external-side-effect posture
```

The gate fails closed for stale context, wrong WorkItem/runtime binding, wrong specialist provenance, missing specialist output, tampered current-work evidence or runtime existence without accepted execution evidence.

One valid specialist output is insufficient. Both required specialist outputs plus the existing J.1 structural gates are required before owner synthesis becomes ready.

## 4. Authority and side-effect boundary

K.1 is internal-analysis-only. It does not authorize or perform:

- authority/government submission;
- client send;
- payment initiation;
- external-provider irreversible action;
- contract signing;
- case lifecycle mutation;
- policy publication;
- production mutation.

Provider/model/runtime identity remains non-authorizing. Runtime tool availability remains subordinate to canonical Context Authority.

The acceptance tests force the existing safe non-LLM execution path. The proof therefore does not depend on a live LLM or network call.

## 5. Exact proof

### Backend SQLite

Exact candidate checkout: `9a7df63511e45f6a0945ae933929522314a04ec3`

```text
1194 passed
20 skipped
1 warning
0 failed
```

Fresh migration/schema proof:

```text
migration head      0081_capability_autonomy_evidence_evaluation_policy
registered tables   124
actual app tables   124
physical schema     PASS
```

### PostgreSQL 16

The governed PostgreSQL lane explicitly includes the K.1 cross-session execution/replay contract.

```text
103 passed
1 warning
0 failed
migration head      0081_capability_autonomy_evidence_evaluation_policy
registered tables   124
physical schema     PASS
```

The new K.1 PostgreSQL contract proves that durable specialist outputs and their execution lineage survive a real database round trip and exact replay from a new SQLModel session.

### Frontend / repository proof

```text
Frontend tests / types / production build   PASS
Repository policy / release / deps / diff   PASS
Repository Policy Check                     PASS
```

GitHub Actions V12 Production Proof `32582805820` completed with all four jobs successful.

### Forward Woodpecker proof

On the exact same K.1 technical candidate:

```text
Woodpecker push #17
  backend-sqlite       PASS
  frontend             PASS
  postgres-governance  PASS
  repository-policy    PASS

Woodpecker PR #18
  backend-sqlite       PASS
  frontend             PASS
  postgres-governance  PASS
  repository-policy    PASS
```

GitHub's commit-status surface independently reported all eight Woodpecker contexts `success`.

## 6. CI optimization successor is separate

After K.1 was technically proven, CI-only successor `24fc51c6d931c9fd0cc2bd71c7a6876fbe9ecef0` removed duplicate feature-branch push+PR execution. Feature branches now run the four heavy gates once through `pull_request`; `push` is retained for `main`, and manual proof remains available.

The live Woodpecker agent was also moved from two to four parallel workflow slots. These CI changes do not alter the K.1 product acceptance boundary, which remains exact candidate `9a7df635...`.

## 7. Accepted properties

K.1 acceptance establishes that:

- both required J.1 specialists can execute through current canonical context using existing AIOS runtime primitives;
- durable current-work outputs are bound to exact WorkItem/context/runtime/execution provenance;
- exact replay is idempotent and does not multiply current-work evidence;
- stale or mismatched context/runtime/provenance fails closed;
- provider/model identity cannot grant authority or forge completion/readiness;
- WorkItem completion alone cannot unlock owner synthesis;
- both current specialist outputs are required for owner synthesis readiness;
- the bounded slice has no external irreversible side effects;
- the contract works on SQLite and real PostgreSQL without a new migration.

## 8. Explicit non-claims

K.1 does not establish:

- a complete Live Organization;
- owner synthesis execution or a material organization decision;
- specialist-to-specialist collaboration visible in Cockpit;
- live-case or professional Austria immigration correctness;
- production external side-effect authority;
- calibrated production cost/latency/GAF;
- autonomy mutation or Dynamic Autonomy Manager behavior;
- automatic promotion or demotion.

Those claims remain outside K.1.

## 9. Next bounded slice

The next product increment is **L — Live Organization proof**.

The first L slice should turn the accepted J.1→K.1 durable activity into a real owner-led organization cycle and expose that persisted truth through Global Mobility AIOS Cockpit/transparency surfaces. It should reuse existing WorkItems, activities, outputs, evidence/rule lineage, autonomy state and execution telemetry before considering any new persistence model.
