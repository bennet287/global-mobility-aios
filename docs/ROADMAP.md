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

**As of:** 2026-08-11

**Development branch:** `roadmap/global-mobility-aios-v11`

<!-- CURRENT_MIGRATION_HEAD: 0071_structured_shortage_occupation_evidence -->

**Code migration head:** `0071_structured_shortage_occupation_evidence`

| Area | State | Current position |
|---|---|---|
| Phases 1-9 | Complete | Core platform, regulatory foundation, profiles, pathways, timelines, and document intelligence delivered |
| Phase 10 software | Complete | Self-updating intelligence, global registry workflow, dashboards, ranking, and multi-year timelines delivered |
| Phase 10 evidence operations | Ongoing | Software workflow is complete; jurisdiction evidence onboarding and independent review remain incomplete |
| Phase 11 | Complete | Corporate, entrepreneur, business, wealth, investment, family-office, and tax/treaty mobility delivered |
| Phase 12 features | Delivered | Portals, partner APIs, governed automation, and government/agency workflows delivered |
| Phase 12 release posture | Stabilized | Database alignment, client-session security, API regression coverage, and local release gates pass |
| Phase 13 | External validation gate active | Board controls and bounded Operations, Technology, Product, Security/CISO, Security Operations/SOC, and Marketing runtimes are delivered; the Phase 13.10.2 external-validation framework is implemented while the real-user/professional validation run and Finance, Communications, People, and Legal remain held |
| Phase 14 | Not started | Global-scale infrastructure and validated platform scaling |

### Current quality evidence

- Web production build: **passing**; the Next.js production build completes successfully with the Phase 13.10.2 `/validation` workspace included.
- Repository policy: passing.
- Migration-chain integrity: code and persistent PostgreSQL are verified at `0071_structured_shortage_occupation_evidence`; Phase 13.10.2.9 adds no schema migration and must preserve this head.
- Docker production-profile validation: passing.
- API regression baseline before Phase 13.10.2.9: **583 passed, 0 failed** at `0071_structured_shortage_occupation_evidence`; the review-workspace patch adds deterministic queue/workspace, snapshot-selection, audit-history, identity-separation, and frontend regressions and requires the complete suite after application.
- SQLite migration compatibility: **passing through current migration head `0071_structured_shortage_occupation_evidence`** via the fresh-database upgrade/downgrade/re-upgrade regression suite.
- Persistent Docker PostgreSQL: **passing at `0071_structured_shortage_occupation_evidence`**; live Austria structured occupation evidence and pathway-v3 hold state are preserved.
- Local quality gate: **passing**; compilation, evidence-pack validation, repository policy, release consistency, migrations, local schema, Docker-profile validation, frontend production build, and the complete API test suite are green.

The Phase 13 governance foundation, Board Packet reporting, evidence-output, bounded
execution-control, external-action gates, bounded Operations, Technology, Product,
Security, Security Operations/SOC, and Marketing department runtimes, and the CEO
coordination loop remain implemented. Phase 13.10.1 is release-closed. Phase
13.10.2 adds durable external-validation scenarios, runs, evidence, external-human
reviews, findings, Board risk acceptance for medium/low findings, and a deterministic
gate at migration head `0068_external_validation_framework`. The external gate remains
held until one real mobility user and one independent professional/operator complete the
workflow successfully. Finance, Communications, People, and Legal remain held.

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
- [x] Confirm the API container reports migration head `0067`.

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
organization flow, the Operations, Technology, Product, Security, Security
Operations/SOC, and Marketing department runtimes, and bounded CEO coordination are
delivered. The COO now delegates general operating objectives to Sales Intelligence,
Operations Coordination, and Business Intelligence, and adds Application Readiness
for mobility-case events. The CTO delegates technology work to the Vice President
of Engineering and Lead Architect for delivery-readiness, architecture, security,
data-handling, integration, and reversibility analysis. The CPO delegates product
work to the Product Manager and Design Agent for product fit, scope, roadmap
alignment, success metrics, design quality, UX research, and accessibility
analysis. The CISO delegates security work to the Security Lead and Threat Analyst
for security controls, attack surface, policy alignment, threat intelligence,
prompt-injection, jailbreak, data-exfiltration, and compromised-agent indicator
analysis, and delegates Security Operations work to the SOC Lead and SOC Analyst
for agent-behavior monitoring, audit-log triage, incident coordination, and
anomaly analysis. The CMO delegates marketing work to the Creative Director and
Marketing Manager for brand fit, creative quality, messaging, audience alignment,
channel fit, campaign plan, growth metrics, and budget-constraint analysis.
Evidence-complete internal L3 matters receive a durable consultation and may be
closed by the CEO Agent; external actions, L4 matters, emergencies, self-approval
conflicts, missing consultation, and dissent fail closed. Cross-functional
consultation requirements are durable and fail closed. The remaining departments
held and not yet operational are Finance, Communications, People, and Legal.

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
- [x] Implement the Security Operations/SOC runtime under the CISO with bounded
  SOC specialists (SOC Lead and SOC Analyst) for agent-behavior monitoring, audit-log
  triage, incident coordination, and anomaly analysis.
