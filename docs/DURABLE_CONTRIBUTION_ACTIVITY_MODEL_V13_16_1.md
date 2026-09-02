# Phase 13.16.1 Durable Contribution and Activity Model

**Phase status:** IMPLEMENTATION IN PROGRESS — DESIGN, 13.16.1A PERSISTENCE,
13.16.1B COMMAND/SERVICE LAYER, AND 13.16.1C AUTHENTICATED ORGANIZATION API COMPLETE

**Design baseline:** `409b8953290a0286a99fde3c760dce569fb3878b`

**Current migration head:** `0074_durable_contribution_activity_model`

**Scope:** authoritative design plus completed 13.16.1A persistence, 13.16.1B
internal command/service, and 13.16.1C authenticated HTTP/API slices

## 1. Purpose and invariant

Phase 13.16.1 defines the durable data boundary required before the Organization
Observatory, department workspaces, dependency views, or owner inbox can report
organizational performance. Slice 13.16.1A implements models and migration `0074`.
Slice 13.16.1B implements the internal, HTTP-independent command boundary. Slice
13.16.1C exposes that boundary through authenticated, tenant-scoped REST schemas and
routes. No real domain Contribution emitters, Observatory/read model, workflow
changes, or UI are implemented yet.

The 13.16.1B authority policy is deliberately narrow. A terminal, attributed
`ExecutiveDecision` in `approved` or `rejected` state is the only currently enabled
source for a validated `AuthoritativeOutcomeDescriptor`. Agent/workflow execution,
tool/LLM calls, AuditLog, retries, messages, and UI interaction are explicitly
rejected as Contribution authority. Plausible domain records remain disabled until
their individual adapters receive review.

`HumanAction` requires an authenticated internal `human` whose actor ID matches the
authenticated user. The separate `external_human` identity does not qualify in this
slice: the repository has no authenticated external-human attestation contract, and
the 0074 database constraint permits only `human`. Phase 13.17 remains the required
acceptance boundary for genuine external-human behavior.

The governing invariant is:

> A successful agent execution creates an Activity only. It must never create a
> Contribution automatically. A Contribution may be created only from an explicit,
> authoritative domain outcome that passes the contribution source adapter for its
> outcome type.

Therefore:

- `AgentRun.completed`, `AgentRun.pending_review`, successful Celery work,
  `OrganizationExecutionAttempt.completed`, completed delegation, completed
  `OrganizationalActionOutput`, and `AuditLog` are not Contributions.
- `OrganizationalWorkItem.completed` proves governed work execution, not a business
  outcome or impact.
- An approved recommendation or Decision is not a Contribution until an authoritative
  affected domain record proves the stated outcome.
- Activity, tool-call, token, message, and retry volume are never organization-success
  metrics.
- Every Contribution identifies the authoritative source object, source version/state,
  accountable department/position, authority, evidence, and supported impact.

## 2. Inspection basis

This design was derived from the current repository, including:

- `AGENTS.md`, `ROADMAP.md`, `CHANGELOG.md`, the v13.0 governance contract, the
  v13.16.0 design/IA foundation, governed automation, audit, controlled-agent,
  agent-review, architecture, data-model, security, and validation documentation;
- every relevant SQLModel entity in `models/domain.py`;
- organization, controlled-agent, automation, audit, external-validation, assessment,
  evidence, and domain schemas/services/routers/tasks/tests;
- Board Room, agent review/console, and Automation web/API-client surfaces;
- organization and controlled-agent role cards and registry contracts; and
- migrations `0056` through current head `0073`, especially organization-ledger
  constraints, execution fencing, and `0072` idempotency conventions.

## 3. Current-state findings

| Existing record | It answers | Phase 13.16.1 classification |
|---|---|---|
| `WorkflowRun` | Did a workflow run and route? | Raw workflow telemetry |
| `AgentRun` | Did a bounded agent produce review-gated output? | Raw agent telemetry; Activity source only |
| `OrganizationExecutionAttempt` | Was work claimed, retried, completed, or failed? | Raw execution telemetry; Activity source only |
| `DelegationRecord` | Which position delegated which task? | Work provenance |
| `OrganizationalActionOutput` | What internal evidence-bearing analysis was recorded? | Work output; never Contribution by itself |
| `OrganizationalWorkItem` | What governed objective is being executed? | Reuse as WorkItem |
| `ExecutiveDecision` | What L3/L4 decision is pending or decided? | Reuse as Decision |
| `RiskEscalation` | What material risk is escalated/contained? | Risk, not general Blocker |
| `AutomationEvent` | What corporate domain event entered automation? | Domain event and Activity source |
| `AutomationDelivery` | Was an approved delivery attempted/reconciled? | Delivery ledger; not outcome proof by itself |
| `AuditLog` | Who changed what, why, and from where? | Audit trail, not Activity or Contribution |
| Domain/validation records | What regulated/operational state is true? | Possible Contribution source when allowlisted |

The Board snapshot currently reports positions, queued work, pending decisions, and
open risks. “Recent organizational work” is a work feed, not an authoritative outcome
feed. Organization execution can validly complete delegations, outputs, attempts, and
routine WorkItems while recording `external_action_authorized=false`. That proves why
execution completion must remain separate from contribution.

### 3.1 Why activity cannot stand in for work or contribution

Activity is cheap and implementation-dependent: retries, fan-out, model/provider
choice, tool granularity, and logging policy can multiply records without advancing an
objective. Conversely, one human attestation or authority submission can be a material
outcome with little execution telemetry. Counting Activity therefore rewards noisy
implementation, obscures failed/replayed work, and can falsely claim regulated or
commercial progress. Work comes from WorkItem state; outcomes come from Contribution;
runtime volume remains separately labelled telemetry.

### 3.2 Existing constraint parity

Migrations define unique constraints that are absent from some current SQLModel
`__table_args__`: position `(position_key, version)`, decision key, risk key, Board
packet key, organization control key, action-output key, and execution attempt
key/token. Migrated databases retain them; fresh `metadata.create_all()` databases do
not derive all of them. Implementation must restore model/migration parity without
recreating already-present database constraints in migration `0074`.

## 4. Persistent-entity inventory

All listed IDs are UUID primary keys unless stated otherwise. Current FKs use default
restricting/`NO ACTION` behavior. JSON fields are encoded strings. “Mutable” below
means audited lifecycle mutation, not untracked overwrite.

Model-to-table names are: `WorkflowRun -> workflow_runs`, `AgentRun -> agent_runs`,
`HumanReview -> human_reviews`, `AuditLog -> audit_logs`, `OrganizationPosition ->
organization_positions`, `OrganizationalWorkItem -> organizational_work_items`,
`OrganizationExecutionAttempt -> organization_execution_attempts`,
`DelegationRecord -> delegation_records`, `OrganizationalActionOutput ->
organizational_action_outputs`, `ExecutiveDecision -> executive_decisions`,
`ExecutiveCouncilConsultation -> executive_council_consultations`, `RiskEscalation ->
risk_escalations`, `BoardPacket -> board_packets`, `OrganizationControl ->
organization_controls`, and otherwise the plural snake-case table stated by the model
family below.

### 4.1 Execution, audit, and human review

| Entity | Fields, identity, and links | Lifecycle / gap |
|---|---|---|
| `WorkflowRun` | optional `lead_id`; workflow name, status, intent, route, input/output/error, start/completion | Mutable telemetry. No idempotency, tenant, department, position, authority, or outcome semantics. |
| `AgentRun` | optional workflow/lead FKs; agent, task, status, input/output, created | Mutable run/review state without updated/completed time or idempotency. Activity source only. |
| `HumanReview` | optional lead/truth/workflow/regulatory-change FKs; type, status, priority, reason/notes, timestamps | Existing generic review queue. Lacks organization assignment, due/ack/completion actors, authority, tenant, and idempotency. Retain for its flows. |
| `AuditLog` | actor/action/entity type/string ID, before/after JSON, reason/source/created | Append-oriented evidence with polymorphic target. Mutation audit, not organization timeline. |

### 4.2 Existing organization ledgers

| Entity | Fields, identity, and links | Lifecycle / gap |
|---|---|---|
| `OrganizationPosition` | position key/title/department/reporting/role card/authority/contract/status/version, actor/timestamps, suspension | Mutable/versioned contract. Migration unique `(position_key, version)`. Reuse. |
| `OrganizationalWorkItem` | unique idempotency key; optional automation event, lead, corporate account/case FKs; title/objective, department/authority/status/assignee/risk; emergency/deadlines/escalation; attempt/token/retry/error/cancellation; context/output; actors/timestamps | Reuse. Strong execution lifecycle. Missing tenant/type/phase/objective, dependencies/parent, fingerprint, profile/application, and source version. Completion is not contribution. |
| `OrganizationExecutionAttempt` | migration-unique attempt key/token; work FK; number/status/actor/start/completion/error | Append-oriented attempt telemetry. |
| `DelegationRecord` | work FK; delegator/delegate/task/authority/status/string result ref/timestamps; model unique work+delegate | Mutable work provenance. Result ref is not FK. |
| `OrganizationalActionOutput` | migration-unique key; work/delegation FKs; position/authority/evidence/confidence/impact/rollback/output/status/timestamps | Recoverable internal output. Current “impact” is expected workflow effect, not measured impact. |
| `ExecutiveDecision` | migration-unique key; optional work FK; authority/requester/owner; question/recommendation/alternatives/evidence/impact; status/coordination lease/result/deadline/timestamps | Reuse. Missing tenant/subjects/source version/type/supersession/expiry/conditions/effect. Approval is not execution. |
| `ExecutiveCouncilConsultation` | unique key; decision/work FKs; requester/consulted positions, domain/evidence/recommendation/confidence/dissent/status/timestamps | Durable decision evidence/dissent, not Decision or Contribution. |
| `RiskEscalation` | migration-unique key; optional work FK; category/severity/title/description/evidence/containment/positions/status/Board/emergency/timestamps | Preserve as Risk. May open/reference a Blocker; not its alias. |
| `BoardPacket` | migration-unique key; type/period/summary/content/status/preparer/published/timestamps | Derived briefing snapshot, not source truth. |
| `OrganizationControl` | migration-unique key; status/reason/actor/timestamps | Global runtime control. Changes emit Activity and AuditLog. |

### 4.3 Automation and corporate work

| Entity | Fields, identity, and links | Lifecycle / gap |
|---|---|---|
| `AutomationEvent` | unique idempotency key; corporate account/case FKs; event/entity type+ID/source/payload/status/occurred/creator | Append-oriented ingress. Strong Activity candidate; not automatic Contribution. |
| `AutomationDelivery` | event/rule/connector FKs; channel/destination/payload/status; review/dispatch/provider/retry/reconciliation/timestamps | Mutable outbox. Transitions emit Activity. Provider acceptance alone may not be a business outcome. |
| `CorporateMobilityCase` | corporate account/optional lead; unique case reference; type/status/countries/sponsor/dates/review/notes/actors/timestamps | Authoritative corporate subject and allowlisted outcome source. |
| `CorporateComplianceEvent` | case FK; type/title/due/status/evidence/review/completion/actors/timestamps | Verified completion may source Contribution; creation is Activity/work. |
| `CorporateRelocationTask` | case/self-dependency FKs; title/category/status/owner/due/approval/notes/submission/completion/actors/timestamps | Existing case-specific work. Keep distinct or explicitly project/link; do not replace. |
| `CorporateRelocationTaskDecision` | task FK; decision/reason/reviewer/created | Append-only domain approval evidence, not ExecutiveDecision. |

### 4.4 Mobility, evidence, and validation outcomes

