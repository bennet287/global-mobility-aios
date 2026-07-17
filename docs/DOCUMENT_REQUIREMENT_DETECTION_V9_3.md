# Missing-Document and Inconsistency Detection v9.3

## Purpose

This Phase 9 increment compares a lead's stored document evidence with an exact,
immutable requirement snapshot. It creates a human-review queue item; it never
creates a document, changes a profile or application, alters eligibility, or
updates a pathway or timeline.

## Requirement provenance

The detector resolves requirements in this order:

1. an explicitly selected human-published pathway version;
2. the exact pathway version pinned by the lead's latest mobility timeline or
   pathway comparison;
3. the latest persisted eligibility assessment that matches the application
   domain and country; or
4. a deterministic application-domain or lead-intent baseline, visibly marked
   as operational guidance requiring human confirmation.

Every assessment snapshots the exact source identifiers, publication/review
provenance, application facts, normalized requirements, document records,
extraction states, and existing consistency assessments.

## Immutable and idempotent assessments

`DocumentRequirementAssessment` stores a SHA-256 assessment key calculated from
its requirement source and current evidence snapshot. Re-running the same scan
returns the existing record. A changed document, expiry date, verification
state, extraction, consistency assessment, application, eligibility assessment,
or pathway version creates a new immutable assessment while preserving history.

## Deterministic findings

Each requirement receives one coverage result:

- `satisfied`;
- `missing`;
- `optional_missing`;
- `rejected`;
- `expired`;
- `present_unverified`; or
- `fact_inconsistency`.

The detector also creates `duplicate_conflict` findings when multiple active
candidates for one requirement have different hashes, expiry dates, or
verification states. Existing document-to-profile/application mismatches are
reused as signals only when they were not rejected by a reviewer.

These findings are triage signals, not authenticity or eligibility decisions.

## Human control

Every assessment begins as `pending` and requires an operator note before it can
be approved or rejected. Review changes only the assessment review state.

The service explicitly reports:

- `source_records_unchanged=true`;
- `documents_created=0`;
- `eligibility_changed=false`; and
- `external_messages_sent=0` for scans.

Withdrawn current profile consent blocks generation and review.

## APIs and workspace

- `POST /api/v1/document-intelligence/requirement-assessments/generate`
- `POST /api/v1/document-intelligence/requirement-assessments/scan`
- `GET /api/v1/document-intelligence/requirement-assessments`
- `GET /api/v1/document-intelligence/requirement-assessments/{assessment_id}`
- `POST /api/v1/document-intelligence/requirement-assessments/{assessment_id}/review`

The `/document-intelligence` workspace provides requirement metrics, exact
source provenance, coverage and inconsistency findings, lead-scoped scans, and
review actions.

## Scheduling and audit

Celery Beat runs a controlled scan every twelve hours. Manual scans use the same
idempotent service. Audit actions are:

- `document_requirement_assessed`;
- `document_requirement_scan_completed`;
- `document_requirement_approved`; and
- `document_requirement_rejected`.

## Migration

Migration `0024_document_requirement_assessments` creates the immutable ledger,
foreign keys, query indexes, and unique assessment-key index. Downgrade removes
only this table.

## Next Phase 9 increment

The next bounded item is human-reviewed fraud-risk indicators. Those indicators
must remain explainable signals, must not label a person or document as
fraudulent automatically, and must not bypass authenticity review.