- [x] Implement the CMO department-head runtime with bounded Marketing specialists
  (Creative Director and Marketing Manager) for brand fit, creative quality,
  messaging, audience alignment, channel fit, campaign plan, growth metrics, and
  budget-constraint analysis.
- [ ] Implement the remaining department-head runtimes: CFO, CCO, CHRO, and CLO.
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

### 13.5.1 Platform hardening and runtime registration checkpoint

Before activating another executive department, preserve the autonomy already
delivered while reducing insecure defaults and central runtime coupling. Marketing
remains delivered; this checkpoint gates Finance, Communications, People, and Legal.

- [x] Default unsigned header-role authentication to disabled and fail closed at
  production startup when authentication is disabled, header-role trust is enabled,
  or production credentials/signing secrets remain missing/default/too short.
- [x] Require production identity-document storage to use TLS-protected, non-default,
  pre-provisioned MinIO/S3-compatible storage with server-side encryption; local
  document storage is prohibited in production.
- [x] Add shared query ceilings for document/lead list paths that previously
  performed unbounded reads.
- [x] Replace inline FastAPI router registration with a declarative `RouterSpec`
  registry and replace path-role authorization branches with ordered declarative
  authorization rules.
- [x] Add a declarative `DepartmentRuntimeSpec` registry and common execution adapter
  covering Technology, Product, Security, Security Operations/SOC, and Marketing,
  so another department does not require another central execution/completion branch.
- [x] Add capability-boundary regression tests proving active departments execute
  only their explicitly allowed action class and held departments remain unavailable.
- [x] Add CI migration/roadmap consistency enforcement against the unique Alembic head.
- [x] Exclude local patch-backup directories from repository policy scans and future
  source control; existing tracked backups must be removed from the Git index once.
### 13.5.2 External mobility validation framework

Phase 13.10.2 turns the pre-department-expansion customer-validation requirement into
repeatable, auditable infrastructure rather than an informal feedback exercise.

- [x] Persist versionable validation scenarios without embedding the expected legal answer.
- [x] Persist validation runs pinned to the scenario, lead, and exact pathway comparison shown to testers.
- [x] Capture durable evidence references for Truth Claims, Verified Rules, Official Sources,
  immutable Source Snapshots, pathway versions, pathway comparisons, documents, and notes.
- [x] Fail closed when the pinned comparison, primary pathway version, verified-rule set,
  jurisdiction/domain, official-source lineage, source snapshots, or lead-scoped Truth Claim
  do not form one coherent governed evidence graph.
- [x] Capture external-human mobility-user and professional/operator reviews separately from
  the internal actor who records them. AI agents cannot self-create the required review pair.
- [x] Record Critical/High/Medium/Low findings with explicit triage and remediation state.
- [x] Enforce that Critical and High findings must be resolved; only Medium/Low findings may
  receive explicit Human Board risk acceptance.
- [x] Calculate a deterministic `held` / `failed` / `passed` gate receipt and record founder
  intervention count as an autonomy metric.
- [x] Add a small operator validation workspace and an Austria first-scenario fixture/template.
- [ ] Complete the first real external run and attach the external reviewer evidence.
- [ ] Resolve/retest every Critical/High issue, triage remaining Medium/Low issues, and record
  a PASS receipt.

The framework is described in
[EXTERNAL_MOBILITY_VALIDATION_V13_10_2.md](EXTERNAL_MOBILITY_VALIDATION_V13_10_2.md).

### 13.10.2.1 PostgreSQL migration portability hardening

The Phase 13.10.2 validation dry run exercised the persistent PostgreSQL
database and exposed migration portability defects that the SQLite development
path had not detected. The schema head remains
`0068_external_validation_framework`; this slice corrects historical migration
execution without introducing a new schema revision.

- [x] Back up the persistent PostgreSQL database before migration repair.
- [x] Replace PostgreSQL-incompatible integer Boolean defaults in
  `0058_deadline_emergency_escalation` with dialect-safe `sa.false()`.
- [x] Preserve native UUID binding for `organization_positions.id` in
  `0065_security_runtime_contract`, `0066_soc_runtime_contract`, and
  `0067_marketing_runtime_contract`.
- [x] Add regression coverage preventing integer Boolean migration defaults and
  VARCHAR bindings for the UUID organization-position identifier.
- [x] Upgrade the historical PostgreSQL database transactionally from
  `0056_ai_organization_governance` through
  `0068_external_validation_framework`.
- [x] Confirm the governed data set survives unchanged: 292 jurisdictions,
  89 official sources, 521 source snapshots, 86 verified rules,
  1 mobility pathway, and 2 mobility pathway versions.
- [x] Confirm the unique Alembic head remains
  `0068_external_validation_framework`.
- [x] Run the complete release gate: **534 tests passed, 0 failed** and the
  complete local quality gate passed.