| Entity/family | Fields and links relevant here | Classification |
|---|---|---|
| `Lead`, `Profile` | Individual identity/facts/status; Profile links lead/predecessor with version/lifecycle/readiness/consent/evidence | Primary subject. Pin profile version when outcome depends on it. Completeness change alone is not contribution. |
| `ApplicationRecord` | optional lead; domain/country/target/status/risk/created | Authoritative application subject; qualifying verified transitions may source Contribution. |
| `AuthorityAppointment` | application; type/authority/location/schedule/status/reference/actors/timestamps | Scheduling is Activity; verified completion may be Contribution through adapter. |
| `AgencySubmission` | application; authority/channel/submission time/reference/tracking/status/actors/timestamps | Strong outcome source after transition/reference validation. Drafting is not submission. |
| `EligibilityAssessment` | lead, optional agent/profile/version; country/domain/score/confidence/status and assessment evidence/timestamps | Candidate only when an explicit adapter validates review and pinned provenance. AgentRun is supporting telemetry. |
| `MobilityPathway`, `MobilityPathwayVersion` | stable pathway/catalogue; version predecessor/source/snapshot/lifecycle/rules/evidence/review/publication | Approved/published version may source contribution. Draft/simulation may not be production outcome. |
| `MobilityPathwayVersionEvidence` | version/source/snapshot FKs, role/publication requirement/metadata; unique identity | Authoritative evidence join; reference, do not copy. |
| `PathwayComparisonAssessment` | lead/profile/pathway/version; status/comparison/cost/risk/alternatives/gaps/review/generator/created | Case context; adapter must validate status, versions, evidence, and review. |
| `ReassessmentAcceptance` | unique key; lead/baseline/profile/generated-assessment; accepted versions/impacts, attestation/status/actor/times | Explicit human/domain outcome; strong HumanAction/Contribution source candidate. |
| `CountryRankingAssessment` | unique key; lead/profile/version; status/input hash/scope/ranking/attestation/readiness/review | Only its bounded stored claim; never infer global completeness/approval. |
| `MobilityScenario`, `MobilityScenarioStage` | lead/profile, status/consent/assumptions/comparison; ordered country/pathway/version stages/dependencies | Simulation Activity/work context; never production contribution. |
| `MobilityTimeline`, `MobilityTimelineMilestone` | lead/profile/scenario, status/strategy/horizon; ordered milestone state/dates/evidence/dependencies | Verified milestone completion may source contribution; projected date may not. |
| `TruthClaim`, `SourceReference` | lead/workflow claim verdict/confidence/review; cited source URL/type/retrieval | Evidence/claim state. Supports a source object; not organization contribution alone. |
| `VerifiedRule`, `SourceSnapshot`, `RegulatoryChange` | source/jurisdiction/snapshot/predecessor/lifecycle/review/publication and change state | Authoritative regulatory provenance. Approved publication/change processing may source Contribution; retrieval/classification is Activity. |
| `ExternalValidationScenario` | unique key, jurisdiction/domain/persona/objectives/evidence/status/source/timestamps | Definition, not outcome. |
| `ExternalValidationRun` | unique key; scenario/lead/comparison; status/gate reasons/interventions/workflow/evaluation | Deterministic passed gate may source bounded validation Contribution. |
| `ExternalValidationReview` | run; unique run/reviewer type; external identity/attestation/ratings/correctness/traceability/findings/feedback/time | Authoritative external-human evidence and HumanAction completion candidate. |
| `ExternalValidationFinding` | run/review; severity/category/status/remediation/resolution/Board acceptance/timestamps | May source/synchronize Blocker; remains validation authority. |
| `ExternalValidationEvidence` | run/finding; type/polymorphic entity/label/URL/metadata/actor | Existing provenance link; reference, do not copy. |

Document verification/intelligence, review-specific decision tables, authority
checklists, source certifications, and regulatory proposals follow the same rule:
their record remains authoritative and 13.16.1 references its qualifying state.
Heterogeneous domain decisions are not collapsed into a generic Decision table.

## 5. Six canonical concepts

### 5.1 Activity

Immutable, ordered statement that something organizationally relevant happened:
work queued, execution completed, decision returned, blocker opened, human action
acknowledged, contribution verified, or delivery reconciled. It is not a raw tool
call/log/heartbeat, proof of impact, mutable state, or substitute for AuditLog.

Append once. A correction is a new row with `supersedes_activity_id`. Ordering is
strict per tenant/stream. Cross-stream presentation sorts by occurrence, insertion,
then UUID and does not claim causal order.

### 5.2 Contribution

Attributable, evidence-linked, verified organizational outcome. It states what
changed in the authoritative domain, accountable department/position, objective or
phase, supported impact, evidence, and outstanding human action.

Contribution rows are immutable and append-only. A proposal belongs in WorkItem,
Decision, or HumanActionRequest, not in the authoritative Contribution ledger. An
adapter inserts an `outcome` record only after explicit verification. Correction or
withdrawal appends a `supersession` or `retraction` record that points to the prior
Contribution. The read model treats an outcome as active only when no later valid
supersession/retraction targets it. Historical rows are never status-updated.

### 5.3 WorkItem

Reuse `OrganizationalWorkItem`: accountable governed work with assignment, authority,
risk, deadlines, bounded execution, retry, cancellation, and completion. Preserve
current states `queued`, `running`, `retry_wait`, `held`, `pending_ceo`,
`pending_board`, `completed`, `failed`, `cancel_requested`, and `cancelled`.
Completion is a work metric only.

### 5.4 Decision

Reuse `ExecutiveDecision` for organizational L3/L4 authority. Domain review decisions
stay in their typed tables. Preserve pending/coordinating/approved/rejected/returned
states and add `superseded` and `expired`. Approval authorizes or accepts the described
decision; it does not prove execution or impact.

### 5.5 Blocker

Current impediment materially gating WorkItem, Decision, Contribution verification,
or domain subject. Risk is exposure; Blocker is a presently gating condition. A Risk
may open a Blocker and a Blocker may cite risks/findings.

Lifecycle: `open -> mitigated|resolved|waived|superseded`. Mitigated remains active
until terminal. Waiver requires explicit human authority and never erases source risk.

### 5.6 HumanAction

Immutable record of an explicit authenticated human intervention: reviewed, approved,
rejected, requested changes, attested, acknowledged, assigned, reassigned, resolved,
declined, or cancelled. It is not every human-originated audit event. A separate
HumanActionRequest support record carries assignable attention lifecycle
`required -> acknowledged -> in_progress -> completed|declined|cancelled|expired`.
Each transition that reflects an actual intervention appends a HumanAction. A human
act does not automatically resolve Blocker or create Contribution/Decision.

### 5.7 Domain invariants

1. Activity never implies Contribution.
2. Only an allowlisted authoritative source adapter writes Contribution.
3. WorkItem completion, Decision approval, HumanAction, and Blocker resolution remain
   separate facts even when one causes another.
4. Domain-specific regulated decisions/evidence remain authoritative in their own
   tables; organization records reference them.
5. Immutable records are corrected by append-only supersession/retraction.
6. Lifecycle changes are authorized, audited, and represented as Activity.
7. Direct FKs carry material common relationships; generic references are validated
   provenance edges, never an integrity shortcut.
8. Tenant/authority boundaries fail closed and agent identity never satisfies a
   human-only action.

## 6. Exact proposed database model

Use SQLModel with explicit SQLAlchemy unique/check constraints. UUIDs use `sa.Uuid()`,
timestamps `sa.DateTime(timezone=True)`, JSON encoded strings, and measurements
`sa.Numeric(18,4)` rather than float. All FKs use `RESTRICT/NO ACTION`; none cascade.

### 6.1 `organization_activity_streams` (new)

- `id UUID PK`
- `tenant_key string NOT NULL`
- `stream_key string NOT NULL`
- `last_sequence bigint NOT NULL DEFAULT 0`
- `created_at`, `updated_at` timezone datetime NOT NULL

Unique `(tenant_key, stream_key)`; check sequence non-negative. PostgreSQL locks the
stream row; SQLite uses its serialized write transaction. Activity uniqueness is the
final duplicate fence.

### 6.2 `organization_activities` (new, append-only)

- identity: `id UUID PK`, `activity_key string NOT NULL`,
  `record_fingerprint char(64) NOT NULL`, `tenant_key string NOT NULL`;
- order: `activity_stream_id UUID FK NOT NULL`, `stream_sequence bigint NOT NULL`;
- semantics: `activity_class` (`domain|work|decision|blocker|human_action|contribution|operational`),
  `activity_type` versioned string, `title`, `summary` NOT NULL;
- attribution: optional `department`, `position_key`, `authority_level`; required
  `actor_type` (`human|agent|worker|system|external_human`) and `actor_id`;
- direct provenance FKs: optional work item, execution attempt, agent run, automation
  event, lead, profile, application, corporate account, corporate case;
- generic source: `source_object_type`, `source_object_id` NOT NULL and optional
  `source_object_version`;
- correlation: optional `correlation_key`, `causation_activity_id` self FK,
  `supersedes_activity_id` self FK;
- `payload_json NOT NULL DEFAULT '{}'`, `occurred_at`, `created_at`, `created_by`;
  deliberately no `updated_at` because immutable.

Unique `(tenant_key, activity_key)` and `(activity_stream_id, stream_sequence)`;
checks for sequence >=1, allowed class/authority, 64-character fingerprint, and no
self-supersession. Index tenant/time, department/time, type/time, direct subjects,
work, agent run, correlation, source, and supersession.

### 6.3 `organization_contributions` (new)

- identity: `id UUID PK`, `contribution_key`, `record_fingerprint char(64)`,
  `tenant_key` NOT NULL;
- meaning: `contribution_type`, `title`, `outcome_summary`, `department`,
  `accountable_position_key`, `authority_level` NOT NULL; optional `objective_key`,
  `phase_key`;
- direct FKs: optional work item, decision, lead, profile, application, corporate
  account, corporate case;
- authoritative source: `source_object_type`, `source_object_id`,
  `source_object_version`, `source_state` NOT NULL;
- verification: `verification_method`
  (`domain_transition|human_attestation|deterministic_gate`), `record_kind`
  (`outcome|supersession|retraction`), required `verified_by/verified_at`, and
  `human_review_state` (`not_required|completed`);
- impact: `impact_kind` (`state_change|risk_reduction|milestone|delivery|validation|knowledge`),
  optional numeric `measured_value/baseline_value/target_value`, optional
  `measurement_unit`, `impact_json`, `evidence_summary_json`;
- `human_action_required boolean NOT NULL DEFAULT false`, `effective_at NOT NULL`;
- correction: optional `supersedes_contribution_id` self FK and `retraction_reason`;
- `created_by`, `created_at` NOT NULL; deliberately no update fields because rows are
  immutable.

Unique tenant+key and one correction per predecessor/kind. Checks exclude
telemetry/audit source types (`agent_run`,
`workflow_run`, `organization_execution_attempt`, `organizational_action_output`,
`audit_log`, `tool_call`, `message`); numeric value requires unit; retraction requires
reason and predecessor; outcome must not have predecessor; predecessor cannot be self.
Index tenant/record-kind/effective, department/effective, type/effective, objective/phase,
subjects/work/decision, source identity/version, and supersession.

### 6.4 `organizational_work_items` (reuse/extend)

Add `tenant_key NOT NULL`, `work_type NOT NULL DEFAULT 'organizational'`, nullable
`idempotency_fingerprint char(64)` for legacy compatibility but mandatory on new
writes, optional `objective_key`, `phase_key`, `parent_work_item_id` self FK,
`profile_id`, `application_id`, `source_object_type/id/version`, and
`requested_by_type/id`; add `priority NOT NULL DEFAULT 'normal'` with
`low|normal|high|critical` check. Preserve all current fields/behavior. Index
tenant+status+due, tenant+department+status, objective, phase, parent, added subjects,
and source. Audit historical status values before adding a DB status check.

### 6.5 `organization_work_item_dependencies` (new)

`id UUID PK`, key/fingerprint/tenant, work and depends-on-work FKs, dependency type
`blocks|requires|informs`, status `active|satisfied|waived|superseded`, optional
`satisfied_by_contribution_id`, waiver actor/reason/time, actors and timestamps.
Unique tenant+key and work+dependency+type; no self dependency; waiver requires human
evidence; satisfaction requires verified contribution or audited domain reference.
Index both directions and tenant/status.

### 6.6 `executive_decisions` (reuse/extend)

Add tenant, `decision_type` (`operational|policy|risk|exception|board_reserved`),
fingerprint, optional lead/profile/application/corporate account/case FKs, source
type/id/version, optional self supersession, `conditions_json DEFAULT '[]'`,
`effect_summary`, and `expires_at`. Restore migration-backed decision-key uniqueness
in model metadata. Index tenant/status/due, subjects, source, expiry, supersession.
Preserve CEO coordination fencing and Board authority.

### 6.7 `organization_blockers` (new)

`id UUID PK`; key/fingerprint/tenant; blocker type
`evidence|dependency|authority|human_input|external|safety|technical`; severity;
title/description/status; department/position/authority; optional work, decision,
contribution, lead, profile, application, corporate account/case FKs; optional risk
and external-validation-finding FKs; source type/id/version;
`requires_human_action`; opened/due/mitigated/resolved times; resolution, waiver
actor/reason; optional self supersession; actors/timestamps.

Unique tenant+key. Allowed status `open|mitigated|resolved|waived|superseded`; at
least one direct target/subject; resolved requires time/summary; waived requires
actor/reason/time; no self-supersession. Index tenant/status/severity/due,
department/status, targets, source, risk/finding, supersession.

### 6.8 Human action tables (new)

`organization_human_action_requests` is lifecycle-mutable support state: `id UUID PK`;
key/fingerprint/tenant; request type
`review|decision|attestation|acknowledgement|provide_information|approval|exception`;
title/instructions/status/priority/required role/optional assignee; requesting actor;
authority; optional WorkItem/Decision/Blocker/Contribution and common subject FKs;
source type/id/version; due/acknowledged/started/completed/declined/cancelled/expiry
actors/times; outcome/completion notes; creators/updaters/timestamps. Unique tenant+key;
terminal states require matching actor/time and outcome/reason; at least one governed
record/subject. Index tenant/status/priority/due, assignee/status/due, role, links,
and source.

