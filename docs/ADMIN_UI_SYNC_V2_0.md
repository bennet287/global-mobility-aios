# Admin UI Sync v2.0

## Purpose

Admin UI Sync v2.0 provides a synced operations dashboard that reflects the newer backend governance modules:

- Truth Resolution Engine
- Document Verification Actions
- Application Lifecycle Engine
- Application Draft Control
- Authority Decision Tracking

The old admin pages still exist for compatibility, but `/admin/v2` is the synced operations dashboard.

## Problem fixed

Older admin pages could show stale workflow affordances such as:

- `Create Draft` even when an active/submitted application already exists.
- Old missing-document cards even after the new document-verification workflow has verified documents.
- Readiness stage without lifecycle or authority outcome.

## New routes

```text
GET /admin/v2
GET /admin/v2/leads/{lead_id}
GET /admin/sync
GET /api/v1/admin-ui-sync/summary
GET /api/v1/admin-ui-sync/leads/{lead_id}
GET /debug/admin-ui-sync
```

## Design rule

Admin views must not collapse readiness, lifecycle, and authority state into one field.

- Readiness: whether prerequisites are satisfied.
- Lifecycle: current application record status.
- Authority: post-submission authority decision state.
