# Application Engine v1

Application Engine v1 introduces the next agency workflow layer after lead intake, truth validation, document handling, and sales qualification.

## Purpose

The module tracks whether a lead is ready to become an actual study, visa, job, or scholarship application.

The core rule is:

```text
Application submission is blocked unless truth, human review, and document guardrails are satisfied.
```

## Routes

```text
GET  /api/v1/applications/queue
GET  /api/v1/applications/leads/{lead_id}/readiness
POST /api/v1/applications/leads/{lead_id}/draft
POST /api/v1/applications/{application_id}/approve
POST /api/v1/applications/{application_id}/submit
GET  /admin/applications
GET  /debug/application-engine
```

## Readiness stages

```text
blocked_truth_rejected
human_review_required
documents_incomplete
ready_for_human_approval
```

## Guardrails

Application approval and submission are blocked by:

- rejected truth claims
- truth claims requiring human review
- pending human reviews
- missing / rejected / needs-review documents
- missing document checklist

## Design note

`blocked_truth_rejected` is a computed application/sales stage. It must not be stored as `Lead.status`.