`organization_human_actions` is append-only: `id UUID PK`, action key/fingerprint/
tenant, optional `human_action_request_id` FK, `action_type`
(`reviewed|approved|rejected|requested_changes|attested|acknowledged|assigned|reassigned|resolved|declined|cancelled`),
required authenticated `human_actor_id`, actor role/position/department/authority,
optional WorkItem/Decision/Blocker/Contribution and common subject FKs, source
type/id/version, `outcome`, `reason`, `metadata_json`, `occurred_at`, `created_at`,
`created_by`; no update fields. Unique tenant+action key; actor type is structurally
human and cannot be supplied as agent/system; at least a request, governed record, or
subject is required. Index tenant/occurred, human actor/occurred, action type/occurred,
request, links, and source.

### 6.9 `organization_record_references` (new, append-only)

A shared subject registry is rejected: it would duplicate Lead, Profile, Application,
and CorporateMobilityCase while still relying on polymorphic validation. Direct
common-subject FKs belong on core records.

A narrow immutable reference ledger is justified for heterogeneous evidence:
`id UUID PK`, deterministic key/fingerprint/tenant; exactly one owner FK among
Activity, Contribution, WorkItem, Decision, Blocker, HumanAction, or
HumanActionRequest; role
`authoritative_outcome|affected_subject|evidence|caused_by|supports|contradicts`;
target type/string ID/optional version/state/hash/label/URL/metadata; optional self
supersession; creator/created only. A portable `CASE` check enforces one owner.
Allowlisted adapters validate target existence, state, and tenant before insert.

## 7. Relationship map

```text
authoritative domain record
       | explicit allowlisted adapter
       v
Contribution <---- WorkItem ----> Decision
     ^              |  ^             |
     |              |  |             |
     +-- dependency-+  +-- Blocker --+
                              |
                         HumanAction

Each state transition -> Activity (ordered, immutable)
Each mutation          -> AuditLog (actor/reason/before/after)
Each evidence edge     -> OrganizationRecordReference

AgentRun / execution attempt / tool telemetry
       -> Activity only
       -X-> Contribution
```

## 8. Idempotency, ordering, transactions, retries

1. Every creation command supplies a deterministic key and canonical SHA-256
   fingerprint, following migration `0072`'s intent.
2. Same key/fingerprint returns existing without duplicate Activity/AuditLog. Same
   key/different fingerprint fails closed and records an anomaly when safe.
3. Activity keys encode source transition/version; Contribution keys encode outcome
   contract, source identity/version/state, and department.
4. Stream sequence allocation and Activity insert share a transaction. A uniqueness
   race re-reads and compares fingerprints.
5. New domain transition, Activity, and AuditLog commit together where they share the
   DB transaction. Contribution insertion, references, Activity, and AuditLog are
   atomic.
6. Legacy post-commit projection is explicitly `reconciled`, idempotent, and preserves
   source time; it never claims unavailable atomicity.
7. Celery retry, duplicate delivery, crash, and lease recovery may add raw attempts
   but cannot duplicate Activity or Contribution.

## 9. Contribution source policy

Use a closed adapter registry. Each adapter declares contract/version, authoritative
SQLModel class, qualifying/prohibited states, evidence/review/certification/gate,
attribution/impact rules, tenant/subject validation, and key/fingerprint construction.

Initial candidates for separate implementation review: verified agency submission,
evidence-backed compliance completion, approved/published regulatory or pathway
lifecycle change, verified mobility milestone, accepted reassessment, and deterministic
external-validation pass. This design does not pre-authorize all candidates.

The eventual emission points are the domain command boundaries that already persist
those outcomes: agency-submission status commands; corporate compliance/relocation
services; `mobility_timelines.py`; pathway catalogue and source-certification review
services; regulatory change/rule publication services; reassessment acceptance; and
external-validation evaluation/review services. `organization_governance.py`,
`controlled_agents.py`, `agent_tasks.py`, and generic automation delivery workers may
emit Activity, but qualify for Contribution only when a separate adapter re-reads one
of those authoritative domain records after its committed qualifying transition.

Hard exclusions: AgentRun, WorkflowRun, attempts, delegation, action outputs,
AuditLog, tool calls, messages, prompts, tokens, UI visits, enqueue results, retries,
and unreviewed/draft/simulation-only records. Controlled-agent and generic worker
services must not call the Contribution writer on execution success; a source-contract
test enforces this.

## 10. Observatory aggregation contract

| Metric | Authoritative basis | Exclusions |
|---|---|---|
| Verified contributions | immutable outcome Contributions not targeted by a valid supersession/retraction, by `effective_at` | Activity, agents, attempts, outputs, work completion |
| Active/completed work | WorkItem state and transition Activity | never labelled impact |
| Open blockers | Blocker open/mitigated by severity/owner/due | risks without gating Blocker |
| Blockers resolved | terminal Blocker transition Activity in period | current-row update time without transition evidence |
| Pending decisions | typed ExecutiveDecision/domain queues | informational updates/recommendations |
| Human attention | active HumanActionRequest plus genuine Board decisions | generic human audits; HumanAction count is shown separately as interventions |
| Human interventions | immutable HumanAction by occurred time/action type | AuditLog actor counts |
| Department throughput | completed WorkItems and active Contributions shown as two separate series; cycle time from WorkItem transition Activity | agent/tool volume and blended “productivity” score |
| Work ageing | now minus WorkItem creation/last material transition for active states | completed/cancelled work and retry count |
| Dependency bottlenecks | active dependency edges, blocked downstream WorkItems, oldest unsatisfied edge, and critical path labels | inferred co-occurrence or agent fan-out |
| Validation state | validation gate plus reviews/findings/evidence | UI/shadow prose |
| Runtime health | agents, attempts, Celery, deliveries/reconciliation | never merged into contribution |

Every aggregate returns `as_of`, timezone, filter scope, coverage start, and source
counts. Use Contribution effective time, Activity occurrence time, and labelled
current-state snapshots. Preserve department/position recorded at event time; do not
retroactively rewrite history after organization changes.

## 11. Activity and raw telemetry boundary

Activity is curated business-semantic history. Raw telemetry remains in AgentRun,
WorkflowRun, attempts, Celery/logging, delivery fields, and future tracing. It may be
linked under Technical provenance.

- one agent run with 12 tool calls -> one execution Activity, 12 raw spans, zero
  Contributions;
- retrying run -> attempt telemetry, at most one semantic completion Activity, zero
  Contributions;
- approved authority-referenced agency submission -> submission Activity and only
  after adapter validation one Contribution;
- approved Decision without execution -> Decision Activity, zero Contributions;
- passed validation with required external-human evidence -> Activity and one bounded
  validation Contribution only if that adapter is enabled.

## 12. Correction, retention, deletion

- Activity/reference are immutable; corrections append successors.
- Contribution is immutable; supersession/retraction is an appended record and the
  read model resolves the chain.
- HumanAction is immutable; HumanActionRequest is the auditable lifecycle record.
- WorkItem/Decision/Blocker/HumanActionRequest are audited state machines; material
  transitions emit Activity and AuditLog.
- Source records keep their existing version/review/lifecycle policy.
- Default governance/provenance retention is permanent pending formal policy.
- No cascades and no ordinary delete endpoints.
- Legally required erasure/redaction acts in authoritative subject systems, retains
  minimum non-personal governance tombstones and legal basis, and prevents
  re-identification without rewriting outcomes.

## 13. Authorization and tenant isolation

- Reads require organization/governance role and tenant. Mobility users receive only
  case-safe projections, never organization-wide ledgers.
- Authenticated `admin` and `operator` callers may append explicit governed Activity
  through the 13.16.1C API. The router derives actor, role, position, authority, and
  tenant from trusted request state; payloads cannot select them. This is an explicit
  command boundary, not automatic domain emission.
- Invoking a Contribution adapter requires operator authority; its immutable outcome
  is inserted only after the adapter validates configured domain reviewer/executive/
  Board authority. Supersession/retraction requires the same or higher authority.
  Agents cannot invoke or write the Contribution ledger.
- Blocker waiver follows the strongest linked constraint and cannot bypass Truth
  Engine, certification, legal, security, or external-human gates.
- HumanActionRequest completion requires an appended action by the assigned human or
  permitted supervisor. Agent identity cannot create HumanAction or satisfy a request.
- `tenant_key` is mandatory on new ledgers. Corporate links must agree with account;
  current local data uses authenticated tenant `default` until a tenant table exists.
- Generic targets pass allowlisted existence/state/tenant validation; client-supplied
  type/ID is never sufficient.

## 14. Migration `0074` after `0073`

Migration `0074_durable_contribution_activity_model` revises
`0073_austria_candidate_integrity` and implements the persistence plan below.

Upgrade order:

1. Preflight historic key duplicates expected to be prevented by `0056/0059/0060`.
2. Add WorkItem/Decision columns nullable or with temporary server defaults, using
   Alembic batch operations where SQLite rebuild is required.
3. Backfill only tenant `default`, work type `organizational`, priority `normal`;
   infer no Activity, Contribution, Blocker, dependency, Decision, HumanActionRequest,
   or HumanAction.
4. Make required fields non-null and remove temporary defaults.
5. Create stream, Activity, Contribution, dependency, Blocker, HumanActionRequest,
   HumanAction, and reference tables in FK-safe order.
6. Create named constraints/composite indexes and restore SQLModel parity for historic
   migration constraints without duplicating them in migrated DBs.
7. Leave existing rows and JSON untouched.

SQLite/PostgreSQL requirements: use `sa.Uuid()` and timezone datetime; named
constraints and `batch_alter_table`; no PostgreSQL-only enum/JSONB/partial index/
generated column/trigger in the first slice; portable `CASE` checks; test FK and
unique races on both; extend the fresh upgrade/downgrade/re-upgrade suite. Downgrade
drops new tables in reverse order then only new columns/indexes. It destroys new-ledger
data and is for test/recovery, not routine production rollback.

## 15. Backfill policy

`0074` performs no semantic history backfill. Existing successful agents, completed
internal analysis, approved decisions, and draft/simulation records cannot safely be
guessed into contributions.

Any later historical command must be separate, reviewed, dry-run-capable, allowlist
exact source model/state/contract, validate tenant/evidence/review/lifecycle/
publication, use deterministic keys/fingerprints, preserve source occurrence/effective
time plus later ledger insertion time, label `backfilled` and command/operator/run,
report create/skip/conflict, and prohibit telemetry/UI/prose conversion. Board review
is required before backfilled data enters headline metrics. Until then APIs expose a
coverage-start timestamp.

## 16. Authenticated API surface

Slice 13.16.1C implements typed ledger APIs in the existing
`/api/v1/organization` namespace. The pre-existing governance router already owns
`/work-items` and `/decisions`, so durable record contracts use the collision-free
`/work-items/records` and `/decisions/records` subresources without changing the
legacy routes. Observatory summary/metric routes remain unimplemented.

| Resource | Reads | Writes / authority | Filters, pagination, ordering |
|---|---|---|---|
| Activity | list/detail plus explicit `POST /activities` | authenticated operator/admin; actor and tenant are server-derived | page/page-size 50/200; newest `occurred_at`, then ID; work/class/type/correlation/actor/time filters |
| Contribution | list/detail under `/contributions`; corrections under `/{id}/corrections` | `POST` invokes only the committed terminal ExecutiveDecision validator; corrections append | page/page-size 50/200; effective time then ID; work/department/type/source filters |
| WorkItem | list/detail/create under `/work-items/records` | explicit start/block/await-human/complete/cancel/assign commands; no generic status PATCH | page/page-size 50/200; creation time then ID; status/department filters |
| Dependency | list/detail under `/work-item-dependencies` | create/satisfy/waive/supersede commands; service retains cycle, tenant, source, and waiver checks | page/page-size 50/200; creation time then ID; work/status filters |
| Blocker | list/detail under `/blockers` | open/mitigate/resolve/waive/supersede; no delete | page/page-size 50/200; creation time then ID; work/status filters |
| Human action request | list/detail under `/human-action-requests` | create/assign/acknowledge/start/complete/decline/cancel/expire; completion appends HumanAction | page/page-size 50/200; creation time then ID; status/assignee filters |
| HumanAction | list/detail plus explicit `POST /human-actions` | authenticated internal human only; no update/delete | page/page-size 50/200; occurrence time then ID; request/actor filters |
| Decision | list/detail/create under `/decisions/records` | record terminal outcome and append-only supersession; CEO/Board service authority preserved | page/page-size 50/200; creation time then ID; status/work filters |
| RecordReference | list/detail/create under `/record-references` | exactly one tenant-safe owner and an allowlisted existent target validated by the service | page/page-size 50/200; creation time then ID; target filters |

