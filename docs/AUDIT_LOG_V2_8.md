# Audit Log v2.8

## Goal

v2.8 adds a dedicated audit layer for high-risk workflow actions.

The system already stored notes, follow-ups, and status changes. The audit log gives those mutations a consistent, queryable trail with before/after state snapshots.

## Data model

```text
AuditLog
- id
- actor
- action
- entity_type
- entity_id
- before_state_json
- after_state_json
- reason
- source
- created_at
```

## Routes

```text
GET /api/v1/audit-logs
GET /api/v1/audit-logs/{audit_log_id}
GET /admin/audit-logs
GET /debug/audit-logs
```

Filters:

```text
action
entity_type
entity_id
limit
include_states
```

Example:

```text
GET /api/v1/audit-logs?action=authority_decision_recorded&include_states=true
```

## Captured actions

```text
truth_claim_resolved
truth_claim_rejected
truth_claim_corrected
human_reviews_closed
document_received
document_verified
document_rejected
documents_bulk_received
documents_bulk_verified
application_drafted
application_approved
application_submitted
application_draft_cancelled
duplicate_application_drafts_cancelled
authority_decision_recorded
onboarding_generated
onboarding_task_completed
client_draft_generated
client_draft_reviewed
client_drafts_reviewed
```

## Files changed

```text
apps/api/app/models/domain.py
apps/api/app/core/db.py
apps/api/app/services/audit_log.py
apps/api/app/routers/audit_logs.py
apps/api/app/main.py
apps/api/app/routers/truth_resolution.py
apps/api/app/routers/document_verification.py
apps/api/app/routers/application_engine.py
apps/api/app/routers/application_draft_control.py
apps/api/app/routers/authority_decision.py
apps/api/app/routers/post_approval_onboarding.py
apps/api/app/routers/client_communications.py
apps/api/app/routers/admin_ui_sync.py
docs/AUDIT_LOG_V2_8.md
```

## Verification

Run:

```powershell
python -m compileall apps/api/app
python scripts/check_repo_policy.py --root .
```

Expected:

```text
Repository policy check passed.
```

## Notes

This is an MVP audit layer. It uses the existing local SQLModel database and stores JSON snapshots as text so the project can stay SQLite-first until the planned PostgreSQL + Alembic milestone.
