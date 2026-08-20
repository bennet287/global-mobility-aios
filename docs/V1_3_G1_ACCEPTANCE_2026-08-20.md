# Global Mobility AIOS — V1.3-G.1 Acceptance

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Accepted implementation head:** `a9abdc7c2a36b290e67eb28c31daeee806b9232c`  
**Status:** COMPLETE / PASS / SEALED

## Accepted capability

V1.3-G.1 establishes the first accepted blind independent-verification path for an F.1-ready R3 eligibility proposal.

Accepted flow:

```text
E.2 governed eligibility proposal
→ F.1 READY_FOR_INDEPENDENT_VERIFICATION
→ separate verifier WorkItem
→ separate verifier OrganizationPosition
→ separate governed ContextBundle
→ distinct independence group
→ distinct provider
→ distinct pinned model
→ blind PRE_COMMIT verifier conclusion
→ AIOS comparison after verifier response
→ AGREES / DISAGREES / INSUFFICIENT_BASIS
→ durable Board-inspectable MATERIAL lineage
```

G.1 does not authorize eligibility mutation. Even an agreeing verifier result remains non-authorizing until a later explicit verification-floor integration contract is accepted.

## Canonical local acceptance evidence

The Human Owner reported the following results on the synchronized V12 branch at the accepted implementation head.

```text
G.1 focused                    15 passed / 1 warning / 0 failed
E.2 + F.1 + G.1               42 passed / 1 warning / 0 failed
D.1–D.3 + E.1–E.2 + F.1–G.1  81 passed / 1 warning / 0 failed
Protected v10.22 regression    1 passed / 1 warning / 0 failed
Repository policy              PASS
Full API regression            1011 passed / 5 skipped / 1 warning / 0 failed
Full API duration              472.92s
Database migration check       PASS
Migration head                 0076_organization_position_active_identity
Registered tables              118
Physical schema                PASS
Local DB schema                PASS
Actual tables                  118
Physical tables                119 incl. alembic_version
git diff --check               clean
V12 branch                     clean / synchronized
```

Known non-blocking warning remains:

```text
StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.
```

No dependency change is implied by this acceptance.

## Accepted G.1 invariants

### Meaningful verifier independence

The accepted first R3 verifier contract requires:

```text
verifier OrganizationPosition != proposer OrganizationPosition
verifier WorkItem              != proposer WorkItem
verifier independence_group    != proposer independence_group
verifier provider              != proposer provider
verifier pinned model          != proposer pinned model
```

Both proposer and verifier model identities must be pinned for this first slice.

Provider/model/runtime identity remains technical execution metadata and never becomes organizational authority.

### Blind review

The verifier does not receive the proposer conclusion, rationale or confidence. AIOS compares conclusions only after verifier output is returned and validated.

Direct contact identity fields such as full name, email and phone are excluded from the verifier prompt.

### Governed authority

The verifier receives its own ContextBundle but must be bound to the same canonical case/pathway authority projection as the proposer, including Lead/Profile fingerprints, pathway version, policy, Evidence, VerifiedRules and SourceSnapshots.

Forged citations or stale governed authority fail closed.

### Freshness

After verifier latency, G.1 recomputes F.1 readiness and verifier context. Case/context changes fail closed before the verification Activity is created.

Lower-layer F.1 readiness invalidation is contained at the G.1 integrity boundary rather than leaking an unrelated exception type to callers.

### Durable transparency

The accepted verifier record is physically stored as an OrganizationActivity class `decision` and carries constitutional transparency class `MATERIAL`.

It is:

- Board inspectable;
- durable;
- full-lineage;
- non-compactable under the constitutional transparency policy;
- explicitly caused by the E.2 governance attempt;
- correlated to the original E.2 trace;
- visible in the verifier WorkItem history and the governed action trace.

### No authorization effect

For all accepted G.1 results:

```text
independent_verification_completed = true
command_gateway_floor_satisfied    = false
authorization_effect               = false
canonical_commit_allowed           = false
```

Only an `AGREES` disposition sets:

```text
eligible_for_verification_floor_integration = true
```

That flag is not itself authorization.

## No migration

G.1 introduces no database migration. The accepted migration head remains:

```text
0076_organization_position_active_identity
```

## CI truth

No GitHub CI PASS is claimed. Acceptance is based on the reported local canonical checks above; attached GitHub status checks were not present on the implementation head when inspected.

## Direction after G.1

The next bounded slice is G.2:

```text
accepted G.1 AGREES verification
→ explicit deterministic verification-floor integration
→ re-evaluate MaterialAction(eligibility.transition)
→ Command Gateway remains sole authority/scope/autonomy/version/idempotency gate
```

G.2 must not let the verifier authorize its own result and must not create a generic Peer Review Network before this vertical integration contract is proven.