Pagination is page-based and tenant-bound with default/max page sizes 50/200.
Detail endpoints return 404 rather than disclose cross-tenant existence. Immutable
commands return the existing row on identical idempotent replay and 409 on fingerprint
conflict. The API uses existing body idempotency keys rather than inventing a second
header transport. Bulk/dashboard mutation and Observatory endpoints are not added.

Services split typed commands, contribution adapters, Activity projection, and read
aggregation rather than further enlarging the current governance service. Typed
responses avoid leaking raw JSON strings.

## 17. Implementation integration points

Implemented in slice 13.16.1A: domain models and migration `0074`.

Implemented in slice 13.16.1B: bounded command context and HTTP-independent errors;
canonical SHA-256 fingerprints and replay/conflict handling; tenant-scoped Activity,
Contribution, WorkItem, dependency, Blocker, HumanActionRequest, HumanAction,
ExecutiveDecision, and heterogeneous reference services; explicit transition
matrices; PostgreSQL stream-row locking and database uniqueness fences; validated
source descriptors; human/authority checks; and same-transaction AuditLog writes.
SQLite and isolated PostgreSQL service tests cover the command contract and rollback
atomicity.

Implemented in slice 13.16.1C: bounded Pydantic command/read/page schemas; router
registration; trusted `OrganizationCommandContext` construction from existing
authentication state; existing read/mutation RBAC; implicit local tenant `default`;
non-disclosing cross-tenant 404 behavior; centralized safe domain-error translation;
tenant-scoped indexed filters and deterministic pagination; OpenAPI generation; and
focused HTTP tests. Raw canonical fingerprints remain private; the ExecutiveDecision
response exposes only the product-safe `source_version` needed by the currently
enabled Contribution command.

Future bounded changes: 13.16.1D internal Activity integration plus reviewed real
domain Contribution adapters, followed by 13.16.1E Observatory/read aggregation. No
existing domain workflow was changed merely to populate the new ledgers, and no
generic execution path imports the Contribution writer.

## 18. Test matrix

| Area | Required coverage |
|---|---|
| Schema/migration | Metadata/Alembic parity; historic constraints; fresh SQLite cycle; upgrade from `0073`; PostgreSQL; no semantic backfill. |
| Idempotency/order | Same key/fingerprint reuse; mismatch conflict; concurrent one-row result; per-stream monotonic uniqueness; deterministic non-causal cross-stream sort. |
| Agent invariant | Sync/async success emits Activity only; queue/run/retry/fail never Contribution; static import/source boundary. |
| Contribution gate | Allowlisted source states create immutable verified outcomes; draft/unreviewed/simulation/telemetry fail; supersession/retraction append; agent cannot write. |
| WorkItem | Existing creation/execution/retry fencing/cancel/pause/holds/CEO/Board remain; completion yields zero Contribution absent source. |
| Decision | L3/L4, self-approval prohibition, leases, override/return/reject, expiry/supersession, no effect inference. |
| Blocker/Risk | Link without collapse; resolving one does not resolve other; waiver authority/reason. |
| HumanAction | Request assignment/role/tenant/lifecycle/idempotency/expiry; each intervention appends one immutable human-authenticated action; agent rejection; no automatic downstream transition. |
| References/dependencies | Exactly one owner; target existence/state/tenant; immutable succession; self/cycle/duplicate rejection; verified satisfaction/waiver. |
| Transactions/audit | Atomic state+Activity+AuditLog; rollback has no orphan; reconciliation labelled. |
| RBAC/tenant | Cross-tenant blocked; mobility user restricted; agents cannot impersonate human. |
| Aggregation | Contributions exclude telemetry/superseded/retracted; all typed metrics reconcile; time boundaries/coverage tested. |
| Backfill/regression | Stable dry run, allowlist only, times/labels/conflicts; complete API, policy, release, migration, schema, web build, Board/Agent/Automation suite. |

## 19. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Completed execution shown as impact | Source exclusions, explicit adapters, separate work/contribution metrics. |
| Polymorphic references weaken integrity | Direct common FKs plus allowlisted target adapters and immutable references. |
| Dual write loses Activity | Same transaction; idempotent labelled reconciliation at legacy boundaries. |
| Parallel generic work/decision models diverge | Reuse and extend WorkItem/ExecutiveDecision. |
| Domain statuses lose meaning | Typed source records stay authoritative; mapping only in read models. |
| Dashboard implies full history | No speculative backfill; explicit activation/coverage. |
| Dialect concurrency differs | Portable schema and dialect locking behind one tested contract. |
| PII leaks into timeline | Small summaries, references not copied payloads, tenant/RBAC/redaction. |

## 20. Rollout sequence

1. Add invariant/source-contract tests and restore historic SQLModel constraint parity.
2. Implement and test the single bounded `0074` schema migration on SQLite and
   PostgreSQL. One migration is reasonable because there is no semantic backfill and
   the new FK graph is one atomic contract; splitting would create unusable interim
   schemas.
3. Add typed Activity, Contribution, Blocker, HumanActionRequest/HumanAction,
   dependency, and reference services with transaction/idempotency tests.
4. Integrate Activity-only emission into agent, organization, automation, and human
   command boundaries.
5. Enable a small reviewed set of authoritative contribution adapters; reconcile each
   adapter against its domain table.
6. Add read APIs/aggregates, then Board packet consumption. Keep legacy Board metrics
   until reconciliation tests prove the new read model.
7. Only after all 13.16.1 gates pass, unlock 13.16.2. Historical backfill remains a
   separate Board-reviewed operation, not part of deployment.

## 21. Acceptance criteria

- All six concepts are durable, typed, attributable, tenant-scoped, evidence-linked,
  and semantically distinct.
- Successful agent execution deterministically yields zero Contributions.
- Every Contribution is an immutable record from an allowlisted authoritative source
  state; retry, correction, and retraction cannot duplicate or rewrite history.
- Existing WorkItem, Decision, Risk, domain decision, validation, automation, audit,
  and evidence semantics remain authoritative and regression-safe.
- Human-only interventions require authenticated human identity; authority/RBAC and
  cross-tenant attempts fail closed.
- Observatory aggregates reconcile to authoritative ledgers and keep runtime telemetry
  separate.
- SQLite and PostgreSQL migration/schema/idempotency/concurrency tests pass, followed
  by repository policy, release consistency, full API, and web build gates.
- No semantic history backfill, dashboard inference, or later Phase 13.16 work occurs
  before these conditions pass.

## 22. Explicit non-goals

This design neither designs nor implements role-based shells (13.16.2), Owner Control
Center (13.16.3), department workspace UI (13.16.4), dependency UI (13.16.5), decision
inbox UI (13.16.6), Mobility User redesign (13.16.7), Professional redesign
(13.16.8), evidence UX consolidation (13.16.9), final responsive/accessibility polish
(13.16.10), Phase 13.17 external-human acceptance, or Phase 14 infrastructure.

Slices 13.16.1A, 13.16.1B, and 13.16.1C create registered persistence, the internal
service contract, and its authenticated HTTP boundary. They do not create workers,
real emitters, read-model code, dashboards, semantic backfill output, new departments,
or claims of overall phase completion.

## 23. Real Contribution Emitter Mapping (13.16.1D0)

This design pass inspects the committed 13.16.1A-C persistence, command, and HTTP
contracts against the domain services that currently own governed outcomes. It is a
design-only gate: no source policy was broadened, no emitter was connected, and no
runtime behavior changed.

### 23.1 Candidate source classification

The classification is deliberately semantic. `ELIGIBLE_EMITTER_SOURCE` means the
existing domain record can support a narrowly named organizational outcome after the
transaction-composability gate is corrected; it does **not** authorize a legal or
immigration conclusion. `DEFER_UNTIL_STRONGER_GOVERNANCE` means the record is
potentially meaningful but lacks a sufficiently strong source-state, attribution,
evidence, or lifecycle contract today. `INELIGIBLE_TELEMETRY_OR_INTERMEDIATE` means
the record must not authorize a Contribution.

| Candidate source | Classification | Qualifying state / evidence | Permitted future Contribution meaning | Key reason |
|---|---|---|---|---|
| `ExecutiveDecision` | `ELIGIBLE_EMITTER_SOURCE`, but explicit-command-only | `approved` or `rejected`; `decided_by` and `decided_at`; current tenant/version validation | A specifically requested governed decision outcome was recorded | Already supported by the closed source validator. Decision remains a separate canonical fact, so every decision must not automatically count as Contribution. |
| `JurisdictionSourceCertification` | `ELIGIBLE_EMITTER_SOURCE` | `approved` or `rejected`; distinct proposer/reviewer; `reviewed_by`/`reviewed_at`; structured evidence-pack hash and independent-human attestation when the structured review contract requires them | Source-certification review completed, approved, or rejected | Strong reviewed governance outcome. `pending_review` and `superseded` never qualify as certified outcomes. |
| Published `InitialRuleAssertion` / resulting `VerifiedRule` | `ELIGIBLE_EMITTER_SOURCE` | assertion `published`, reviewed approval, `published_rule_id`, published actor/time; resulting rule has official source/snapshot provenance and `approved_by`/`published_at` | Verified regulatory rule publication completed | Publication is an explicit governed transition with immutable source/snapshot lineage. Draft/pending/approved-but-unpublished assertions do not qualify as published. |
| `RegulatoryChange` publication | `ELIGIBLE_EMITTER_SOURCE` | change `published`; prior review complete; `reviewed_by`, `reviewed_at`, `published_at`; resulting verified-rule lineage | Reviewed regulatory change publication completed | The publication boundary is material and source-controlled. Detection, classification, and pending review are Activity/intermediate state only. |
| `MobilityPathwayVersion` publication | `ELIGIBLE_EMITTER_SOURCE` | `lifecycle_status == "published"`; `approved_by`, `published_at`; publication-evidence readiness passed | Governed pathway-version publication completed | This means catalogue publication only, never applicant eligibility or visa approval. Draft/internal-simulation versions are prohibited sources. |
| `JurisdictionImmigrationAssessment` | `DEFER_UNTIL_STRONGER_GOVERNANCE` | reviewed `approved`/`rejected` with distinct proposer/reviewer | Potentially “jurisdiction assessment review completed” | The review record has durable reviewer attribution, but the current review service commits without an accompanying source-transition AuditLog. Do not promote it until that audit gap is corrected under a separate bounded change. |
| `ReassessmentAcceptance` | `DEFER_UNTIL_STRONGER_GOVERNANCE` | `accepted`, explicit user acceptance, current consent, deterministic acceptance key | Potentially “reassessment acceptance recorded” | The record is meaningful but its authority mixes user attestation with an internal `recorded_by` actor; durable external/user actor attribution is not strong enough to claim the user as the Contribution actor. |
| `ExternalValidationRun` | `DEFER_UNTIL_STRONGER_GOVERNANCE` | only `status == "completed"` and `gate_status == "passed"`, with both required external-human reviews, complete evidence, zero unsupported certainty, no unresolved critical/high findings, and all medium/low findings triaged | Potentially “external validation gate passed” | The deterministic gate is strong, but Phase 13.17 genuine external-human acceptance is still outstanding and durable external-human identity is intentionally not accepted by `OrganizationHumanAction`. Do not enable this adapter before that governance boundary is satisfied. |
| `CorporateComplianceEvent` | `DEFER_UNTIL_STRONGER_GOVERNANCE` | completed with reviewer/evidence requirements actually satisfied | Potentially “compliance event verified complete” | The current row has completion actor/time but no typed evidence/review linkage sufficient to prove the required evidence was governed. |
| `MobilityTimelineMilestone` | `DEFER_UNTIL_STRONGER_GOVERNANCE` | completed; all dependencies complete; human approval where required; stage-specific evidence contract | Potentially an allowlisted milestone completion | Generic milestone completion is too broad. Stage-specific adapters must define what evidence and approval make the milestone material. |
| `AgencySubmission` / `AuthorityAppointment` | `DEFER_UNTIL_STRONGER_GOVERNANCE` | verified authority receipt/attendance state, not merely an operator-entered status | Potentially verified submission/appointment completion | The present status machines record operational progress but do not always prove external-authority receipt or attendance. They remain Activity/work until a stronger verification contract exists. |
| `EligibilityAssessment` | `INELIGIBLE_TELEMETRY_OR_INTERMEDIATE` | none in the current model | none | Generated assessment with no authoritative reviewer/version contract; may be linked to `AgentRun`. It must never mean visa/permit approval. |
| `PathwayComparisonAssessment` | `INELIGIBLE_TELEMETRY_OR_INTERMEDIATE` | none in the current model | none | Generated comparison, often `needs_profile_review`/`ready_for_review`, with `human_review_required`; no authoritative review completion field. |
| `CountryRankingAssessment` | `INELIGIBLE_TELEMETRY_OR_INTERMEDIATE` | none in the current model | none | Reviewed-catalogue ranking is still a generated decision-support artifact, not an authoritative organizational outcome or legal conclusion. |
| `SourceSnapshot`, retrieval/check/classification runs | `INELIGIBLE_TELEMETRY_OR_INTERMEDIATE` | none by themselves | none | Capturing or classifying evidence is Activity/provenance. Verification/publication occurs in separate governed records. |
| `ExternalValidationReview` / `ExternalValidationFinding` | `INELIGIBLE_TELEMETRY_OR_INTERMEDIATE` by themselves | none by themselves | none | Reviews are evidence/attestation and findings are defects/risks/blockers. The aggregate run gate, not an individual review/finding, is the potential validation outcome. |
| `AgentRun`, `WorkflowRun`, execution attempts, action outputs, tool/LLM calls, `AuditLog`, automation retries, messages, UI interactions | `INELIGIBLE_TELEMETRY_OR_INTERMEDIATE` | never | none | Execution/telemetry remains explicitly excluded by the 13.16.1B source policy. |

