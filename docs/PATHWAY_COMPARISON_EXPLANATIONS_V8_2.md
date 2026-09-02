# Pathway Comparison and Explanations v8.2

## Purpose

This Phase 8 increment turns pathway matches into reproducible internal mobility
plans. It explains why one published pathway ranks above another, what it may
cost, which risks are declared or derived, and what profile/document evidence is
still missing.

The output is an internal planning assessment, not legal advice, an eligibility
guarantee, or a client-facing recommendation. `human_review_required` is always
true.

## Immutable assessment record

Each `PathwayComparisonAssessment` records:

- lead and exact Universal Mobility Profile ID/version
- primary pathway and exact published pathway version
- complete primary and alternative comparison payloads
- normalized cost and risk summaries
- alternative pathway IDs and cross-pathway evidence gaps
- status, summary, generation actor, and timestamp

Re-running a comparison creates a new assessment. Historical plans therefore do
not change when the profile, catalogue, rules, costs, or source freshness later
change.

## Cost explanation

Published pathway cost structures are normalized into:

- one-time payable fees
- recurring monthly amounts
- recurring annual amounts
- minimum-funds eligibility thresholds
- original named cost components and operator notes

Minimum funds are intentionally not added to payable fees. Missing cost data is
shown explicitly rather than interpreted as zero. Every cost response warns that
catalogue estimates require operator verification before client use.

## Risk explanation

Risk is deterministic and separated by origin:

- **Declared risk:** reviewed risks stored on the published pathway version.
- **Evidence risk:** missing profile facts, skills, qualifications, languages,
  funds, or documents found during matching.
- **Regulatory risk:** inactive/missing verified rules, rule confidence below
  0.90, inactive official sources, missing snapshots, or snapshots older than
  180 days.

The combined score maps to low, medium, or high. This score prioritizes human
review; it is not a prediction of authority refusal.

## Alternatives and explanations

Only currently effective published pathways in the target country are compared.
The highest deterministic match is the primary option. Remaining matches become
ranked alternatives and retain their own:

- profile match and confidence
- reasons and benefits
- costs and processing range
- risk decomposition
- tradeoffs and missing evidence
- source, snapshot, and verified-rule provenance

If no published pathway matches, the assessment is stored as
`insufficient_pathways`. An incomplete or absent profile produces
`needs_profile_review`. A sufficiently complete profile with matches produces
`ready_for_review`.

## Consent and audit

Withdrawn consent returns a `restricted` response and creates only a minimal
`pathway_comparison_restricted` audit event. No derived comparison assessment is
stored. Successful or insufficient comparisons create
`pathway_comparison_generated` audit events with profile provenance and summary
counts.

## API

- `POST /api/v1/pathways/compare/{lead_id}` generates and persists a comparison.
- `GET /api/v1/pathways/comparisons/{lead_id}/latest` returns the latest persisted
  assessment.
- `GET /api/v1/pathways/comparisons/{lead_id}` returns immutable history.

## Operator workspace

The Next.js `/planning` workspace provides:

- lead selection and explicit comparison generation
- primary option and alternative route cards
- upfront fees versus minimum funds
- risk origin and evidence-gap explanations
- pathway/source/snapshot/rule provenance
- immutable assessment history
- direct links to profile and catalogue remediation

## Database and rollback

Migration `0013_pathway_comparison_assessments` creates the persisted comparison
table and foreign keys to leads, profiles, pathways, and pathway versions. Its
downgrade removes the table. Fresh SQLite upgrade/downgrade/re-upgrade and live
PostgreSQL upgrade are release gates.

## Next Phase 8 increment

The multi-stage mobility timeline engine will transform an immutable comparison
into sequenced profile, evidence, application, authority, relocation, and
settlement milestones with dependencies and human-controlled state transitions.
