# Application Engine v1.2

Application Engine v1.2 fixes UUID path handling.

## Fix

FastAPI path parameters arrive as strings, but the SQLModel/SQLAlchemy UUID primary-key columns expect `uuid.UUID` objects. Passing a string into `session.get()` can cause:

```text
AttributeError: 'str' object has no attribute 'hex'
```

This patch adds `_uuid_or_404()` and uses it for:

- `GET /api/v1/applications/leads/{lead_id}/readiness`
- `POST /api/v1/applications/leads/{lead_id}/draft`
- `POST /admin/applications/leads/{lead_id}/draft`
- application approval/submission lead lookups
- application ID lookups

## Invariant

Path IDs are converted at API boundaries before database lookup.