- [x] Release-close the portability hardening before resuming the Austria
  external-mobility validation run.

### 13.6 Departmental expansion

After the first organization flow and Board Room pass their release gates, and after the hardening checkpoint above:

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
- [x] Expand Security Operations (SOC): SOC Lead and SOC Analyst under CISO
  accountability, with bounded delegation, agent-behavior and audit-log analysis,
  required evidence/output contracts, and hardened role cards.
- [x] Add Marketing: CMO, Creative Director, and Marketing Manager under CMO
  accountability, with bounded delegation, brand/creative/channel analysis, and
  required evidence/output contracts.
- [ ] **External-validation gate:** do not activate another executive department
  until at least one real mobility user and one professional/operator have tested
  an end-to-end Truth Engine/pathway workflow and the resulting defects are triaged.
- [ ] Add Finance: CFO, Accounts Lead, and Investor Relations Lead under CFO
  accountability, with bounded delegation, spend/investment/contract analysis,
  and required evidence/output contracts.
- [ ] Add Communications: CCO, Communications Lead, and PR/Government Relations Lead
  under CCO accountability, with bounded delegation, message/channel/stakeholder
  analysis, and required evidence/output contracts.
- [ ] Add People: CHRO, HR Lead, and Culture/Recruitment Lead under CHRO
  accountability, with bounded delegation, workforce/talent/policy analysis, and
  required evidence/output contracts.
- [ ] Add Legal: CLO, General Counsel, and Public Policy/Compliance Lead under
  CLO accountability, with bounded delegation, risk/authority/policy analysis,
  and required evidence/output contracts.
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
- [x] Evidence-complete internal L3 Marketing work resolves through a distinct
  CEO decision receipt that consults the CMO, without authorizing an external
  action or interrupting the Board.

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
| 13.0-13.10.2.1 software | AI organization governance, Board Room, bounded Operations/Technology/Product/Security/SOC/Marketing runtimes, platform hardening, and durable external-mobility validation infrastructure | [AI_ORGANIZATION_GOVERNANCE_V13_0.md](AI_ORGANIZATION_GOVERNANCE_V13_0.md), [EXTERNAL_MOBILITY_VALIDATION_V13_10_2.md](EXTERNAL_MOBILITY_VALIDATION_V13_10_2.md) |

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

### 13.10.2.2 Controlled official-source authority remediation

- [x] Add a bounded, audited official-source authority-reassignment API for correcting
  duplicate authority ownership discovered during external mobility validation.
- [x] Require the target authority to be the jurisdiction's independently approved
  `primary_immigration` authority and fail closed on cross-jurisdiction moves.
- [x] Refuse reassignment when the source already has a pending or approved source
  certification, preserving certification provenance.
- [x] Preserve the official-source identity and therefore existing monitor, retrieval,
  and immutable snapshot lineage; only the source-to-authority relationship changes.
- [x] Make retries idempotent when the source is already attached to the approved
  primary authority.
- [ ] Complete the live Austria remediation, submit `supplemental_visa` certification
  for the Skilled Workers in Shortage Occupations source, and obtain independent review.

### 13.10.2.3 Existing-source baseline linkage hardening

- [x] Persist authority, official-source, and existing-monitor linkage when a
  coverage batch certifies an already-onboarded source without repeating source
  onboarding.
- [x] Resolve legacy certification-only batch items read-only from their immutable
  source certification so baseline status can reuse existing evidence.
- [x] Preserve existing source, monitor, retrieval, and immutable-snapshot identity;
  no replacement evidence is created by linkage resolution.
- [x] Add regression coverage for the certification-only legacy batch condition
  discovered during Austria skilled-employment validation.
- [x] Add an audited, idempotent reconciliation operation for legacy
  certification-only batch items; conflicting non-null linkage fails closed.
- [x] Reconcile the existing live Austria batch-item linkage and confirm it resolves
  to the already captured immutable baseline before initial-rule assertions.

### 13.10.2.4 Supplemental source-certification multiplicity hardening

#### Validation evidence

- [x] Isolated SQLite migration smoke test passed through
  `0068_external_validation_framework -> 0069_source_certification_multiplicity`,
  downgrade to `0068`, and re-upgrade to `0069`.
- [x] PostgreSQL production-shape database migrated successfully to
  `0069_source_certification_multiplicity`.
- [x] PostgreSQL now enforces separate partial unique indexes for
  jurisdiction-scoped `primary_immigration` certification and
  source-scoped supplemental certification lineages.
- [x] Historical `uq_jsc_scope_version` database constraint was removed.
- [x] Pre-migration PostgreSQL backup created at
  `gmai-postgres-before-0069-20260810-040926.dump`
  with SHA-256
  `26BEA6AD1D83BB5E4B453141FD921797F05000A6B20E5D8C47086C475996E535`.
- [x] Live Austria verification proved three supplemental visa source
  lineages can coexist: the existing skilled-worker source remains approved,
  the Austria-wide 2026 source remains pending review, and the regional 2026
  source was independently created as version 1 with no supersession pointer.