### 23.2 Round 6 / Austria safety pin

The current Round 6 Austria v4 state emits **zero automatic Contributions**. In
particular, no adapter may turn the current assessment into “Austria eligibility
established”, “occupation eligibility confirmed”, “source certified”, “pathway
published”, or any equivalent legal conclusion. The pinned state remains draft,
`simulation_candidate`, `INTERNAL_SIMULATION_ONLY`, not a production recommendation,
not publication-ready, unpublished, with national and regional occupation
certifications `pending_review`, the binding job offer absent/blocking, occupation
`AMBIGUOUS`, unknown-province regional result `INSUFFICIENT_INFORMATION`, qualification
mapping `UNRESOLVED`, EUR 218 government fee, 14 canonical gaps, and human review
required.

A future organizational Contribution may describe a **governed work outcome** such as
“source-certification review completed” or “pathway version published” only when the
corresponding source record actually reaches that qualifying state. That Contribution
must not be worded as applicant approval or legal eligibility.

### 23.3 Current source-policy result

The committed `validate_authoritative_outcome()` policy remains intentionally closed.
It accepts only `source_type == "executive_decision"` and requires an attributed
terminal `approved`/`rejected` decision with an exact source version. Agent/workflow
runs, attempts, action outputs, tool/LLM requests, `AuditLog`, retries, messages, and UI
activity are explicitly rejected. 13.16.1D0 does not broaden this policy.

For future adapters, the allowlist contract must include the exact model, qualifying
and prohibited states, tenant/subject check, required reviewer or publication
attribution, source-version derivation, evidence/certification gate, and deterministic
key/fingerprint construction. A caller-supplied `verified=True`-style flag can never
substitute for adapter validation.

### 23.4 Transaction composability finding — hard gate

**Classification: `REQUIRES_SERVICE_TRANSACTION_REFACTOR`.**

`create_contribution()` calls `commit_mutations()`. `commit_mutations()` flushes the
session, appends `AuditLog`, calls `session.commit()`, refreshes records, and rolls the
whole session back on exception. The correction/retraction path does the same. This
contract is correct for the standalone 13.16.1B/13.16.1C command boundary, but it is
not safe as a nested domain-emitter primitive because it takes ownership of the
caller's transaction.

The inspected source services likewise own their commits at their authoritative
transition boundaries, including `review_source_certification()`,
`publish_initial_rule_assertion()`, `publish_regulatory_change()`,
`publish_pathway_version()`, `create_reassessment_acceptance()`,
`evaluate_external_validation_run()`, `transition_milestone()`, and agency/corporate
status commands.

Calling Contribution **after** a source service commits would create an unsafe
best-effort dual write: the source could be authoritative while its Contribution is
lost. Calling the current `create_contribution()` **before** the source service's
existing commit can incidentally commit all pending source mutations in the same
SQLAlchemy session, but that is still not an acceptable composability contract: the
nested Contribution service would unexpectedly own the caller's transaction, and any
source-side work after that call could fail outside the already committed unit.

Therefore no real emitter may be wired until a bounded 13.16.1D1 transaction slice
provides a caller-owned transaction path. A durable outbox is not required for the
initial adapters because the source records, Contribution ledger, and AuditLog use the
same relational database and can commit atomically. The existing automation delivery
outbox remains a separate external-side-effect mechanism and must not be repurposed as
an organizational outcome ledger.

### 23.5 Required 13.16.1D1 transaction contract

The corrective slice should preserve the current public command behavior while adding
an internal staging primitive that does **not** commit. Conceptually:

1. the source service owns the transaction;
2. it validates and stages the authoritative source transition;
3. it stages the source transition AuditLog;
4. an allowlisted adapter validates the in-transaction source state;
5. it stages one idempotent Contribution and its AuditLog without committing;
6. the source service performs the single final `session.commit()`;
7. any failure rolls back source transition, Contribution, and both audit records.

Prefer a dedicated internal `stage_contribution(...)`/equivalent plus a standalone
wrapper that retains today's commit-on-command behavior. Do not add a casual public
`commit=False` flag that any caller can use to bypass transaction ownership. Source
services should receive similarly explicit transaction-owned integration points only
where needed.

Required rollback tests must prove:

- source transition failure leaves no Contribution;
- Contribution validation/audit failure leaves the source uncommitted;
- final commit failure leaves neither source nor Contribution committed;
- retry with the same source revision returns one Contribution and no duplicate audit;
- semantic mismatch on the same deterministic key fails closed.

### 23.5.1 13.16.1D1 implementation status

**State: COMPLETE / PASS.** The bounded D1 patch introduces a
caller-owned staging path without changing the public/API commit-on-command contract or
broadening the source allowlist. `stage_mutations()` flushes domain changes and their
`AuditLog` rows without committing, refreshing, or rolling back; the existing
`commit_mutations()` now delegates to that staging primitive and retains standalone
commit/rollback ownership.

`stage_contribution()` and `stage_contribution_correction()` are explicit internal
integration primitives. They stage one idempotent Contribution (or correction) plus its
audit and never call `session.commit()` or `session.rollback()`. The existing
`create_contribution()` and `append_contribution_correction()` wrappers retain the
13.16.1B/13.16.1C standalone behavior, including safe replay without an incidental
commit. No `commit=False` switch was added to the public command contract.

Focused D1 acceptance passed for caller-owned rollback, Contribution audit failure,
final caller commit failure, replay without duplicate audit, semantic idempotency
conflict, correction rollback, and standalone-wrapper regression. Local evidence is
8/8 focused transaction tests, 50 passed + 1 expected PostgreSQL-only skip in the
combined organization service/API/platform regression, and 722 passed + 1 expected
PostgreSQL-only skip in the complete API suite. Repository policy, release consistency,
migration consistency, and `git diff --check` pass at migration head
`0074_durable_contribution_activity_model` with 118 registered tables. 13.16.1D2 is now COMPLETE / PASS after bounded source/Contribution/audit acceptance;
13.16.1D3 publication adapters are unlocked but not started.

### 23.5.2 13.16.1D2 source-certification adapter implementation status

**State: COMPLETE / PASS.** The bounded D2 patch connects only
the authenticated `JurisdictionSourceCertification` review route to the durable
Contribution ledger. The source-certification transition remains the outer transaction
owner: reviewed state, the existing source-review `AuditLog`, one staged
`OrganizationContribution`, and its Contribution audit are committed together or rolled
back together. No post-commit best-effort write is used.

The generic authenticated `/api/v1/organization/contributions` source validator remains
ExecutiveDecision-only. D2 adds a separate sealed source-certification validator used
only by the reviewed domain adapter, so a caller cannot promote an arbitrary source or
self-assert a certification outcome. The adapter accepts only terminal `approved` or
`rejected` certification rows with distinct proposer/reviewer attribution. Structured
certifications additionally require the existing deterministic evidence-pack SHA-256,
pinned immutable source snapshot, and independent-human attestation before review can
reach the emitter. `pending_review` and `superseded` remain non-emitting states.

The source-version identity is a canonical SHA-256 over the certification identity,
version/scope/source, terminal review state, reviewer, notes, and exact review-evidence
payload. The deterministic Contribution key is
`source-certification-review:<certification-id>:v<version>:<approved|rejected>`. The
Contribution semantic is always `source_certification_review_completed`; even an
approved review is described as a governed source-review outcome and explicitly does
not establish applicant eligibility, occupation eligibility, or pathway publication.
Reviewer and admin HTTP roles are mapped to authenticated internal-human organization
contexts; operator and other roles cannot activate the emitter. Legacy direct service
calls that do not carry trusted reviewer-role context preserve their pre-D2 no-emitter
behavior, while the authenticated runtime review route supplies the trusted role.

The D2 test patch covers pending/no-emission behavior, approved and rejected structured
review emission, evidence-attestation rejection, source+Contribution+both-audits rollback
on emitter failure, unauthorized-role rollback, idempotent replay without duplicate
audit, and the legacy direct-service compatibility boundary. Acceptance passes **8/8**
focused emitter tests, **12/12** existing source-certification evidence-pack tests, **58
passed + 1 expected PostgreSQL-only skip** in the D1/organization service/API/platform
regression, and **730 passed + 1 expected PostgreSQL-only skip** in the complete API
suite. Repository policy, release consistency, migration consistency, and `git diff
--check` pass at migration head `0074_durable_contribution_activity_model` with 118
registered tables. The replay defect discovered during acceptance was corrected with
DB-stable UTC normalization before canonical fingerprinting, so persisted/reloaded
review timestamps preserve idempotent replay.

### 23.5.3 13.16.1D3A initial-rule / VerifiedRule publication adapter implementation and acceptance status

**State: COMPLETE / PASS.** The first publication adapter is
limited to the existing authenticated `InitialRuleAssertion` publication boundary. An
independently reviewed assertion that passes the existing approved-coverage,
source-certification, immutable-snapshot, confidence, publication-attestation, and
proposer/publisher-separation gates may stage exactly one
`verified_rule_publication_completed` Contribution when it is published as a
`VerifiedRule`.

The source workflow remains the transaction owner. `InitialRuleAssertion.status =
published`, `VerifiedRule` creation, regulatory-knowledge-graph projection, the existing
publication and coverage-reconciliation audits, the Contribution, and the Contribution
audit are committed together. Contribution validation/staging or final commit failure
rolls the full publication unit back. The idempotent already-published branch performs no
historical backfill: a publication that predates D3A remains unchanged and does not gain
a synthetic Contribution merely because it is read again.

D3A uses a separate sealed validator rather than expanding the generic authenticated
Contribution API. The validator requires the default legacy tenant, authenticated
internal-human admin/reviewer authority, a `published` assertion with review and
publication attribution, proposer distinct from reviewer and publisher, an active
human-published `VerifiedRule`, exact assertion/rule jurisdiction, official-source,
immutable-snapshot, rule-key/domain, statement, confidence, effective-period, and
publication-timestamp provenance. Its deterministic source version binds the assertion
SHA-256 and the material published rule state; the Contribution key binds the assertion
ID and published rule ID. The Contribution explicitly records governed knowledge
publication only and cannot be interpreted as applicant eligibility, occupation
eligibility, visa approval, or pathway publication.

Legacy direct service calls without trusted HTTP publisher-role context retain their
pre-D3A no-emitter behavior. The authenticated runtime publication route supplies the
trusted role. Focused D3A coverage includes authenticated publication emission, HTTP
replay without duplicates, persisted adapter replay, fail-closed published-source drift, and atomic
rollback when Contribution staging fails. Local acceptance passes **8/8** focused
initial-rule publication tests, **4/4** coverage-reconciliation tests, **78 passed + 1
expected PostgreSQL-only skip** in the combined D1/D2/organization
service/API/platform regression, and **734 passed + 1 expected PostgreSQL-only skip** in
the complete API suite. Repository policy, release consistency, migration consistency,
and `git diff --check` pass at Alembic head
`0074_durable_contribution_activity_model` with 118 registered tables.

### 23.5.4 13.16.1D3B regulatory-change publication adapter implementation and acceptance status

**State: COMPLETE / PASS.** The second publication adapter is
limited to the existing authenticated `RegulatoryChange` publication boundary. Only a
previously reviewed `approved` change backed by its hashed current `SourceSnapshot` may
become `published` and stage exactly one `regulatory_change_publication_completed`
Contribution when the workflow creates its active `VerifiedRule`. Detection, source
retrieval, classification proposals, pending review, rejected changes, and
approved-but-unpublished changes remain non-emitting.

The authenticated HTTP publisher is now authoritative for publication attribution. The
legacy request `reviewer` field must match the authenticated publisher identity; a body
cannot name a different publisher. The resulting `VerifiedRule.approved_by`, knowledge
graph projection, supersession attribution when present, publication audit, and
Contribution actor therefore share the authenticated identity. Direct service callers
that omit trusted publisher actor/role context retain their pre-D3B no-emitter behavior.

