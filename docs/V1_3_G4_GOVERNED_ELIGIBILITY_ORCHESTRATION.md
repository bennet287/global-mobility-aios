# Global Mobility AIOS — V1.3-G.4 Governed Eligibility Orchestration

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Status:** IMPLEMENTED / CANONICAL ACCEPTANCE PENDING

## Purpose

G.4 makes the accepted governed eligibility vertical reachable through one bounded orchestration contract without creating a second governance path or a generic workflow framework.

Accepted upstream chain:

```text
E.2 governed eligibility proposal
→ F.1 deterministic Decision Readiness
→ G.1 blind independent verification
→ G.2 verification-floor integration
→ G.3 canonical EligibilityAssessment effect
```

G.4 coordinates those already-sealed services; it does not replace them.

Permanent rule:

> **The initiating human may request governed work; the request does not choose the AI employee, runtime, provider, model, autonomy, capability authority, or verification policy.**

## New service

```text
app.services.organization_eligibility_orchestration
```

Primary entry point:

```text
orchestrate_governed_eligibility(...)
```

The bounded orchestration state machine is:

```text
PROPOSAL_BLOCKED
NOT_READY
HUMAN_INPUT_REQUIRED
VERIFICATION_DISAGREES
VERIFICATION_INSUFFICIENT_BASIS
AWAITING_AUTHORITY
CANONICAL_EFFECT_COMMITTED
```

The orchestrator does not turn every non-terminal state into an exception. Constitutional routing remains explicit and inspectable.

## Trusted execution plan

Technical/runtime/authority inputs are carried only by:

```text
GovernedEligibilityExecutionPlan
```

It contains:

```text
producer_position_key
producer_runtime_profile
producer_provider
verifier_position_key
verifier_runtime_profile
verifier_provider
authority
```

This type is deliberately **not** an HTTP schema.

The first R3 orchestration contract validates before runtime execution that:

```text
producer position != verifier position
producer independence group != verifier independence group
producer provider != verifier provider
producer pinned model != verifier pinned model
CapabilityAuthority.tenant == authenticated orchestration tenant
CapabilityAuthority.actor == producer OrganizationPosition
CapabilityAuthority.capability == mobility.eligibility
provider adapters match their bound runtime profiles
```

G.1 still independently enforces its accepted verifier-independence contract; G.4 preflight is an additional fail-fast boundary, not a replacement.

## HTTP boundary

New route:

```text
POST /api/v1/organization/eligibility/orchestrate
```

Request fields are only:

```text
proposal_work_item_id
verification_work_item_id
idempotency_key
```

The request schema forbids extra fields.

It cannot supply:

```text
tenant_key
actor_id
actor_type
position_key
producer_position_key
verifier_position_key
provider
model
runtime profile
autonomy level
CapabilityAuthority
risk tier
allowed scopes
allowed action types
```

The authenticated human initiator is mapped through the existing trusted organization-auth boundary. Current initiation is limited to authenticated internal `admin` / `operator` roles.

The human initiator does **not** become the E.2/G.2/G.3 material-action actor. The producer `OrganizationPosition` from the trusted execution plan remains the organizational actor.

## Provider-egress boundary

The route's default execution-plan dependency intentionally returns:

```text
503 Governed eligibility execution policy is not configured.
```

This is deliberate.

G.4 does not reinterpret the legacy global `LLMProviderFactory` switch as permission to send case-scoped personal data to an external provider. Production execution must bind the dependency to a trusted server-side provider-egress/runtime/authority policy.

Therefore:

```text
route exists
≠ external provider egress is automatically authorized
```

Tests override the trusted dependency with bounded fake providers; request JSON never provides them.

## Full-chain orchestration semantics

When a trusted execution plan is present, G.4 calls the sealed services in order:

```text
E.2 governed_eligibility_transition_intent
→ F.1 assess_eligibility_decision_readiness
→ G.1 verify_eligibility_proposal_independently
→ G.2 integrate_eligibility_verification_floor
→ G.3 commit_governed_eligibility_effect
```

Routing semantics remain owned by those stages:

