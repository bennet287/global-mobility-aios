# Human-Reviewed Document Fraud-Risk Indicators v9.4

## Purpose

This increment creates explainable document-integrity indicators for specialist
triage. It does not determine fraud, score a person, reject evidence, change an
application or eligibility result, or trigger any external action.

Every assessment is immutable and content-addressed against the exact document,
extraction, approved consistency, approved requirement, profile, application,
and cross-record provenance used to generate it.

## Deterministic indicators

The scanner can surface:

- exact uploaded file bytes reused across different leads;
- one file classified as multiple document types for the same lead;
- identity and material-fact mismatches from human-approved consistency assessments;
- conflicting duplicate evidence and cross-document inconsistencies from
  human-approved requirement assessments;
- rejected or invalid evidence states;
- server extraction failures caused by immutable upload-hash mismatch; and
- repeated document identifiers across leads, using only human-approved
  structured extractions.

Repeated identifiers are stored and displayed as SHA-256 hashes plus masked
suffixes. Raw identifiers are not copied into indicator evidence.

## Human control

An assessment containing indicators enters `pending` review. A reviewer must add
notes and choose one of:

- `cleared`;
- `specialist_review_required`; or
- `dismissed`.

A clean assessment is retained with `review_status=not_required`. Review decisions
are triage outcomes only and remain separate from document authenticity,
application, eligibility, communications, and authority-decision workflows.

## Safety boundaries

The assessment and scan responses explicitly report:

- `fraud_determinations=0`;
- `documents_rejected=0`;
- `eligibility_changed=false`;
- `external_actions_triggered=0`; and
- `adverse_action_taken=false`.

Current profile-consent withdrawal blocks generation and review. All list,
detail, generation, scan, and review endpoints remain within the restricted
Document Intelligence surface.

## API and workspace

- `POST /api/v1/document-intelligence/fraud-risk-assessments/generate`
- `POST /api/v1/document-intelligence/fraud-risk-assessments/scan`
- `GET /api/v1/document-intelligence/fraud-risk-assessments`
- `GET /api/v1/document-intelligence/fraud-risk-assessments/{assessment_id}`
- `POST /api/v1/document-intelligence/fraud-risk-assessments/{assessment_id}/review`

The `/document-intelligence` workspace includes risk-review metrics, a manual
lead-scoped scan, indicator evidence, source-record counts, and controlled review
actions. Celery Beat performs a twelve-hour global scan.

## Audit and migration

Migration `0025_document_fraud_risk_assessments` creates the immutable assessment
ledger and indexes. Generation, scheduled/manual scans, and every review decision
write audit events. Downgrade removes only the v9.4 table.
