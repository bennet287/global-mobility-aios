# AIOS V2 — Phase 1B Route-by-Route Behavioral Audit

**Status:** COMPLETE — first behavioral classification  
**Audit baseline:** `58fcec31d51d9ec1fba8e86e893721ca5735196d`  
**Documentation branch:** `docs/aios-v2-master-plan`  
**Production mutation:** none

This document classifies the existing App Router surfaces by user intent, observed behavior, authority/mutation posture, V2 conceptual home, and migration action.

The classification is a product-migration plan, not permission to delete routes. Deep-link and workflow compatibility remain mandatory.

---

## 1. Route audit rules

Each current route is classified using:

- current audience,
- primary purpose,
- observed read APIs,
- observed governed mutations/actions,
- whether the surface is primarily read-only, mixed, or action-heavy,
- V2 conceptual home,
- migration posture.

Migration posture vocabulary:

- **FLAGSHIP REBUILD** — critical V2 surface; redesign from the new system
- **REDESIGN** — preserve domain/capability, rebuild presentation
- **CONSOLIDATE** — capability moves under a stronger V2 parent
- **CONTEXTUALIZE** — retain route/deep link, remove from constant primary navigation
- **PRESERVE WRAPPER** — thin compatibility wrapper around another workspace
- **AUDIT DOMAIN** — domain remains valid but final V2 placement needs product review

---

# 2. Owner / Board / Organization

## `/cockpit`

**Current purpose:** Owner organizational cockpit.

**Observed reads:**
- Board packet
- organization observatory summary/departments
- global intelligence
- Activities
- HumanActionRequests
- blockers
- dependencies
- WorkItems

**Observed governed action:**
- create HumanActionRequest

**Current posture:** mixed read + bounded intervention.

**Finding:** extremely valuable but cognitively dense; current page is ~61.6 KB.

**V2 home:** **Home**

**Action:** **FLAGSHIP REBUILD**

**V2 first viewport:**
1. organizational situation,
2. needs attention,
3. active Missions,
4. Live Organization preview,
5. recent material change.

Technical/provenance details move deeper without losing availability.

---

## `/cockpit/live-organization`

**Current purpose:** canonical Austria Live Organization / replay / environmental-memory surface.

**Observed reads:**
- latest Live Organization
- latest living scene
- latest Replay
- latest Environmental Memory

**Observed bounded action:**
- Owner synthesis command

**Current posture:** mixed, strongly governed.

**Finding:** strongest truth foundation for the future spatial product; presentation remains prototype/engineering-oriented.

**V2 home:** **Organization → Living Organization**

**Action:** **FLAGSHIP REBUILD**

Preserve all canonical mismatch, unsupported-dimension, no-local-fabrication, and non-authoritative-renderer protections.

---

## `/cockpit/decisions`

**Current purpose:** Executive Decision Explorer.

**Observed reads:**
- organization decision records
- individual decision record
- WorkItem
- record references
- Activity

**Observed domain mutation:** none.

**Current posture:** read-only transparency/exploration.

**V2 home:** **Decisions → History / Decision Explorer**

**Action:** **FLAGSHIP REBUILD**

This becomes the structured companion to Board/authority views.

---

## `/owner-inbox`

**Current purpose:** aggregate Owner attention, decisions and escalations.

**Observed reads:**
- Board packet
- HumanActionRequests
- WorkItems
- blockers
- dependencies
- Activity

**Observed domain mutation:** none.

**Current posture:** read-only attention aggregation.

**V2 home:** **Home / Decisions → Needs Attention**

**Action:** **CONSOLIDATE + CONTEXTUALIZE**

The capability remains; the standalone route can remain for deep links, but primary navigation should expose a unified attention model rather than a separate competing inbox.

---

## `/board-room`

**Current purpose:** Board authority and organizational control.

**Observed read:**
- Board packet

**Observed governed mutation:**
- organization control update

**Current posture:** high-authority mixed surface.

**V2 home:** **Decisions → Board**

**Action:** **FLAGSHIP REBUILD**

This must receive the strongest Hick/Von-Restorff/error-prevention treatment in the product.

---

## `/validation`

**Current purpose:** external validation, scenario fixture, review ledger, evidence/remediation.

**Observed reads:**
- validation scenarios/runs
- leads
- pathway comparison

**Observed mutations/actions:**
- seed validation scenario
- create validation run
- draft/simulation comparison
- update validation run
- submit validation review
- evaluate validation run

