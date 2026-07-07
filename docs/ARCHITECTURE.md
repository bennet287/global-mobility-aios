# Architecture

## Design Pattern

Global Mobility AIOS is workflow-first and agent-assisted.

```text
Lead / Client / Employer
        ↓
API Gateway
        ↓
Workflow Orchestrator
        ↓
Domain Service
        ↓
Truth Engine / Data / Documents
        ↓
Human Approval if sensitive
        ↓
Automation / Follow-up / CRM
```

## Components

Repository scope for architecture dependencies is restricted by the allowlist in `docs/REPOSITORY_POLICY.md`.

### API Gateway
FastAPI exposes typed endpoints and OpenAPI documentation.

### CRM Service
Stores leads, status, intent, source, target country, and notes.

### Truth Engine
Validates claims using official-source evidence and red-flag detection.

### Education Service
Builds study-abroad recommendations after profile and rule verification.

### Recruitment Service
Matches candidates with job pathways and application workflows.

### Document Service
Stores document metadata and supports future MinIO/OCR integration.

### Agent Layer
Agents are role-bound workers, not independent authorities.

### n8n
Handles business automations like forms, WhatsApp, email, reminders, and CRM transitions.

### LangGraph
Handles stateful, auditable, human-in-loop workflows.

### Data Layer
PostgreSQL for transactional data, Qdrant for semantic memory, Redis for state/cache, MinIO for documents.
