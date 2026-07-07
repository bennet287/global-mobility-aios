# Global Mobility AIOS

Production-grade, local-first scaffold for an AI-powered global mobility agency operating system.

This monorepo contains the first runnable foundation for:

- CRM and lead intake
- Education recommendation engine
- Overseas job/recruitment engine
- Visa and immigration truth engine
- Document handling metadata service
- AI department/agent role registry
- Workflow automation through n8n
- CRM dashboard and Truth Review Queue web app
- Local-first infrastructure: PostgreSQL, Redis, Qdrant, MinIO, n8n, optional Ollama

> This is not a chatbot project. It is a workflow-first AI organization OS where AI agents are bounded workers inside auditable business workflows.

## Quick Start

### 1. Copy environment

```bash
cp .env.example .env
```

### 2. Start infrastructure + API

```bash
docker compose up --build
```

API docs:

```text
http://localhost:8000/docs
```

Web dashboard:

```text
http://localhost:3000
```

n8n:

```text
http://localhost:5678
```

MinIO console:

```text
http://localhost:9001
```

Qdrant dashboard:

```text
http://localhost:6333/dashboard
```

### 3. Test the API

```bash
curl http://localhost:8000/health
```

Create a lead:

```bash
curl -X POST http://localhost:8000/api/v1/leads \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Bennet Allryn","email":"bennet@example.com","intent":"study_abroad","target_country":"Germany","source":"web_form"}'
```

Verify a visa claim:

```bash
curl -X POST http://localhost:8000/api/v1/truth/verify \
  -H "Content-Type: application/json" \
  -d '{"claim":"Germany student visa can be guaranteed without financial proof","domain":"visa","country":"Germany"}'
```

## Repository Layout

```text
global-mobility-aios/
├── apps/
│   ├── api/                  # FastAPI backend
│   └── web/                  # Next.js CRM dashboard + truth review queue
├── agents/                   # AI department role cards
├── workflows/                # LangGraph + n8n workflows
├── knowledge/                # Official source registry and RAG documents
├── infrastructure/           # Monitoring, deployment, local infra
├── docs/                     # Architecture and operational docs
├── scripts/                  # Helper scripts
├── docker-compose.yml
└── .env.example
```

## Repository Governance

Dependency and repository usage is controlled through the project allowlist policy:

- See `docs/REPOSITORY_POLICY.md`
- ADR: `docs/ADR/0001-approved-repository-strategy.md`
- CI policy check: `.github/workflows/repo-policy-check.yml`
- Local policy check script: `scripts/check_repo_policy.py`

## MVP-1 API Surface

- `POST /api/v1/workflows/lead-intake` (lead intake -> profile -> routing -> truth -> review/follow-up)
- `GET/POST /api/v1/leads`
- `GET /api/v1/leads/{lead_id}`
- `GET/POST /api/v1/profiles`
- `GET /api/v1/profiles/{profile_id}`
- `POST /api/v1/truth/verify`
- `GET /api/v1/truth/queue`
- `POST /api/v1/truth/queue/{audit_id}/resolve`
- `GET /api/v1/reviews`
- `POST /api/v1/reviews/{review_id}/resolve`
- `GET/POST /api/v1/documents`
- `GET /api/v1/documents/checklist`
- `GET /api/v1/agents`
- `POST /api/v1/agents/run`

## Build Order

1. Run the API and infrastructure locally.
2. Use `/api/v1/leads` as the CRM entry point.
3. Use `/api/v1/truth/verify` before showing any visa/job/admission recommendation.
4. Connect n8n to API webhooks for follow-up automation.
5. Add real official sources country by country.
6. Add LangGraph workflows for stateful human-in-the-loop processing.
7. Add CrewAI role execution after the workflow states are stable.

## Safety Rule

Visa, immigration, legal, scholarship, or job claims must not be generated directly by an LLM.
They must pass through the Truth Engine and include:

- source URL
- domain classification
- country
- confidence score
- verification status
- timestamp
- human-review flag where needed