- [x] Regional 2026 certification
  `f4cf5f04-0519-4cad-b5c2-88ec1183ded5` is linked to coverage batch
  `0bd5b76d-49f5-4dbd-ba54-feeb4591676c` and monitor
  `09295bbc-8b68-45e8-9387-4184b7172d8a`.
- [x] Behavioral regression proves approving one supplemental source does
  not mutate independently approved or pending sources, while a later
  version of the same source supersedes only its own lineage.
- [x] Focused certification/linkage suite: **18 passed**.
- [x] Complete API suite: **552 passed**, with one non-blocking
  Starlette/httpx deprecation warning.
- [ ] Austria-wide and regional 2026 certifications remain pending genuine
  independent human review; this hardening does not satisfy that review gate.

- [x] Add Alembic migration
  `0069_source_certification_multiplicity` to replace the historical
  jurisdiction/scope/version uniqueness constraint with explicit primary and
  supplemental lineage invariants.
- [x] Preserve database-enforced jurisdiction-scoped version uniqueness for
  `primary_immigration`.
- [x] Enforce source-scoped version uniqueness for supplemental certifications
  so independently governed sources in the same jurisdiction/domain may
  coexist.
- [x] Mirror both partial unique indexes in SQLModel metadata so fresh test
  databases and Alembic-managed databases express the same invariant.
- [x] Add regression coverage proving two supplemental sources can both start
  at version 1 while duplicate versions within one source remain blocked.

- [x] Preserve jurisdiction-scoped versioning and supersession for
  `primary_immigration` certification.
- [x] Scope `supplemental_<domain>` pending-review guards, version lineage, and
  supersession to the exact official source so multiple independently reviewed
  sources may coexist within one jurisdiction/domain.
- [x] Prevent approval of one supplemental visa source from superseding approved
  supplemental visa certifications belonging to other official sources.
- [x] Clear legacy cross-source `supersedes_certification_id` pointers at review
  time without replacing certification, source, monitor, retrieval, or snapshot
  identity.
- [x] Add regression coverage for primary-vs-supplemental lineage semantics.
- [ ] Re-verify the live Austria 2026 Austria-wide certification, submit the
  regional 2026 certification concurrently, and confirm the previously approved
  skilled-worker source certification remains approved.
- [ ] Obtain genuine independent review of both 2026 shortage-list source
  certifications before proposing regulatory assertions.

### 13.10.2.5 Pathway multi-source evidence provenance

- [x] Add normalized `mobility_pathway_version_evidence` records so one immutable
  pathway version can declare multiple official source/snapshot pairs with explicit
  evidence roles.
- [x] Preserve the historical `official_source_id` / `source_snapshot_id` fields as
  the backward-compatible `core_route` pair rather than performing a disruptive
  pathway API rewrite.
- [x] Add Alembic migration `0070_pathway_version_evidence_provenance` and backfill
  every historical version that already has a source/snapshot pair into a
  `core_route` evidence row without database-specific UUID generation.
- [x] Add input/read schemas for evidence links and persist normalized links on new
  pathway drafts.
- [x] Fail closed on duplicate or mismatched core evidence, cross-country evidence,
  cross-jurisdiction evidence, and source/snapshot mismatch.
- [x] Require every human-published Verified Rule referenced by a published pathway
  version to have its exact source/snapshot pair declared by that version.
- [x] Require non-core evidence marked `required_for_publication` to have an approved
  certification for that exact official source before pathway publication. Drafts
  may still carry pending evidence so governance review is not bypassed.
- [x] Prevent certification bypass by requiring any non-core evidence used by a
  referenced Verified Rule to be publication-required and certified, and hold a
  `core_route` source when it has entered certification but has no approved state.
- [x] Extend multi-year mobility scenarios to pin every pathway evidence snapshot,
  not only the legacy core snapshot.
- [x] Extend pathway risk analysis across every declared evidence source/snapshot and
  surface stale, missing, inactive, or certification-regressed evidence by role.
- [x] Extend regulatory-impact source matching and impact receipts across every
  declared pathway evidence source/snapshot.
- [x] Add focused regression coverage for required supplemental certification,
  undeclared rule provenance, legacy core fallback, multi-source risk inspection,
  and regulatory-impact source matching.
- [x] Applied `0070` to the persistent PostgreSQL database after a verified
  custom-format backup:
  `C:\\Users\\Bennet Allryn\\Downloads\\gmai-postgres-before-0070-20260810-124945.dump`
  (3,631,344 bytes; SHA-256
  `7EC3E2E5E350A59EC21D4345662AC1B6E36B9F172C422BFA454675025FEB7E5C`).
- [x] Verified the PostgreSQL `0069` -> `0070` migration transactionally:
  `missing_core_backfills = 0`, four historical `core_route` evidence rows were
  created, and the database revision is
  `0070_pathway_version_evidence_provenance`.
- [x] Complete post-migration validation passed: focused Phase 13.10.2.5 suite
  **14 passed, 1 warning**; complete API suite **560 passed, 1 warning**;
  repository policy, release consistency, database migration, Docker production
  profile, and local database-schema checks all passed.
