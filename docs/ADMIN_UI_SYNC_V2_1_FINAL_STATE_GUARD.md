# Admin UI Sync v2.1 Final-State Draft Guard

## Purpose

Admin UI Sync v2.1 fixes a visible product issue in `/admin/v2`.

After an application reached `approved_by_authority` and the lead became `converted`, the synced dashboard still allowed `Create Controlled Draft`.

That is not a safe production default. A final authority outcome should block fresh draft creation until a future reapplication workflow exists.

## Guarded statuses

Draft creation is now blocked when a lead has any application in one of these statuses:

```text
draft
approved
submitted
decision_pending
approved_by_authority
rejected_by_authority
withdrawn
```

`cancelled` remains non-blocking.

## Files changed

```text
apps/api/app/routers/application_draft_control.py
apps/api/app/routers/admin_ui_sync.py
```

## Design rule

A converted/finalized lead should not silently create a new application draft. Reapplication must be a separate explicit workflow.
