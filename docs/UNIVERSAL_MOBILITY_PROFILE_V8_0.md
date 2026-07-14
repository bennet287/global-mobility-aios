# Universal Mobility Profile v8.0

## Purpose

This increment implements the first Phase 8 capability in the canonical
[`GLOBAL_MOBILITY_AIOS_VISION_V1.md`](GLOBAL_MOBILITY_AIOS_VISION_V1.md): one
versioned client fact record shared by eligibility, opportunity matching, future
pathway planning, documents, and controlled agents.

The profile is not an eligibility decision. Regulated conclusions still require
verified rules, official-source provenance, Truth Engine controls, and human
review before they become client-facing.

## Covered facts

Each immutable profile version can record:

- current country and mobility goals
- education and employment history
- skills, language ability, and test results
- family and dependant context
- available finances and funding source
- constraints and target timing
- purpose-limited consent and expiry
- lead-owned document evidence references

Legacy scalar profile columns remain populated for backwards compatibility.
Structured sections are stored as deterministic JSON until later normalized
schemas need independent querying.

## Version lifecycle

`PUT /api/v1/profiles/leads/{lead_id}/current` creates a new version; it never
overwrites the current version. The former current version becomes
`superseded`, and the new record links to it through `supersedes_profile_id`.

Lifecycle states:

- `active`: current and available to permitted internal decision services
- `restricted`: current, but consent has been withdrawn
- `superseded`: retained for audit and assessment reproducibility

Read endpoints:

- `GET /api/v1/profiles/leads/{lead_id}/current`
- `GET /api/v1/profiles/leads/{lead_id}/history`

Every created version records the authenticated actor and creates a
`mobility_profile_version_created` audit event containing the prior and new
states.

## Completeness and readiness

Completeness is a deterministic 100-point ledger:

| Section | Weight |
| --- | ---: |
| Current country | 10 |
| Education | 10 |
| Employment or experience | 10 |
| Skills | 10 |
| Languages | 10 |
| Confirmed family context | 5 |
| Finances | 10 |
| Goals | 15 |
| Confirmed constraints | 5 |
| Granted consent | 10 |
| Evidence documents | 5 |

Readiness stages are `foundation`, `developing`, `pathway_ready`, and
`evidence_ready`. Withdrawn consent always produces `restricted`, regardless of
the numerical completeness score. Missing section names are returned by the API
and shown in the operator workspace.

## Consent and privacy controls

- Consent records a status, permitted purposes, optional expiry, and timestamp.
- `withdrawn` blocks automated eligibility and opportunity matching. Eligibility
  returns an `insufficient_profile` result with no pathways; opportunity matching
  returns no matches.
- `not_recorded` remains available for legacy compatibility but does not earn
  completeness credit. A later consent-policy increment can make it restrictive
  after existing records are remediated.
- Evidence IDs are accepted only when the document exists and belongs to the
  same lead. Files are not duplicated into the profile.
- Superseded versions are retained to reproduce historical decisions. Production
  retention and erasure jobs must preserve the audit/regulated-record policy
  while removing personal data when legally required; those jobs remain a
  dedicated security and compliance increment.
- APIs remain protected by the existing RBAC middleware. No profile version is
  made public or directly client-facing.

## Decision-service provenance

Eligibility assessments now persist `profile_id` and `profile_version`. Their
factor record also contains completeness, readiness, and consent state.
Opportunity match responses expose the same profile provenance and completeness.
This prevents a later profile edit from silently changing the facts attributed
to an earlier assessment.

Profile request overrides on the eligibility endpoint are scenario-only inputs;
they do not create or alter a persisted profile version. Verified rules and
country policy remain separate inputs to regulated conclusions.

## Operator workspace

The Next.js `/profiles` workspace provides:

- lead selection and document evidence selection
- structured editing for every covered fact section
- explicit consent purposes and withdrawal warning
- completeness, readiness, missing-section, and lifecycle status
- immutable version creation and history

## Database and rollback

Migration `0011_universal_mobility_profile` adds profile version/lifecycle,
structured section JSON, completeness/readiness/consent metadata, audit actor,
and eligibility profile provenance. It supports both SQLite batch migration and
PostgreSQL UUID foreign keys. Its downgrade removes the added assessment and
profile fields, indexes, and foreign keys.

Before downgrade, export any versioned profile history required for audit or
regulated-record retention; downgrade intentionally loses the Phase 8 fields.

## Verification

Automated coverage includes:

- immutable versions and supersession
- completeness and readiness calculation
- authenticated audit attribution
- cross-lead evidence rejection
- withdrawn-consent restrictions
- eligibility and opportunity profile provenance
- fresh-database migration to head and rollback-path definition
- Next.js strict type and production build validation

## Next Phase 8 increments

The universal profile foundation is ready for the versioned pathway catalogue,
verified-rule-linked conclusions, cost and risk explanations, alternative
pathways, missing-evidence reasoning, and the multi-stage mobility timeline.