- E.2 `BLOCK` stops before readiness;
- F.1 `NOT_READY` stops before verification;
- F.1 `HUMAN_INPUT_REQUIRED` stops before verification;
- G.1 `DISAGREES` or `INSUFFICIENT_BASIS` stops before floor integration;
- G.2 non-authorizing A1/A2 result becomes `AWAITING_AUTHORITY` and creates no canonical assessment;
- only G.2 `eligible_for_effect_integration=true` may enter G.3;
- only G.3's fresh final `AUTO_EXECUTE` may commit canonical eligibility truth.

G.4 itself does not weaken any Gateway rule.

## Durable replay

G.4 adds a bounded post-commit replay fast path.

For an exact retry after G.3 already committed:

```text
governance:<original E.2 / orchestration idempotency key>
→ EligibilityAssessmentRevision
→ EligibilityAssessment
→ G.1 verification Activity
→ G.2 floor Activity
→ G.3 semantic Activity
```

The orchestrator validates the expected WorkItems and E.2→G.1→G.2→G.3 causation chain, then returns:

```text
state = CANONICAL_EFFECT_COMMITTED
gateway_outcome = IDEMPOTENT_REPLAY
replayed = true
```

Neither producer nor verifier model is called again.

A torn or conflicting durable record fails closed rather than being silently repaired.

This first slice does not yet claim that a retry interrupted *before* G.3 commit can avoid all repeated runtime work. Canonical effect duplication remains prevented by the accepted lower-layer idempotency contracts.

## Result contract

G.4 returns bounded durable identifiers rather than provider transcript content:

```text
schema_version
state
trace_id
proposal_activity_id
readiness_state
verification_activity_id
verification_disposition
verification_floor_activity_id
gateway_outcome
assessment_id
revision_id
semantic_activity_id
canonical_effect_committed
replayed
```

This gives future Cockpit/Operations/API consumers trace/effect identity without treating provider output as canonical truth.

## No automatic legacy side effects

The new organization route does not call the legacy `/eligibility/evaluate` pipeline.

Therefore G.4 does not automatically:

- run the legacy eligibility score engine;
- call `persist_eligibility_assessment(...)` directly;
- generate client communications;
- mutate Lead lifecycle;
- mutate an Application;
- send external messages;
- submit anything to government.

G.3 remains the only canonical effect in this vertical.

## Focused tests

`apps/api/tests/test_organization_eligibility_orchestration.py` covers:

1. trusted A5 orchestration reaches the accepted G.3 canonical effect;
2. exact post-commit retry resolves durable effect identity without model calls;
3. A1 stops after verified floor and creates no canonical effect;
4. verifier disagreement stops before G.2/G.3;
5. non-independent/untrusted execution plan fails before runtime;
6. HTTP route fails closed with 503 when no trusted execution policy is installed;
7. trusted dependency override executes the route end-to-end;
8. request JSON cannot smuggle provider/runtime/position/autonomy fields;
9. reviewer/non-operator human initiation is denied;
10. human initiator cannot replace the producer CapabilityAuthority actor.

Pytest's actual collected count is canonical.

## Migration posture

G.4 adds no migration.

Expected migration head remains:

```text
0077_canonical_eligibility_assessment_revision
```

Expected schema remains:

```text
registered tables 119
actual tables     119
physical tables   120 including alembic_version
```

## Acceptance gate

Canonical G.4 acceptance should include:

- focused orchestration/API tests;
- E.2→G.4 vertical neighborhood;
- existing organization/OpenAPI boundary test;
- repository policy;
- full API regression;
- migration/schema checks;
- `git diff --check`;
- clean synchronized V12 branch.

No GitHub CI PASS may be claimed without attached check evidence.

## Deliberate non-claims

G.4 does not claim:

- provider-egress/sensitivity policy completion;
- automatic external LLM activation in production;
- asynchronous worker durability or resume-from-mid-pipeline;
- eligibility reassessment/version-2 support;
- a generic orchestration engine;
- a generic canonical-effect framework;
- Mission Room / Organization Fabric implementation;
- client-facing eligibility publication;
- external action authorization.

## Next bounded consolidation

After G.4 orchestration behavior is accepted, the now-proven vertical may promote only stable shared seams, especially:

- public E.2 action reconstruction helpers currently shared through G.2/G.3 internals;
- one mobility intent→domain mapping;
- one documented system-bound-agent command-context constructor;
- public pathway publication-integrity contract;
- narrower freshness invalidation only when the complete ContextBundle dependency set is proven.

These are vertical hardening steps, not an invitation to create a horizontal AI framework.