**Current posture:** action-heavy professional validation tooling.

**V2 home:** **Evidence → Validation / Tools**

**Action:** **CONSOLIDATE + CONTEXTUALIZE**

Not a permanent Owner-primary destination.

---

## `/global-intelligence`

**Current purpose:** global jurisdiction/source intelligence and coverage governance.

**Observed reads:**
- global intelligence dashboard
- jurisdiction registry
- regulatory authorities
- official sources
- coverage worklist/batches
- tranche assistant config
- baseline status
- initial rule assertions

**Observed mutations/actions:**
- propose/review assessments
- propose/review source certification
- queue coverage baselines
- prepare coverage tranche
- create coverage batch
- submit rule assertions

**Current posture:** large mixed governance workspace; ~67 KB.

**V2 home:** **Intelligence → Global**

**Action:** **REDESIGN**

Split overview/situation from specialist governance work.

---

## `/intelligence`

**Current purpose:** regulatory intelligence operations.

**Observed reads:**
- regulatory dashboard/changes
- classification proposals
- knowledge graph
- VerifiedRules
- SourceSnapshots
- jurisdictions

**Observed mutations/actions:**
- source monitor
- regulatory review
- classification generation/review
- publish regulatory change
- retire VerifiedRule
- onboard regulatory source

**Current posture:** specialist mixed governance workspace.

**V2 home:** **Intelligence → Regulatory**

**Action:** **REDESIGN**

Separate observation/source/recommendation/verified-rule truth classes visibly.

---

## `/source-certification-review`

**Current purpose:** immutable-source evidence review and certification.

**Observed reads:**
- review queue
- review workspace

**Observed mutation:**
- jurisdiction source-certification review

**Current posture:** review-focused governed action.

**V2 home:** **Evidence → Source Review**

**Action:** **CONSOLIDATE + CONTEXTUALIZE**

Should be reached naturally from Evidence/Source objects and relevant work queues.

---

## `/document-intelligence`

**Current purpose:** large document intelligence, extraction, consistency, fraud, requirements, access-control workspace.

**Observed reads:**
- leads
- schemas
- storage posture
- lead detail
- access grants
- extractions
- consistency assessments
- expiry reminders
- fraud-risk assessments
- requirement assessments

**Observed mutations/actions:**
- seed schemas
- queue/review extraction
- review consistency
- issue/revoke access grants
- scan/review fraud risks and related workflows

**Current posture:** action-heavy specialist workspace; ~42.6 KB.

**V2 home:** **Evidence → Documents**

**Action:** **REDESIGN**

Likely needs local sub-navigation rather than one huge surface.

---

## `/cross-department-friction`

**Current purpose:** read organizational blockers/dependencies across departments and create governed human intervention requests.

**Observed reads:**
- Board packet
- departments
- WorkItems
- blockers
- dependencies
- HumanActionRequests
- Activity

**Observed governed mutation:**
- create HumanActionRequest

**Current posture:** mixed organization diagnostic.

**V2 home:** **Organization → Friction / Dependencies**

**Action:** **CONTEXTUALIZE**

Friction should appear from Organization/Missions and become a dedicated analytical mode when needed.

---

## `/agents/review`

**Current purpose:** multi-agent review queue.

**Observed reads:**
- review dashboard
- health
- leads

**Observed mutations:**
- bulk approve
- bulk reject
- bulk convert

**Current posture:** professional action queue.

**V2 home:** **Organization / Tools → Agent Governance**

**Action:** **CONTEXTUALIZE**

High-value capability, but not primary Owner navigation.

---

## `/agents/review/[id]`

**Current purpose:** individual AgentRun review.

**Observed reads:**
- AgentRun detail
- leads

**Observed mutations:**
- approve
- reject
- convert

**Current posture:** focused governed review.

**V2 home:** **Employee/Agent governance inspector**

**Action:** **REDESIGN + CONTEXTUALIZE**

Use as a focused record detail reachable from Agent Governance, Activity, Mission, or Employee views.

---

## `/agents/console`

**Current purpose:** run controlled agents and inspect review state.

**Observed reads:**
- leads
- controlled agents
- review dashboard
- health

**Observed mutations:**
- run controlled agent
- run batch

**Current posture:** professional execution/tooling.

**V2 home:** **Tools / Employee technical controls**

**Action:** **CONTEXTUALIZE**

