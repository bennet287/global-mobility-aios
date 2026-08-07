# Global Mobility AIOS Delivery Roadmap

This is the canonical delivery plan for
[Global Mobility AIOS](GLOBAL_MOBILITY_AIOS_VISION_V1.md). It describes what is
complete, what is operationally incomplete, what must be stabilized, and what
will be built next.

Detailed release notes belong in [CHANGELOG.md](CHANGELOG.md). Feature-level
design and evidence belong in the linked specification documents. This roadmap
does not duplicate either of them.

## 1. Product Direction

Global Mobility AIOS is being built as an **AI-operated global mobility
organization**, not as a conventional application with several disconnected AI
assistants.

The human owner is the Board. A governed CEO Agent operates the organization,
coordinates executive agents and departments, and escalates only Board-reserved
decisions, material risks, and unresolved executive exceptions. Routine work is
delegated through explicit authority limits and remains observable, attributable,
auditable, reversible where possible, and subject to emergency shutdown.

```text
Human Owner / Board
  -> CEO Agent
      -> CTO Agent: technology and engineering
      -> COO Agent: operations, sales, and business intelligence
      -> CISO Agent: security, threat intelligence, and resilience
      -> CMO Agent: marketing and product marketing
      -> CPO Agent: product, design, and product management
      -> CFO Agent: finance, accounts, M&A, and investor relations
      -> CCO Agent: communications, PR, and government relations
      -> CHRO Agent: people, culture, and recruitment
      -> CLO Agent: legal, public policy, and compliance
```

The target operating model is defined in
[AI_ORGANIZATION_GOVERNANCE_V13_0.md](AI_ORGANIZATION_GOVERNANCE_V13_0.md).

## 2. Current Release Posture

**As of:** 2026-08-07

**Development branch:** `roadmap/global-mobility-aios-v11`

**Code migration head:** `0065_security_runtime_contract`

| Area | State | Current position |
|---|---|---|
| Phases 1-9 | Complete | Core platform, regulatory foundation, profiles, pathways, timelines, and document intelligence delivered |
| Phase 10 software | Complete | Self-updating intelligence, global registry workflow, dashboards, ranking, and multi-year timelines delivered |
| Phase 10 evidence operations | Ongoing | Software workflow is complete; jurisdiction evidence onboarding and independent review remain incomplete |
| Phase 11 | Complete | Corporate, entrepreneur, business, wealth, investment, family-office, and tax/treaty mobility delivered |
| Phase 12 features | Delivered | Portals, partner APIs, governed automation, and government/agency workflows delivered |
| Phase 12 release posture | Stabilized | Database alignment, client-session security, API regression coverage, and local release gates pass |
| Phase 13 | Governance hardening in progress | Board controls, bounded Operations, Technology, Product, and Security/CISO runtimes, external-action gates, the executive-consultation ledger, and evidence-backed CEO coordination are delivered; remaining executive departments are held and not yet operational |
| Phase 14 | Not started | Global-scale infrastructure and validated platform scaling |

### Current quality evidence

- Web production build: passing, 35 application routes.
- Repository policy: passing.
- Migration-chain integrity: passing with one head at `0065`.
- Docker production-profile validation: passing.
- API tests: **passing and 0 failing**.
- Local SQLite database: aligned at `0065`.
- Docker PostgreSQL database: runtime not active during this slice; migration
  `0065` will apply through the existing migration job on next startup.
- Local quality gate: passing.

The repository is release-ready for the Phase 13 governance foundation, Board
Packet reporting, evidence-output, bounded execution-control, external-action
gates, the bounded Operations, Technology, Product, and Security department
runtimes, and the CEO coordination loop. The remaining departments held and not
yet operational are Marketing, Finance, Communications, People, and Legal.

## 3. Execution Order

Work must proceed in this order. A later programme must not hide an earlier red
release gate.

1. **Phase 10B evidence operations** — continue independently reviewed
   jurisdiction onboarding without claiming global completeness.
2. **Phase 13 governance foundation** — the hierarchy, authority matrix, executive
   decision ledger, and Board Room are delivered; harden the first autonomous
   flow and prove end-to-end delegation, escalation, and override.
3. **Phase 13 departmental expansion** — add executives and specialist teams only
   after the governance loop is proven end to end.
4. **Phase 14 scale work** — adopt new infrastructure only after measured demand
   justifies it.

## 4. Stabilized: Phase 12

Phase 12 is delivered and stabilized. The items below were completed before the
Phase 13 foundation was introduced.

### 12.S1 Runtime database alignment — done