The `RegulatoryChange` workflow remains transaction owner. The `published` transition,
new `VerifiedRule`, optional old-rule supersession/deactivation, regulatory knowledge
graph projection, existing publication/supersession audits, one staged Contribution, and
its audit are committed together. Contribution staging or final commit failure rolls the
whole publication unit back. The existing already-published branch does not synthesize a
Contribution, preserving the no-historical-backfill boundary.

D3B uses a separate sealed validator rather than widening the generic authenticated
Contribution source policy. It requires the default legacy tenant, authenticated
internal-human admin/reviewer authority, `RegulatoryChange.status == published`, prior
review attribution, a publication timestamp, a current hashed source snapshot belonging
to the same official source, and an active human-published `VerifiedRule` with exact
regulatory-change, jurisdiction, official-source, snapshot, domain, publisher, and
publication-timestamp lineage. The canonical source version binds the reviewed change,
current snapshot, publication transition, and material VerifiedRule state. The
deterministic Contribution key binds the change ID and resulting rule ID.

The Contribution records governed regulatory-knowledge publication only. It explicitly
does not establish applicant eligibility, occupation eligibility, visa approval, or
pathway publication. Focused D3B coverage includes non-emitting pre-publication state,
authenticated emission, HTTP and adapter replay, fail-closed published-rule drift,
source+rule+Contribution rollback on emitter failure, request-body publisher spoofing,
and confirmation that the generic Contribution API remains closed to
`regulatory_change`. Local acceptance passes **8/8** focused D3B emitter tests, **9/9**
existing regulatory-intelligence/knowledge-graph/pathway-impact regression tests, **86
passed + 1 expected PostgreSQL-only skip** in the combined D1-D3A/organization
regression, and **742 passed + 1 expected PostgreSQL-only skip** in the complete API
suite. Repository policy, release consistency, migration consistency, and
`git diff --check` pass at Alembic head `0074_durable_contribution_activity_model` with
118 registered tables.

### 23.5.5 13.16.1D3C pathway-version publication adapter acceptance

**State: COMPLETE / PASS.** D3C is limited to the existing
authenticated `MobilityPathwayVersion` publication boundary. A draft version remains
non-authoritative until the existing catalogue publication gate succeeds, an independent
human publisher is attributed, the version is staged as `published`, and the parent
`MobilityPathway` is active. Draft, simulation-only, retired, or otherwise unpublished
versions cannot emit. The current Round 6 Austria v4 draft therefore remains a
zero-emitter safety pin.

The HTTP publication path now supplies the trusted authenticated role to the domain
service. Existing admin/operator publication authorization is preserved; the adapter also
accepts reviewer authority for trusted internal composition, while the public route still
follows the existing auth policy. The publisher must remain distinct from the version
creator. Direct service callers that omit trusted publisher-role context retain their
pre-D3C no-emitter behavior, so D3C introduces no historical backfill.

The `MobilityPathway`/`MobilityPathwayVersion` workflow remains transaction owner. The
previous published version(s), if any, are staged as `superseded`; the selected draft is
staged `published`; the pathway is activated; the existing
`mobility_pathway_version_published` audit is staged; then one
`pathway_version_published` Contribution and its audit are staged before one final commit.
Contribution staging or final commit failure rolls the whole publication unit back. A
later immutable pathway version emits a distinct Contribution rather than rewriting the
prior publication outcome.

D3C uses a sealed validator rather than widening the generic authenticated Contribution
source policy. It requires the default legacy tenant, an authenticated internal-human
publisher, published/active source state, proposer/publisher separation, and exact reuse
of the catalogue's existing publication-evidence blocker contract after the transition is
staged. That preserves required official-source/snapshot provenance, verified-rule
provenance, source-certification gates, and the Austria structured occupation-evidence
requirements without creating a second competing publication policy. The canonical source
version also binds the immutable pathway/version content, evidence links, verified-rule
state, publication actor, and publication timestamp using DB-stable datetime
normalization.

The Contribution records only that a governed pathway catalogue version was published.
It explicitly does not establish applicant eligibility, occupation eligibility, visa
approval, or an authority decision for any mobility case. Focused D3C tests pass **8/8**
for non-emitting draft state, authenticated publication, preserved operator compatibility,
persisted adapter replay, fail-closed rule drift, atomic rollback on emitter failure,
revision supersession with a distinct Contribution, and confirmation that the generic
Contribution source policy remains closed to `mobility_pathway_version`. Existing pathway
governance regression passes **23/23**, the combined D1-D3B/organization protection set
passes **94 passed + 1 expected PostgreSQL-only skip**, and the complete API suite passes
**750 passed + 1 expected PostgreSQL-only skip, 0 failed** with exit code 0. Repository
policy, release consistency, migration consistency, and `git diff --check` pass at Alembic
head `0074_durable_contribution_activity_model` with 118 registered tables.

### 23.6 Future emission points and source versions

| Source | Exact future boundary | Proposed source version | Proposed Contribution semantics | WorkItem link |
|---|---|---|---|---|
| `JurisdictionSourceCertification` | `jurisdiction_registry.review_source_certification()` immediately after the reviewed state/evidence is staged and before the single outer commit | `certification_version` plus immutable review evidence identity; structured reviews also bind the evidence-pack SHA-256/source snapshot | `source_certification_review_completed` with outcome approved/rejected; approved may additionally carry a narrowly named certification-approved semantic | optional |
| Published `InitialRuleAssertion` / `VerifiedRule` | `initial_rule_assertions.publish_initial_rule_assertion()` after the rule, assertion publication state, graph projection, and coverage-reconciliation audits are staged | assertion SHA-256 + published rule ID + material VerifiedRule publication state | `verified_rule_publication_completed` | optional |
| `RegulatoryChange` | `regulatory_intelligence.publish_regulatory_change()` after published state, resulting VerifiedRule, graph projection, and publication/supersession audits are staged | canonical reviewed change + current hashed snapshot + resulting rule publication state | `regulatory_change_publication_completed` | optional |
| `MobilityPathwayVersion` | `pathway_catalogue.publish_pathway_version()` after publication evidence passes and published state is staged | pathway ID + `version_number` + publication transition | `pathway_version_published` | optional |
| `ExecutiveDecision` | no automatic emitter; retain explicit Contribution command after terminal decision validation | existing record fingerprint or committed `updated_at` fallback | caller-specific governed decision contribution only when explicitly requested | optional |

For every adapter the deterministic key should be derived from stable semantics, for
example `contribution:<tenant>:<source_type>:<source_id>:<source_version>:<transition>:<contribution_type>`.
Random UUIDs and server-generated timestamps must not be the replay identity. A later
material source revision gets a new source version and therefore a new key.

### 23.7 Actor attribution and corrections

The Contribution actor is the accountable organizational actor for the authoritative
transition, not the agent/tool that may have produced draft material. The adapter must
preserve source reviewer/publisher attribution in `verified_by`/provenance and use the
authenticated command context for the organization actor that invokes the transition.
Where those identities differ, both must remain visible rather than collapsing
producer, reviewer, authority, and emitter into one identity.

Corrections never rewrite the original Contribution. A corrected/superseding source
revision emits a new Contribution with a new deterministic key and the committed
`supersedes_contribution_id`/retraction relationship where appropriate. A status
change to `superseded` must not mutate the prior immutable outcome.

### 23.8 External-human boundary

13.16.1D does not weaken the committed HumanAction identity rule. `external_human`
remains rejected by the durable HumanAction command until an accepted authentication
contract exists. External-validation reviews remain authoritative evidence only inside
the existing external-validation gate. The `ExternalValidationRun` adapter stays
deferred until genuine Phase 13.17 external-human acceptance and the attribution
contract are satisfied; the AI organization must not self-attest that gate.

### 23.9 Recommended implementation slices

1. **13.16.1D1 — transaction composability correction. COMPLETE / PASS.**
   Caller-owned Contribution/AuditLog staging is explicit while standalone commands
   retain commit ownership; local transaction and full regression acceptance pass.
2. **13.16.1D2 — first reviewed adapter: source-certification review. COMPLETE / PASS.**
   Only authenticated `JurisdictionSourceCertification` approved/rejected review
   outcomes are connected, with structured evidence-pack/independent-review requirements
   preserved. Round 6 pending national/regional certifications emit zero Contributions.
3. **13.16.1D3A — initial-rule / VerifiedRule publication adapter. COMPLETE / PASS.**
   Connect only the independently reviewed initial-rule publication boundary; keep the
   generic Contribution API unchanged and prohibit any applicant/pathway legal
   conclusion.
4. **13.16.1D3B — regulatory-change publication adapter. COMPLETE / PASS.**
   Authenticated publication, sealed validation, deterministic replay, and atomic rollback
   are accepted under the local focused/full-suite/repository gates.
5. **13.16.1D3C — pathway-version publication adapter. COMPLETE / PASS.**
   The bounded source-owned transaction, sealed pathway-publication validator, draft/internal
   simulation exclusion, deterministic replay, supersession behavior, and atomic rollback
   pass focused, pathway-regression, full-suite, and repository acceptance.
6. **13.16.1D4 — deferred-domain review and integrated regression. COMPLETE / PASS.**
   The repository review keeps jurisdiction assessments, reassessment acceptance,
   timeline milestones, agency submissions/appointments, corporate compliance, and
   external validation deferred for the specific attribution/evidence/audit reasons
   documented below. The generic API negative-source regression is expanded across
   sealed, deferred, telemetry, and assessment sources; no new runtime emitter is
   authorized by D4.
7. **13.16.1E — Observatory/read model** is **UNLOCKED / NOT STARTED** after D4 acceptance.
   It may now begin, but aggregate/read-model acceptance still requires enabled adapters
   to reconcile exactly to their authoritative source tables on SQLite and PostgreSQL.

### 23.10 D4 deferred-domain re-evaluation

The post-D3C review finds **no additional source safe to enable in 13.16.1D4**. This is
a governance result, not an implementation shortfall. The accepted real-domain emitters
are intentionally sparse and D4 does not broaden the generic Contribution source policy.

| Deferred source | D4 result | Remaining blocker | Earliest safe future condition |
|---|---|---|---|
| `JurisdictionImmigrationAssessment` | `DEFER_UNTIL_STRONGER_GOVERNANCE` | Review transition has no source `AuditLog`; proposal can omit official-source/snapshot provenance. | Require governed immutable provenance for authoritative states and make review/audit transactionally composable before any adapter. |
| `ReassessmentAcceptance` | `DEFER_UNTIL_STRONGER_GOVERNANCE` | Explicit user attestation is stored, but durable authenticated end-user identity is not represented; `recorded_by` is the internal recorder. | Introduce an accepted user/external-human authentication and attribution contract without weakening the internal HumanAction boundary. |
| `ExternalValidationRun` | `DEFER_UNTIL_STRONGER_GOVERNANCE` | Phase 13.17 genuine external-human acceptance is still outstanding; durable external-human actor contract is intentionally held. | Complete genuine 13.17 acceptance and bind the passed gate to authenticated external-human reviews. |
| `CorporateComplianceEvent` | `DEFER_UNTIL_STRONGER_GOVERNANCE` | Completion has actor/time/audit but no typed evidence linkage or distinct reviewer approval despite evidence/review flags. | Bind required evidence and independent review/approval to completion in one governed transaction. |
| `MobilityTimelineMilestone` | `DEFER_UNTIL_STRONGER_GOVERNANCE` | Generic completion enforces dependencies and optional approval note but not stage-specific `required_evidence_json`. | Define allowlisted milestone types with exact evidence/approval contracts; do not enable generic completion. |
| `AgencySubmission` | `DEFER_UNTIL_STRONGER_GOVERNANCE` | Status progression is operator-recorded; reference/tracking evidence is optional and no immutable authority receipt is required. | Bind an immutable authority receipt/decision artifact to the exact terminal transition. |
| `AuthorityAppointment` | `DEFER_UNTIL_STRONGER_GOVERNANCE` | `completed` is operator-recorded and does not prove attendance or authority acknowledgement; reference number is optional. | Require governed attendance/authority evidence for an allowlisted material appointment outcome. |

Assessment-generation records (`EligibilityAssessment`, `PathwayComparisonAssessment`,
`CountryRankingAssessment`), external-validation component reviews/findings, telemetry,
AuditLog, retries, messages, UI interactions, tools, and LLM output remain ineligible as
direct Contribution authority.

The generic authenticated Contribution command remains terminal `ExecutiveDecision` only.
The accepted sealed integration sources remain exactly:

1. reviewed `JurisdictionSourceCertification`;
2. published `InitialRuleAssertion` / resulting `VerifiedRule`;
3. published `RegulatoryChange` / resulting `VerifiedRule`; and
4. published `MobilityPathwayVersion`.

