# Document Intelligence Foundation v9.0

## Purpose

This first Phase 9 increment moves extraction from a browser-supplied text flow
to auditable server jobs. Uploaded bytes are retrieved by a worker, checked
against their original SHA-256 hash, extracted, parsed with a published schema,
and held for human review.

Extraction approval confirms only that an operator accepts the structured
transcription. It does not verify authenticity, eligibility, consistency, or a
regulated claim, and it does not silently update profile or application facts.

## Versioned schemas

`DocumentSchemaDefinition` stores an immutable schema key/version, JSON Schema,
deterministic extraction rules, lifecycle status, approval provenance, and
timestamps. The baseline publishes version 1 schemas for:

- passports
- CVs and resumes
- degree certificates
- academic transcripts
- employment letters
- bank statements and proof of funds

Document-type aliases resolve existing checklist names to these canonical
schemas. Every job records the exact schema ID and version used.

## Extraction lifecycle

`DocumentExtractionJob` records document and lead provenance, input hash,
worker task ID, engine, language, attempts, extracted text, structured fields,
per-field confidence, warnings, errors, review decision, and timestamps.

The lifecycle is:

1. `queued`
2. `processing`
3. `needs_review` or `failed`
4. `approved` or `rejected`

Only `needs_review` outputs can be decided. Approval stores a reviewed extraction
reference in document metadata while deliberately leaving `DocumentRecord.status`
unchanged for the separate authenticity-verification workflow.

## Server extraction

The worker supports:

- UTF-8 text, CSV, and Markdown
- PDF embedded text through pypdf
- PNG, JPEG, TIFF, BMP, and WebP OCR through Tesseract

Empty OCR, unsupported formats, unavailable engines, missing storage objects,
and hash mismatches fail closed with structured errors and audit events. Scanned
PDF page rasterization is not included yet; a PDF without a text layer fails
explicitly instead of producing an unreliable empty result.

## Storage and access controls

Local storage retrieval resolves and validates paths inside the configured root
to prevent traversal. MinIO retrieval closes and releases response connections.
Jobs accept only server-readable `local` or `minio` uploads.

Extracted document data is restricted to admin, operator, and reviewer roles.
Only admin and reviewer roles can approve or reject extracted fields. Current
profile consent withdrawal blocks new lead-linked extraction jobs.

## API and workspace

- `POST /api/v1/document-intelligence/schemas/seed`
- `GET /api/v1/document-intelligence/schemas`
- `POST /api/v1/document-intelligence/documents/{document_id}/extract`
- `GET /api/v1/document-intelligence/extractions`
- `GET /api/v1/document-intelligence/extractions/{job_id}`
- `POST /api/v1/document-intelligence/extractions/{job_id}/review`

The `/document-intelligence` workspace provides lead/document selection, queue
status, schema provenance, structured fields, confidence, warnings, failures,
and human approval/rejection notes.

## Audit and migration

The pipeline records schema seeding, queueing, completion, failure, approval,
and rejection events. Migration `0015_document_intelligence_foundation` creates
the versioned schema and extraction-job tables and removes them in dependency
order on downgrade.

## Next Phase 9 increment

The next increment will compare approved extracted fields with immutable profile
versions and application facts, producing human-reviewed consistency findings
without overwriting either source of truth.
