# Global Mobility AIOS — V1.3-D.2 Acceptance

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Slice:** V1.3-D.2 — Agent Runtime Profile + Employee/Runtime Identity Separation  
**Status:** COMPLETE / PASS / SEALED

## Accepted scope

D.2 establishes the provider-neutral runtime-binding boundary above persistent organizational identity and governed ContextBundle state.

Accepted invariants:

- `OrganizationPosition` remains the persistent AI employee identity;
- provider/model/runtime/session identity is replaceable execution state rather than employee identity;
- `AgentRuntimeProfile` describes technical capability only and does not grant authority, autonomy, risk, Evidence status, policy authority or organizational decision rights;
- `bind_employee_runtime(...)` re-resolves canonical ContextBundle state before binding;
- stale canonical context fails closed;
- forged in-memory ContextBundle tool grants cannot become runtime authority;
- effective runtime tools remain `ContextBundle.allowed_tools ∩ AgentRuntimeProfile.available_tools`;
- runtime binding identity is deterministic over canonical context and runtime-profile inputs;
- no database migration is introduced by D.2.

## Canonical local acceptance evidence

The Human Owner reported the prescribed D.2/D.3 acceptance sequence green on the canonical Windows V12 checkout.

Exact reported evidence:

```text
Focused context/runtime/authority/transparency neighborhood   36 passed / 1 warning / 0 failed
Repository policy                                             PASS
Full API regression                                           961 passed / 5 skipped / 1 warning / 0 failed
Database migration check                                      PASS
Migration head                                                0076_organization_position_active_identity
Registered tables                                             118
Physical schema                                               ok
Database revision                                             0076_organization_position_active_identity
Local DB schema check                                         PASS
Actual tables                                                 118
Physical tables                                               119
Infrastructure tables                                         ["alembic_version"]
git diff --check                                              clean
V12 branch status                                             clean / synchronized
```

Known non-blocking warning:

```text
StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.
```

No dependency change is made as part of this acceptance.

## Non-claims

This acceptance does not claim:

- a GitHub CI PASS;
- production provider invocation through the D.2 binding;
- Munder runtime adoption;
- persistent runtime-session storage;
- provider routing optimization;
- independent verifier selection;
- Flight Recorder completion;
- full V1.3 completion.

No attached GitHub status checks were available for this slice, so no CI result is asserted.

## Seal decision

V1.3-D.2 is accepted as the runtime-separation foundation. Runtime/provider capability remains subordinate to AIOS organizational identity, governed ContextBundle state and later command/authority boundaries.
