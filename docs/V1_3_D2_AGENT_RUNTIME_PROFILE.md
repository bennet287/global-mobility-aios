# V1.3-D.2 — Agent Runtime Profile + Employee/Runtime Identity Separation

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Status:** COMPLETE / PASS / SEALED

## Purpose

D.2 creates the first provider-neutral AIOS runtime-binding contract above existing provider/LLM implementations.

The architectural separation is:

```text
OrganizationPosition
    persistent organizational employee identity
        ↓
ContextBundle
    current governed work/context identity
        ↓
EmployeeRuntimeBinding
    replaceable technical execution choice
        ↓
AgentRuntimeProfile
    hosted API / CLI / local / specialized / donor adapter
        ↓
provider/model/process/session
    ephemeral runtime implementation
```

The runtime is not the employee.

## Runtime profile contract

`AgentRuntimeProfile` describes technical execution capability only:

- `profile_key`
- `runtime_class`
- `adapter_key`
- `provider_key`
- optional `model_key`
- technical capabilities
- technically available tools
- verification/independence group
- profile version
- enabled state

Runtime classes are frozen initially as:

- `hosted_api`
- `cli`
- `local`
- `specialized`
- `donor_adapter`

The `donor_adapter` class is the future controlled landing zone for compatible Munder-derived execution mechanics. It does not activate the vendored donor runtime by itself.

## Permanent separation

The runtime profile deliberately contains no:

- authority level;
- autonomy level;
- risk tier;
- Evidence references;
- VerifiedRules;
- policy authority;
- organizational decision authority;
- session/process identity.

Therefore:

```text
runtime technical capability != organizational authority
```

and:

```text
provider/model identity != employee identity
```

## Fresh-context requirement

`bind_employee_runtime(...)` does not trust a previously created ContextBundle blindly.

Before binding it re-resolves the current governed ContextBundle from canonical organization state and compares its deterministic context hash and position version with the supplied bundle.

If canonical assignment, employee status/contract, WorkItem context or other hash-bearing state changed, the binding fails closed with `RuntimeBindingStale`.

This prevents execution against stale organizational context.

## Tool-authority rule

An `AgentRuntimeProfile` can declare tools that its runtime is technically capable of using.

That declaration is not authorization.

The effective runtime tool set is:

```text
canonical ContextBundle.allowed_tools
INTERSECT
AgentRuntimeProfile.available_tools
```

D.2 intentionally re-resolves the canonical ContextBundle before performing that intersection. A caller cannot copy a ContextBundle in memory, add fake `allowed_tools`, retain the old hash and thereby grant a runtime new tool authority.

D.3 now supplies governed ContextBundle tool entitlements from the explicit transitional position-contract authority namespace, so D.2's intersection is operational rather than merely preparatory.

## Binding fingerprint

`EmployeeRuntimeBinding.binding_hash` is deterministic over:

- schema version;
- tenant;
- persistent position identity/version;
- effective ContextBundle hash/purpose;
- runtime-profile fingerprint;
- requested technical capability;
- effective allowed tools.

The wall-clock `bound_at` timestamp is excluded.

Changing provider/model/profile can therefore change runtime-binding identity without changing persistent employee identity or ContextBundle identity.

## Verification independence

`independence_group` is carried as technical metadata for future independent-verification routing.

D.2 does not yet implement R3+ verifier selection. It merely prevents the runtime abstraction from blocking that future requirement.

## Relationship to existing LLM code

Existing `LLMProviderFactory` and provider implementations remain execution infrastructure.

D.2 does not rewrite or adopt them into organizational authority. Future vertical runtime execution may adapt those providers, CLI runtimes, local models, specialized runtimes and Munder-derived mechanics behind `AgentRuntimeProfile`, but only after governed context and vertical semantics are established.

## Tests

`apps/api/tests/test_organization_agent_runtime.py` covers:

1. runtime binding preserves persistent employee identity;
2. runtime profiles contain no authority/autonomy/risk fields;
3. alternate providers change binding identity without changing employee/context identity;
4. runtime profiles and forged in-memory ContextBundles cannot grant tools;
5. required technical capability must be present;
6. stale canonical context fails closed;
7. disabled profiles fail closed;
8. profile normalization and binding hashes are deterministic.

## Migration posture

D.2 is read-only and introduces no database migration.

Persistent runtime-session/AgentRun lineage is intentionally deferred to the later Flight Recorder/runtime execution evolution rather than forcing a premature schema before the runtime port is proven.

## Non-claims

D.2 does not claim:

- actual provider invocation through this binding;
- Munder runtime adoption;
- persistent runtime-session storage;
- provider routing optimization;
- independent verifier selection;
- AI Economics;
- Flight Recorder completion;
- full V1.3-D completion;
- GitHub CI PASS.

## Acceptance evidence

Canonical Windows V12 acceptance reported by the Human Owner:

```text
Focused context/runtime/authority/transparency neighborhood   36 passed / 1 warning / 0 failed
Repository policy                                             PASS
Full API regression                                           961 passed / 5 skipped / 1 warning / 0 failed
Database migration check                                      PASS
Migration head                                                0076_organization_position_active_identity
Registered tables                                             118
Local DB schema check                                         PASS
Actual tables                                                 118
Physical tables                                               119 incl. alembic_version
git diff --check                                              clean
V12 branch status                                             clean / synchronized
```

Canonical acceptance record:

`docs/V1_3_D2_ACCEPTANCE_2026-08-20.md`

No GitHub CI PASS is claimed because no attached status checks were present.

## Seal decision

V1.3-D.2 is COMPLETE / PASS / SEALED.

The next product-direction priority is not a generic runtime-port abstraction in isolation. D.2 is now a sealed supporting primitive for the first end-to-end governed Global Mobility vertical, with runtime execution introduced only where that vertical provides a real consumer.
