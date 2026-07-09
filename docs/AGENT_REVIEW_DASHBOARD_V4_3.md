# Agent Review Dashboard v4.3

## Purpose

v4.3 polishes the agent output review workflow added in v4.2.

This milestone does not add new AI logic, autonomous actions, sending, submission, or document verification. It improves operator usability and traceability.

## Improvements

| Area | Change |
| --- | --- |
| Review dashboard | Replaced the simple queue page with a filtered dashboard. |
| Filters | Added filters for status, agent name, and lead ID. |
| Status badges | Shows pending review, approved, rejected, and converted states clearly. |
| Lead links | Review rows link back to the lead-level agent console. |
| Conversion labels | Shows the allowed conversion target for each output. |
| Reviewer notes | Shows the latest reviewer or conversion note from audit logs. |
| Review history | Run detail pages now show review/conversion audit history. |
| Empty states | Filtered empty results show a clear empty message. |
| Debug marker | `/debug/controlled-agents` now reports v4.3 dashboard filters. |

## Routes

Admin:

| Route | Purpose |
| --- | --- |
| `GET /admin/agent-output-reviews` | Filtered review dashboard. |
| `GET /admin/agent-output-reviews?status=approved` | Filter by review status. |
| `GET /admin/agent-output-reviews?agent_name=sales_summary_agent` | Filter by agent. |
| `GET /admin/agent-output-reviews?lead_id={lead_id}` | Filter by lead. |
| `GET /admin/agent-output-reviews/runs/{run_id}` | Detail view with review history. |

API:

| Route | Purpose |
| --- | --- |
| `GET /api/v1/agent-output-reviews/dashboard` | Dashboard summary and filtered items. |
| `GET /api/v1/agent-output-reviews/queue` | Pending items, now filterable by agent and lead. |
| `GET /api/v1/agent-output-reviews/reviewed` | Reviewed items, now filterable by status, agent, and lead. |

## Safety

v4.3 keeps the same safety model:

- unapproved output cannot be converted
- converted client communication output becomes a pending draft only
- sales summary output becomes an internal note only
- no email sending
- no WhatsApp sending
- no application submission
- no document verification
- no lead conversion

## Verification

Run:

```powershell
python -m compileall apps/api/app apps/api/tests scripts/seed_demo_data.py scripts/check_database_migrations.py scripts/check_docker_profile.py
python scripts/check_repo_policy.py --root .
python scripts/check_database_migrations.py
python scripts/check_docker_profile.py

$env:PYTHONPATH="apps/api"
python -m pytest apps/api/tests -q
```

Expected:

```text
35 passed
```