Do not confuse “employee identity” with raw “agent execution console.”

---

## `/automation`

**Current purpose:** automation rules/events/deliveries.

**Observed reads:**
- corporate accounts
- rules
- events
- deliveries

**Observed mutations:**
- create automation rule
- update rule status

**Current posture:** tools/configuration.

**V2 home:** **Tools → Automation**

**Action:** **REDESIGN + CONTEXTUALIZE**

Not primary Owner navigation; reachable from Tools and relevant domain context.

---

## `/workspace/[department]`

**Current purpose:** department-specific organizational read model with bounded intervention.

**Observed reads:**
- Board packet
- observatory departments
- WorkItems
- blockers
- dependencies
- HumanActionRequests
- Activities
- Contributions

**Observed mutation:**
- create HumanActionRequest

**Current posture:** mixed department workspace.

**V2 home:** **Organization → Department**

**Action:** **REDESIGN**

This becomes the structured counterpart of clicking a department in the architectural world.

---

# 3. Professional / Operator

## `/`

**Current purpose:** Operations Workspace: cases and governed decisions needing attention.

**Current posture:** operational workspace.

**V2 home:** **Work**

**Action:** **REDESIGN**

This becomes the Operator’s task-focused home, not a parallel executive dashboard.

---

## `/profiles`

**Current purpose:** mobility profile editing/history.

**Observed reads:**
- current profile
- profile history
- lead details/health

**Observed mutation:**
- replace current mobility profile

**V2 home:** **Profiles**

**Action:** **REDESIGN**

Forms need V2 field, validation, save-state, history, and provenance patterns.

---

## `/eligibility`

**Current purpose:** eligibility assessment and blockers/gaps.

**Observed read:**
- latest assessment

**Observed mutation/action:**
- evaluate eligibility

**V2 home:** **Work → Eligibility / Pathway**

**Action:** **REDESIGN**

Keep strong “what prevents progress” and next-action framing.

---

## `/planning`

**Current purpose:** comparisons, country ranking, reassessment acceptance.

**Observed reads:**
- pathway comparison/history
- reassessment candidate/acceptances
- country-ranking history

**Observed actions:**
- run comparison
- generate ranking
- create/execute reassessment acceptance

**V2 home:** **Work → Planning**

**Action:** **REDESIGN**

Use clear separation between simulation/comparison and canonical action.

---

## `/pathways`

**Current purpose:** pathway catalogue and regulated pathway/version lifecycle.

**Observed reads:**
- pathways
- jurisdictions
- official sources
- SourceSnapshots
- VerifiedRules
- regulatory impacts

**Observed actions:**
- create pathway/version
- publish
- retire
- review regulatory impact

**V2 home:** **Pathways**

**Action:** **REDESIGN**

Requires strong draft/published/retired and evidence lineage grammar.

---

## `/timelines`

**Current purpose:** mobility timeline generation/activation/milestone transitions.

**Observed reads:**
- leads
- latest comparison
- timelines

**Observed actions:**
- generate timeline
- activate timeline
- transition milestone

**V2 home:** **Work → Timeline**

**Action:** **REDESIGN**

Distinguish generated proposal from activated/canonical timeline.

---

## `/communications`

**Current purpose:** communication-draft list.

**Observed reads:**
- communication drafts
- health

**V2 home:** **Communication**

**Action:** **REDESIGN**

Use one communication taxonomy with employee/Mission/case context.

---

## `/communications/auto`

**Current purpose:** automated communication templates and scheduled/sent messages.

**Observed reads:**
- templates
- auto communications

**Observed action:**
- create automated communication

**V2 home:** **Communication → Automation**

**Action:** **CONTEXTUALIZE**

---

## `/communications/drafts/[id]`

**Current purpose:** individual communication draft review/edit.

**Observed read:**
- draft

**Observed mutations:**
- update draft
- mark reviewed

**V2 home:** **Communication → Draft**

**Action:** **REDESIGN**

Focused detail rather than generic page styling.

---

## `/communications/leads/[id]`

**Current purpose:** communications for a specific lead.

**Observed read:**
- lead communications

**Observed actions:**
- generate draft pack
- mark all reviewed

**V2 home:** **Profile/Case → Communication**

**Action:** **CONTEXTUALIZE**

---

## `/coaching`

**Current purpose:** agent coaching/training cases and feedback.

**Observed reads:**
- coach reviews
- training cases

**Observed actions:**
- generate training cases
- run training case
- submit feedback

