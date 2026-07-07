# Sales Follow-up Engine v1

## Purpose

Sales Follow-up Engine v1 turns operational lead data into an actionable sales pipeline.

It does not bypass the Truth Engine. Sales action is downstream of verified guidance, document status, and human-review status.

## Added routes

### API

- `GET /api/v1/sales/pipeline`
- `GET /api/v1/sales/follow-ups`
- `POST /api/v1/sales/leads/{lead_id}/follow-ups`
- `POST /api/v1/sales/leads/{lead_id}/qualify`
- `POST /api/v1/sales/leads/{lead_id}/convert`
- `POST /api/v1/sales/follow-ups/{follow_up_id}/complete`

### Admin

- `GET /admin/sales`
- `GET /debug/sales-engine`

## Pipeline stages

The pipeline stage is computed from existing evidence:

1. `blocked_truth_rejected`
2. `human_review`
3. `needs_documents`
4. `follow_up_pending`
5. fallback to lead status such as `new`, `qualified`, `converted`, or `closed`

## Governance rule

Sales conversion must not be treated as immigration, visa, or job-placement approval. It only means the lead became a client or active case in the agency workflow.
