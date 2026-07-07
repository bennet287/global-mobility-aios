# Application Engine v1.5

Application Engine v1.5 fixes draft response serialization and UUID lookup handling for application records.

## Problem

Draft creation succeeded, but the API returned:

```json
"application": {}
```

This prevented PowerShell from assigning:

```powershell
$appId = $draft.application.id
```

## Fix

- Added `_application_record_to_dict()` to serialize ApplicationRecord fields explicitly.
- Replaced application response serialization with `_application_record_to_dict(app)`.
- Ensured UUID path values are coerced before `session.get()` for Lead and ApplicationRecord lookups.

## Expected result

Draft creation now returns:

```json
"application": {
  "id": "...",
  "lead_id": "...",
  "domain": "visa",
  "target_country": "Germany",
  "status": "draft",
  "risk_score": 0.5,
  "created_at": "..."
}
```

## Invariant

Computed stages such as `blocked_truth_rejected` remain outside persisted enum-backed workflow status fields.
