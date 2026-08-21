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

`pytest` was added as a development/test dependency at this historical checkpoint.

## Test database

The original v2.9 suite used an in-memory SQLite database through SQLModel and overrode FastAPI's `get_session` dependency.

This kept tests isolated from the local development database.

## Run

This document records the historical v2.9 suite, but commands should be run against the **current repository dependency contract**. The accepted V12 production-proof baseline requires `requirements.txt` together with `constraints.txt`; do not install `requirements.txt` alone for a proof-equivalent environment.

From the repository root:

```powershell
python -m pip install -r apps/api/requirements.txt -c apps/api/constraints.txt
python -m pip check
$env:PYTHONPATH = "apps/api"
python -m pytest apps/api/tests -q
```

Also keep the repository checks appropriate to the current branch, including:

```powershell
python -m compileall apps/api/app apps/api/tests
python scripts/check_repo_policy.py --root .
python scripts/check_release_consistency.py --root .
python scripts/check_python_dependency_constraints.py
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

v2.9 was the first regression layer, not the current complete production-proof suite. The active V12 proof additionally covers the broader backend regression, constrained dependencies, migrations and physical schema, a PostgreSQL 16 governance lane, and frontend install/security/tests/types/build/compiled-auth checks. See `.github/workflows/v12-production-proof.yml` and the current H.1 Production Proof records for the accepted proof boundary.
