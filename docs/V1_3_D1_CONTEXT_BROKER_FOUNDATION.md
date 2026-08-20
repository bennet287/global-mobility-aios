# V1.3-D.1 — Context Broker / ContextBundle Foundation

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**State:** **IMPLEMENTED / CANONICAL REPOSITORY ACCEPTANCE PENDING**

## Purpose

D.1 establishes the first provider-neutral, purpose-scoped Context Broker contract after the sealed V1.3 governance and transparency foundations.

It follows the final combined architecture ordering:

```text
Governance / Constitutional Contracts
        ↓
Transparency Foundation
        ↓
Context + Organization Semantics
        ↓
Organization Fabric / runtime integration
        ↓
Powerful execution
```

The goal is not to maximize prompt size. The goal is:

> **More relevant truth, not more tokens.**

## Existing canonical primitives reused

D.1 deliberately reuses the existing AIOS organization model rather than creating a second employee/runtime system.

### Persistent organizational identity

`OrganizationPosition` remains the durable employee/position identity boundary. It already owns:

- `position_key`;
- title;
- department;
- reporting line;
- role-card identity;
- authority level;
- organization contract;
- active/suspended state;
- position version.

D.1 does **not** introduce a parallel `Agent`, `Employee`, roster or provider-owned identity table.

### Work scope

`OrganizationalWorkItem` remains the bounded work anchor. It already owns tenant scope, objective, assignment, risk, authority requirement, source references and working `context_json`.

### Canonical serialization

D.1 reuses the existing organization-command canonical JSON and SHA-256 fingerprint primitives so context identity follows the same deterministic repository conventions as governed commands.

## New runtime contract

Implementation:

```text
apps/api/app/services/organization_context_broker.py
```

Focused tests:

```text
apps/api/tests/test_organization_context_broker.py
```

Primary contract:

```python
build_work_item_context_bundle(
    session,
    tenant_key=...,
    position_key=...,
    work_item_id=...,
    purpose=...,
) -> ContextBundle
```

## ContextBundle v1

The foundation bundle contains:

```text
schema version
+ tenant
+ purpose
+ active OrganizationPosition context
+ assigned WorkItem context
+ bounded canonical object references
+ explicit empty Evidence / VerifiedRule / SourceSnapshot bindings
+ explicit empty tool binding
+ explicit empty policy binding
+ context hash
+ generation timestamp
```

The bundle is immutable at the Python contract level and provider-neutral.

### Position context

Includes:

- position key;
- title;
- department;
- reporting position;
- authority level;
- role-card name;
- position version;
- canonicalized position contract JSON.

### WorkItem context

Includes:

- WorkItem identity;
- title/objective;
- department;
- required authority level;
- assigned position;
- status/priority/risk/emergency state;
- objective/phase keys;
- bounded source reference;
- WorkItem `updated_at`;
- canonicalized **working** context JSON.

### Canonical references

D.1 projects references already carried by the WorkItem, including where present:

- lead;
- profile;
- application;
- corporate account;
- corporate mobility case;
- source object + source version.

It does not dump unrestricted domain records into the bundle.

## Trust boundary

A critical D.1 rule is:

```text
WorkItem.context_json = working context
WorkItem.context_json != Evidence
WorkItem.context_json != VerifiedRule
WorkItem.context_json != tool authority
WorkItem.context_json != policy authority
WorkItem.context_json != provider/runtime identity
```

Even if arbitrary working context contains keys such as:

```text
evidence_refs
verified_rule_refs
allowed_tools
provider
model
```

those values remain inside working context. They do not self-promote into authority-bearing ContextBundle fields.

D.1 therefore ships with these authoritative bindings intentionally empty:

```text
evidence_refs = ()
verified_rule_refs = ()
source_snapshot_refs = ()
allowed_tools = ()
policy_version = None
```

Later D/E slices may populate them only through governed, typed adapters.

## Employee identity is independent from runtime identity

The legacy `AgentRun` model still contains a weak provider-era shape (`agent_name`, task, input/output). D.1 does not extend that legacy model yet.

The architecture boundary is now explicit:

```text
OrganizationPosition
    = persistent organizational employee identity

ContextBundle
    = purpose-scoped governed context

future AgentRuntimeProfile
    = provider/model/runtime/session binding
```

Therefore:

```text
employee identity != provider
employee identity != model
employee identity != runtime process
employee identity != runtime session
```

This prepares D.2 and the Munder M1/M3 donor slices without allowing donor roster/runtime semantics to become canonical AIOS identity.

## Fail-closed behavior

D.1 rejects:

- missing tenant/position scope;
- unsupported context purpose;
- foreign-tenant WorkItem access through the existing non-disclosing tenant boundary;
- WorkItems assigned to a different position;
- inactive/suspended positions;
- malformed/non-object position contract JSON;
- malformed/non-object WorkItem context JSON;
- incomplete source-object references;
- a source version without a source identity.

The service is read-only and introduces no canonical mutation path.

## Deterministic context identity

`context_hash` is calculated over the semantically relevant bundle state and deliberately excludes `generated_at`.

Therefore:

```text
same governed state + same purpose
→ same context_hash
```

while a meaningful WorkItem/position/context change produces a different hash.

This gives later AgentRun / Flight Recorder / Replay work a stable context identity without requiring a persistence migration in D.1.

## D.1 non-goals

D.1 does not yet implement:

- a new database table;
- runtime/provider selection;
- model selection;
- AgentRuntimeProfile persistence;
- Munder runtime execution;
- Hive communication;
- Skills/tool authorization;
- Evidence retrieval;
- VerifiedRule hydration;
- memory retrieval;
- Mission Rooms;
- Dynamic Squads;
- AgentConversation/AgentMessage persistence;
- a new AgentRun schema;
- Cockpit UI.

Those belong to later bounded slices and must remain behind the existing governance/transparency architecture.

## Focused acceptance matrix

The D.1 tests cover:

1. deterministic provider-neutral bundle assembly;
2. context-hash change when canonical working state changes;
3. inactive position fail-closed behavior;
4. tenant mismatch / non-disclosing boundary preservation;
5. assigned-position scope enforcement;
6. malformed WorkItem context fail-closed behavior;
7. prevention of working-context self-promotion to Evidence/tools/runtime authority;
8. malformed position contracts and incomplete source references fail closed.

## Next dependency after D.1 acceptance

If D.1 passes canonical repository acceptance, proceed to a bounded D.2 slice:

```text
Agent Runtime Profile + Employee ↔ Runtime Binding
```

D.2 should preserve:

```text
OrganizationPosition owns employee identity
AIOS owns authority and semantics
runtime adapters are replaceable
provider/model/session identity is operational, not organizational authority
```

Only after that should the first bounded Munder-derived runtime/provider pilot be attached behind an AIOS port.
