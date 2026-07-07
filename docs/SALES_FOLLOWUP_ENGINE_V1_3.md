# Sales Follow-up Engine v1.3

## Purpose

Sales Engine v1.2 introduced status reconciliation, but the first implementation treated `blocked_truth_rejected` as both:

1. a computed pipeline stage, and
2. a persisted `Lead.status` value.

That is unsafe because some database/model configurations only allow operational lead statuses such as `new`, `human_review`, `qualified`, or `converted`.

## Decision

`blocked_truth_rejected` remains a computed pipeline stage only.

When sales guardrails are active, reconciliation persists the lead as:

- `human_review`

The pipeline can still display:

- `stage = blocked_truth_rejected`
- `guardrails.hard_blockers = ["truth_claim_rejected"]`
- `recommended_status = human_review`

## Required database repair

If v1.2 was already tested and the API started returning 500 errors after `/api/v1/sales/reconcile`, run:

```powershell
python .\repair_sales_statuses_sqlite.py
```

This replaces unsafe persisted `blocked_truth_rejected` lead statuses with `human_review` in the local SQLite database.
