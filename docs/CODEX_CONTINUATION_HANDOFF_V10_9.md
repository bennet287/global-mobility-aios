# Continuation Handoff — v10.9

## Starting point

The supplied v10.8 workspace was verified at migration head
`0024_document_requirement_assessments`. The next bounded Phase 9 item was
human-reviewed fraud-risk indicators.

## Delivered

Document Fraud-Risk Indicators v9.4 is implemented as product continuation
v10.9:

- migration `0025_document_fraud_risk_assessments`;
- immutable SHA-256 keyed assessment snapshots;
- deterministic exact-file reuse, conflicting-type, approved identity mismatch,
  approved material mismatch, approved duplicate-conflict, rejected-evidence,
  extraction-integrity, and approved identifier-reuse indicators;
- cross-lead identifiers stored only as hashes and masked suffixes;
- twelve-hour Celery Beat scanning plus lead-scoped manual scans;
- restricted list, detail, generate, scan, and review APIs;
- `cleared`, `specialist_review_required`, and `dismissed` human outcomes with
  mandatory notes;
- Document Intelligence risk metrics, queue, provenance, and review controls;
- explicit zero automated fraud determinations, document rejections, eligibility
  changes, or external actions; and
- regression coverage for idempotency, masking, source linkage, human review,
  and non-mutation.

## Verification

- 192 API tests pass.
- Fresh migration upgrade, downgrade, and re-upgrade pass.
- Next.js production build passes all 21 routes.

## Migration

Current head: `0025_document_fraud_risk_assessments`.

## Next bounded roadmap item

Signed, expiring document access and production object-storage controls. The
next implementation should replace direct or durable object access with
short-lived, audited grants; preserve local/MinIO compatibility; enforce lead
and role scope; and avoid exposing storage credentials or unrestricted keys.