D4 expands the generic API regression across all sealed and deferred source names so a
caller cannot bypass source-owned governance by selecting one of those types in the
request body. Existing source-owned emitter tests remain the authority for positive
emission, idempotent replay, fail-closed drift, and atomic rollback.

Round 6 Austria v4 remains a mandatory negative control: draft,
`simulation_candidate`, `INTERNAL_SIMULATION_ONLY`, publication-ready false, unpublished,
national/regional certification `pending_review`, binding job offer absent/blocking,
occupation `AMBIGUOUS`, unknown-province regional result `INSUFFICIENT_INFORMATION`, and
qualification mapping `UNRESOLVED`. D4 authorizes no legal-conclusion emitter from that
state.

D4 local acceptance is **COMPLETE / PASS**: 17/17 organization-record API tests, 40/40
combined D1-D3C Contribution transaction/emitter tests, and 49/49 deferred-domain
regression tests pass; the complete API suite passes 750 with 1 expected PostgreSQL-only
skip, 0 failures, and exit code 0. Repository policy, release consistency, migration
consistency, and `git diff --check` pass at Alembic head
`0074_durable_contribution_activity_model` with 118 registered tables. No new emitter
was enabled by D4.

### 23.11 Emitter acceptance tests

The runtime slices must prove at least: AgentRun/WorkflowRun success emits zero
Contributions; draft/simulation assessment emits zero Contributions; pending source
certification emits zero certified Contribution; an exact eligible terminal source
emits one Contribution; replay is idempotent; a changed semantic payload under the
same key fails closed; corrected source revisions append linked corrections;
cross-tenant and missing/stale sources fail; required reviewer/certification/publication
states are enforced; source transition + Contribution + AuditLog commit atomically;
rollback leaves no partial outcome; the current Round 6 Austria state emits no false
legal conclusion; no historical backfill occurs; 13.16.1C API behavior remains
unchanged; and Observatory remains absent until 13.16.1E.


### 23.12 13.16.1E0 Observatory/read-model source reconciliation design

**State: DESIGN COMPLETE / RUNTIME NOT STARTED.** E0 reconciles the accepted durable
ledgers and D2-D4 emitter behavior to the Observatory aggregation contract before any
summary endpoint is allowed to present organization-wide metrics. E0 changes
specification only: no router, service, schema, migration, database, dashboard, or UI
behavior is added.

#### 23.12.1 Read-model authority and non-goals

The first read model is a live, tenant-scoped projection over authoritative tables. It
must not create a second mutable source of truth, materialized metric table, cache, or
semantic backfill. Reads produce no AuditLog row and mutate no source state.

The safe source map is:

| Read concern | Authoritative rows | Safe in E1 | Explicitly not inferred |
|---|---|---:|---|
| Verified Contributions | `organization_contributions` plus correction edges | yes | Activity, AgentRun, WorkflowRun, attempts, outputs, work completion |
| Work snapshot | `organizational_work_items` | yes | impact or contribution from status alone |
| Blocker snapshot | `organization_blockers` | yes | resolved-in-period from `updated_at` |
| Pending decisions | `executive_decisions` | yes | approval effect/execution not recorded by the decision |
| Human attention | active `organization_human_action_requests` plus genuine pending Board decisions, reported separately | yes | generic audits or agent prompts |
| Human interventions | immutable `organization_human_actions` | yes | AuditLog actor counts |
| Dependency snapshot | `organization_work_item_dependencies` plus linked WorkItems | yes | inferred dependency from co-occurrence or agent fan-out |
| Curated semantic history | `organization_activities` | only where rows actually exist | AuditLog, raw telemetry, mutable-row timestamps |
| Runtime health | AgentRun/WorkflowRun/attempt/Celery/delivery records | technical-only later | organizational contribution or productivity |

Every Observatory response must include one stable `as_of` instant, timezone `UTC`,
tenant/filter scope, source-row counts, coverage start/basis, and warnings for partial or
unavailable metrics. Empty data means zero only where the authoritative source coverage
is established; otherwise the response must say coverage is not established.

#### 23.12.2 Active Contribution resolution

An active verified Contribution is an immutable row with `record_kind = 'outcome'` that
is not the target of any valid `supersession` or `retraction` row in the same tenant.
Correction rows remain visible as history/correction counts but are not counted as new
active outcome Contributions. The read model never updates the original row and never
turns Activity or WorkItem completion into Contribution.

The first summary must expose at least historical outcome count, active outcome count,
supersession count, retraction count, and active outcomes grouped by department and
`contribution_type`. Filtering uses `effective_at` for Contribution periods. Actor/tool
volume is never a contribution metric.

#### 23.12.3 Accepted source reconciliation

Every accepted Contribution must reconcile back to its authoritative source identity and
version. The read model may extract pure read-only source-version/provenance helpers from
the sealed validators, but it must **not** call mutation validators by fabricating an
admin/reviewer/operator authority context and must not widen `validate_authoritative_outcome()`.

| Contribution source | Contribution -> source validation | Source -> Contribution completeness |
|---|---|---|
| `executive_decision` | decision exists in same tenant; terminal approved/rejected state, governed decision attribution, and stored source version still match | not required: ExecutiveDecision remains explicit-command-only |
| `jurisdiction_source_certification` | default-tenant certification exists; approved/rejected reviewed state, reviewer/time, certification version/scope, and review-evidence fingerprint match | required only inside established automatic-emitter coverage |
| `initial_rule_assertion` | default-tenant assertion remains published and points to the exact active human-published `VerifiedRule`; assertion/source/snapshot/content/version provenance match | required only inside established automatic-emitter coverage |
| `regulatory_change` | default-tenant change remains published and maps to the exact active human-published `VerifiedRule`, immutable current snapshot, review, supersession, and source version | required only inside established automatic-emitter coverage |
| `mobility_pathway_version` | default-tenant version remains published under an active pathway and still satisfies the exact catalogue evidence/certification/rule gate and deterministic source version | required only inside established automatic-emitter coverage |

The reconciliation result classifies at least: `matched`, `missing_source`,
`source_state_drift`, `source_version_drift`, `duplicate_outcome`, and
`missing_contribution_in_coverage`. A mismatch is reported; a GET must never repair,
re-emit, approve, publish, or backfill anything.

#### 23.12.4 No-backfill coverage semantics

D2-D3 intentionally performed no historical backfill, and the repository has no durable
emitter-rollout watermark. E1 therefore must not label all historic terminal sources as
missing Contributions.

For each automatic sealed source type, the initial coverage start is the earliest
observed matching Contribution `created_at`, reported with
`coverage_basis = 'first_observed_contribution'`. Terminal source transitions earlier
than that instant are `precoverage_source_rows` and excluded from completeness. Eligible
source transitions at or after the established coverage start that have no matching
Contribution are reconciliation gaps. If no Contribution has ever been observed for an
automatic source type, coverage is `not_established`, not silently zero-complete.

`ExecutiveDecision` is different: terminal decisions do not automatically imply a
Contribution, so the read model validates Contributions that reference decisions but
never reports every terminal decision without a Contribution as a gap.

The source transition timestamp used for coverage is `reviewed_at` for source
certifications and `published_at` for initial-rule, regulatory-change, and pathway
publication. The Contribution coverage watermark uses `created_at`; business-period
metrics continue to use `effective_at`.

#### 23.12.5 Safe E1 snapshot metrics

E1 may expose point-in-time metrics that are reproducible from current authoritative
rows without reconstructing missing semantic history:

- WorkItems by current status/department/priority, active vs terminal, overdue active
  count, and current oldest active creation time.
- Blockers in `open`/`mitigated` state by severity/department/due status.
- Pending ExecutiveDecision rows in `pending_ceo`, `coordinating_ceo`, or
  `pending_board`, with Board-reserved/L4 attention reported distinctly.
- HumanActionRequests in `required`, `acknowledged`, or `in_progress`, separately from
  immutable HumanAction intervention counts.
- Active dependency edges and currently blocked downstream WorkItems.
- Active/historical Contribution counts and Contribution-source reconciliation.

E1 must **not** expose authoritative WorkItem cycle time, completed-work period
throughput, blockers-resolved-in-period, last-material-transition ageing, or a complete
semantic organization timeline until Activity coverage exists.

#### 23.12.6 Activity-coverage gap and required later slice

Repository inspection confirms that current WorkItem, Blocker, HumanActionRequest, and
ExecutiveDecision command transitions write their domain row plus `AuditLog`, but do not
automatically append curated `OrganizationActivity` rows. The standalone Activity append
service also owns `session.commit()`. Therefore a full historical Observatory cannot be
made correct by querying `updated_at`, counting AuditLog rows, or calling the current
Activity command after a source commit.

Before transition-period metrics are enabled, a later bounded E slice must add an
explicit caller-owned Activity staging path and source-owned semantic Activity adapters,
with the same atomicity rule used for D1 Contributions. Only then may cycle-time,
resolved-blocker throughput, transition-based work ageing, and complete department
throughput be marked authoritative. Until that gate closes, these metrics are returned as
unavailable/partial rather than fabricated.

#### 23.12.7 Planned E1 HTTP/read contract

The first runtime slice should add read-only organization endpoints under the existing
authenticated organization boundary, without mutation methods:

- `GET /api/v1/organization/observatory/summary`
- `GET /api/v1/organization/observatory/contribution-reconciliation`
- `GET /api/v1/organization/observatory/departments`

Schemas should separate metric values from coverage metadata. Reads inherit the trusted
tenant/role context used by 13.16.1C; payload/query parameters cannot select another
tenant. Default tenant legacy source reconciliation is explicit. Reconciliation detail
uses bounded pagination (default 50, max 200) and deterministic ordering. No endpoint is
named or shaped as a mutation, and no dashboard/frontend work belongs in E1.

#### 23.12.8 E1 acceptance plan

E1 must prove at least:

1. empty-ledger summaries are deterministic and distinguish zero from coverage not established;
2. Contribution active counts exclude any outcome targeted by supersession/retraction;
3. correction rows remain visible without becoming active outcomes;
4. AgentRun/WorkflowRun/tool/retry/activity volume cannot increase Contribution metrics;
5. current WorkItem/Blocker/Decision/HumanActionRequest/dependency counts reconcile exactly to tenant-scoped source rows;
6. human interventions come only from immutable HumanAction records;
7. cross-tenant reads do not disclose counts or identifiers;
8. each accepted sealed Contribution reconciles to its exact source/version;
9. missing/deleted source, state drift, version drift, and duplicate outcomes fail reconciliation visibly without mutation;
10. precoverage historic source rows are excluded and reported separately;
11. eligible post-coverage automatic source rows without Contributions are reported as gaps;
12. terminal ExecutiveDecision without Contribution is not treated as a completeness failure;
13. current Round 6 Austria draft/pending state produces no false published/certified/eligibility Contribution metric;
14. GET requests create no AuditLog, Activity, Contribution, or source mutation;
15. SQLite and PostgreSQL reconciliation fixtures produce the same semantic result;
16. Alembic head remains `0074_durable_contribution_activity_model` and registered tables remain 118.

E0 does not unlock Phase 13.16.2. 13.16.1E1 is the next implementation slice. Full
Observatory historical throughput remains gated on the later semantic Activity-coverage
slice described above.

### 23.13 13.16.1E1 safe snapshot and Contribution-reconciliation read API

**State: COMPLETE / PASS.** E1 adds the first runtime
Observatory projection without introducing a mutable read-model table, cache, migration,
dashboard, or write path. The existing authenticated organization router now exposes:

- `GET /api/v1/organization/observatory/summary`;
- `GET /api/v1/organization/observatory/contribution-reconciliation`;
- `GET /api/v1/organization/observatory/departments`.

All three derive tenant/role identity from the trusted 13.16.1C request context. No
payload or query parameter can select another tenant. Reconciliation detail uses the
existing default/max page sizes of 50/200 with deterministic newest-first ordering and
optional source/status filters. GETs append no AuditLog, Activity, Contribution, or
source mutation.

The summary reports only the E0-safe current-state metrics: WorkItems by status,
department, and priority; active/terminal and overdue-active work; open/mitigated
Blockers; pending/Board-attention ExecutiveDecisions; pending/overdue HumanActionRequests;
immutable HumanAction count; active dependency edges/currently blocked downstream work;
and historical/active Contribution outcomes with supersession/retraction counts and
active department/type breakdowns. Department reads aggregate only directly attributable
current rows; HumanActionRequests without a linked WorkItem department remain unassigned
rather than being inferred from actor or audit context.

Contribution active-state resolution follows the immutable correction model: an
`outcome` remains active unless it is the target of a same-tenant `supersession` or
`retraction`. Correction rows remain visible history and never increment active outcome
counts. Activity, AgentRun, WorkflowRun, retries, tool calls, messages, and mutable work
status alone cannot increase Contribution metrics.