- [x] Re-verified live Austria integrity after migration: skilled-worker pathway
  versions 1 and 2 remain `draft`, unpublished and unapproved; both retain matching
  `core_route` source/snapshot evidence and no national/regional evidence links were
  introduced by migration.
- [x] Confirmed the existing general skilled-worker supplemental source certification
  remains `approved`, while the Austria-wide and regional 2026 shortage-list source
  certifications remain `pending_review`. The historical Austria-wide cross-source
  supersedes pointer remains untouched for controlled cleanup during genuine review.
- [ ] Create a future Austria pathway version only after the two 2026 evidence links
  are deliberately attached and the publication gate can evaluate their real
  certification state after genuine independent review.

### 13.10.2.6 Structured 2026 shortage-occupation evidence

- [x] Add normalized `shortage_occupation_entries` derived from immutable official
  source snapshots rather than encoding hundreds of occupation labels as
  `VerifiedRule` statements.
- [x] Add Alembic migration `0071_structured_shortage_occupation_evidence` with
  source/jurisdiction/snapshot foreign keys, deterministic source ordinals, exact
  extraction hashes, and snapshot/year/scope uniqueness.
- [x] Add a bounded `austria_migration_shortage_v1` parser for the official
  migration.gv.at Austria-wide and regional shortage-occupation pages. Extraction
  requires one declared year, contiguous numbered groups, an operator-pinned expected
  group count, and exact official source URL/scope provenance.
- [x] Preserve source category titles and exact source-listed occupation aliases;
  normalize only Unicode, dash, spacing, slash, and comma presentation differences.
  No translation, fuzzy classification, embedding similarity, or LLM inference is
  allowed in deterministic lookup.
- [x] Model regional applicability with official Austrian federal-province codes
  (`AT-1` through `AT-9`) and fail closed when a regional source group has no
  recognized province list.
- [x] Make materialization immutable and idempotent: a repeated extraction from the
  same snapshot/year/scope reuses the same entry hashes, while any conflicting
  derived projection for an immutable snapshot is rejected rather than overwritten.
- [x] Add exact occupation lookup states for `matched`, `not_found`,
  `province_required`, `not_applicable_in_province`, and `ambiguous`; multiple exact
  source matches fail closed as ambiguous.
- [x] Keep source-list applicability separate from governance readiness. Lookup may
  report that a label is present in an immutable list while still returning
  `governance_ready = false` when that source has no approved certification; it never
  asserts case eligibility, qualification equivalence, job-offer sufficiency, or an
  authority outcome.
- [x] Add regulatory-intelligence API routes for controlled snapshot materialization
  and read-only exact lookup, plus regression coverage for national/regional parsing,
  province applicability, year/ordinal fail-closed behavior, ambiguity, idempotency,
  audit receipts, and pending-vs-approved certification state.
- [x] Harden the fresh-database Alembic regression for slower Windows hosts by
  increasing the subprocess wall-clock budget for the upgrade/downgrade/re-upgrade
  chain from 60 to 180 seconds. This is test-harness resilience only; it does not
  change migration logic, runtime database timeouts, or production behavior.
- [x] Apply the incremental patch to the `fbe4796` base, run focused and complete API
  verification, and record the resulting test counts.
- [x] Back up persistent PostgreSQL immediately before the `0070` -> `0071` migration,
  apply `0071`, and verify the new table/index/constraint shape without modifying
  existing pathway versions or source certifications.
- [x] Materialize the live Austria 2026 Austria-wide snapshot
  `a1032556-81f1-49bf-acd6-fa8f43e45341` and regional snapshot
  `7a3503f3-dc9d-4ded-bf31-7a80738b7434`; record entry counts and deterministic
  entry-set hashes from those exact immutable snapshots.
- [x] Confirm the Austria-wide and regional 2026 source certifications remain
  `pending_review` after structuring. Structured extraction is not source approval.
- [x] Do not create or publish a new Austria skilled-worker pathway version in this
  slice; the external-human validation gate and genuine independent-review gates
  remain held.


- [x] Applied `0071_structured_shortage_occupation_evidence` to persistent
  PostgreSQL after verified custom-format backup
  `C:\Users\Bennet Allryn\Downloads\gmai-postgres-before-0071-20260810-135554.dump`
  (3,637,418 bytes; SHA-256
  `7355C9A9C18A61E2FD261AF9333FDEC4B0FDDBAAF660F3CA0996458758C95FB6`).
- [x] Post-patch validation passed with **39 focused tests** and **571 complete
  API tests**, with one existing Starlette TestClient/httpx deprecation warning;
  the complete local quality gate passed.
- [x] Materialized immutable Austria 2026 shortage evidence into **64 national**
  and **66 regional** structured occupation groups.
- [x] National entry-set SHA-256:
  `43f1b9fad49777a89da280395124a6d3e4608219b835d144765f47e148d00301`.
