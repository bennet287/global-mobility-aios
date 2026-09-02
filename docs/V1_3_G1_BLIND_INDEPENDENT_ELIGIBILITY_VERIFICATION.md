# Global Mobility AIOS — V1.3-G.1 Blind Independent Eligibility Verification

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Status:** IMPLEMENTED / CANONICAL ACCEPTANCE PENDING

## Purpose

G.1 is the first bounded implementation of constitutionally required independent verification for the accepted R3 eligibility vertical.

It consumes only an F.1 result that is already:

```text
READY_FOR_INDEPENDENT_VERIFICATION
```

and asks a second, meaningfully independent AI employee to reach its own bounded conclusion from the same governed case/pathway authority.

The first G.1 chain is:

```text
accepted E.2 REVIEW_REQUIRED eligibility proposal
→ accepted F.1 READY_FOR_INDEPENDENT_VERIFICATION
→ separate verification WorkItem
→ separate verifier OrganizationPosition
→ separate governed verifier ContextBundle
→ distinct verifier runtime / provider / model
→ blind PRE_COMMIT verification
→ typed verifier conclusion
→ AIOS comparison after verifier response
→ durable MATERIAL verification lineage
→ AGREES / DISAGREES / INSUFFICIENT_BASIS
```

G.1 deliberately stops before Command Gateway verification-floor integration or any eligibility mutation.

Permanent G.1 rule:

> **Independent verification may establish evidence-based agreement or disagreement; it does not itself authorize organizational action.**

## Why G.1 uses a separate WorkItem

The Context Broker correctly enforces assignment scope:

```text
ContextBundle position
    must equal
OrganizationalWorkItem.assigned_position_key
```

Therefore a verifier cannot safely reuse the proposer WorkItem under another employee identity.

G.1 requires a separate verification WorkItem that is:

- in the same tenant;
- assigned to a different verifier `OrganizationPosition`;
- bound to the same Lead;
- bound to the same current Profile;
- bound to the same governed `MobilityPathwayVersion`.

This preserves D.1/D.3 assignment and authority semantics rather than creating an exception for peer review.

## Employee independence

The proposing and verifying organizational actors must differ:

```text
proposer OrganizationPosition.position_key
    !=
verifier OrganizationPosition.position_key
```

Provider/model/runtime identity remains technical execution metadata, not organizational authority.

## Runtime independence

G.1 intentionally applies a stricter R3 runtime contract than generic D.2 binding.

The verifier must use:

- `hosted_api` in this first slice;
- `structured_output` capability;
- a different `independence_group` from the proposer;
- a pinned proposer model identity;
- a pinned verifier model identity;
- a different provider from the proposer;
- a different model identity from the proposer.

The explicitly supplied provider adapter must match the verifier runtime's bound provider before execution. The actual response provider/model must also match the bound verifier runtime.

This first slice is deliberately conservative. Later independence policy may permit more nuanced configurations only after evidence demonstrates that they remain genuinely independent.

## Blind-review contract

The verifier receives governed case/pathway authority but does **not** receive:

- proposer conclusion;
- proposer rationale;
- proposer confidence.

AIOS compares proposer and verifier conclusions only after the verifier has returned its own structured output.

The verifier prompt explicitly declares:

```text
proposer_conclusion_exposed = false
proposer_rationale_exposed  = false
proposer_confidence_exposed = false
```

G.1 also excludes direct contact identity fields from the case payload, including:

- full name;
- email;
- phone.

The case payload contains only bounded professional/mobility facts required for the verification task.

A prior defensive implementation that searched the entire payload for proposer *value strings* was rejected during static review because governed source text could coincidentally contain the same string. Blindness is enforced structurally by payload construction and covered with unique-marker tests rather than by brittle substring censorship of Evidence text.

## Governed authority equivalence

The verifier gets its own ContextBundle.

G.1 compares a canonical authority projection between proposer and verifier containing only subject/authority identity:

