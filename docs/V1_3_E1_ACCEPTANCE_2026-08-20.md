# V1.3-E.1 — Governed Mobility Pathway Brief Acceptance

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Status:** COMPLETE / PASS / SEALED

## Accepted scope

V1.3-E.1 proves the first bounded end-to-end runtime consumer of the sealed governance, transparency, Context Broker and employee/runtime-separation foundations:

```text
Tenant-bound OrganizationalWorkItem
→ persistent OrganizationPosition employee
→ governed ContextBundle
→ published mobility Evidence / VerifiedRules / SourceSnapshots / CountryPolicy
→ EmployeeRuntimeBinding
→ bounded hosted LLM runtime
→ strict structured-output validation
→ internal mobility pathway brief
→ mandatory human review
```

E.1 remains deliberately read-only. It does not create or mutate eligibility truth, client-facing decisions, external actions, AgentRun lineage or OrganizationActivity records.

## Canonical local acceptance evidence

The Human Owner ran the prescribed local acceptance on 2026-08-20 and supplied the following exact results:

```text
Repository policy check        PASS
Full API regression            969 passed / 5 skipped / 1 warning / 0 failed
Duration                       378.54s
Database migration check       PASS
Migration head                 0076_organization_position_active_identity
Registered tables              118
Physical schema                ok
Local DB schema check          PASS
Actual tables                  118
Physical tables                119
Infrastructure tables          ["alembic_version"]
git diff --check               clean
Working tree                   clean
```

Known non-blocking warning:

```text
StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.
```

No dependency change is implied by this warning.

## Branch-state nuance

At the end of the acceptance run, local Git reported:

```text
## roadmap/global-mobility-aios-v12...origin/roadmap/global-mobility-aios-v12 [behind 2]
```

This does **not** invalidate E.1 acceptance. The remote commits ahead of the tested checkout were downstream E.2 work; comparison against the current V12 branch confirms they did not modify:

- `apps/api/app/services/organization_mobility_pathway_brief.py`
- `apps/api/tests/test_organization_mobility_pathway_brief.py`

The local tree itself was clean and the current remote branch is a descendant of the accepted E.1 implementation.

Therefore E.1 is sealed without falsely claiming that the local checkout was synchronized at the exact moment of the run.

## Acceptance conclusion

E.1 is accepted as:

```text
COMPLETE / PASS / SEALED
```

What is proven:

- a persistent AIOS employee receives governed mobility truth through ContextBundle;
- runtime/provider identity remains separate from employee identity;
- only authority admitted by D.3 can reach the bounded E.1 runtime payload;
- arbitrary WorkItem working context cannot self-promote into Evidence, rules, policy, tools or provider selection;
- runtime citations cannot escape the governed authority set;
- provider/model drift fails closed;
- safety flags remain deterministic and non-negotiable;
- no canonical mobility decision or external action is produced.

## Non-claims

This acceptance does not claim:

- eligibility determination or transition;
- Decision Readiness;
- independent verification;
- client-facing legal advice;
- canonical mutation;
- AgentRun / Flight Recorder completion;
- case-data provider-egress authorization;
- CLI/local/Munder runtime adoption;
- GitHub CI PASS.

No GitHub CI PASS is claimed because no attached GitHub status/check evidence was supplied for this checkpoint.

## Next bounded slice

V1.3-E.2 remains the next downstream vertical proof:

```text
case/profile-bound ContextBundle
→ EmployeeRuntimeBinding
→ typed EligibilityTransitionIntent
→ deterministic domain validation
→ MaterialAction(eligibility.transition)
→ Command Gateway
→ REVIEW_REQUIRED / BLOCK
→ durable Board-inspectable attempt
```

E.2 must not mutate eligibility state until later Decision Readiness and genuinely independent verification are implemented and accepted.