- [x] Regional entry-set SHA-256:
  `5fd467b7bb3d1681dcf90f604d648af83483dfec443e4ae1d6bc5faf8e7bc238`.
- [x] Idempotency re-run confirmed zero duplicate writes:
  national `created_count = 0`, `existing_count = 64`; regional
  `created_count = 0`, `existing_count = 66`; both entry-set hashes remained
  unchanged.
- [x] Deterministic lookup smokes returned `matched` and
  `list_applicability = true` while correctly retaining
  `governance_ready = false`.
- [x] Both Austria-wide and regional 2026 source certifications remain
  `pending_review`; structured materialization grants no source approval.
- [x] Re-verified the Austria skilled-worker pathway after materialization:
  versions 1 and 2 remain `draft`, unapproved, and unpublished. No pathway
  version was created or published by this slice.

### 13.10.2.7 Austria pathway integration of structured 2026 evidence

- [x] Reserve `national_occupation_list` and `regional_occupation_list` pathway
  evidence roles for canonical structured shortage-occupation projections. These
  roles must be `required_for_publication` and cannot be used as optional evidence
  to bypass source-certification governance.
- [x] Require each structured occupation evidence link to pin the exact materialized
  projection identity: year, scope, entry count, entry-set SHA-256, extraction
  version, and immutable source-snapshot content hash. Draft creation fails closed
  when any pinned value differs from the persisted projection.
- [x] Add a controlled structured-occupation integration workflow that clones the
  current immutable pathway version into a new draft, preserves its core route and
  Verified Rules, and adds canonical national/regional occupation-list evidence.
- [x] Require the Austria `at-rwr-skilled-worker-shortage-occupation` pathway to carry
  both structured occupation-list evidence roles before any version can publish. This
  keeps historical core-only drafts v1/v2 fail-closed instead of leaving an older
  publication path around the new evidence gate.
- [x] Make the integration idempotent by persisting a deterministic integration
  signature in pathway-version metadata. Repeating the same integration returns the
  existing draft instead of creating another version. A stale source-version branch
  is rejected rather than silently forking pathway history.
- [x] Add a read-only pathway publication-readiness endpoint that reports the
  deterministic evidence blocker plus certification status by evidence role without
  mutating or approving the pathway. Independent human review remains a separate
  publication requirement even when evidence readiness becomes green.
- [x] Add focused regressions for canonical projection binding, operator-pinned hash
  mismatch, required-for-publication enforcement, idempotency, stale-source rejection,
  pending certification hold state, and synthetic post-certification publication.
- [x] Keep Alembic head at `0071_structured_shortage_occupation_evidence`; this slice
  changes pathway integration/governance behavior and requires no database migration.
- [x] Apply the incremental patch to the clean `8eb84af` base and run focused plus
  complete API/local quality verification before any live pathway write.
- [x] Back up persistent PostgreSQL immediately before the live Austria pathway-draft
  integration even though this slice has no schema migration.
- [x] Create or idempotently reuse Austria skilled-worker pathway version 3 from
  source version `cb17657f-be9f-4ea9-b7ce-795cf0e1b1d5`, binding the existing
  `core_route` plus the immutable 2026 national and regional occupation projections.
- [x] Verify live version 3 remains `draft`, unapproved and unpublished, and that
  publication readiness is held while both 2026 supplemental source certifications
  remain `pending_review`.
- [x] Do not approve either 2026 source, publish the pathway, or release the external
  validation gate in this slice. Genuine independent review remains required.

#### Phase 13.10.2.7 closure evidence

- [x] Focused verification passed with **14 tests**. Complete API verification
  passed with **577 tests**, with only the existing Starlette TestClient/httpx
  deprecation warning; the complete local quality gate passed.
- [x] No schema migration was introduced. Persistent PostgreSQL remained at
  `0071_structured_shortage_occupation_evidence`.
- [x] The canonical PostgreSQL backup immediately before the first successful
  live pathway-v3 write is
  `C:\Users\Bennet Allryn\Downloads\gmai-postgres-before-at-pathway-v3-20260811-022050.dump`
  (3,673,174 bytes; SHA-256
  `590342DB52783D804034D3F5C36F97B9910897F482E7E6FCB794682DDA494383`).
- [x] Created Austria skilled-worker pathway version 3
  `35412414-2cfd-489b-8731-c375d41d6f52` from version 2
  `cb17657f-be9f-4ea9-b7ce-795cf0e1b1d5`. Version 3 remains `draft`,
  with no `approved_by` value and no `published_at` value.
- [x] Version 3 carries exactly three required publication evidence roles:
  `core_route`, `national_occupation_list`, and `regional_occupation_list`.
  The structured roles pin the existing immutable 2026 national snapshot
  `a1032556-81f1-49bf-acd6-fa8f43e45341` and regional snapshot
  `7a3503f3-dc9d-4ded-bf31-7a80738b7434`.
- [x] Publication-readiness evaluation remains fail-closed:
  `ready = false` and `requires_independent_reviewer = true`.
  `core_route` is approved, while both `national_occupation_list` and
  `regional_occupation_list` remain `pending_review`.
