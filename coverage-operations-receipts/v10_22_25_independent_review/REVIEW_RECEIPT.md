# Coverage independent-review receipt — v10.22.25

Review date: 2026-07-23

Reviewer: `bennet-coverage-reviewer`

Scope: evidence batches v10.22.20 through v10.22.24.

## Decisions

- Immigration-authority assessments reviewed: 20
- Immigration-authority assessments approved: 20
- Primary-source certifications reviewed: 20
- Primary-source certifications approved: 18
- Primary-source certifications rejected: 2
- Pending authority assessments after review: 0
- Pending source certifications after review: 0

The authority approvals confirm only the narrow government/service relationships described in
the proposals. They do not establish client eligibility, legal outcomes, or comprehensive
immigration-law coverage.

## Remediation exceptions

- Peru (`PE`) certification `9b4b7bb1-daed-4b0d-a661-db83cddcda25` was rejected. The official
  portal and authority relationship are credible, but the pinned extraction is not substantive
  enough for a controlled baseline assertion. Onboard and snapshot the prepared narrower
  official page, then submit a new certification for independent review.
- Qatar (`QA`) certification `4eae06f0-c25c-4d27-af74-88af13e7c191` was rejected for the same
  fail-closed reason. The current Ministry of Interior page supports the narrow authority
  relationship, but a more substantive pinned source is required for assertion drafting.
- Senegal (`SN`) certification was approved against its valid immutable 2026-07-18 snapshot and
  narrow entry-visa scope. During the 2026-07-23 review the live Foreign Ministry endpoint
  redirected to a Drupal installation error. Monitor recovery or source replacement is required
  before newly retrieved content is relied upon.

## Resulting gate state

Eighteen batch items are baseline-ready because their independently approved assessment and
source certification are paired with an immutable snapshot. Peru and Qatar remain blocked at
source certification. No initial rule assertion was proposed, reviewed, or published by this
review, so registry coverage readiness remains 65/243 and the global coverage claim remains
false.
