# Agent Output Review v4.2

## Purpose

v4.2 adds a human review lifecycle for controlled agent outputs.

v4.0 introduced controlled agents. v4.1 exposed them in the operator console. v4.2 makes their outputs reviewable before they can be reused.

## Review States

Agent outputs use `AgentRun.status`:

| Status | Meaning |
| --- | --- |
| `completed` | Agent output generated and pending review. |
| `approved` | Human reviewer approved the output. |
| `rejected` | Human reviewer rejected the output. |
| `converted` | Approved output was converted into an allowed internal artifact. |

No new database table is introduced in v4.2.

## API Routes

| Route | Purpose |
| --- | --- |
| `GET /api/v1/agent-output-reviews/queue` | List generated outputs pending review. |
| `GET /api/v1/agent-output-reviews/reviewed` | List approved, rejected, and converted outputs. |
| `POST /api/v1/agent-output-reviews/runs/{run_id}/approve` | Approve one output with reviewer note. |
| `POST /api/v1/agent-output-reviews/runs/{run_id}/reject` | Reject one output with reviewer note. |
| `POST /api/v1/agent-output-reviews/runs/{run_id}/convert` | Convert an approved output into an allowed target. |

## Admin Routes

| Route | Purpose |
| --- | --- |
| `GET /admin/agent-output-reviews` | Review queue and reviewed output list. |
| `GET /admin/agent-output-reviews/runs/{run_id}` | Review detail page for one run. |
| `POST /admin/agent-output-reviews/runs/{run_id}/approve` | Approve from the UI. |
| `POST /admin/agent-output-reviews/runs/{run_id}/reject` | Reject from the UI. |
| `POST /admin/agent-output-reviews/runs/{run_id}/convert` | Convert from the UI. |

## Allowed Conversions

| Approved agent output | Conversion target |
| --- | --- |
| `client_drafting_agent` | Pending `FollowUp` communication draft. |
| `sales_summary_agent` | Internal note appended to the lead. |

Other agent outputs can be approved or rejected, but they do not have conversion targets in v4.2.

## Audit Events

v4.2 records:

- `agent_output_approved`
- `agent_output_rejected`
- `agent_output_converted_to_client_draft`
- `agent_output_converted_to_internal_note`

## Safety Rules

Unapproved outputs cannot be converted.

Converted communication drafts remain pending. They are not sent automatically.

The review queue does not let agents:

- send messages
- submit applications
- approve applications
- verify documents
- convert leads
- bypass truth, document, or application readiness gates

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
33 passed
```
