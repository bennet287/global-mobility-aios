# Global Mobility AIOS — V1.3-G.4 Acceptance Record

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Accepted implementation head:** `9ffd677e89473a9a495bc6a01fdfd80a2d9784e9`  
**Status:** COMPLETE / PASS / SEALED

## Scope accepted

V1.3-G.4 makes the already-accepted governed eligibility vertical operationally reachable through one bounded organization orchestration contract without creating a second governance path or a generic workflow/effect framework.

Accepted chain:

```text
trusted organization request / WorkItems
→ trusted server-side execution plan
→ E.2 governed eligibility proposal
→ F.1 deterministic Decision Readiness
→ G.1 blind independent verification
→ G.2 verification-floor integration
→ G.3 fresh final authorization + canonical EligibilityAssessment effect
→ durable trace/effect identifiers returned
```

The implementation preserves the existing constitutional rule:

> The initiating human may request governed work; the request does not choose the AI employee, runtime, provider, model, autonomy, capability authority, risk, scope or verification policy.

## Accepted runtime/API boundary

New route:

```text
POST /api/v1/organization/eligibility/orchestrate
```

Accepted request fields are only:

```text
proposal_work_item_id
verification_work_item_id
idempotency_key
```

Extra fields are forbidden. Provider, model, employee identity, runtime profile, autonomy and CapabilityAuthority remain trusted server-side dependencies.

The default execution-plan dependency intentionally fails closed with HTTP 503 until a governed provider-egress/runtime/authority policy is configured.

Authenticated `admin` / `operator` users may initiate the route, but the human initiator does not become the material-action actor. The producer `OrganizationPosition` remains the actor through E.2/G.2/G.3.

The existing global auth middleware remains the canonical mutation-role boundary. Reviewer access is rejected before execution-plan/provider resolution.

## Accepted orchestration states

```text
PROPOSAL_BLOCKED
NOT_READY
HUMAN_INPUT_REQUIRED
VERIFICATION_DISAGREES
VERIFICATION_INSUFFICIENT_BASIS
AWAITING_AUTHORITY
CANONICAL_EFFECT_COMMITTED
```

G.4 does not weaken lower-layer routing. In particular:

- G.1 disagreement or insufficient basis never reaches floor/effect integration;
- A1/A2 remain review-required after the verification floor and create no canonical effect;
- only a G.2 result eligible for effect integration may enter G.3;
- only G.3 fresh final `AUTO_EXECUTE` may commit canonical eligibility truth.

## Accepted replay contract

After a canonical G.3 effect is already durable, an exact G.4 retry resolves from:

```text
governance:<idempotency_key>
→ EligibilityAssessmentRevision
→ EligibilityAssessment
→ G.1 verification Activity
→ G.2 floor Activity
→ G.3 semantic Activity
```

The chain and WorkItems are validated before returning:

```text
state = canonical_effect_committed
gateway_outcome = IDEMPOTENT_REPLAY
replayed = true
```

Neither producer nor verifier model is called again.

Torn or conflicting durable lineage fails closed.

## Canonical acceptance evidence

User-observed local acceptance on the exact synchronized V12 implementation head:

```text
G.4 focused orchestration/API          10 passed / 1 warning / 0 failed
G.4 + OpenAPI boundary                 11 passed / 1 warning / 0 failed
E.2 → G.4 governed eligibility vertical
                                       81 passed / 1 warning / 0 failed
Repository policy                      PASS
Full API regression                    1050 passed / 5 skipped / 1 warning / 0 failed
Duration                               488.05s
Database migration check               PASS
Migration head                         0077_canonical_eligibility_assessment_revision
Registered tables                      119
Local DB schema                        PASS
Actual tables                          119
Physical tables                        120 incl. alembic_version
git diff --check                       clean
V12 branch                             clean / synchronized
```

The known non-blocking warning remains:

```text
StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.
```

No dependency change is implied.

## Boundary repairs during acceptance

Two test-only corrections were required while converging the acceptance target:

1. the G.4 reviewer-denial test originally expected a route-local generic 403 body, while the canonical global auth middleware correctly rejected the reviewer first with the existing structured role-denial response;
2. the platform hardening test still expected exactly 65 registered router features, while the new governed eligibility router legitimately raised the registry inventory to 66. The repaired test also explicitly requires `organization-governed-eligibility` so accidental route removal cannot satisfy the count.

Neither repair changed G.4 production behavior.

## Migration/schema posture

G.4 adds no migration.

Accepted database truth remains:

```text
migration head      0077_canonical_eligibility_assessment_revision
registered tables   119
actual tables       119
physical tables     120 including alembic_version
```

## Deliberate non-claims

G.4 does not claim:

- automatic production external-provider activation;
- provider-egress/sensitivity policy completion;
- asynchronous durable resume from a mid-pipeline interruption;
- eligibility reassessment/version-2 semantics;
- generic orchestration/effect framework completion;
- client-facing eligibility publication;
- external action authorization;
- Mission Room / Organization Fabric implementation.

## Post-G.4 bounded hardening

With the first governed vertical now operationally reachable and accepted, the next bounded hardening may consolidate only proven shared seams:

- public eligibility MaterialAction reconstruction/original E.2 payload helpers;
- canonical mobility `LeadIntent → domain` mapping;
- one documented system-bound-agent `OrganizationCommandContext` constructor;
- public pathway publication-integrity contract;
- shared canonical reference/fingerprint helpers only where semantics are already identical across real consumers;
- replacement of conservative `session.expire_all()` only after a dependency-aware freshness resolver proves complete coverage of every hash-bearing ContextBundle dependency.

These are vertical hardening steps, not permission to create speculative generic frameworks.

## Seal

V1.3-G.4 is **COMPLETE / PASS / SEALED** at implementation head:

```text
9ffd677e89473a9a495bc6a01fdfd80a2d9784e9
```

No GitHub CI PASS is claimed because no attached status checks were present on the accepted head.
