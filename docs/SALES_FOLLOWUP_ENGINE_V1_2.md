# Sales Follow-up Engine v1.2

## Purpose

Sales Follow-up Engine v1.2 adds status reconciliation for legacy or test data that was created before guardrails existed.

In v1.1, new qualification and conversion actions are blocked when the Truth Engine or Human Review layer identifies hard blockers. However, earlier test records may already have statuses such as `qualified` or `converted`. v1.2 detects and repairs that mismatch.

## New routes

- `GET /api/v1/sales/inconsistencies`
- `POST /api/v1/sales/leads/{lead_id}/reconcile`
- `POST /api/v1/sales/reconcile`
- `POST /admin/sales/reconcile`

## Reconciliation logic

If a lead has a sales-positive status such as:

- `qualified`
- `converted`

but the guardrails contain hard blockers such as:

- `truth_claim_rejected`
- `truth_claim_needs_review`
- `human_review_pending`

then the status is reconciled to:

- `blocked_truth_rejected` when a truth claim was rejected
- `human_review` when review is still pending or required

## Admin behavior

The Sales Pipeline page now shows a `Status Integrity` column. It also includes a button:

`Reconcile blocked sales statuses`

This is useful after a new guardrail release, data import, or manual database editing.

## Governance rule

Sales status must never contradict Truth Engine or Human Review state.

A lead cannot remain `qualified` or `converted` when official-source verification or human-review governance says the case is blocked.
