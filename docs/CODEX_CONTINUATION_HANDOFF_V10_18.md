# Codex Continuation Handoff v10.18

## Completed increment

Phase 10B now includes controlled baseline capture for independently approved
coverage evidence batches.

## Key behavior

- Only batch items with approved immigration-rule assessment and approved primary
  authority/source certification can be queued.
- Queueing creates durable `SourceRetrievalRun(status="queued")` rows before
  Celery dispatch.
- The worker accepts the exact run ID and updates that record in place.
- Repeated queue actions do not duplicate queued/running work or existing
  baseline snapshots.
- Failed retrievals remain visible and can be deliberately requeued.
- Baseline capture publishes no verified rule and creates no coverage claim.

## New files

- `apps/api/app/services/coverage_baseline_capture.py`
- `apps/api/tests/test_coverage_baseline_capture.py`
- `scripts/Capture-ApprovedCoverageBaselines.ps1`
- `docs/CONTROLLED_COVERAGE_BASELINE_CAPTURE_V10_18.md`
- `docs/CODEX_CONTINUATION_HANDOFF_V10_18.md`

## Modified files

- `apps/api/app/routers/live_intelligence.py`
- `apps/api/app/services/source_retrieval.py`
- `apps/api/app/tasks/source_monitor_tasks.py`
- `apps/web/app/global-intelligence/page.tsx`
- `apps/web/app/globals.css`
- `apps/web/lib/api.ts`
- `docs/CHANGELOG.md`
- `docs/ROADMAP.md`

## Release gates

- API tests: 217 passed across four isolated groups; one existing SQLModel
  deprecation warning.
- Focused baseline/source-retrieval tests: 12 passed.
- Next.js production build: passed all 21 routes.
- Local quality gate: passed against a migrated temporary SQLite database.
- Database migration head remains `0031_global_coverage_source_onboarding`.

## Operator next steps

1. Finish independent assessment and source-certification review for the v10.17
   five-jurisdiction tranche.
2. Open the Coverage workspace and use **Capture approved baselines**, or run:
   `scripts/Capture-ApprovedCoverageBaselines.ps1 -BatchId <uuid> -WhatIf`.
3. Inspect retrieval results and immutable snapshots in Regulatory Operations.
4. Review any detected regulatory changes and publish verified rules only after
   the existing human-review gates pass.
5. Repeat with additional evidence tranches; global coverage remains blocked.
