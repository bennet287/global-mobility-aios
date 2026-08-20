# Global Mobility AIOS — V1.3-F.1 Acceptance

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Accepted implementation head:** `0fc7084c8980a5dcec4d44bcc0e1dfd9ff8c9eb0`  
**Status:** COMPLETE / PASS / SEALED

## Accepted slice

V1.3-F.1 establishes the first deterministic eligibility Decision Readiness contract downstream of the accepted E.2 governed eligibility-intent vertical.

The accepted chain is:

```text
accepted E.2 REVIEW_REQUIRED proposal
→ durable E.2 governance attempt
→ fresh governed ContextBundle
→ current Lead / Profile / pathway state
→ deterministic F.1 readiness gates
→ READY_FOR_INDEPENDENT_VERIFICATION
   or NOT_READY
   or HUMAN_INPUT_REQUIRED
```

F.1 remains routing/quality infrastructure only.

Permanent acceptance boundary:

```text
READY_FOR_INDEPENDENT_VERIFICATION
≠ eligibility truth
≠ independent verification complete
≠ Command Gateway authorization
≠ canonical mutation
```

## Canonical acceptance evidence

Evidence reported from the synchronized Windows V12 checkout:

```text
Repository policy             PASS
Full API regression           996 passed / 5 skipped / 1 warning / 0 failed
Duration                      359.39s
Database migration check      PASS
Migration head                0076_organization_position_active_identity
Registered tables             118
Local DB schema               PASS
Actual tables                 118
Physical tables               119 incl. alembic_version
git diff --check              clean
V12 branch                    clean / synchronized
```

The existing warning is the known non-blocking Starlette/httpx deprecation warning. No dependency change is implied by this acceptance.

No separate focused-test count is invented here because the Human Owner supplied the canonical full-suite result rather than restating each focused command result.

No GitHub CI PASS is claimed because no attached GitHub status/check evidence was observed for the accepted head.

## Accepted deterministic contract

F.1 accepts only an E.2 proposal that is durably proven to have:

```text
action_type            eligibility.transition
outcome                REVIEW_REQUIRED
reason                 POLICY_REVIEW_REQUIRED
effective risk         R3
verification floor     independent_verification_not_yet_satisfied
```

The durable attempt must agree with the supplied typed proposal on trace, WorkItem, actor, action fingerprint, intent fingerprint, context hash, runtime-binding hash, Profile identity/version and pathway-version identity.

BLOCKed proposals, including A0 `AUTONOMY_PROHIBITED`, cannot be reclassified by Decision Readiness.

## Accepted readiness states

```text
READY_FOR_INDEPENDENT_VERIFICATION
NOT_READY
HUMAN_INPUT_REQUIRED
```

The first five deterministic gates are:

```text
proposal_state_actionable
governed_authority_complete
required_case_facts_present
pathway_publication_integrity
material_fact_preconditions
```

The `readiness_score` is descriptive only and has no authorization effect.

Model confidence is not a gate. Generic Profile `completeness_score` / `readiness_stage` are not material-decision authorization proxies.

## Accepted safety posture

F.1 performs no:

- LLM call;
- AgentRun creation;
- OrganizationActivity creation;
- EligibilityAssessment creation;
- eligibility-state mutation;
- application-state mutation;
- client-facing recommendation;
- external action;
- Command Gateway authorization change.

The result preserves:

```text
independent_verification_required = true
authorization_effect              = false
canonical_commit_allowed          = false
```

## Migration/schema truth

F.1 introduces no migration.

Accepted migration/schema truth remains:

```text
migration head      0076_organization_position_active_identity
registered tables   118
actual tables       118
physical tables     119 incl. alembic_version
```

## Non-claims

This acceptance does not claim:

- legal eligibility;
- independent verification completion;
- canonical eligibility mutation;
- applicant-document Evidence readiness beyond current governed context;
- provider-egress policy completion;
- generic readiness-framework completion;
- Flight Recorder completion;
- Munder adoption;
- GitHub CI PASS.

## Direction after F.1

The next bounded slice is V1.3-G.1 Independent Verification.

G.1 must accept only:

```text
EligibilityDecisionReadinessResult.state
    == READY_FOR_INDEPENDENT_VERIFICATION
```

and must prove meaningful verifier independence rather than merely calling the same proposing runtime/provider with the same context and conclusion exposure.

Only after an independent verification contract is itself accepted may the project reconsider E.2's explicit R3 `HUMAN_REQUIRED` verification floor.
