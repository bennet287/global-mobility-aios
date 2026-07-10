# Automated Test Suite v2.9

## Goal

v2.9 adds the first pytest regression suite for the workflow-first MVP.

The tests focus on the guardrails most likely to regress:

```text
truth blocks
document readiness
application draft/approval/submission
authority approval
post-approval onboarding
client communication enum-safe status mapping
audit log creation and filtering
```

## Files added

```text
apps/api/tests/__init__.py
apps/api/tests/conftest.py
apps/api/tests/test_application_guardrails.py
apps/api/tests/test_truth_resolution.py
apps/api/tests/test_document_verification.py
apps/api/tests/test_authority_onboarding.py
apps/api/tests/test_client_communications.py
apps/api/tests/test_audit_logs.py
docs/TEST_SUITE_V2_9.md
```

## Files updated

```text
apps/api/requirements.txt
```

`pytest` is now listed as a development/test dependency.

## Test database

The suite uses an in-memory SQLite database through SQLModel and overrides FastAPI's `get_session` dependency.

This keeps tests isolated from the local development database.

## Run

From the repository root:

```powershell
pip install -r apps/api/requirements.txt
$env:PYTHONPATH = "apps/api"
pytest apps/api/tests -q
```

Also keep the existing checks:

```powershell
python -m compileall apps/api/app apps/api/tests
python scripts/check_repo_policy.py --root .
```

## Covered behavior

```text
Rejected truth claim blocks controlled application draft.
Ready lead can create, approve, and submit an application.
Application actions write audit records.
Truth claim resolution clears review blockers and writes audit records.
Bulk document verification updates readiness and writes audit records.
Authority approval converts the lead and writes audit records.
Onboarding generation and task completion write audit records.
Client communication drafts store pending but display draft.
Reviewed client communication drafts store completed but display reviewed.
Unreviewed client draft send/export placeholder is blocked.
Audit log API can filter by action and include before/after states.
```

## Note

This is the first regression layer, not a complete production test suite. Later versions should add fixtures for demo data reset, authentication/role permissions, PostgreSQL runs, and negative API validation cases.