- [x] Back up the local SQLite and Docker PostgreSQL databases.
- [x] Upgrade local SQLite from `0046` to `0056`.
- [x] Upgrade Docker PostgreSQL from `0054` to `0056`.
- [x] Confirm registered models and actual columns/tables are aligned.
- [x] Confirm the API container reports migration head `0056`.

### 12.S2 Secure portal-session correction — done

- [x] Replace the session-only random pseudo-device identifier with a durable,
  explicit session design.
- [x] Do not cache a portal URL containing a bearer token.
- [x] Prefer a one-time token exchange into an HttpOnly, Secure, SameSite cookie.
- [x] Define new-device enrolment, session revocation, expiry, recovery, and
  device-list management.
- [x] Preserve immediate server-side revocation and lead-scoped projections.
- [x] Add an explicit cache and storage purge on sign-out.

The existing Phase 12.8.7 implementation is a PWA/mobile-web foundation. It is
not a native iOS or Android application and must not be described as one.

### 12.S3 Error-contract and test repair — done

- [x] Align the client-portal `403` device-mismatch response, frontend parser,
  and API test around one documented response schema.
- [x] Restore the full API suite to green.
- [x] Run the complete local quality gate after database alignment.

### 12.S4 Frontend regression coverage — done

- [x] Add browser-level smoke coverage for the client portal and secure-session
  lifecycle.
- [x] Add regression coverage for authority appointments, agency submissions,
  external agency assignments, and submission checklists.
- [x] Cover primary empty, populated, validation-error, and authorization-error
  states.

### Phase 12 stabilization exit criteria

- [x] Local and Docker databases report `0058`.
- [x] API tests, frontend build/type checks, migration checks, schema checks,
  Docker checks, and repository policy all pass.
- [x] No bearer token is persisted in a service-worker cache key.
- [x] A legitimate returning client is not locked out merely by closing and
  reopening the installed portal.
- [x] Revoked and expired portal sessions fail closed online and offline.

## 5. Ongoing Operational Programme: Phase 10B Coverage

The software workflow is complete. The remaining work is evidence collection,
independent review, publication, and continuous freshness maintenance.

### Coverage rules

- Never infer an immigration-rule relationship from a territory's registry
  presence.
- Require reviewed authority and official-source evidence.
- Require independent assessment and source-certification decisions.
- Capture immutable baseline snapshots only after both reviews pass.
- Publish initial verified rules through separate proposal, review, and
  publication identities.
- Keep the global-coverage claim false until every required jurisdiction passes
  the release gates.

### Operating cycle

1. Select the next evidence gaps from the prioritized worklist.
2. Research the jurisdiction, authority, relationship, and official source.
3. Submit an atomic evidence batch.
4. Complete independent assessment and source-certification review.
5. Queue only approved baseline captures.
6. Draft, independently review, and explicitly publish snapshot-pinned rules.
7. Reconcile the readiness receipt and maintain source freshness.

The last recorded readiness in the delivery evidence is **82/243**. This is an
operational data state, not a software-completeness measure, and must be
recalculated from the active database before any external statement.

Key specifications:

- [GLOBAL_COVERAGE_EVIDENCE_OPERATIONS_V10_15.md](GLOBAL_COVERAGE_EVIDENCE_OPERATIONS_V10_15.md)
- [GLOBAL_COVERAGE_SOURCE_ONBOARDING_V10_16.md](GLOBAL_COVERAGE_SOURCE_ONBOARDING_V10_16.md)
- [INITIAL_RULE_ASSERTIONS_V10_19.md](INITIAL_RULE_ASSERTIONS_V10_19.md)
- [COVERAGE_READINESS_RECEIPTS_V10_20.md](COVERAGE_READINESS_RECEIPTS_V10_20.md)
- [Coverage tranche operations v10.22](COVERAGE_TRANCHE_OPERATIONS_V10_22.md)
  — multi-batch tranche operations with independent review gates
- Initial-rule assertion schema: migration `0032_initial_rule_assertions`

## 6. Active Gate: Phase 13 — AI Organization Governance and Autonomous Operations

