# Document Engine v1.1

Document Engine v1.1 adds an operations layer on top of the v1 checklist and verification workflow.

## Added routes

- `GET /api/v1/leads/{lead_id}/documents/summary`
- `GET /api/v1/documents/missing`
- `GET /api/v1/documents/summary`
- `POST /api/v1/operations/leads/{lead_id}/request-missing-documents`
- `GET /admin/documents`
- `GET /admin/documents/missing-card`
- `GET /admin/leads/{lead_id}/documents/summary-card`

## Purpose

- Summarize each lead's document status.
- Surface missing, rejected, and needs-review documents.
- Generate a follow-up message requesting pending documents.
- Add a document operations dashboard without changing the core truth-engine workflow.

## Design rule

The engine does not make visa decisions. It only manages document completeness and verification workflow status.