- tenant;
- Lead reference/fingerprint;
- Profile reference/fingerprint;
- MobilityPathwayVersion reference/fingerprint;
- CountryPolicy reference/fingerprint;
- pathway Evidence references/fingerprints;
- VerifiedRule references/fingerprints;
- SourceSnapshot references/fingerprints;
- authority unknowns/contradictions;
- policy version.

Employee, WorkItem and runtime identity are intentionally excluded from this equality projection because those are expected to differ for independent verification.

The authority projection must match exactly before the verifier executes.

## Governed verifier payload

G.1 reuses the already-hardened E.1 governed pathway dereference helper as a bounded internal dependency rather than building a second Evidence/rule/source truth path.

The verifier receives:

- bounded case facts;
- published pathway identity/version and structured content;
- explicit pathway Evidence;
- OfficialSource identity;
- bounded SourceSnapshot content;
- governed VerifiedRules;
- active CountryPolicy;
- allowed citation tokens;
- verifier ContextBundle/readiness fingerprints.

If E.1 governed dereference detects stale/malformed Evidence, rules, SourceSnapshots or policy, G.1 converts that failure into a verifier-integrity failure and does not execute the verifier.

This private-helper reuse is intentionally provisional. A public governed mobility payload abstraction should be extracted only after multiple accepted vertical consumers prove the common contract.

## Typed verifier output

The verifier must return exactly:

```text
conclusion
evidence_basis
rule_basis
findings
unresolved_questions
```

Allowed conclusions are:

```text
supports_potential_eligibility
supports_potential_ineligibility
insufficient_basis
contradiction_found
```

Evidence/rule citations must be non-empty subsets of authority supplied in the verifier ContextBundle.

Forged citations fail before durable verification Activity is created.

## AIOS comparison after blind review

Only after verifier output passes structural/authority validation does AIOS compare it with the E.2 proposer conclusion.

Result dispositions:

```text
AGREES
DISAGREES
INSUFFICIENT_BASIS
```

`contradiction_found` is conservatively routed to `INSUFFICIENT_BASIS` for this slice because the contradiction requires further resolution before any verification floor can be considered satisfied.

Agreement means only that two independently executed, governed assessments reached compatible bounded conclusions.

It does not itself authorize eligibility mutation.

## Freshness after verifier latency

After verifier runtime execution, G.1:

1. expires session state;
2. recomputes F.1 Decision Readiness;
3. requires the same readiness fingerprint;
4. rebuilds the verifier ContextBundle;
5. requires the same verifier context hash.

A case, profile, pathway, Evidence, rule, policy or relevant employee-context change during verifier latency fails closed before durable verification completion.

## Durable verification lineage

A completed verification is persisted as one `OrganizationActivity`.

Physical storage class:

```text
decision
```

Constitutional transparency class in payload:

```text
MATERIAL
```

This distinction is required because the existing physical Activity schema predates the V1.3 constitutional activity taxonomy.

The `MATERIAL` constitutional class gives the record:

- Board inspection;
- durable-record requirement;
- full-lineage requirement;
- no policy-window compaction.

The verification Activity records:

- verification schema/mode/kind;
- deterministic verification fingerprint;
- verifier conclusion/disposition;
- Evidence basis;
- rule basis;
- findings;
- unresolved questions;
- proposer trace/activity/position/runtime binding;
- proposer independence group;
- F.1 readiness fingerprint;
- verifier position/context/authority/runtime binding;
- verifier independence group;
- provider/model;
- blind-review flags;
- verification-floor integration eligibility;
- explicit no-authorization/no-commit flags.

Lineage is explicit:

```text
E.2 governance attempt
    ↓ causation_activity_id
G.1 independent verification Activity
```

The verification Activity also carries the E.2 proposer trace as its correlation key, so the existing governed trace reconstruction can expose the verifier result alongside the material proposal lineage.

## Verification result safety flags

For all G.1 results:

```text
independent_verification_completed = true
command_gateway_floor_satisfied    = false
authorization_effect               = false
canonical_commit_allowed           = false
```