**Status:** Governance foundation, Board reporting, the first bounded autonomous
organization flow, the Operations, Technology, Product, and Security department
runtimes, and bounded CEO coordination are delivered. The COO now delegates
general operating objectives to Sales Intelligence, Operations Coordination, and
Business Intelligence, and adds Application Readiness for mobility-case events.
The CTO delegates technology work to the Vice President of Engineering and Lead
Architect for delivery-readiness, architecture, security, data-handling,
integration, and reversibility analysis. The CPO delegates product work to the
Product Manager and Design Agent for product fit, scope, roadmap alignment,
success metrics, design quality, UX research, and accessibility analysis. The
CISO delegates security work to the Security Lead and Threat Analyst for
security controls, attack surface, policy alignment, threat intelligence,
prompt-injection, jailbreak, data-exfiltration, and compromised-agent indicator
analysis. Evidence-complete internal L3 matters receive a durable consultation
and may be closed by the CEO Agent; external actions, L4 matters, emergencies,
self-approval conflicts, missing consultation, and dissent fail closed.
Cross-functional consultation requirements are durable and fail closed. The
remaining departments held and not yet operational are Marketing, Finance,
Communications, People, and Legal.

**Goal:** Operate Global Mobility AIOS through a governed hierarchy of executive,
manager, and specialist agents, with the human owner acting as the Board.

### 13.0 Governance contract and stabilization dependency

- [ ] Complete the Phase 12 stabilization gate.
- [x] Adopt
  [AI_ORGANIZATION_GOVERNANCE_V13_0.md](AI_ORGANIZATION_GOVERNANCE_V13_0.md)
  as the canonical organizational runtime specification.
- [x] Define Board-reserved matters, executive authority, emergency escalation,
  and global shutdown rules.
- [x] Define what agents may never do, regardless of delegated authority.

### 13.1 Organization registry and position contracts

- [x] Add versioned organization, department, position, reporting-line, and
  agent-assignment records.
- [x] Upgrade the CEO and department-head role cards into executable position
  contracts containing mission,
  authority, tools, budget, inputs, outputs, KPIs, reports-to, direct reports,
  escalation triggers, and prohibited actions.
- [x] Register the CEO, CTO, COO, CMO, CPO, CFO, CCO, CHRO, and CLO as the
  initial executive council.
- [x] Register the existing Head of Product card under the CPO organization.
- [ ] Preserve position history when roles, reporting lines, or authority change.

### 13.2 Authority, risk, and executive decisions

- [x] Add a deterministic authority matrix with L1-L4 classifications.
- [x] Add durable organizational task, delegation, decision, escalation,
  override, and executive-decision ledgers.
- [x] Require every action to identify its accountable position, authority basis,
  evidence, confidence, impact, and rollback posture. Delegated organizational
  outputs satisfy this contract, and executable external paths require a durable
  human-review or approval receipt.
- [x] Prevent an agent from approving its own restricted recommendation.
- [x] Add deadlines, reminders, delegation expiry, and escalation-on-timeout.

| Level | Default owner | Typical scope |
|---|---|---|
| L1 | Specialist agent | Research, analysis, internal summaries, reversible routine updates |
| L2 | Manager or department head | Department workflows and bounded operational recommendations |
| L3 | Executive or CEO | Cross-department decisions and material but delegated operating changes |
| L4 | Human Board | Reserved matters, major spending, contracts, legal exposure, market entry, and irreversible actions |
| Emergency | CEO to Board immediately | Client harm, security incident, regulatory breach, financial loss, or serious reputation risk |

### 13.3 CEO and executive council runtime

- [x] Implement the CEO Agent as an orchestrator with no unrestricted direct
  action path.
- [x] Implement the COO department-head runtime with bounded Operations specialists.
- [x] Implement the CTO department-head runtime with bounded Technology specialists
  (VP Engineering and Lead Architect) for delivery, architecture, security, data,
  integration, and reversibility analysis.
- [x] Implement the CPO department-head runtime with bounded Product specialists
  (Product Manager and Design Agent) for product fit, scope, roadmap alignment,
  success metrics, design quality, UX research, and accessibility analysis.
- [x] Implement the CISO department-head runtime with bounded Security specialists
  (Security Lead and Threat Analyst) for security controls, attack surface, policy
  alignment, threat intelligence, prompt-injection, jailbreak, data-exfiltration,
  and compromised-agent indicator analysis.
- [ ] Implement the remaining department-head runtimes: CMO, CFO, CCO, CHRO, and CLO.
- [x] Let the COO delegate to registered direct reports and receive structured,
  evidence-grounded results.
- [x] Extend the same delegation contract to the CTO and CPO runtimes.
- [ ] Complete cross-functional executive consultation when an action touches
  multiple domains. The durable requirement and fail-closed ledger are delivered;
  executive completion and dissent-submission paths remain.
- [x] Escalate L4 matters, emergency risks, CEO self-approval conflicts, and
  recorded executive dissent to the Board.
- [ ] Add deadline-based escalation for unresolved executive consultations.

### 13.4 First autonomous organization flow

Prove the model with one bounded end-to-end workflow before expanding the org.