**V2 home:** **Tools → Agent Quality**

**Action:** **CONTEXTUALIZE**

---

## `/corporate-mobility`

**Current purpose:** corporate accounts, controlled mobility cases, sponsors, dependants, compliance, tasks, venture/evidence.

**Observed posture:** very action-heavy; 9 forms, ~20 buttons, ~41.5 KB.

**V2 home:** **Tools / Corporate Mobility**

**Action:** **AUDIT DOMAIN + REDESIGN**

This likely deserves a dedicated local workspace architecture rather than being one monolithic page.

---

## `/business-advisory`

**Current purpose:** commercial objective → ranked route map / strategic brief.

**Observed reads:**
- existing advisories
- leads

**Observed action:**
- create business advisory

**V2 home:** **Tools → Advisory**

**Action:** **AUDIT DOMAIN + REDESIGN**

---

## `/investment-mobility`

**Current purpose:** verified investment programs and evidence lifecycle.

**Observed reads:**
- programs
- pathways
- official sources
- readiness
- rule proposals
- snapshots

**Observed actions:**
- create program
- publish version
- review proposal

**V2 home:** **Tools → Investment**

**Action:** **AUDIT DOMAIN + REDESIGN**

---

## `/investment-suitability`

**Current purpose:** client-specific investment route comparison/suitability.

**Observed reads:**
- leads
- programs
- suitability assessments

**Observed action:**
- create assessment

**V2 home:** **Tools → Investment → Suitability**

**Action:** **CONSOLIDATE / AUDIT DOMAIN**

Potentially local navigation within the Investment workspace.

---

## `/family-office`

**Current purpose:** family/ownership/wealth/mobility coordination assessment.

**Observed reads:**
- leads
- assessments

**Observed actions:**
- create assessment
- review/update assessment

**V2 home:** **Tools → Family Office**

**Action:** **AUDIT DOMAIN + REDESIGN**

---

## `/tax-residency`

**Current purpose:** residence/treaty fact pattern, evidence, issue map.

**Observed reads:**
- leads
- official sources
- SourceSnapshots
- treaty evidence
- tax residency assessments

**Observed actions:**
- create assessment
- create treaty evidence
- review/update assessment/evidence

**V2 home:** **Tools → Tax**

**Action:** **AUDIT DOMAIN + REDESIGN**

Truth-class and evidence-authority presentation are critical.

---

# 4. Authority Operations

## `/authority-appointments`

**Purpose:** create/manage authority appointments.

**Reads:** applications, appointments.

**Actions:** create appointment, update status.

**V2 home:** **Work → Authority**

**Action:** **CONTEXTUALIZE**

---

## `/agency-submissions`

**Purpose:** create/manage agency submissions.

**Reads:** applications, submissions.

**Actions:** create submission, update status.

**V2 home:** **Work → Authority**

**Action:** **CONTEXTUALIZE**

---

## `/external-agency-assignments`

**Purpose:** external agency directory and assignments.

**Reads:** applications, agencies, assignments.

**Actions:** create/update agencies and assignments.

**V2 home:** **Work → Authority / External Parties**

**Action:** **CONTEXTUALIZE**

---

## `/authority-submission-checklist`

**Purpose:** template library + per-application authority checklist.

**Reads:** applications, templates, checklist items.

**Actions:** create template, apply template, create/update/delete items, emit reminders.

**V2 home:** **Case/Work → Authority Checklist**

**Action:** **CONTEXTUALIZE**

This is best reached from the relevant case/application instead of global navigation.

---

# 5. Case / Lead / Intake

## `/leads/[id]`

**Current purpose:** large case detail/decision workspace.

**Observed reads:**
- lead detail
- eligibility
- pathway comparison
- mobility timeline
- document requirements
- authority appointments
- submissions
- agency assignments
- authority checklist

**Current posture:** primarily composed read model with links/next actions.

**Finding:** ~51 KB — one of the largest pages.

**V2 home:** **Work / Profile / Case**

**Action:** **REDESIGN**

Likely becomes a case workspace with stable local navigation rather than one giant page.

---

## `/opportunities`

**Purpose:** opportunity catalog and matching.

**Observed reads:** opportunities.

**Observed actions:** seed catalog, run matching.

**V2 home:** **Tools / Opportunities**

**Action:** **AUDIT DOMAIN**

---

## `/intake`

**Purpose:** public/initial intake and document-assisted case creation.