Only `AGREES` sets:

```text
eligible_for_verification_floor_integration = true
```

`DISAGREES` and `INSUFFICIENT_BASIS` keep it false.

Crucially:

```text
eligible_for_verification_floor_integration
    !=
command_gateway_floor_satisfied
```

The next bounded G slice must define how an accepted agreeing verification is represented to the existing E.2/Command Gateway verification floor. G.1 does not silently invent that authorization bridge.

## No eligibility mutation

G.1 creates no:

- `EligibilityAssessment`;
- Lead eligibility state change;
- application state change;
- client-facing recommendation;
- external communication;
- government/external action;
- new Command Gateway authorization;
- AgentRun.

The only new durable effect is the independent verification Activity itself.

## Provider-egress posture

Like E.2, G.1 requires an explicitly supplied provider adapter.

It does not use `LLMProviderFactory` automatically for case-scoped verification.

This continues the conservative position that case-data provider egress must not become implicit before a dedicated sensitivity/provider-egress policy exists.

## Tests

`apps/api/tests/test_organization_independent_eligibility_verification.py` covers the G.1 contract, including:

1. blind agreeing verification with no eligibility mutation or authorization effect;
2. disagreement remains non-authorizing;
3. insufficient basis remains non-authorizing;
4. separate verifier employee and WorkItem are mandatory;
5. same runtime independence group is rejected;
6. same provider is rejected even with a different model;
7. same model identity is rejected even with a different provider;
8. proposer/verifier model identities must be pinned;
9. provider adapter identity must match the bound verifier runtime before execution;
10. verification WorkItem must reference the same case/pathway;
11. forged/readiness fingerprint fails closed;
12. forged verifier rule citation fails before verification Activity;
13. case change during verifier runtime fails before verification Activity;
14. verifier response provider/model drift fails closed;
15. proposer conclusion/rationale/confidence and direct contact identity are absent from the verifier prompt;
16. physical `decision` / constitutional `MATERIAL` transparency semantics are preserved;
17. verifier Activity has explicit causation to E.2 and appears in both verifier WorkItem history and the original governed action trace.

Parameterization means the actual pytest collected count is canonical and should be recorded from the local acceptance run rather than inferred from this list.

## Migration posture

G.1 introduces no database migration.

It reuses:

- `OrganizationPosition`;
- `OrganizationalWorkItem`;
- ContextBundle / Context Authority;
- AgentRuntimeProfile / EmployeeRuntimeBinding;
- E.2 governed proposal;
- F.1 Decision Readiness;
- `OrganizationActivity`;
- existing Board transparency reconstruction.

## Acceptance gate

Canonical acceptance should include:

- G.1 focused tests;
- E.2 + F.1 + G.1 vertical chain;
- D.1–D.3 context/runtime/authority chain where practical;
- protected `v10.22` ROADMAP regression because V12.12 was materially rewritten before G.1;
- repository policy;
- full API regression;
- migration/schema checks;
- `git diff --check`;
- clean synchronized V12 branch.

No GitHub CI PASS may be claimed without attached check evidence.

## Non-claims

G.1 does not claim:

- canonical eligibility truth;
- Command Gateway verification-floor satisfaction;
- authorized eligibility mutation;
- generic Peer Review Network completion;
- all possible independence policies;
- applicant-document verification beyond governed inputs;
- provider-egress policy completion;
- Flight Recorder completion;
- Munder adoption;
- GitHub CI PASS.

## Direction after G.1

If G.1 passes, the next bounded slice should remain vertical:

```text
G.2  accepted agreeing verification
     → explicit verification-floor integration contract
     → re-evaluate MaterialAction(eligibility.transition)
     → Command Gateway still owns authority/scope/autonomy/version/idempotency
```

Only after that integration itself is accepted should AIOS implement the first authorized canonical eligibility effect.

Do not build a generic Peer Review Network, Mission Room or runtime fabric before this accepted eligibility vertical proves the required semantics.
