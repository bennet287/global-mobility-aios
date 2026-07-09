# Demo Release Runbook v5.1

## Status

Local demo release-candidate runbook for the v5.0 verified workflow.

## Current Verified Baseline

```text
v5.0 Agent-to-client-draft workflow verified locally
quality gate: 45 passed, 1 external warning
demo readiness: ready
```

## One-Command Quality Gate

Run:

```powershell
python scripts/check_local_quality.py
```

Expected:

```text
Local quality gate passed.
45 passed
```

## Reset Demo State

Run:

```powershell
Copy-Item .\gmai.db .\gmai.backup-before-demo-v5.1.db -ErrorAction SilentlyContinue
python scripts/seed_demo_data.py --reset-all --yes
python scripts/check_demo_readiness.py
```

Expected:

```text
"status": "ready"
"demo_leads": 4
```

## Start API

Run:

```powershell
$env:PYTHONPATH="apps/api"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Print Demo URLs

Run:

```powershell
python scripts/print_demo_runbook.py
```

Or as JSON:

```powershell
python scripts/print_demo_runbook.py --json
```

## Export Demo Snapshot

Run:

```powershell
python scripts/export_demo_snapshot.py --format markdown
```

Expected:

```text
Demo snapshot written to ...\demo_exports\demo-snapshot-v5.2.md
```

## Main URLs

| Page | URL |
|---|---|
| Health | `http://127.0.0.1:8000/health` |
| Admin v2 | `http://127.0.0.1:8000/admin/v2` |
| Agent Console | `http://127.0.0.1:8000/admin/controlled-agents` |
| Agent Review Queue | `http://127.0.0.1:8000/admin/agent-output-reviews` |
| Client Communications | `http://127.0.0.1:8000/admin/client-communications` |
| Communication Drafts | `http://127.0.0.1:8000/admin/client-communications/drafts` |
| Audit Logs | `http://127.0.0.1:8000/admin/audit-logs` |

## Demo Flow

1. Open Admin v2 and show four demo leads.
2. Open Agent Console.
3. For Demo 1, run a sales summary and reject it in the review queue.
4. For Demo 3, run `Draft Client Update`.
5. Approve the `client_drafting_agent` output.
6. Convert it to a client communication draft.
7. Open Communication Drafts and confirm Demo 3 appears as a draft.
8. Preview/Edit the draft.
9. Mark the draft reviewed.
10. Open Audit Logs and confirm the trace.

## Expected Audit Trail

```text
controlled_agent_run
agent_output_approved
agent_output_converted_to_client_draft
client_draft_reviewed
```

## Safety Rules

- Controlled agents produce internal outputs only.
- Agent output conversion creates reviewable drafts only.
- Client communication drafts require human review.
- No automatic email sending exists.
- No WhatsApp sending exists.
- No client portal send exists.
- No application submission happens from this flow.
- No lead conversion happens from this flow.

## Verification

Run:

```powershell
python -m compileall apps/api/app apps/api/tests scripts/check_local_quality.py scripts/print_demo_runbook.py
python scripts/check_repo_policy.py --root .
python scripts/print_demo_runbook.py --json
python scripts/export_demo_snapshot.py --format markdown
python scripts/check_local_quality.py
```

Expected:

```text
Local quality gate passed.
48 passed
```
