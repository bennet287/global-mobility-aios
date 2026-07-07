# Document Verification Actions v1.2

## Purpose

Document Verification Actions v1.2 adds agency-facing actions for moving a lead's document checklist through controlled states:

```text
missing -> received -> verified
```

It does not implement real file upload yet. For local workflow testing, bulk receive / verify actions generate local placeholder filenames and storage keys so downstream guardrails can be exercised without bypassing the document layer.

## API routes

```text
GET  /api/v1/document-verification/leads/{lead_id}/summary
POST /api/v1/document-verification/leads/{lead_id}/bulk-receive
POST /api/v1/document-verification/leads/{lead_id}/bulk-verify
POST /api/v1/document-verification/documents/{document_id}/receive
POST /api/v1/document-verification/documents/{document_id}/verify
POST /api/v1/document-verification/documents/{document_id}/reject
```

## Admin routes

```text
GET  /admin/document-verification
GET  /admin/document-verification/leads/{lead_id}
```

## Design rule

Application submission must remain blocked until required documents are received or verified. These actions provide controlled state transitions instead of manually editing database rows.
