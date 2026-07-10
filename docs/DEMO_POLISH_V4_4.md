# Demo Polish v4.4

## Purpose

v4.4 makes the local demo presentation-ready after the controlled-agent milestones.

It does not add new AI behavior, external automation, sending, or submission. It improves demo data, demo validation, and admin navigation.

## Demo Seed Updates

`scripts/seed_demo_data.py` still creates exactly four demo leads:

| Lead | Scenario |
| --- | --- |
| Demo 1 - Blocked Visa Claim | Unsafe visa claim rejected; human review required. |
| Demo 2 - Documents Pending | Truth clear; documents missing or needing review. |
| Demo 3 - Ready For Application | Truth clear; documents verified; application-ready. |
| Demo 4 - Completed Journey | Authority approved; onboarding and client communication complete. |

v4.4 also seeds controlled-agent outputs:

| Status | Agent | Demo purpose |
| --- | --- | --- |
| `completed` | `document_checklist_agent` | Pending review output for documents-pending lead. |
| `approved` | `application_readiness_agent` | Approved internal readiness explanation. |
| `rejected` | `truth_explanation_agent` | Rejected unsafe truth explanation. |
| `converted` | `client_drafting_agent` | Converted output into pending communication draft. |

## Demo Readiness Check

New script:

```powershell
python scripts/check_demo_readiness.py
```

It verifies:

- four required demo leads exist
- demo agent runs cover `completed`, `approved`, `rejected`, and `converted`
- required audit events exist
- core admin entrypoints are listed for presentation

## Recommended Demo Reset

For a clean local demo database:

```powershell
python scripts/check_local_db_schema.py
python scripts/seed_demo_data.py --reset-all --yes
python scripts/check_demo_readiness.py
```

Expected readiness output:

```text
"status": "ready"
```

## Admin Quick Links

Admin v2 now includes demo quick links to:

- Agent Console
- Agent Review Dashboard
- Client Communications
- Document Uploads
- Audit Trail

## Verification

Run:

```powershell
python -m compileall apps/api/app apps/api/tests scripts/seed_demo_data.py scripts/check_demo_readiness.py scripts/check_database_migrations.py scripts/check_docker_profile.py
python scripts/check_repo_policy.py --root .
python scripts/check_database_migrations.py
python scripts/check_docker_profile.py

$env:PYTHONPATH="apps/api"
python -m pytest apps/api/tests -q
```

Expected:

```text
37 passed
```
