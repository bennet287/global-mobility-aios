# Document-to-Profile and Application Validation v9.1

## Purpose

This Phase 9 increment compares human-approved structured document extractions
with lead identity, an exact immutable Universal Mobility Profile version, and a
snapshot of the selected application record. It identifies facts requiring
operator resolution without deciding which source is true or changing any
source record.

## Immutable assessment

Each `DocumentConsistencyAssessment` stores:

- approved extraction job and document IDs
- lead and exact profile ID/version
- optional application ID
- complete lead, profile, application, and extraction fact snapshots
- deterministic field-level findings
- result counts and summary
- independent human review status, actor, notes, and timestamps

Generation is idempotent for the same extraction, profile version, and
application. A later profile version creates a new assessment; historical
findings and snapshots remain unchanged.

## Comparison outcomes

Every finding is classified as:

- `match`
- `mismatch`
- `missing_document_value`
- `missing_source_value`
- `not_comparable`

The engine compares identity names, experience duration, profession and roles,
qualifications, education institutions/programmes, employment facts, document
relevance to the application domain, and target-employer details when the source
document is explicitly a job offer or employment contract.

Comparisons use normalized strings, token overlap, or bounded numeric tolerance.
They are triage signals, not truth decisions. Missing profile concepts are shown
explicitly. Semantically different values are not forced into comparisons: for
example, a bank-statement closing balance is not treated as equal to a declared
mobility budget.

## Consent and human control

Only an extraction already approved by a human reviewer can be assessed.
Current profile consent must remain granted for generation and assessment
review. A reviewer approves or rejects the assessment itself; that decision does
not update document verification, profile facts, application facts, eligibility,
or regulatory claims.

## API and workspace

- `POST /api/v1/document-intelligence/extractions/{job_id}/validate`
- `GET /api/v1/document-intelligence/validations`
- `GET /api/v1/document-intelligence/validations/{assessment_id}`
- `POST /api/v1/document-intelligence/validations/{assessment_id}/review`

The `/document-intelligence` workspace now displays pinned profile/application
provenance, consistency counts, field-level explanations, immutable history, and
human assessment review controls.

## Audit and migration

Assessment generation emits `document_consistency_assessed`. Human decisions
emit `document_consistency_approved` or `document_consistency_rejected`.
Migration `0016_document_consistency_assessments` creates the assessment table
and its provenance/query indexes; downgrade removes it.

## Next Phase 9 increment

The next increment will monitor document expiry dates and create deduplicated,
auditable reminder tasks without sending uncontrolled external messages.
