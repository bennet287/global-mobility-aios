# Initial Verified-Rule Assertions v10.19

## Purpose

An initial immutable source snapshot is a baseline, not a detected regulatory
change. This increment allows an operator to state a narrowly scoped rule that
the baseline explicitly supports, route it through independent review, and
publish it as the jurisdiction's first verified rule without creating a false
change event.

## Governance lifecycle

1. The jurisdiction relationship and primary authority/source certification
   must already be independently approved.
2. The official source must have an immutable `baseline` snapshot with a content
   hash and extracted text.
3. An operator proposes a content-addressed assertion containing the exact
   jurisdiction, source, snapshot, domain, rule key, statement, evidence excerpt,
   rationale, confidence, and effective dates.
4. A different authenticated reviewer approves or rejects the assertion with
   mandatory notes.
5. Publication is a separate explicit action with attestation and notes.
6. Publication creates a human-published `VerifiedRule` linked through
   `initial_rule_assertion_id`; `regulatory_change_id` remains null.

## Safety boundaries

- A baseline assertion never claims that the official source changed.
- No assertion is generated automatically from extracted text.
- The proposer cannot review or publish their own assertion.
- Publication confidence must be at least 0.90.
- An active rule with the same jurisdiction, domain, and rule key blocks
  duplicate publication.
- Later source changes continue through classification, change review,
  supersession, and retirement controls.
- Initial assertions do not enter the Opportunity Radar, which remains based on
  human-published change events only.
- Initial assertions do not create pathway-impact records because they are not
  post-publication regulatory changes.

## API

- `GET /api/v1/global-intelligence/registry/coverage-batches/{batch_id}/initial-rule-assertions`
- `POST /api/v1/global-intelligence/registry/coverage-batches/{batch_id}/initial-rule-assertions`
- `POST /api/v1/global-intelligence/registry/initial-rule-assertions/{assertion_id}/review`
- `POST /api/v1/global-intelligence/registry/initial-rule-assertions/{assertion_id}/publish`

The Coverage workspace exposes the same proposal, review, publication, and
history workflow.

## Graph provenance

Knowledge-graph edges now link each rule to exactly one reviewed provenance
record:

- `regulatory_change_id` for a detected and published source change; or
- `initial_rule_assertion_id` for an independently reviewed baseline assertion.

Both paths retain the exact immutable source snapshot and human publication
actor.
