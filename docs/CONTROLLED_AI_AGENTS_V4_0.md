# Controlled AI Agents v4.0

## Purpose

v4.0 adds a controlled internal agent layer without introducing autonomous actions, external LLM dependencies, CrewAI orchestration, or client-facing sending.

The system remains workflow-first:

1. Workflow decides.
2. Controlled agent assists.
3. Truth, document, and readiness gates remain authoritative.
4. Human review is required before client-facing or lifecycle actions.
5. Agent runs are persisted and audited.

## Controlled Agents

| Agent | Department | Purpose |
| --- | --- | --- |
| `truth_explanation_agent` | Truth | Explains truth claim status and safe next actions. |
| `document_checklist_agent` | Documents | Summarizes missing and verified documents. |
| `client_drafting_agent` | Client communications | Drafts internal client update text. |
| `sales_summary_agent` | Sales | Prepares sales-safe lead summaries. |
| `application_readiness_agent` | Applications | Explains application readiness blockers. |

## Guardrails

All v4.0 agents are deterministic internal helpers.

They cannot:

- send email
- send WhatsApp messages
- submit applications
- approve applications
- verify documents
- convert sales leads
- create new immigration policy facts
- promise visas, jobs, admissions, scholarships, or processing times

## API

List controlled agents:

```http
GET /api/v1/controlled-agents
```

Run one controlled agent:

```http
POST /api/v1/controlled-agents/run
```

Example body:

```json
{
  "agent_name": "client_drafting_agent",
  "task": "Draft a safe client update.",
  "lead_id": "00000000-0000-0000-0000-000000000000",
  "context": {
    "subject": "Application update"
  },
  "actor": "operator"
}
```

Debug marker:

```http
GET /debug/controlled-agents
```

## Persistence

Each run creates:

- `AgentRun`
- `AuditLog` with action `controlled_agent_run`

No new database table is introduced in v4.0.

## Legacy Compatibility

The older endpoint remains available:

```http
POST /api/v1/agents/run
```

Legacy names are routed through controlled v4.0 agents:

| Legacy name | Controlled agent |
| --- | --- |
| `visa_truth_agent` | `truth_explanation_agent` |
| `document_officer` | `document_checklist_agent` |
| `sales_followup_agent` | `sales_summary_agent` |
| `study_abroad_advisor` | `application_readiness_agent` |
| `ai_ceo` | `application_readiness_agent` |
| `recruitment_specialist` | `sales_summary_agent` |

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
All tests pass.
```
