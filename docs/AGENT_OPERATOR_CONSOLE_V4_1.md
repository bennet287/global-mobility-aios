# Agent Operator Console v4.1

## Purpose

v4.1 makes the controlled AI agents from v4.0 usable by operators through admin UI pages.

This milestone does not add autonomous AI behavior. Agents remain internal workflow assistants.

## New Admin Pages

| Route | Purpose |
| --- | --- |
| `GET /admin/controlled-agents` | Main operator console with lead-level agent actions and recent runs. |
| `GET /admin/controlled-agents/leads/{lead_id}` | Lead-specific agent action panel and generated context preview. |
| `POST /admin/controlled-agents/leads/{lead_id}/run/{agent_name}` | Run one approved controlled agent for a lead. |
| `GET /admin/controlled-agents/runs/{run_id}` | Review the input and output of one controlled agent run. |

The Admin v2 navigation now links to the agent console.

## Operator Actions

The console exposes five safe actions:

| Button | Controlled agent |
| --- | --- |
| Generate Sales Summary | `sales_summary_agent` |
| Explain Readiness | `application_readiness_agent` |
| Summarize Documents | `document_checklist_agent` |
| Explain Truth Status | `truth_explanation_agent` |
| Draft Client Update | `client_drafting_agent` |

Each action creates:

- an `AgentRun`
- an `AuditLog` entry with action `controlled_agent_run`

## Safety Rules

The console cannot:

- send email
- send WhatsApp messages
- submit applications
- approve applications
- verify documents
- convert leads
- bypass truth or document readiness gates

All generated outputs are internal and require human review.

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
28 passed
```
