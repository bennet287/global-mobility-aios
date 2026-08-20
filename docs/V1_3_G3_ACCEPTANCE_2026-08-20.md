# Global Mobility AIOS — V1.3-G.3 Acceptance

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Accepted implementation head:** `9ffd677e89473a9a495bc6a01fdfd80a2d9784e9`  
**Status:** COMPLETE / PASS / SEALED

## Accepted capability

V1.3-G.3 commits the first governed canonical eligibility effect end-to-end.

Accepted flow:

```text
E.2 governed eligibility proposal
→ F.1 READY_FOR_INDEPENDENT_VERIFICATION
→ G.1 blind independent AGREES verification
→ G.2 verification-floor re-evaluation
→ G.3 final Command Gateway authorization
→ atomic canonical governance Activity + EligibilityAssessment + EligibilityAssessmentRevision + semantic effect Activity
```

Permanent rule:

> **Independent verification satisfies a verification requirement; the Command Gateway authorizes the effect; the canonical effect is committed only in the same transaction as its final durable governance authorization.**

G.3 introduces no HTTP surface, no client-facing recommendation, no external action, and no automatic reassessment/supersession.

## Canonical local acceptance evidence

The Human Owner reported the following results on a clean synchronized checkout at the accepted implementation head.

```text
Updated hardening test                1 passed / 1 warning / 0 failed
Full API regression                 1050 passed / 5 skipped / 1 warning / 0 failed
Full API duration                  488.05s
Repository policy                    PASS
Database migration check             PASS
Migration head                     0077_canonical_eligibility_assessment_revision
Registered tables                    119
Physical schema                      PASS
Local DB schema                      PASS
Actual tables                        119
Physical tables                      120 incl. alembic_version
git diff --check                     clean
V12 branch                           clean / synchronized
```

Known non-blocking warning remains:

```text
StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.
```

No dependency change is implied by this acceptance.

## Accepted G.3 invariants

### First canonical effect only

G.3 creates only canonical revision `v1` with `lifecycle_status = active`. If an active revision already exists for the same `eligibility:<tenant>:<lead_id>:<pathway_id>` aggregate, G.3 fails closed.

### No score synthesis

The persisted `EligibilityAssessment.overall_score` is `0.0`. There is no canonical eligibility score in the accepted E.2/F.1/G.1/G.2 contract. Consumers must not present `0.0` as a computed eligibility score.

### Canonical idempotency slot

G.3 consumes the original E.2 idempotency slot:

```text
governance:<original E.2 idempotency key>
```

Exact retries return the durable committed effect and validate every fingerprint, causation link, and lineage record. Torn or corrupted persisted state fails closed.

### Atomic transaction

For a fresh authorized effect, G.3 stages and commits in one transaction:

```text
canonical governance authorization Activity
+ EligibilityAssessment
+ EligibilityAssessmentRevision
+ semantic eligibility Activity
```

The final governance Activity is causally linked to the accepted G.2 floor Activity. The semantic Activity is causally linked to the final governance Activity.

### Authorization remains Gateway-owned

G.3 reconstructs the exact accepted E.2 `MaterialAction` and performs a fresh final `evaluate_material_action(...)` with `PolicyDisposition.ALLOW`. Only `GatewayOutcome.AUTO_EXECUTE` may enter the canonical effect transaction.

A0/A1/A2 cannot commit through G.3. A3 may commit with `post_review_required=true`.

### Replay integrity

Replay recomputes the aggregate/effect fingerprint and verifies:

- E.2 action fingerprint
- E.2 intent fingerprint
- F.1 readiness fingerprint
- G.1 verification fingerprint
- G.2 verification-floor fingerprint
- Lead/Profile/pathway scope
- assessment payload fields
- governance→G.2 causation
- governance→semantic causation
- constitutional activity class

### Legacy compatibility

Existing legacy `EligibilityAssessment` rows remain untouched. Only an assessment linked through `EligibilityAssessmentRevision` is a V1.3 governed canonical eligibility effect.

### Transparency

The semantic effect uses:

```text
activity_class = decision
activity_type = organization.eligibility.assessment_committed.v1
constitutional_activity_class = MATERIAL
```

It is Board-inspectable, durable, full-lineage and non-compactable under the constitutional MATERIAL transparency rule.

## Migration posture

G.3 introduces one migration:

```text
0077_canonical_eligibility_assessment_revision
```

Registered/physical table counts increased by one after the migration. No existing eligibility row is rewritten by the migration.

## Acceptance gate

Canonical G.3 acceptance included:

- focused G.3 tests;
- G.2 + G.3 integration tests;
- E.2 → F.1 → G.1 → G.2 → G.3 vertical tests;
- D.1–D.3 + E.1–E.2 + F.1–G.3 governed vertical neighborhood where practical;
- repository policy;
- full API regression;
- Alembic migration upgrade to head;
- migration/schema checks;
- `git diff --check`;
- clean synchronized V12 branch.

## Non-claims

G.3 does not claim:

- eligibility reassessment/supersession support;
- a generic canonical-effect framework;
- client-facing eligibility publication;
- legal/professional sign-off where required;
- HTTP/worker orchestration for the new vertical;
- generic Peer Review Network completion;
- provider-egress policy completion;
- GitHub CI PASS.

## Direction after G.3

After G.3 acceptance, the first governed eligibility vertical is proven end-to-end.

The next bounded work should be selected from proven needs, in this order:

1. **Bounded vertical hardening** — extract stable eligibility-specific contracts from duplicated/private helpers:
   - `system_agent_command_context(...)`
   - `original_eligibility_action(...)` / `rebuild_eligibility_action(...)`
   - `mobility_intent_domain(...)`
   - `pathway_publication_integrity(...)`
   - shared reference/freshness resolver
2. **Governed HTTP/worker orchestration surface** — expose the accepted vertical through a route that starts/inspects governed work rather than bypassing it through the legacy immediate-persistence path.
3. **Reassessment/supersession** — extend E.2 with an explicit expected canonical eligibility revision precondition, then introduce version-2 active/superseded semantics.

Do not jump to Mission Rooms, generic Peer Review Network, Flight Recorder or broad Munder runtime expansion before the vertical is hardened and orchestrated.
