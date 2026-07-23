# Global Mobility AIOS v1.0 Product Blueprint

## Purpose

This document is the canonical product direction for Global Mobility AIOS. It
preserves the complete target described in the original vision while separating
current capabilities from planned work. Feature documents and implementation
plans must link back to a capability in this blueprint.

Global Mobility AIOS is a global mobility intelligence operating system for the
movement of people, talent, families, businesses, and capital across borders. It
serves students, professionals, families, entrepreneurs, investors, HNWIs,
corporations, governments, mobility agencies, and integration partners.

It is broader than a study-abroad platform or immigration CRM. Its intended
category combines workflow CRM, regulatory intelligence, opportunity discovery,
document intelligence, and controlled AI workers.

## Product Vision

The platform supports a person's full mobility lifecycle:

```text
Dream
  -> Study abroad
  -> Graduate work rights
  -> Skilled migration
  -> Entrepreneurship
  -> Investment migration
  -> Permanent residence
  -> Citizenship
  -> Global citizen
```

The operating model remains workflow-first and agent-assisted. AI agents are
bounded workers. Official evidence, human review, audit logs, and permissions
remain authoritative for regulated or client-facing decisions.

## Complete Capability Scope

### Individual mobility

- Study abroad, university discovery, admissions, and scholarships
- Overseas jobs, skills-shortage matching, and employer sponsorship
- Immigration, visas, residence permits, settlement, permanent residence, and citizenship
- Graduate work rights and post-study pathways
- Digital nomad and remote-work programs
- Family and dependent mobility
- Universal mobility profiles, eligibility, risk, cost, and timeline planning

### Wealth and business mobility

- Entrepreneur and startup visas
- Residency by investment and citizenship by investment
- International business relocation
- HNWI and family-office mobility
- Tax residency intelligence and double-taxation treaty context
- Corporate employee mobility, work permits, dependants, relocation, and compliance

### Global regulatory intelligence

- Every UN-recognized country
- Autonomous immigration jurisdictions and territories with independent rules
- Official immigration, embassy, gazette, legislation, education, accreditation,
  labour, sponsorship, investment, tax, and treaty sources
- Continuous source monitoring, retrieval, extraction, classification, comparison,
  provenance, and human validation
- Detection of new programs, removed programs, rule changes, salary thresholds,
  age limits, occupation lists, quotas, processing times, and policy changes
- Self-updating verified rules and country intelligence

### Intelligence products

- New visa-program dashboard
- Immigration-change dashboard
- Processing-time dashboard
- Skilled-occupation dashboard
- Salary and investment-threshold dashboard
- Global country activity heatmap
- Opportunity radar for emerging destinations and programs
- Predictive mobility and regulatory analytics after sufficient verified history exists

### User intelligence and lifecycle planning

The universal profile must support education, qualifications, experience, skills,
languages, nationality, family, finances, budget, desired countries, goals,
constraints, risk tolerance, and consent. It drives:

- Best-fit countries and pathways
- Evidence-backed eligibility and confidence
- Risks, blockers, required evidence, and alternatives
- Expected costs and timelines
- A multi-stage global mobility timeline from the current state through long-term goals

### Document intelligence

- Secure upload and object storage
- OCR and structured extraction
- Validation and verification workflow
- Missing-document detection
- Expiry monitoring and reminders
- Fraud-risk indicators with human investigation; never autonomous fraud accusations
- Passports, degrees, transcripts, language results, contracts, bank statements,
  civil records, professional credentials, and authority decisions

### Platform channels

- Client web portal
- Operator and compliance workspace
- Mobile application
- Employer and partner portal
- Public and partner APIs
- Automation channels such as email, messaging, calendar, and CRM integrations

## Target Logical Architecture

```text
Web / Mobile / Partner Portal / APIs
                |
Identity, consent, API gateway, RBAC and ABAC
                |
Workflow orchestration and controlled agent routing
                |
Mobility domain services and human review queues
                |
Truth Engine / regulatory intelligence / documents / opportunities
                |
Transactional store / search / vectors / knowledge graph / object storage
                |
Audit, telemetry, security monitoring and analytics
```

### Controlled AI workforce

The long-term workforce includes study, visa truth, employment, scholarship,
settlement, compliance, tax residency, investment migration, corporate mobility,
HNWI mobility, risk assessment, document, communication, coaching, and orchestration
roles. Every agent requires:

- A versioned role contract and structured output schema
- Explicit permitted and prohibited actions
- Official-source requirements for regulated claims
- Confidence, uncertainty, and missing-information reporting
- Human review for sensitive or client-facing output
- Complete run and decision audit history

### Knowledge and intelligence layer

The target knowledge layer includes visa, university, job-market, regulatory, and
country intelligence graphs. It must retain source URL, authority classification,
jurisdiction, effective dates, retrieved time, content hash, extraction version,
supersession relationships, confidence, and review status.

RAG content is never authoritative without provenance. Model output cannot update a
verified rule directly.

## Target Technology Direction

These are target capabilities, not mandatory immediate dependencies:

- Frontend: Next.js, React, TypeScript; web first, mobile and partner clients later
- Backend: FastAPI, Python, SQLModel, PostgreSQL, Alembic, Redis, Celery
- AI: provider-independent hosted/local models, LangGraph-style stateful workflows,
  embeddings, and provenance-aware RAG
- Search: OpenSearch or Elasticsearch when relational search is insufficient
- Vector store: Qdrant
- Knowledge graph: Neo4j when graph use cases are validated
- Storage: S3-compatible storage such as MinIO
- Event streaming: Kafka only when durable cross-service event volume requires it
- Orchestration: n8n for business automation; Temporal-class orchestration when
  long-running workflow durability requires it
- Observability: OpenTelemetry, Prometheus, Grafana, Loki, and distributed tracing
- Deployment: edge protection, API gateway, containers, then Kubernetes when scale
  and operational maturity justify it; AWS, Azure, GCP, and on-premise are targets

## Security and Compliance Baseline

- RBAC now and ABAC as partner/corporate boundaries mature
- Tenant isolation before partner or corporate access
- Signed, expiring document access
- Encryption in transit and at rest
- Managed secrets and key rotation
- Consent, retention, deletion, and data-residency controls
- Immutable audit evidence for sensitive transitions
- Least-privilege service and human identities
- Rate limiting, abuse detection, backups, recovery exercises, and incident response
- No visa, legal, tax, scholarship, employment, or investment claim without verified
  evidence and the required review state

## Delivery Map

### Foundation and current MVP

- Local and Docker development, FastAPI, Next.js, SQLModel, PostgreSQL/SQLite
- CRM, public intake, client return, eligibility, opportunity matching
- Documents and browser OCR
- Truth Engine and official-source registry
- Controlled agents, coaching, review queues, communications, and audit logging
- Authentication, migrations, tests, CI policy, release and demo tooling

### Regulatory intelligence foundation

- Canonical jurisdiction and authority models
- Source onboarding and monitoring schedules
- Retrieval snapshots, hashes, parsers, and change sets
- Human validation and verified-rule publication
- New, changed, and retired program events

### Mobility intelligence MVP

- Universal profile v2
- Country/pathway catalogue and evidence-backed eligibility
- Study, work, visa, scholarship, settlement, and digital-nomad pathways
- Cost, risk, document, and mobility timeline engines
- Client and operator intelligence dashboards

### Business and wealth expansion

- Corporate cases, employees, dependants, sponsors, and compliance calendars
- Entrepreneur, investment, HNWI, family-office, and tax-residency intelligence
- Employer, partner, and government-facing workflows

### Global intelligence and scale

- Progressive global jurisdiction coverage with measurable freshness and quality
- Search and knowledge graph services
- Country heatmaps, opportunity radar, and historical analytics
- Mobile and partner clients, external APIs, event streaming, durable orchestration
- Kubernetes and multi-cloud/on-premise deployment profiles

## Coverage Ledger

The following ledger prevents scope loss. Status values are `current`, `next`,
`planned`, and `scale-gated`.

| Vision capability | Status | Delivery area |
| --- | --- | --- |
| Study abroad | current | Mobility MVP |
| Overseas jobs | current | Mobility MVP |
| Immigration and visa intelligence | current | Truth Engine, then regulatory intelligence |
| Digital nomad programs | planned | Mobility intelligence MVP |
| Investment migration and HNWI mobility | planned | Business and wealth expansion |
| Tax residency intelligence | planned | Business and wealth expansion |
| Corporate mobility | in progress | Corporate case foundation and governed relationships delivered; broader business and wealth expansion remains |
| Real-time immigration monitoring | next | Regulatory intelligence foundation |
| Self-updating regulations | next | Retrieval, change sets, verified-rule publication |
| New visa detection | next | Regulatory event pipeline |
| All countries and independent jurisdictions | planned | Progressive coverage programme |
| Live dashboards and opportunity radar | planned | Intelligence products |
| Controlled AI workforce | current | Expand role-by-role |
| Human review and compliance | current | Continuous hardening |
| Universal user profile | current | Universal profile v2 next |
| Mobility timeline | planned | Mobility intelligence MVP |
| OCR, extraction, validation, expiry, fraud indicators | current | Validation/expiry/fraud indicators next |
| Mobile and partner portals | planned | Platform channels |
| Knowledge graphs and Neo4j | scale-gated | Knowledge layer |
| Search engine | scale-gated | Search layer |
| Kafka/event streaming | scale-gated | Platform scale |
| Temporal-class orchestration | scale-gated | Platform scale |
| Full observability stack | planned | Production hardening |
| Kubernetes and multi-cloud/on-premise | scale-gated | Deployment maturity |

## Definition of Directional Compliance

A feature is aligned with this blueprint when it:

1. Advances a capability in the coverage ledger.
2. Preserves official-source provenance and jurisdiction/effective-date semantics.
3. Uses controlled agents rather than autonomous authority.
4. Includes human review and audit evidence where risk requires it.
5. Extends the shared profile, case, document, rule, or event model instead of
   creating an isolated demo path.
6. Includes migrations, tests, API contracts, operational notes, and security review.