- [x] Idempotency re-run returned `created = false` for the same version
  `35412414-2cfd-489b-8731-c375d41d6f52`. A direct database check confirmed
  exactly three pathway versions exist; no version 4 was created.
- [x] Neither 2026 supplemental source was approved, no pathway version was
  published, and the genuine independent-review/external-validation gates
  remain held.

### 13.10.2.8 Independent review readiness and certification evidence packs

- [x] Add a deterministic reviewer-facing evidence pack for source certifications that
  have structured shortage-occupation projections. The pack binds the certification,
  jurisdiction, authority, official source, immutable source snapshot, declared
  year/scope, extraction version, entry count, entry-set SHA-256, and every structured
  occupation row without inferring case eligibility.
- [x] Include the immutable source text alongside the structured rows so a reviewer can
  perform a source-to-projection comparison. The deterministic pack SHA-256 is computed
  from canonical evidence identity/content rather than from mutable review status.
- [x] Fail closed when a source has multiple structured projections unless the reviewer
  pins the exact `source_snapshot_id`; a certification review must not silently choose
  among multiple years or snapshots.
- [x] Require an explicit independent-human attestation plus the exact deterministic
  evidence-pack SHA-256 before any certification backed by structured occupation data can
  be approved or rejected. Reviewer/proposer identity separation is case-insensitive.
- [x] Preserve the existing review path for certifications with no structured projection,
  avoiding an unrelated migration or forced retrofit of historical source reviews.
- [x] Record structured review evidence in the durable audit log, including reviewer,
  decision, pack version/hash, pinned source snapshot, structured projection identity,
  and human attestation. The source certification remains the only explicit approval
  action; generating a review pack grants no approval.
- [x] Aggregate pathway publication-readiness blockers instead of exposing only the first
  source-certification failure. Austria v3 can therefore report both national and
  regional pending-review blockers at the same time while remaining fail-closed.
- [x] Keep Alembic head at `0071_structured_shortage_occupation_evidence`; this slice
  changes review/readiness behavior and requires no database migration.
- [x] Apply the incremental patch to clean base `b61ddd7`, run focused tests, then run the
  complete API/local quality gate before restarting the host API.
- [x] Restart the host API and materialize read-only reviewer packs for the live Austria
  2026 national and regional certifications. Record each exact pack SHA-256 and confirm
  the packs pin the already materialized 64/66-entry projections.
- [x] Confirm both live 2026 certifications remain `pending_review`, Austria pathway v3
  remains draft/unapproved/unpublished, and publication readiness reports both structured
  certification blockers after pack generation.
- [x] Do not submit the independent-human attestation, approve/reject either certification,
  publish v3, or release the external-validation gate unless a genuine separate human
  reviewer personally performs the review.

#### Phase 13.10.2.8 closure evidence

- [x] Focused and complete verification passed. The complete API suite reached
  **583 passed**, with only the existing Starlette TestClient/httpx deprecation
  warning, and the complete local quality gate passed.
- [x] No database migration or live regulatory write was required. Persistent
  PostgreSQL remained at `0071_structured_shortage_occupation_evidence`.
- [x] Generated a deterministic independent-review evidence pack for Austria's
  2026 national shortage-occupation source certification
  `599f7ce7-b85e-4d02-b3ca-ea17b75aba84`, covering all **64** structured
  national entries.
- [x] National independent-review pack SHA-256
  `b8073504eef684a1d02c5e99efb16c9bf1225c89c807196ce103b0bb9b9cffe7`.
- [x] Generated a deterministic independent-review evidence pack for Austria's
  2026 regional shortage-occupation source certification
  `f4cf5f04-0519-4cad-b5c2-88ec1183ded5`, covering all **66** structured
  regional entries.
- [x] Regional independent-review pack SHA-256
  `46f4b74a379aaea9a3bd90f1da14166a1ea408842020cf2b700059ff8687920d`.
- [x] Review-pack generation remained read-only. Both exact certifications
  remained `pending_review`; no independent-human attestation was submitted.
- [x] Austria skilled-worker pathway version 3
  `35412414-2cfd-489b-8731-c375d41d6f52` remained `draft`, unapproved and
  unpublished.
- [x] Publication readiness remained fail-closed with
  `ready = false` and `requires_independent_reviewer = true`. Readiness now
  aggregates both outstanding required-evidence blockers:
  `national_occupation_list` and `regional_occupation_list`.
- [x] The generated review packs are preparation artifacts only. Certification
  approval remains reserved for a genuine separate human reviewer who personally
  reviews the exact evidence pack.


### 13.10.2.9 Independent review workflow UX and audit closure

- [x] Add a dedicated `/source-certification-review` operator workspace for structured
  source certifications instead of forcing independent reviewers through generic
  registry controls.
- [x] Add a deterministic read-only structured certification review queue that exposes
  pending certification identity, jurisdiction/authority/source provenance, available
  immutable projections, exact pack readiness, authenticated reviewer identity conflict,
  and whether submission is currently allowed.