**Observed action:** create public intake.

**V2 home:** **Work → Intake** or external acquisition flow.

**Action:** **REDESIGN**

Should not inherit internal operator density when used by external users.

---

# 6. Mobility User / External Portals

## `/my-mobility`

**Current purpose:** case-first landing page.

Current content already articulates useful Mobility mental-model areas:

- Case
- Pathway
- Documents
- Timeline
- Next actions
- Communication

It explicitly avoids exposing protected case records before secure portal access.

**V2 home:** **Mobility Overview**

**Action:** **REDESIGN**

This is directionally aligned with V2 and should remain simple.

---

## `/portal`

Thin wrapper around `ClientPortalPage`.

**V2 home:** **My Case**

**Action:** **PRESERVE WRAPPER + REDESIGN UNDERLYING COMPONENT**

---

## `/return`

Legacy wrapper around the same `ClientPortalPage`.

**Action:** **PRESERVE COMPATIBILITY / ALIAS**

Do not delete until external links and return flows are verified.

---

## `/partner-portal`

Thin wrapper around `EcosystemPortalPage`.

**V2 home:** external ecosystem/partner workspace.

**Action:** **AUDIT DOMAIN + REDESIGN UNDERLYING COMPONENT**

---

# 7. Behavioral conclusions

## 7.1 The app contains four distinct interaction classes

### A. Read-only transparency
Examples:
- Decision Explorer
- Owner Inbox
- portions of Cockpit/observatory

V2 design priority:
clarity, hierarchy, comparison, provenance.

### B. Governed authority action
Examples:
- Board control
- Agent review
- source review
- regulatory review

V2 design priority:
error prevention, authority cues, confirmation, evidence context.

### C. Professional execution
Examples:
- document intelligence
- pathways
- planning
- authority operations
- corporate mobility

V2 design priority:
dense but structured local workspaces; fast navigation; stable forms/tables.

### D. Mobility/external
Examples:
- My Mobility
- Client Portal
- Partner Portal
- Intake

V2 design priority:
simplicity, trust, privacy, next action, low internal-system leakage.

These classes should not all share one generic page template.

---

# 8. V2 navigation consequence

The route audit confirms the selected V2 IA.

Owner primary navigation should not contain validation, source review, agent review, automation, and friction as constant peer destinations.

Operator primary navigation should not contain 26 permanent links.

Instead:

```text
PRIMARY DOMAIN
      ↓
LOCAL NAVIGATION
      ↓
CONTEXTUAL OBJECT
      ↓
POWER SEARCH / COMMAND
```

Deep routes remain available.

---

# 9. V2 mutation/authority consequence

The route audit also confirms that V2 needs a formal action taxonomy:

```text
READ
RECOMMEND
DRAFT
SIMULATE
REVIEW
APPROVE
REJECT
PUBLISH
ACTIVATE
TRANSITION
CONTROL
DELETE/RETIRE
EXTERNAL EFFECT
```

UI treatment must derive from action semantics and authority, not merely from “primary/secondary button” styling.

Examples:

- `evaluate` must not look like `approve`
- `generate` must not look like `activate`
- `recommendation` must not look like `human decision`
- `publish` must be visually distinct from `save draft`
- `organization control` must be stronger than a normal form submit.

This becomes part of the AIOS Design Skill.

---

# 10. V2 workspace families derived from real routes

The 44 routes can be served by a smaller number of layout/workspace families:

1. **Executive Situation**
2. **Organization / Spatial**
3. **Mission**
4. **Decision / Authority**
5. **Evidence / Review**
6. **Intelligence**
7. **Case / Profile**
8. **Professional Operations**
9. **Configuration / Tools**
10. **Mobility User**
11. **External Partner**
12. **Temporal / Replay**

This is a major V2 simplification: reduce visual-system count without reducing domain capability.

---

# 11. Phase 1B status

```text
44 App Router pages identified
Owner/organization behavior classified
Operator behavior classified
Authority operations classified
Mobility/external behavior classified
Primary V2 home mapped
Initial migration action mapped

Pass B — COMPLETE
```

Next:

**Phase 1C — Component + State Audit**

Focus:
- repeated cards/panels/status patterns,
- loading/empty/error/partial states,
- forms and action patterns,
- technical disclosure,
- evidence/provenance,
- shells/portals,
- Living Organization component graph,
- component candidates for preserve/refactor/retire.