```text
Lead or case event
  -> COO classifies operational work
  -> Sales and Application Readiness agents execute bounded analysis
  -> COO resolves L1/L2 work
  -> CEO receives only L3 or cross-functional risk
  -> Board receives only L4 or emergency escalation
  -> every delegation, result, decision, and override is recorded
```

- [x] Consume an existing governed domain event idempotently.
- [x] Create an organizational task and delegate it to the correct specialist.
- [x] Record evidence-grounded outputs and confidence through the durable,
  idempotently keyed organizational action-output ledger.
- [x] Route L1/L2/L3/L4 outcomes according to the authority matrix.
- [x] Demonstrate timeout and escalation-on-timeout safety.
- [x] Enforce bounded retries, Board-controlled cancellation, durable execution
  attempts, retry scheduling, and duplicate-delivery/replay safety.
- [x] Prove that no client message, authority submission, payment, contract, or
  production deployment bypasses its required gate. Client delivery and authority
  submission validate durable approval receipts at execution time; payment,
  contract, and production-deployment executors remain unregistered and fail closed.

### 13.5 Board Room and executive reporting

- [x] Build a Board Room scaffold with pending Board decisions,
  material risks, organizational health, autonomous actions, and overrides.
- [x] Generate recurring, on-demand, and incident-triggered Board Packets.
- [x] Show the CEO recommendation, evidence, alternatives, expected impact,
  dissenting executive views, cost, urgency, and exact approval requested.
- [x] Complete all Board controls. Approve, reject, return-for-analysis, and
  global pause are implemented; override and per-agent suspension are now
  implemented too.
- [x] Notify the owner only for L4, emergency, overdue, or explicitly subscribed
  matters. (Escalation paths now route emergency and overdue items to the Board; explicit
  subscription and notification channel remain.)

### 13.6 Departmental expansion

After the first organization flow and Board Room pass their release gates:

- [x] Expand Operations: Sales Intelligence, Operations Coordination, Business
  Intelligence, and case-specific Application Readiness under COO accountability.
- [x] Expand Technology: VP Engineering, Lead Architect, and hardened CTO
  delegation contracts under Technology accountability. (Engineering managers,
  technical leads, and engineering members remain future scale work.)
- [x] Expand Product: CPO, Product Manager, and Design Agent with bounded
  delegation, required evidence/output contracts, and hardened role cards under
  Product accountability.
- [x] Expand Security: CISO, Security Lead, and Threat Analyst with bounded
  delegation, threat-intelligence/prompt-injection/compromised-agent analysis,
  required evidence/output contracts, and hardened role cards under Security
  accountability.
- [ ] Add Marketing: CMO, Product Marketing, and Marketing Managers.
- [ ] Add Finance: CFO, Accounts, M&A, and Investor Relations.
- [ ] Add Communications: CCO, Communications, PR, and Government Relations.
- [ ] Add People: CHRO, HR, Culture, and Recruitment.
- [ ] Add Legal: CLO, General Counsel, Public Policy, and Compliance.
- [ ] Add time-bounded cross-functional programmes with one accountable executive
  sponsor and explicit participating positions.

### Phase 13 non-negotiable controls

- No position receives authority merely because its prompt claims authority.
- No agent may change its own position contract, reporting line, authority, or
  budget.
- No autonomous spending, contract signature, legal filing, authority submission,
  production deployment, or client-facing send outside an explicit gate.
- Regulated conclusions remain source-controlled and review-gated.
- Cross-tenant access remains prohibited.
- Every meaningful action is attributable and audited.
- The Board can suspend one agent, one department, or the complete organization.

### Phase 13 release criteria

- [x] One complete hierarchy from Board to specialist is executable.
- [x] Authority classification is deterministic and covered by tests.
- [x] Restricted actions fail closed.
- [x] Delegation and escalation are idempotent and traceable.
- [x] The CEO produces an evidence-backed Board Packet.
- [x] The Board can approve, reject, override, and stop execution. Approve,
  reject, return-for-analysis, global pause, override, and per-agent suspension
  are implemented.
- [x] An emergency scenario reaches the Board without delay.
- [x] Routine L1/L2 work completes without unnecessary Board interruption.
- [x] Evidence-complete internal L3 Operations work resolves through a distinct
  CEO decision receipt without authorizing an external action or interrupting the
  Board.

## 7. Phase 14: Global Scale Platform

**Status:** Not started; implement only after validated operational demand.

- [ ] Expand reviewed evidence coverage across all required jurisdictions.
- [ ] Add OpenSearch or Elasticsearch only when PostgreSQL search is measured as
  insufficient.
- [ ] Add Neo4j only when validated graph traversal requires a dedicated graph
  database.
