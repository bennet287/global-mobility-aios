# Application Draft Control v1.8

## Purpose

Application Draft Control v1.8 prevents duplicate active application drafts and provides a safe cleanup workflow for duplicate drafts created during testing.

## Model inspection result

`ApplicationRecord.status` is a plain string field, not an enum-backed field:

```python
status: str = "draft"
```

The SQLite column is also `VARCHAR`, so v1.8 can safely use `cancelled` for inactive duplicate drafts.

## Active statuses

```text
draft
approved
submitted
```

If a lead already has any active application, controlled draft creation is blocked.

## API routes

```text
GET  /api/v1/applications/draft-control/duplicates
GET  /api/v1/applications/leads/{lead_id}/draft-control
POST /api/v1/applications/leads/{lead_id}/controlled-draft
POST /api/v1/applications/{application_id}/cancel-draft
POST /api/v1/applications/leads/{lead_id}/cancel-duplicate-drafts
```

## Admin route

```text
GET /admin/application-draft-control
```

## Existing draft endpoint guard

The existing application draft endpoint is patched with a duplicate guard so that direct calls to:

```text
POST /api/v1/applications/leads/{lead_id}/draft
```

are blocked when an active application already exists.