- [x] Add a bounded review-workspace API that returns the exact deterministic evidence
  pack plus explicit submission requirements and durable review history from the existing
  audit log. The workspace performs no certification mutation.
- [x] Preserve fail-closed multi-projection behavior in the UX: when more than one
  structured projection exists, no review pack or submission is available until the
  reviewer pins an exact `source_snapshot_id`.
- [x] Require the reviewer UI to confirm the exact 64-character deterministic pack
  SHA-256, enter substantive review notes, and explicitly attest genuine independent
  human review before the existing certification-review endpoint can be submitted.
- [x] Display immutable source text and structured entries side-by-side, expose the
  source ordinal/aliases/province mapping/entry hash, and allow downloading the exact
  JSON review pack for offline inspection without changing review state.
- [x] Surface durable review audit receipts in the same workspace after a decision,
  including actor, decision, notes, attestation state, exact pack hash, snapshot, and
  structured projection identity.
- [x] Keep certification approval and pathway publication separate. A successful source
  review does not publish Austria pathway v3 or release the external-validation gate.
- [x] Keep Alembic at `0071_structured_shortage_occupation_evidence`; reuse the existing
  certification and audit-log tables rather than introducing a migration for presentation
  or derived review state.
- [ ] Apply the incremental patch to clean base `934b073` and run focused API tests plus
  the complete API/local quality gate including the Next.js production build.
- [ ] Restart the host API and perform a read-only live smoke of the Austria 2026 review
  queue/workspaces. Confirm the national pack hash remains
  `b8073504eef684a1d02c5e99efb16c9bf1225c89c807196ce103b0bb9b9cffe7` and the regional
  pack hash remains `46f4b74a379aaea9a3bd90f1da14166a1ea408842020cf2b700059ff8687920d`.
- [ ] Confirm the live smoke leaves both certifications `pending_review`, pathway v3
  `draft`, and the publication/external-validation gates held.
- [ ] Do not use the new submission UI to approve or reject either live Austria source
  unless a genuine separate human reviewer personally completes the exact pack review.

#### Phase 13.10.2.9 closure evidence

- [x] Complete verification passed with **589 API tests** and the complete local
  quality gate. The only warning remained the existing Starlette
  TestClient/httpx deprecation warning.
- [x] No schema migration or live regulatory write was introduced. Persistent
  PostgreSQL remained at `0071_structured_shortage_occupation_evidence`.
- [x] Added the dedicated `/source-certification-review` workspace with
  structured-review queue, deterministic evidence-pack inspection, exact
  source/projection comparison, pack download, reviewer identity controls,
  explicit pack-hash confirmation, human attestation controls, and review
  history/audit presentation.
- [x] Read-only Austria reviewer-workspace smoke passed with exactly two pending
  structured source certifications in the queue.
- [x] National certification
  `599f7ce7-b85e-4d02-b3ca-ea17b75aba84` remained `pending_review`; its
  workspace reported pack state `ready`, **64 entries**, zero review-history
  entries, and deterministic pack SHA-256
  `b8073504eef684a1d02c5e99efb16c9bf1225c89c807196ce103b0bb9b9cffe7`.
- [x] Regional certification
  `f4cf5f04-0519-4cad-b5c2-88ec1183ded5` remained `pending_review`; its
  workspace reported pack state `ready`, **66 entries**, zero review-history
  entries, and deterministic pack SHA-256
  `46f4b74a379aaea9a3bd90f1da14166a1ea408842020cf2b700059ff8687920d`.
- [x] Austria skilled-worker pathway version 3
  `35412414-2cfd-489b-8731-c375d41d6f52` remained `draft`, with
  `publication_ready = false` and `requires_independent_reviewer = true`.
- [x] Publication readiness continued to expose both outstanding required
  evidence blockers: `national_occupation_list` and
  `regional_occupation_list`, while `core_route` remained approved.
- [x] Pre-smoke and post-smoke database hold-state checks were identical:
  national 2026 structured entries remained **64**, regional remained **66**,
  both certifications remained `pending_review`, and pathway version 3
  remained draft.
- [x] The smoke performed no certification review, source approval, pathway
  publication, or external-validation release. A live decision remains reserved
  for a genuine separate human reviewer who personally reviews the exact pack.


## 10. Historical Evidence

- Release-level history: [CHANGELOG.md](CHANGELOG.md)
- Canonical product scope: [GLOBAL_MOBILITY_AIOS_VISION_V1.md](GLOBAL_MOBILITY_AIOS_VISION_V1.md)
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Security baseline: [SECURITY_AND_COMPLIANCE.md](SECURITY_AND_COMPLIANCE.md)
- Agent organization target:
  [AI_ORGANIZATION_GOVERNANCE_V13_0.md](AI_ORGANIZATION_GOVERNANCE_V13_0.md)
- Feature-specific evidence: versioned documents under `docs/`
- Exact implementation history: Git commits and Alembic migrations