- [ ] Add durable event streaming and Temporal-class workflows when throughput and
  recovery requirements justify them.
- [ ] Add OpenTelemetry, Prometheus, Grafana, Loki, tracing, SLOs, backups, and
  disaster-recovery exercises.
- [ ] Add Kubernetes and cloud/on-premise deployment profiles when operationally
  justified.

## 8. Completed Delivery Map

| Phase | Outcome | Evidence |
|---|---|---|
| 1-5 | Local-first platform, CRM, intake, Truth Engine, documents, eligibility, controlled agents, audit, and RBAC | [GLOBAL_MOBILITY_AIOS_VISION_V1.md](GLOBAL_MOBILITY_AIOS_VISION_V1.md) |
| 6 | Foundation and repository alignment | [ARCHITECTURE.md](ARCHITECTURE.md) |
| 7 | Regulatory intelligence, monitored official sources, immutable snapshots, reviewed changes, and verified rules | [TRUTH_ENGINE_SPEC.md](TRUTH_ENGINE_SPEC.md) |
| 8 | Universal profile, governed pathways, deterministic comparison, and operational timelines | [GLOBAL_MOBILITY_AIOS_VISION_V1.md](GLOBAL_MOBILITY_AIOS_VISION_V1.md) |
| 9 | Server-side document extraction, validation, integrity findings, reminders, and controlled access | [DOCUMENT_INTELLIGENCE_FOUNDATION_V9_0.md](DOCUMENT_INTELLIGENCE_FOUNDATION_V9_0.md) |
| 10A | Self-updating regulatory intelligence, controlled classification, graph projection, and pathway impacts | [CONTROLLED_REGULATORY_CLASSIFICATION_V10_4.md](CONTROLLED_REGULATORY_CLASSIFICATION_V10_4.md) |
| 10B software | Registry, evidence batches, source onboarding, baseline capture, rule assertions, readiness receipts, and tranche operations | [COVERAGE_TRANCHE_OPERATIONS_V10_22.md](COVERAGE_TRANCHE_OPERATIONS_V10_22.md) |
| 10C-10E | Global dashboards, reviewed ranking, and immutable multi-year mobility scenarios | [MULTI_YEAR_MOBILITY_SCENARIOS_V10_14.md](MULTI_YEAR_MOBILITY_SCENARIOS_V10_14.md) |
| 11 | Corporate, business, wealth, investment, family-office, and tax/treaty mobility | [BUSINESS_WEALTH_ADVISORY_V11_4.md](BUSINESS_WEALTH_ADVISORY_V11_4.md) |
| 12 | Client/ecosystem portals, partner APIs, governed automation, appointments, submissions, assignments, checklists, and reminders | [GOVERNED_AUTOMATION_FOUNDATION_V12_3.md](GOVERNED_AUTOMATION_FOUNDATION_V12_3.md) |

## 9. Delivery Governance

Every software slice must include:

- an accountable product owner and runtime owner;
- acceptance criteria tied to the canonical vision;
- migration and rollback paths when data changes;
- least-privilege authorization and tenant boundaries;
- audit events for sensitive actions and transitions;
- provenance and Truth Engine integration for regulated claims;
- backend tests and frontend build/type validation;
- browser-level validation for critical user journeys;
- security, privacy, consent, retention, and operational notes;
- roadmap, feature-document, and changelog updates;
- an explicit statement of what remains incomplete.

### Status rules

- **Delivered** means the code exists and focused verification passes.
- **Complete** means the phase exit criteria and full quality gate pass.
- **Operationally ongoing** means the software is complete but live evidence,
e  review, monitoring, or data expansion continues.
- **Blocked** identifies the exact external or technical dependency; it is not a
  substitute for unfinished work.
- A UI without its authoritative backend, permissions, audit, and tests is not a
  completed capability.
- A role card without runtime registration, authority enforcement, and an output
  contract is not an operational agent.

## 10. Historical Evidence

- Release-level history: [CHANGELOG.md](CHANGELOG.md)
- Canonical product scope: [GLOBAL_MOBILITY_AIOS_VISION_V1.md](GLOBAL_MOBILITY_AIOS_VISION_V1.md)
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Security baseline: [SECURITY_AND_COMPLIANCE.md](SECURITY_AND_COMPLIANCE.md)
- Agent organization target:
  [AI_ORGANIZATION_GOVERNANCE_V13_0.md](AI_ORGANIZATION_GOVERNANCE_V13_0.md)
- Feature-specific evidence: versioned documents under `docs/`
- Exact implementation history: Git commits and Alembic migrations