E1 implements read-only source reconciliation for the accepted source inventory:

| Source | Contribution -> source | Source -> Contribution completeness |
|---|---|---|
| `executive_decision` | tenant-scoped terminal attributed decision and stored version | explicit-command-only; no automatic completeness gap |
| `jurisdiction_source_certification` | terminal independent review plus deterministic review-evidence version | automatic only after first observed Contribution |
| `initial_rule_assertion` | published assertion and exact active human-published `VerifiedRule` provenance/version | automatic only after first observed Contribution |
| `regulatory_change` | reviewed published change, immutable current snapshot, exact active `VerifiedRule` and version | automatic only after first observed Contribution |
| `mobility_pathway_version` | active published pathway version still passing catalogue evidence/certification/rule gates | automatic only after first observed Contribution |

The reconciliation classifications are `matched`, `missing_source`,
`source_state_drift`, `source_version_drift`, `duplicate_outcome`,
`missing_contribution_in_coverage`, and `unsupported_source`. Any mismatch is reported in
the GET response; E1 never repairs, re-emits, approves, publishes, certifies, or backfills.

Automatic-source completeness uses the E0 no-backfill contract. Coverage begins at the
earliest observed outcome Contribution `created_at` for each sealed source type with
`coverage_basis = first_observed_contribution`. Earlier eligible source transitions are
reported as precoverage history; eligible transitions on/after coverage start without an
exact source-ID/version Contribution are visible gaps. If no Contribution exists for an
automatic type, coverage remains `not_established` even if eligible source rows exist.
ExecutiveDecision is reported separately as `explicit_command_only`.

Every E1 response carries one UTC `as_of`, trusted tenant scope, source-row counts,
coverage metadata, and explicit warnings. Historical WorkItem cycle time,
completed-throughput periods, blockers-resolved-in-period, last-material-transition
ageing, and a complete semantic timeline remain unavailable because current source
transitions do not yet guarantee curated OrganizationActivity emission.

E1 acceptance is complete: focused Observatory tests pass **10/10**, the protected
organization/emitter regression passes **65/65**, and the complete API suite passes
**760 passed + 1 expected PostgreSQL-only skip, 0 failed** with exit code 0. Repository
policy, release consistency, migration consistency, and `git diff --check` pass with code
head `0074_durable_contribution_activity_model` and 118 registered tables.

The PostgreSQL acceptance boundary is explicit. The authoritative integration database
`gmai` was queried only inside a strict read-only transaction and remains preserved at
`0073_austria_candidate_integrity`; no migration was run and E1 execution is not claimed
against schema that does not contain the 0074 organization ledgers. The isolated
PostgreSQL service database is at `0074_durable_contribution_activity_model`, exposes all
eight durable organization tables, and passed execution of the current E1
`observatory_summary`, `observatory_departments`, and
`observatory_contribution_reconciliation` functions with transaction read-only protection
retained before and after the reads. The smoke exited 0 with internally consistent tenant
scope, source-row counts, and coverage projections. Its current organization/source rows
were empty, so automatic sealed-source coverage correctly reported `not_established` and
ExecutiveDecision remained `explicit_command_only`; no production completeness inference
is made from the empty fixture.

Acceptance also corrected two bounded defects without widening authority: blockers linked
to WorkItems are attributed to the WorkItem department before falling back to the blocker
record's department, and the OpenAPI architecture boundary permits exactly the three E1
GET-only Observatory endpoints while retaining the prohibition on arbitrary dashboard,
metrics, observatory-root, or unapproved summary surfaces.

E1 does not unlock Phase 13.16.2. E2 caller-owned Activity staging plus source-owned semantic transition adapters is now **COMPLETE / PASS**; 13.16.1E3 is **IN PROGRESS**: E3A writer inventory/coverage-epoch design is **COMPLETE** and E3B legacy WorkItem material-writer adapters are **UNLOCKED / NOT STARTED**.
Only after that coverage exists may historical throughput/cycle-time metrics be
implemented. Round 6 Austria v4 remains draft/simulation-only/unpublished with pending
national/regional certifications and must not appear as a published, certified, or
eligibility Contribution.


### 23.14 13.16.1E2 caller-owned Activity staging and semantic transition coverage

**State: COMPLETE / PASS.** E2 implements the transaction
boundary identified by E0/E1 without changing the 0074 persistence model. No migration,
new table, router, public mutation endpoint, dashboard, materialized read model, or
historical backfill is introduced.

The Activity command now has two explicit modes. `append_activity(...)` remains the
standalone authenticated mutation command and continues to own its commit. The new
`stage_activity(...)` is an internal composition primitive: it allocates/locks the
tenant-scoped Activity stream, appends the immutable Activity row, and stages the
`organization.activity.append` audit without calling commit or rollback. Source services
that use it already own authorization and the surrounding transaction. This distinction
preserves reviewer-authorized sealed D2/D3 publication flows without opening a reviewer
standalone Activity command.

Modern 13.16.1 command paths now append curated semantic Activity for the following
authoritative transitions:

| Source family | Covered semantic events | Stream basis |
|---|---|---|
| `OrganizationalWorkItem` | create, status transition, assignment change | WorkItem id |
| `OrganizationWorkItemDependency` | create, satisfied, waived, superseded | owning WorkItem id |
| `OrganizationBlocker` | open, mitigated, resolved, waived, predecessor superseded | Blocker id |
| `ExecutiveDecision` | create, approved, rejected | Decision id |
| `OrganizationHumanActionRequest` | create, assignment, acknowledge/start/decline/cancel/expire/completed | HumanActionRequest id |
| `OrganizationHumanAction` | immutable append | HumanActionRequest stream when linked, otherwise HumanAction id |
| `OrganizationContribution` | outcome, supersession, retraction | original Contribution lineage root |

A semantic source transition follows one transaction contract: source row changes are
staged, the existing source `AuditLog` is staged, semantic Activity and its Activity
`AuditLog` are staged, and only then does the source command commit. Any Activity or
Activity-audit failure rolls back the entire source unit. The caller-owned Contribution
path follows the same rule, so D2/D3 sealed emitters now include Contribution Activity in
their already caller-owned publication/review transaction. Idempotent source replay
returns before another Activity is appended.

Activity is still not organizational success authority. The Activity row points to the
semantic source/transition and may carry domain ownership/provenance, but it never creates
a Contribution by itself. AuditLog, AgentRun, WorkflowRun, retry count, tool calls,
messages, and provider/model telemetry remain non-authoritative. Contribution source
validation and all D2/D3 governance gates remain unchanged.

Attribution is deliberately domain-aware. Where an Activity belongs to a WorkItem, the
WorkItem department/position/authority is used instead of blindly inheriting the actor's
request context; authenticated actor identity remains the `actor_type`/`actor_id` on the
Activity. This mirrors E1's blocker department correction and prevents owner/board actors
from making operational work appear to belong to the executive department merely because
they performed the transition.

E2 does **not** establish complete semantic history. Repository review found material
legacy WorkItem and ExecutiveDecision writer paths in `organization_governance.py` and the
organization-governance router that still bypass the modern 13.16.1 command services.
Those writers are not silently backfilled or reconstructed from mutable `updated_at` or
AuditLog. Consequently E1's Observatory response intentionally keeps
`activity_history_basis = partial_activity_coverage` and
`activity_history_established = false`. Historical WorkItem cycle time, completed-work
period throughput, blocker-resolution throughput, last-material-transition ageing, and a
complete organization semantic timeline remain unavailable until the remaining writer
surface is reconciled or retired in a bounded later E step.

E2 adds 11 focused tests: 10 default SQLite tests for staging/rollback, ordered semantic
streams, WorkItem/dependency/Blocker/Decision/HumanAction/Contribution coverage, replay,
Activity-not-Contribution separation, atomic rollback on Activity audit failure, and the
still-partial Observatory flag; plus one PostgreSQL-only caller-owned staging contract.
The existing D1 transaction test is extended so staged Contribution now requires the
Contribution Activity and its audit inside the same caller-owned unit. Acceptance is
complete: the complete API suite passes **770 passed + 2 expected PostgreSQL-only skips,
0 failed** with exit code 0; repository policy, release consistency, migration consistency,
and `git diff --check` pass at Alembic 0074 with 118 registered tables.

The two bounded PostgreSQL Activity transaction contracts run against the existing isolated
0074 service database and pass **2/2** with 35 non-PostgreSQL tests deselected. Read-only
post-test verification confirms zero persisted `organization_activity_streams` and zero
persisted `organization_activities`, proving the outer transaction rollback/no-residue
contract. The authoritative integration database `gmai` remains preserved at
`0073_austria_candidate_integrity`, stopped and unmigrated. E2 is therefore **COMPLETE /
PASS**. Phase 13.16.2 remains locked because complete-writer reconciliation is still
outstanding. E3A writer inventory/coverage-epoch design is now **COMPLETE**; E3B legacy
WorkItem material-writer adapters are **UNLOCKED / NOT STARTED**.


### 23.15 13.16.1E3A legacy-writer inventory and coverage-epoch design

**State: DESIGN COMPLETE; E3 OVERALL IN PROGRESS.** A fresh audit of exact baseline
`8bfbd40a1b4e460757b99d943a139cfd2ef83316` maps the remaining legacy
`OrganizationalWorkItem` / `ExecutiveDecision` writer surface and records the mandatory
semantic-vs-telemetry disposition in
[ORGANIZATION_ACTIVITY_WRITER_RECONCILIATION_V13_16_1E3.md](ORGANIZATION_ACTIVITY_WRITER_RECONCILIATION_V13_16_1E3.md).

The material gaps are bounded to the legacy organization-governance router/service: direct
Work/Decision creation, requeue/control/deadline/escalation/emergency paths, governance
holds and final execution dispositions, cancellation/retry/evidence-readiness controls,
Decision hold/Board promotion/outcomes, and their coupled Work side effects. Execution
claim leases, per-attempt retry state, delegation/action-output progress, CEO coordination
leases, Decision evidence-only refresh, and reminder timestamps are explicitly excluded
from curated Activity.

E3A also establishes that complete writer adaptation is necessary but not sufficient to
set `activity_history_established = true`. Historic rows that predate semantic adapters
are intentionally not reconstructed, and E1 currently persists no Activity coverage
watermark. E3D must therefore create an explicit immutable coverage-epoch Activity after
all material writers pass acceptance and expose its occurrence time as Observatory
coverage start. Only periods at or after that epoch may later support authoritative
throughput/cycle-time metrics. Pre-epoch Activity remains partial evidence; no backfill is
authorized.

Implementation is now sequenced as E3B WorkItem material-writer adapters, E3C
ExecutiveDecision/coupled adapters, and E3D explicit coverage-epoch/Observatory
activation. `activity_history_established` remains false throughout E3A-E3C. Phase 13.16.2
remains locked.


## 24. Readiness and recommendation

The design, durable persistence foundation, bounded internal command/service layer,
and authenticated organization REST API are complete. The 13.16.1D0 real-emitter
mapping/design and 13.16.1D1 caller-owned transaction staging are **COMPLETE / PASS**.
The first narrow 13.16.1D2 source-certification review adapter is **COMPLETE / PASS**.
13.16.1D3A initial-rule / VerifiedRule publication emission is **COMPLETE / PASS**;
13.16.1D3B regulatory-change publication is **COMPLETE / PASS**;
13.16.1D3C pathway publication is **COMPLETE / PASS**; 13.16.1D4 deferred-domain
review/integrated regression is **COMPLETE / PASS**. The 13.16.1E0 Observatory/read-model
source reconciliation design is **COMPLETE** and 13.16.1E1 safe snapshot + Contribution
reconciliation API is **COMPLETE / PASS**, so Phase 13.16.1 remains **IN PROGRESS**.
E2 Activity transaction/semantic coverage is **COMPLETE / PASS**. 13.16.1E3 is **IN PROGRESS**: E3A writer inventory/coverage-epoch design is **COMPLETE** and E3B legacy WorkItem material-writer adapters are **UNLOCKED / NOT STARTED**.

Recommended next step: begin 13.16.1E3B and adapt the mapped legacy WorkItem material
writer surface while preserving the E3A semantic-vs-telemetry exclusions. E3C must then
close the remaining Decision/coupled writers, and E3D must establish an explicit coverage
epoch before enabling any historical throughput/cycle-time metrics. Preserve E1's read-only snapshot/reconciliation
contract and keep `activity_history_established` false until writer coverage is demonstrably
complete. Every later adapter must preserve draft/unpublished exclusion, caller-owned
atomic transaction semantics, deterministic replay, and narrow organizational wording. No
automatic legal conclusion or broad source-policy expansion is authorized. Do not start
Phase 13.16.2, and do not accept an Observatory dashboard as authoritative until the
13.16.1E read model reconciles enabled adapters to their authoritative source tables on
SQLite and PostgreSQL.
