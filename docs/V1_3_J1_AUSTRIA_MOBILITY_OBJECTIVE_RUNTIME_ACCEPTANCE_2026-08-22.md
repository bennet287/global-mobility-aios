# Global Mobility AIOS — V1.3 J.1 Austria Mobility Objective Runtime Acceptance

**Date:** 2026-08-22
**Status:** COMPLETE / PASS / SEALED
**Technical candidate:** `b30ae8d885f8f54285b2342a873acfe5c94ca525`
**V12 Production Proof:** `32565671588` — 4/4 PASS
**Repository Policy Check:** `32565671592` — PASS
**Parent programme:** V12.24 Outcome Evidence + Live Organization Programme

## 1. Accepted scope

J.1 proves the first bounded native AIOS organization-runtime vertical for one Austria mobility objective without introducing a parallel Mission model, agent framework, schema or authority system.

The accepted topology is:

```text
Austria mobility objective
→ Global Mobility Operations Lead (persistent owner)
   ├─ Pathway & Eligibility Operations Specialist WorkItem
   └─ Regulatory Intelligence Analyst WorkItem
→ fresh canonical ContextBundles
→ provider-neutral EmployeeRuntimeBindings
→ structural specialist-completion gate
→ owner synthesis readiness
```

The implementation is:

```text
apps/api/app/services/organization_mobility_objective_runtime.py
apps/api/tests/test_organization_mobility_objective_runtime.py
```

J.1 reuses canonical AIOS primitives already present in the repository:

```text
OrganizationPosition
OrganizationalWorkItem
OrganizationActivity
ContextBundle
AgentRuntimeProfile
EmployeeRuntimeBinding
```

No new persistence primitive was required.

## 2. Organization contract

The bounded objective uses the existing persistent positions:

```text
owner       mobility_operations_lead
specialist  pathway_operations_specialist
specialist  regulatory_intelligence_analyst
```

The root WorkItem is the durable objective anchor. The two specialist WorkItems are direct children of that root, share its `objective_key`, and have explicit J.1 phase identities.

Exact replay of objective creation must return the same WorkItems without duplicate topology or duplicate Activity lineage.

Owner synthesis readiness is deliberately structural. It becomes true only when:

1. the supplied root is the canonical J.1 mobility-objective root;
2. the root remains owned by `mobility_operations_lead` and is running;
3. exactly one required child exists for each specialist;
4. both children belong to the exact root/objective/phase topology; and
5. both specialist WorkItems are completed.

This readiness state is not an immigration conclusion, quality score, legal approval or authority grant.

## 3. Runtime and authority boundary

Each specialist runtime is bound only after rebuilding a fresh canonical ContextBundle for the exact WorkItem and persistent position.

Provider/model/runtime identity remains technical execution metadata. Rebinding the same canonical employee context to a different provider may change the runtime binding hash, but cannot change:

```text
persistent position identity
position version
authority level
canonical ContextBundle hash
tool authorization
WorkItem completion state
owner synthesis rules
```

Runtime tools remain the intersection of:

```text
canonical Position/Context Authority tool entitlement
∩
technical runtime availability
```

A runtime profile cannot grant tools that the Context Authority contract does not permit.

A ContextBundle captured before a WorkItem state change is rejected as stale when a runtime binding is attempted later.

## 4. Exact proof

### Backend SQLite regression

Exact candidate checkout: `b30ae8d885f8f54285b2342a873acfe5c94ca525`

```text
1188 passed
19 skipped
1 warning
0 failed
```

The warning is the pre-existing Pydantic `model_metadata_json` protected-namespace warning and is non-blocking.

Fresh SQLite migration/schema proof:

```text
migration head      0081_capability_autonomy_evidence_evaluation_policy
registered tables   124
actual app tables   124
physical tables     125
infrastructure      alembic_version only
physical schema     PASS
```

### PostgreSQL governance contracts

PostgreSQL 16 fresh migration through `0081` passed.

```text
102 passed
1 warning
0 failed
registered tables   124
physical schema     PASS
```

The exercised concurrency suite may emit expected database constraint errors while proving race handling; the governed pytest contract completed PASS.

### Frontend and repository proof

```text
Frontend tests / types / production build   PASS
Repository policy / release / deps / diff   PASS
Repository Policy Check                     PASS
```

V12 Production Proof `32565671588` completed with all four jobs successful.

## 5. Accepted properties

J.1 acceptance establishes that:

- one real mobility objective can be decomposed onto persistent AIOS positions using existing WorkItems;
- two specialist roles can receive independently scoped canonical working contexts;
- technical runtimes can bind to those employee contexts without becoming authority;
- provider/model changes cannot rewrite organizational identity or completion semantics;
- stale context fails closed;
- exact replay does not duplicate the organization topology;
- durable OrganizationActivity lineage exists without introducing a second event/mission store;
- owner synthesis cannot begin merely because a runtime exists; the required specialist work must complete.

## 6. Explicit non-claims

J.1 does **not** establish:

- model/tool execution by the specialists;
- durable specialist `OrganizationalActionOutput` acceptance;
- specialist-to-specialist message/coworker execution;
- Austria immigration/legal correctness;
- a professionally reviewed Austria gold set;
- a Live Organization;
- external side-effect authority;
- autonomy mutation;
- Dynamic Autonomy Manager behavior;
- automatic autonomy promotion/demotion;
- provider/model authority;
- calibrated production cost, latency or GAF.

Those claims remain outside J.1.

## 7. Next bounded slice

The next programme increment is **K.1 — bounded specialist execution / coworker runtime**.

K.1 should reuse the accepted J.1 WorkItems, ContextBundles, runtime bindings and existing organization execution/output primitives. It must not add a new orchestration framework unless measured evidence demonstrates a native AIOS gap.

The initial K.1 proof should require durable current-work outputs for both specialists, exact replay/idempotency, fail-closed stale-context behavior, no external side effects, and owner synthesis readiness that depends on current durable specialist execution evidence rather than WorkItem completion alone.
