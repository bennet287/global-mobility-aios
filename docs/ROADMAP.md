# Global Mobility AIOS Delivery Roadmap

The canonical product scope is defined in
[`GLOBAL_MOBILITY_AIOS_VISION_V1.md`](GLOBAL_MOBILITY_AIOS_VISION_V1.md). This
roadmap turns that complete vision into incremental delivery phases. A later phase
does not remove any capability from the canonical blueprint.

## Delivery Status — v11.4.1 (2026-07-25)

- Enhanced the Business & Wealth Mobility situation-advisory endpoint (`POST /api/v1/business-mobility-advisory/advise`) to deliver situation-aware, commercially specific recommendations with a responsive success meter.
- Added intent-specific actions and critical factors for startup, expansion, passive investment, family-office relocation, tax-residency planning, and asset-and-family mobility scenarios.
- Introduced per-strategy fit scoring so the highest-matching lawful option is recommended even when it is not the first archetype in the intent map.
- Risk-flagged situations now return the strongest lawful alternative plus remediation/specialist guidance instead of a generic refusal; prohibited-conduct signals remain capped and escalated with lawful remediation offered.
- Updated `docs/BUSINESS_WEALTH_ADVISORY_V11_4.md` and regression tests.
- See `docs/BUSINESS_WEALTH_ADVISORY_V11_4.md`.

## Delivery Status — v12.4.1 (2026-07-25)

Current database migration head: `0053_automation_delivery_reconciliation`.

- v12.4.1 hardens the governed automation connector layer before external-provider integrations are enabled. Connector credentials are encrypted at rest using Fernet and masked on every API response and audit-log entry.
- Provider adapters now expose a `health_check` contract; the `console` adapter reports healthy and the `smtp` adapter verifies login against the configured server. `POST /api/v1/automation/connectors/{config_id}/health-check` runs the check and returns `200` or `503` while always writing an audit record.
- Delivery reconciliation is introduced for console deliveries: long-dispatched console messages are marked `reconciled` with `reconciled_at` and audited. The `reconcile_automation_deliveries_task` Celery beat task runs once per day.
- Regression tests cover encryption at rest, credential masking, health-check success and failure, and reconciliation.
- See `docs/GOVERNED_AUTOMATION_FOUNDATION_V12_3.md`.

## Delivery Status — v12.8 (2026-07-24)

Current database migration head: `0051_authority_submission_checklist`.

- v12.8 adds authority submission checklists. Operators can define reusable per-authority templates of required documents, fees, forms, and steps, and then apply those templates to individual applications.
- Checklist items track a status of `pending`, `completed`, or `not_applicable`. Applying a template is idempotent; items already present for an application are not duplicated. Manual items can also be added.
- Items can be listed per application or across applications and filtered by status. Every template creation, item creation, status change, and deletion is audited with before/after state.
- See `docs/AUTHORITY_SUBMISSION_CHECKLIST_V12_8.md`. Blocking gates that require checklist completion before submission, and reminders tied to pending items, remain future slices.

## Delivery Status — v12.8.1 (2026-07-24)

Current database migration head: `0051_authority_submission_checklist`.

- v12.8.1 bridges external agency assignment status changes into the governed automation outbox. When an assignment status changes and the application's lead is linked to an active corporate mobility case, an automation event is created (`external_agency_assignment.status_changed`).
- The event carries the application, lead, case reference, and new status, scoped to the linked corporate account. Existing corporate automation rules can match it and route handoff updates through email, messaging, calendar, or CRM connectors under the same review and retry controls as case, compliance, task, appointment, and submission events.
- When no corporate case link exists, the status change still completes but no automation event is created, keeping the bridge scoped to the employer/corporate workflow boundary.
- See `docs/EXTERNAL_AGENCY_ASSIGNMENT_V12_7.md` and `docs/GOVERNED_AUTOMATION_FOUNDATION_V12_3.md` for the combined domain description.

## Delivery Status — v12.8.2 (2026-07-24)

Current database migration head: `0051_authority_submission_checklist`.

- v12.8.2 adds blocking gates and governed reminders to the authority submission checklist. `POST /api/v1/agency-submissions` now rejects submission with `409` when any required checklist item for the target authority is still `pending`. Marking the item `completed` or `not_applicable` satisfies the gate.
- A new endpoint, `POST /api/v1/applications/{application_id}/authority-checklist/reminders`, emits one `authority_checklist.reminder` automation event per pending checklist item when the application's lead is linked to an active corporate mobility case.
- Reminder events are idempotent per item per UTC day and flow through the same account-scoped rule matching, human review, retry, and delivery controls as other automation events.
- See `docs/AUTHORITY_SUBMISSION_CHECKLIST_V12_8.md` and `docs/GOVERNED_AUTOMATION_FOUNDATION_V12_3.md`.

## Delivery Status — v12.8.3 (2026-07-24)

Current database migration head: `0051_authority_submission_checklist`.

- v12.8.3 adds scheduled authority checklist reminders. A Celery beat task runs daily to scan for pending checklist items and emit one `authority_checklist.reminder` automation event per pending item for applications whose lead is linked to an active corporate mobility case.
- The scan is idempotent per item per UTC day and flows through the same account-scoped rule matching, human review, retry, and delivery controls as other automation events. This removes the need for operators to trigger reminders manually.
- See `docs/AUTHORITY_SUBMISSION_CHECKLIST_V12_8.md` and `docs/GOVERNED_AUTOMATION_FOUNDATION_V12_3.md`.

## Delivery Status — v12.8.4 (2026-08-01)

Current database migration head: `0051_authority_submission_checklist`.

- v12.8.4 extends the client portal dashboard with agency workflow visibility. Clients can now see authority appointments, agency submissions, external agency assignments, and authority checklist items for their lead, scoped by the existing lead-scoped portal grant.
- Projections remain client-safe: internal notes, actor identities, audit fields, and contact details are omitted. Only status, authority/agency names, reference numbers, scheduled/submitted/handoff/completed timestamps, and checklist labels/categories/status are exposed.
- The dashboard aggregates workflow data across all applications belonging to the lead.
- The client portal TypeScript types and UI were updated to render the four agency workflow sections (appointments, submissions, external agency assignments, and authority checklist grouped by authority).
- See `docs/CLIENT_PORTAL_FOUNDATION_V12_0.md`.

## Delivery Status — v12.8.7 (2026-08-01)

Current database migration head: `0055_client_portal_device_binding`.

- v12.8.7 delivers the Phase 12 native/mobile slice as a PWA/mobile-web foundation with device-specific secure session controls for the client portal.
- `ClientPortalAccessGrant` now carries `device_fingerprint`, `device_label`, and `user_agent`. The first successful dashboard access binds the presenting device fingerprint to the grant; subsequent accesses require the same fingerprint.
- A mismatched or missing device fingerprint returns `403` with `action: "request_new_grant"`, and the portal UI explains that the client must contact their consultant for a new access link.
- The portal gained a Next.js PWA manifest (`/manifest.json`), a minimal offline-aware service worker (`/sw.js`), mobile viewport meta tags, and a browser install prompt. The bound device label is shown in the session header.
- Existing grants remain usable until first access under the new code binds them, preserving backward compatibility.
- See `docs/CLIENT_PORTAL_FOUNDATION_V12_0.md`. A full native wrapper remains a future, usage-driven decision.

## Delivery Status — v12.8.5 (2026-07-24)

Current database migration head: `0051_authority_submission_checklist`.

- v12.8.5 adds authority appointment reminders. A Celery beat task runs every hour to scan for scheduled appointments occurring within the next 24 hours and emit one `appointment.reminder` automation event per appointment when the linked application's lead is associated with an active corporate mobility case.
- Reminder events are idempotent per appointment per UTC day and include authority name, appointment type, scheduled time, location, and reference number. They flow through the same account-scoped rule matching, human review, retry, and delivery controls as other automation events, so corporate automation rules can route them through email, messaging, or calendar connectors.
- See `docs/AUTHORITY_APPOINTMENT_TRACKING_V12_5.md` and `docs/GOVERNED_AUTOMATION_FOUNDATION_V12_3.md`.

## Delivery Status — v12.8.6 (2026-07-24)

Current database migration head: `0052_external_agency_assignment_sla`.

- v12.8.6 adds SLA tracking to external agency assignments. `ExternalAgency` now carries `sla_due_hours` (default 72) and `ExternalAgencyAssignment` carries `sla_due_at`, `sla_status`, and `sla_breached_at`.
- New assignments inherit the agency's SLA window and start `on_track`. A scheduled Celery task re-evaluates active assignments hourly, marking them `due_soon` within 12 hours of the due time and `breached` once the due time passes. Completed assignments are marked `completed` (or `breached` if finished after the due time); cancelled assignments are marked `completed`.
- The client portal dashboard exposes `sla_due_at`, `sla_status`, and `sla_breached_at` alongside each external agency assignment.
- See `docs/EXTERNAL_AGENCY_ASSIGNMENT_V12_7.md`.

## Delivery Status — v12.7 (2026-07-24)

Current database migration head: `0050_external_agency_assignment`.

- v12.7 adds external agency assignment tracking. Operators can maintain a directory of external mobility agencies (name, country, city, contact details, website) and mark each agency as `active`, `suspended`, or `retired`.
- Applications can be assigned to an active external agency with a controlled handoff lifecycle: `assigned` → `in_progress` → `handed_off` → `completed` or `cancelled`. Terminal states are immutable.
- Only one active assignment is allowed per application at a time. `handoff_at` and `completed_at` are recorded automatically when the assignment reaches those statuses.
- Assignments can be listed per application or across the system and filtered by status. Every agency and assignment mutation is audited with before/after state.
- See `docs/EXTERNAL_AGENCY_ASSIGNMENT_V12_7.md`. Agency portal sync, SLA tracking, and automation outbox integration for handoff events remain future slices.

## Delivery Status — v12.6.1 (2026-07-24)

Current database migration head: `0049_agency_submission_tracking`.

- v12.6.1 bridges authority appointment and agency submission status changes into the governed automation outbox. When an appointment or submission status changes and the application's lead is linked to an active corporate mobility case, an automation event is created (`appointment.status_changed` or `submission.status_changed`).
- Existing corporate automation rules can now match these events and route notifications through email, messaging, calendar, or CRM connectors under the same review and retry controls as case/compliance/task events.
- When no corporate case link exists, the status change still completes but no automation event is created, keeping the bridge scoped to the employer/corporate workflow boundary.
- See `docs/GOVERNED_AUTOMATION_FOUNDATION_V12_3.md` and the appointment/submission feature docs for the combined domain description.

## Delivery Status — v12.6 (2026-07-24)

Current database migration head: `0049_agency_submission_tracking`.

- v12.6 adds agency submission tracking for applications. Operators can record when and how an application was submitted to a government or mobility agency (online, in person, courier, or agency hand-off), including the authority name, reference number, tracking URL, and notes.
- Submissions move through a forward-only lifecycle: `submitted` → `acknowledged` → `under_review` → `decision_received` or `returned`. Terminal states are immutable.
- Submissions can be listed for an application and filtered by status. Every creation and status change is recorded in the audit log with the actor and before/after state.
- See `docs/AGENCY_SUBMISSION_TRACKING_V12_6.md`. Authority-specific submission checklists, external portal sync, and automation outbox integration remain future slices.

## Delivery Status — v12.5 (2026-07-24)

Current database migration head: `0048_authority_appointment_tracking`.

- v12.5 starts Phase 12's government and mobility-agency workflow layer with authority appointment tracking for applications.
- Operators can schedule application-facing appointments with consulates, visa application centres, biometric collection points, and other agencies. Each appointment records its type (`biometric`, `interview`, `document_submission`, `other`), authority name, location, scheduled time, timezone, and optional reference number.
- Status transitions are controlled: new appointments are `scheduled`, and operators can move them only to `completed`, `cancelled`, or `no_show`. Terminal states are immutable.
- Appointments can be listed for an application and filtered by status. Every creation and status change is recorded in the audit log with the actor and before/after state.
- See `docs/AUTHORITY_APPOINTMENT_TRACKING_V12_5.md`. Calendar sync, reminder notifications, and client-portal visibility remain future slices.

## Delivery Status — v12.4 (2026-07-24)

Current database migration head: `0047_automation_connector_config`.

- v12.4 adds credential-backed connector configs for email, messaging, calendar, and CRM channels. Each config is scoped to one active corporate account and one channel; only one active config is allowed per account/channel pair.
- Provider adapters follow a minimal abstract interface. The `console` adapter is used for local/test runs; the `smtp` adapter sends real email via STARTTLS using credentials stored in the connector config. Credentials are persisted as JSON and should be encrypted at rest or moved to a secret manager in production.
- Deliveries now link to an active connector config at creation time and expose `next_attempt_at` for scheduled retry. The `dispatch_automation_deliveries_task` Celery beat worker runs every 60 seconds and dispatches due `ready` or `retry` deliveries.
- Dispatch attempts are limited to 3 with exponential backoff (60s, 300s, 900s). A missing connector or adapter failure moves the delivery to `retry` and records the error; the final attempt moves it to `failed` with `next_attempt_at` cleared. Every dispatch and retry attempt is audited.
- Operators can trigger dispatch per delivery via `POST /api/v1/automation/deliveries/{delivery_id}/dispatch`. Connector config management endpoints allow create, list, and status changes with audit.
- See `docs/GOVERNED_AUTOMATION_FOUNDATION_V12_3.md` for the full automation domain description; the v12.4 additions are appended there.

## Delivery Status — v12.3 (2026-07-23)

Current database migration head: `0046_governed_automation_outbox`.

- v12.3 establishes an account-scoped case-event ledger and governed multichannel outbox for email, messaging, calendar, and CRM actions.
- Corporate case creation and status changes, compliance creation and resolution, and relocation-task transitions now create idempotent domain events in the same database transaction as the source change.
- Active rules match only events from their corporate account. They create minimized channel projections without internal notes or contact fields; cross-account rules never receive another tenant's event.
- Email, messaging, and calendar actions always require a different human reviewer before becoming connector-ready. CRM-only rules may be explicitly approval-free, while dispatch remains separate from provider-receipt recording.
- The new Automation Hub supports account selection, rule creation, pause/reactivation, immutable event visibility, delivery review, and operational readiness metrics. See `docs/GOVERNED_AUTOMATION_FOUNDATION_V12_3.md`.

## Delivery Status — v12.2 (2026-07-23)

Current database migration head: `0045_partner_api_credentials`.

- v12.2 adds stable path-versioned public metadata and partner data contracts at `/api/public/v1` and `/api/partner/v1`.
- Partner API credentials are expiring, revocable, scope-limited, and bound to one active corporate account. Raw keys are returned only at issuance and only their SHA-256 digests are persisted.
- Account, case, and compliance projections derive tenant scope exclusively from the credential. They omit internal notes, contact details, lead identifiers, evidence, reviews, audit records, and operator actions.
- Every successful partner request is audited. Missing scopes are forbidden, while invalid, expired, revoked, and suspended-account credentials fail closed.
- Responses identify contract version `1.0`, disable shared caching for tenant data, and use bounded page pagination. See `docs/VERSIONED_PUBLIC_PARTNER_APIS_V12_2.md`.

## Delivery Status — v12.1 (2026-07-23)

Current database migration head: `0044_ecosystem_portal_tenancy`.

- v12.1 adds a dedicated employer and authorized-partner workspace without extending internal operator roles to external users.
- Every expiring grant is scoped to exactly one corporate account and one recorded audience. Raw tokens are returned once and persisted only as SHA-256 digests.
- All downstream case, employee-label, task, and compliance queries derive their scope from the resolved grant. The caller cannot supply or switch the tenant identifier.
- The external projection omits internal notes, lead IDs, contact details, review records, truth claims, controlled evidence, audit records, and operator actions. Suspended or closed accounts fail closed.
- Operators can issue tenant links from Corporate Mobility; creation, access, expiry, and revocation are audited. See `docs/ECOSYSTEM_PORTAL_TENANCY_V12_1.md`.

## Delivery Status — v12.0 (2026-07-23)

Current database migration head: `0043_client_portal_foundation`.

- v12.0 starts Phase 12 with a dedicated responsive client web portal backed by revocable, expiring, lead-scoped grants. Raw portal tokens are returned once and stored only as SHA-256 digests.
- The client-safe dashboard exposes status, next action, milestone progress, and document metadata without returning internal notes, truth claims, review queues, agent outputs, or cross-client data.
- The legacy public email-or-phone lookup is disabled. New intake and operator-issued links use the same portal-token boundary; create, access, expiry, and revocation are audited.
- The internal lead workspace can issue a one-time portal link, while the client routes remove the token from the address bar, keep it in session storage, and hide internal agent controls.
- See `docs/CLIENT_PORTAL_FOUNDATION_V12_0.md`. Native/mobile access, partner tenancy, external API contracts, ecosystem automation, and agency workflows remain Phase 12 work.

## Delivery Status — v11.12 (2026-07-23)

Current database migration head: `0042_tax_residency_treaty`.

- v11.12 closes the missing reviewer-separation guard in pathway publication. A pathway draft creator can no longer publish the same version; the affected pathway, ranking, regulatory-impact, reassessment, and investment tests now use an explicitly different reviewer.
- Austria's replacement Self-employed Key Worker pathway version passed an independent publication review against its active investment-domain official source, immutable snapshot, and four verified rules.
- A separately proposed investor-entrepreneur program version records the EUR 100,000 capital-transfer indicator as non-exclusive, preserves the official alternative macroeconomic-benefit bases, exposes authority separation, evidence, fees, benefits, and material risks, and makes no eligibility or approval guarantee.
- A different authenticated reviewer published the program. Austria's investment-program onboarding state is now `published` with no blockers, completing Phase 11's independently verified jurisdiction-program onboarding milestone.
- The durable publication record is stored at `docs/AUSTRIA_PROGRAM_PUBLICATION_V11_12.md`.

## Delivery Status — v11.11 (2026-07-23)

Current database migration head: `0042_tax_residency_treaty`.

- v11.11 adds a client-linked tax-residency issue map and a separate source-pinned treaty evidence registry. The registry only accepts active tax-domain official sources and their exact content-addressed snapshots.
- Treaty records remain unavailable to client assessments until a different authenticated reviewer publishes them. Assessments reject unrelated jurisdiction pairs, unpublished records, and records outside the selected tax year.
- Readiness is split across dated fact completeness, client-owned controlled evidence, treaty grounding, and specialist coordination. The result exposes domestic-residence, dual-residence, entity/permanent-establishment, employment/payroll, and departure/arrival workstreams without making a tax determination.
- Every assessment requires a different specialist reviewer. Concealment, sham-residence, tax-evasion, false-return, backdating, or misrepresentation signals prevent operationalization and cap readiness.
- The new Tax & Treaty workspace combines the client fact pattern, issue matrix, accountable workstreams, source-controlled proposal desk, and independent publication queue.

## Delivery Status — v11.10 (2026-07-23)

Current database migration head: `0041_family_office_mobility`.

- v11.10 adds a dedicated HNWI and family-office mobility control plane instead of leaving private-client work as a generic advisory label.
- Each immutable assessment links to a principal client and evaluates five transparent workstreams: identity and family, source of wealth and funds, ownership and control, governance/banking/specialists, and source-controlled mobility routes.
- Client-owned controlled evidence, beneficial-ownership disclosure, PEP/sanctions screening posture, entity inventories, tax and legal adviser coverage, succession continuity, banking readiness, and target-jurisdiction grounding now produce explicit blockers and accountable actions.
- Concealment, evasion, sanctions-circumvention, false-document, or ownership-misrepresentation signals cap readiness and prevent operationalization. Every assessment remains pending independent human review and makes no eligibility, tax, banking, investment, or asset-protection guarantee.
- The new Family Office workspace presents the readiness components and workstreams without hiding material gaps behind a single score.

## Delivery Status — v11.9 (2026-07-23)

Current database migration head: `0040_investment_rule_review`.

- v11.9 adds an immutable, source-pinned investment-rule proposal ledger with explicit pending, approved, and rejected decisions.
- A proposal can only target a draft business, investment, wealth, or entrepreneur pathway backed by an active same-country official source and its exact content-addressed snapshot.
- Approval requires a different authenticated reviewer. It creates independently verified rules and a replacement pathway draft while superseding the unverified draft; it does not publish the pathway or any investment program.
- The Investment Programs workspace now exposes pending rule statements, source provenance, decision notes, and separate approve/reject controls. Austria's v11.8 extraction passed independent review on 2026-07-23, producing four active verified rules and a replacement pathway draft; the pathway itself remains unpublished.

## Delivery Status — v11.8 (2026-07-23)

Current database migration head: `0039_investment_suitability`.

- v11.8 starts real jurisdiction program onboarding with Austria's official Self-employed Key Worker route. The controlled retriever returned HTTPS 200 and stored immutable snapshot SHA-256 `905a6e47c821be64863efc9037e99b611e31d0d797a6b6799d1fc8b2e5f8ba38`.
- A source-grounded Austria investment pathway version now exists as a draft. It records the macroeconomic-benefit test, the EUR 100,000 capital-transfer indicator and its non-exclusive alternatives, required evidence, authority roles, duration context, fees, and material risks.
- The evidence pack passed independent rule review on 2026-07-23. Four source-pinned rules are active and the unverified pathway draft was superseded by a replacement draft; separate pathway publication review is still required. This does not create eligibility, approval, return, tax, or capital-safety claims, and no investment program is published yet.
- Investment onboarding readiness now exposes the verified-rule gate separately, preventing a draft pathway from appearing immediately publishable when reviewed rules are still absent.

## Delivery Status — v11.7 (2026-07-23)

Current database migration head: `0039_investment_suitability`.

- v11.7 adds a jurisdiction-level onboarding readiness pipeline across eligible official sources, content-addressed snapshots, independently published pathways, program drafts, and independently published program versions.
- The Investment Programs workspace now explains why a jurisdiction is blocked and identifies its next controlled action instead of presenting an unexplained empty catalogue.
- Program grounding now rejects sources from unrelated regulatory domains; a visa-domain source cannot be reused as investment evidence merely because its country matches.
- The software workflow is complete, but independently verified jurisdiction program data remains operational work and stays unchecked in Phase 11 until real programs pass every gate.

## Delivery Status — v11.6 (2026-07-23)

Current database migration head: `0039_investment_suitability`.

- v11.6 adds client-specific investment-mobility readiness comparisons across independently published program versions. Assessments rank routes using declared capital coverage, controlled evidence, family scope, risk constraints, and currency comparability while preserving the exact program, pathway, source, and snapshot versions used.
- Currency mismatches fail closed without an invented exchange rate, cross-client evidence is rejected, source-of-funds and capital-preservation constraints become explicit blockers, and concealment or evasion signals cap readiness and prevent operationalization.
- Every comparison is immutable, audited, pending independent human review, and explicitly disclaims eligibility, approval probability, investment returns, tax treatment, or capital safety. The new Investor Suitability workspace exposes score components, blockers, and controlled next actions.

## Delivery Status — v11.5 (2026-07-23)

Current database migration head: `0038_investment_programs`.

- v11.5 adds a governed residence-by-investment, citizenship-by-investment, and investor-entrepreneur program catalogue with immutable versions, recorded capital thresholds, qualifying structures, holding and presence context, family scope, due diligence, fees, benefits, and material risks.
- Every draft must reference an active business/investment pathway, its published version, an active same-country official source, and a content-addressed snapshot. Publication requires a different authenticated reviewer and supersedes rather than rewrites the previous published version.
- Published programs now strengthen Business & Wealth advisory grounding for investment-related intentions. Thresholds are not treated as eligibility, capital is not treated as suitability, and the interface rejects guaranteed authority-outcome claims. Jurisdiction-by-jurisdiction program evidence onboarding remains operational work.

## Delivery Status — v11.4 (2026-07-23)

Current database migration head: `0037_business_advisory`.

- v11.4 adds a Business & Wealth Mobility advisory workspace that converts a detailed commercial situation into three ranked strategy options, explicit blockers, evidence requirements, and a sequenced action plan.
- A new `POST /api/v1/business-mobility-advisory/advise` endpoint returns a single recommended solution with a 0–100 success meter, alternative options, critical factors, and concrete next actions. It uses the configured LLM when available and falls back to deterministic scoring when no LLM is configured or when risk flags are present.
- The feasibility meter combines information completeness, controlled evidence, commercial fit, and published-pathway grounding. It is decision-support readiness, not an approval probability, legal or tax opinion, investment recommendation, or authority prediction.
- Assessments are immutable pending-review records with actor attribution and audit events. Material risk indicators trigger specialist escalation; deception, concealment, sham arrangements, evasion, and unlawful circumvention are not operationalized and instead produce blockers plus lawful remediation paths.

## Delivery Status — v11.3 (2026-07-23)

Current database migration head: `0036_entrepreneur_ventures`.

- v11.3 adds entrepreneur/startup case dossiers linked to existing founder leads, controlled venture evidence, optional declared funding metadata, and append-only independent completeness decisions.
- Venture dossiers are restricted to entrepreneur/startup cases, founder and destination consistency is enforced, linked documents must belong to the founder, and review submission requires an explicit completeness attestation plus at least one controlled document.
- Review confirms dossier completeness only. The API and workspace expose no visa eligibility, investment qualification, funding verification, program recommendation, or autonomous regulated conclusion.

## Delivery Status — v11.2 (2026-07-23)

Current database migration head: `0035_relocation_tasks`.

- v11.2 adds account-scoped relocation task orchestration with owner roles, due dates, explicit dependencies, controlled lifecycle transitions, and immutable terminal states.
- Dependency tasks must complete before downstream work becomes ready. Blocking and cancellation require operator notes, sensitive completions enter an approval state, and the submitting operator cannot approve their own work.
- Independent task decisions are append-only and actor-attributed, all task mutations are audited, closed cases reject new or changed tasks, and the Corporate Mobility case control plane exposes the governed task sequence without automating regulated actions.

## Delivery Status — v11.1 (2026-07-23)

Current database migration head: `0034_corp_relationships`.

- v11.1 adds account-scoped sponsor entities, immutable-history sponsor assignments, dependant links to existing consent-controlled lead profiles, and case compliance events.
- Every relationship mutation is actor-attributed and audited. Cross-account sponsorship is blocked, duplicate active relationships are rejected, removed links and resolved events are terminal, closed cases cannot receive new relationships, and every compliance event remains explicitly human-review-required.
- The Corporate Mobility workspace now provides a focused case control plane for sponsor assignment, dependant linking, and compliance scheduling without creating eligibility, sponsorship approval, filing, or autonomous compliance decisions.

## Delivery Status — v11.0 (2026-07-23)

Current database migration head: `0033_corporate_mobility_foundation`.

- v11.0 starts Phase 11 with governed corporate accounts and corporate mobility cases linked to existing employee leads. Cases capture relocation, dependant, or sponsor-compliance scope, origin and destination, sponsor context, target dates, and compliance deadlines while remaining human-review-required.
- All account and case mutations are actor-attributed and audited. State transitions are explicit, closed records are immutable, read-only mutation is forbidden, employee links are validated, and no delete, eligibility, sponsorship approval, application submission, or autonomous compliance-decision path is exposed.
- The new Corporate Mobility operator workspace supports account onboarding, account-scoped case management, employee linking, compliance dates, and controlled transitions. Backend tests, migration checks, repository policy checks, the production Next.js build, and all 22 frontend route generations pass.

## Delivery Status — v10.22.28 (2026-07-23)

Current database migration head: `0042_tax_residency_treaty`.

- The user separately authorized publication of the 17 independently approved initial-rule assertions for Albania (`AL`), Bosnia and Herzegovina (`BA`), Liechtenstein (`LI`), Malta (`MT`), Hungary (`HU`), Tanzania (`TZ`), Somalia (`SO`), Sierra Leone (`SL`), Namibia (`NA`), Uganda (`UG`), Zambia (`ZM`), Liberia (`LR`), Lesotho (`LS`), Eswatini (`SZ`), Chile (`CL`), Malaysia (`MY`), and the Republic of Korea (`KR`).
- All 17 assertions were published under actor `bennet-coverage-publisher` with an explicit provenance attestation. Every publication created an active verified rule and moved its jurisdiction to coverage-ready.
- Coverage readiness moved from **65/243 to 82/243**. Senegal (`SN`) remains the only pending initial assertion from this packet; the global coverage claim remains false.
- The durable publication receipt is stored at `coverage-operations-receipts/v10_22_28_assertion_publication/PUBLICATION_RECEIPT.md`.

## Delivery Status — v10.22.27 (2026-07-23)

Current database migration head: `0042_tax_residency_treaty`.

- The user explicitly approved the recommended 17 assertions from the v10.22.26 review packet. Decisions were recorded under independent reviewer `bennet-initial-rule-reviewer`, separate from proposer `coverage-assertion-drafter-v10-22-25`.
- Senegal (`SN`) remains `pending_review` while its live Foreign Ministry endpoint is unavailable. No review decision was recorded for Senegal.
- The 17 assertions were approved but remained unpublished at this checkpoint. The later v10.22.28 publication moved readiness from 65/243 to 82/243.

## Delivery Status — v10.22.26 (2026-07-23)

Current database migration head: `0042_tax_residency_treaty`.

- v10.22.26 adds 18 human-edited, source-pinned initial-rule assertions for the baseline-ready items produced by v10.22.25. The constrained assistant was used only for dry-run discovery; navigation-heavy and insufficient automatic drafts were replaced with narrow statements grounded in the immutable snapshots.
- All 18 records were submitted under proposer `coverage-assertion-drafter-v10-22-25`, with confidence 0.90. The later v10.22.27 decision approved 17 and held Senegal; none were published and coverage readiness remained 65/243.
- Independent human approval is now required. The recommended decision is to approve 17 and hold Senegal (`SN`) until its live Foreign Ministry endpoint recovers or is replaced, then perform publication as a separate explicit action.
- The decision-ready packet is stored at `coverage-operations-receipts/v10_22_26_assertion_review/ASSERTION_REVIEW_PACKET.md`.

## Delivery Status — v10.22.25 (2026-07-23)

Current database migration head: `0042_tax_residency_treaty`.

- Independent review is complete for the 20 immigration-authority assessments and 20 primary-source certifications submitted in v10.22.20 through v10.22.24. All 20 narrow authority relationships were approved by an actor different from the proposers.
- Eighteen source certifications were approved. Peru (`PE`) and Qatar (`QA`) were rejected because their pinned extracts were not sufficiently substantive for controlled baseline assertions; both require a narrower official source, a new immutable snapshot, and a new independent certification.
- The 18 approved items have current immutable snapshots and are `baseline_ready`. Senegal (`SN`) retains its valid July 18 snapshot, but its live Foreign Ministry endpoint currently returns a Drupal error and must recover or be replaced before newly retrieved content is relied upon.
- Both pending-review queues are now empty. Coverage readiness remains **65/243** because these jurisdictions still lack independently reviewed and published initial rule assertions. No rule, regulatory change, client eligibility conclusion, or global-coverage claim was created by this review.
- The durable operational summary is recorded in `coverage-operations-receipts/v10_22_25_independent_review/REVIEW_RECEIPT.md`.

## Delivery Status — v10.23.4 (2026-07-19)

Current database migration head: `0032_initial_rule_assertions`.

- v10.23.4 replaces the tilted dashboard status cards with one aligned System Pulse panel that presents pipeline, Truth Engine, controlled-agent, backend-health, and review-gate state in a calmer operational hierarchy.
- The desktop workspace rail now keeps destination names visible and matches every label to its page title. At narrower widths it returns to the compact icon rail with accessible hover and keyboard-focus labels.
- Light-mode surfaces now use a warm ivory system instead of flat white while preserving the deep-indigo contrast palette, semantic status colors, dark theme, and all existing workflow behavior. The production build, TypeScript validation, and all 21 route generations pass.

## Delivery Status — v10.23.3 (2026-07-19)

Current database migration head: `0032_initial_rule_assertions`.

- v10.23.3 replaces the expanding left navigation groups with a stable 76px workspace rail. Every destination remains directly accessible through a consistent icon, active-state marker, accessible label, hover tooltip, theme control, and backend-health indicator without changing the page layout.
- The shared interface now uses an original neutral-stone and deep-indigo visual system rather than reproducing the reference palettes. Light and dark themes receive clearer surface hierarchy, restrained shadows, semantic success colors, refined typography, and consistent interaction transitions.
- The production build, TypeScript validation, and all 21 static/dynamic route generations pass. The running Docker UI returns HTTP 200 for `/`, `/pathways`, and `/global-intelligence` with no runtime errors after the independent host build.

## Delivery Status — v10.23.2 (2026-07-19)

Current database migration head: `0032_initial_rule_assertions`.

- v10.23.2 isolates the Docker Next.js development cache at `.next-docker` in its own container volume while host production builds continue to use `.next`. This prevents concurrent dev and build processes from sharing incompatible webpack manifests and chunks.
- The stale cache responsible for the missing `447.js` runtime module was removed and the web container was recreated. Both `/` and `/global-intelligence` return HTTP 200 before and after an independent host production build, with no module-resolution errors in the container logs.

## Delivery Status — v10.23.1 (2026-07-19)

Current database migration head: `0032_initial_rule_assertions`.

- v10.23.1 replaces long-form operator pages with task-focused workspace navigation. The home dashboard now exposes Cases, Verification, Intake, and Governance as wired views, displaying one operational context at a time instead of stacking every workflow vertically.
- Global Intelligence coverage is split into Readiness, Evidence, Rules, and Registry workspaces. Evidence batches use a horizontal review rail, long rule/result lists are internally bounded, shared evidence filters collapse when unused, and the registry remains a dedicated scrollable ledger.
- The left navigation now uses compact Mobility, Operations, and Engagement groups, eliminating the permanently expanded tool list and the duplicated active home states. The Next.js production build and static generation continue to pass for all 21 routes; backend controls and schemas remain unchanged.

## Delivery Status — v10.23 (2026-07-19)

Current database migration head: `0032_initial_rule_assertions`.

- v10.23 introduces a reference-led editorial design system for the operator web application: a dark olive navigation rail, quiet off-white workspace canvas, flatter border-led panels, restrained lime status accents, stronger typographic hierarchy, and reduced visual noise.
- The operations dashboard now opens with a connected-system posture canvas, direct links to active cases and safety gates, an editorial workload introduction, and simplified metric presentation. Shared navigation, topbar, buttons, tables, forms, queue cards, status states, and responsive behavior inherit the new system across all application routes.
- No backend workflow, review gate, truth control, role boundary, API contract, or database schema changed. The Next.js production build compiles, type-checks, and statically generates all 21 frontend routes successfully.

## Delivery Status — v10.22.24 (2026-07-18)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.24 adds a pending-review Europe coverage evidence tranche 1F for Hungary (`HU`), Malta (`MT`), Liechtenstein (`LI`), Bosnia and Herzegovina (`BA`), and Albania (`AL`). The atomic batch onboarded five authorities, five official sources, and five monitors, and created five immigration assessments plus five primary-source certifications in `pending_review`.
- The controlled API-container retriever returned HTTPS 200 and suitable content-quality scores for all five selected endpoints. Lithuania (`LT`) was excluded after its controlled probe returned HTTP 403; retrieval controls were not weakened.
- Across v10.22.20 through v10.22.24, 20 assessments and 20 primary-source certifications now await independent decisions. Coverage readiness remains 65/243; no new baseline capture, assertion, publication, regulatory change, or coverage claim was created. The v10.22.24 content-addressed pack, SHA-256 receipt, and submission receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.23 (2026-07-18)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.23 consolidates the 15 jurisdictions in evidence tranches v10.22.20 through v10.22.22 into one independent-review handoff. The generated operations receipts confirm 15 pending assessments, 15 pending primary-source certifications, and no baseline-eligible item before those human decisions.
- Read-only snapshot analysis found 13 sources suitable for narrow assertion drafting. Peru (`PE`) and Qatar (`QA`) require narrower monitored evidence; controlled probes identified official remediation candidates scoring 67 and 85 respectively, but neither candidate has been certified or onboarded.
- Coverage readiness remains 65/243. The handoff creates no review decisions, baseline captures, assertions, publications, regulatory changes, or coverage claim.

## Delivery Status — v10.22.22 (2026-07-18)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.22 adds a pending-review Africa coverage evidence tranche 2B for Namibia (`NA`), Sierra Leone (`SL`), Somalia (`SO`), Senegal (`SN`), and Tanzania (`TZ`). The atomic batch onboarded five authorities, five official sources, and five monitors, and created five immigration assessments plus five primary-source certifications in `pending_review`.
- The controlled API-container retriever returned HTTPS 200 with usable content for all five selected endpoints. Senegal's proposal is explicitly limited to the entry-visa function evidenced by the Foreign Ministry page; broader immigration scope requires separate evidence and reviewer judgment.
- Coverage readiness remains 65/243. No assessment or certification in this tranche has been approved, no baseline capture has been queued, no assertion or rule has been published, and the global coverage claim remains false. The content-addressed evidence pack, SHA-256 receipt, and submission receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.21 (2026-07-18)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.21 adds a pending-review Africa coverage evidence tranche 2A for Eswatini (`SZ`), Lesotho (`LS`), Liberia (`LR`), Zambia (`ZM`), and Uganda (`UG`). The atomic batch onboarded five authorities, five official sources, and five monitors, and created five immigration assessments plus five primary-source certifications in `pending_review`.
- The controlled API-container retriever returned HTTPS 200 with usable content for all five selected endpoints. Algeria (`DZ`) and The Gambia (`GM`) were excluded after transport failures, and Nigeria (`NG`) was excluded after HTTP 403; retrieval controls were not weakened.
- Coverage readiness remains 65/243. No assessment or certification in this tranche has been approved, no baseline capture has been queued, no assertion or rule has been published, and the global coverage claim remains false. The content-addressed evidence pack, SHA-256 receipt, and submission receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.20 (2026-07-18)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.20 adds a pending-review Asia/Americas coverage evidence tranche 1B for the Republic of Korea (`KR`), Malaysia (`MY`), Chile (`CL`), Peru (`PE`), and Qatar (`QA`). The atomic batch onboarded five authorities, five official sources, and five monitors, and created five immigration assessments plus five primary-source certifications in `pending_review`.
- The controlled API-container retriever returned HTTPS 200 with usable content for all five selected endpoints. Thailand (`TH`), Vietnam (`VN`), and Mexico (`MX`) were excluded after controlled probes returned HTTP 403, a transport failure, and challenge-only content respectively; retrieval controls were not weakened.
- Coverage readiness remains 65/243. No assessment or certification has been approved, no baseline capture has been queued, no assertion or rule has been published, and the global coverage claim remains false. The content-addressed evidence pack, SHA-256 receipt, and submission receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.19 (2026-07-18)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.19 adds the Asia/Americas coverage evidence tranche 1A for Japan (`JP`), Indonesia (`ID`), Philippines (`PH`), Argentina (`AR`) and Brazil (`BR`). All five jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 60/243 to 65/243; the global coverage claim remains false.
- Japan's official source is the Ministry of Justice English portal at `moj.go.jp/EN/`. Indonesia's official source is the Directorate General of Immigration portal at `imigrasi.go.id/`. The Philippines' official source is the Bureau of Immigration portal at `immigration.gov.ph/`. Argentina's official source is the National Migration Directorate page on the government portal at `argentina.gob.ar/interior/migraciones`. Brazil's official source is the Ministry of Justice and Public Security portal at `gov.br/mj/`.
- All endpoints were locally probed from the API container and returned HTTPS 200 responses with usable immigration, residence, justice, citizenship or foreigner-related content. The v10.22.19 evidence pack, SHA-256 receipt, and operations receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.18 (2026-07-18)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.18 adds the Europe coverage evidence tranche 1E for Romania (`RO`), Bulgaria (`BG`), Luxembourg (`LU`), North Macedonia (`MK`) and Serbia (`RS`). All five jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 55/243 to 60/243; the global coverage claim remains false.
- Romania's official source is the Ministry of Internal Affairs at `mai.gov.ro/`. Bulgaria's official source is the Ministry of the Interior at `mvr.bg/`. Luxembourg's official source is the government administrative portal at `guichet.lu/`, which redirects to `guichet.public.lu/` for service content. North Macedonia's official source is the Ministry of Internal Affairs at `mvr.gov.mk/`. Serbia's official source is the Ministry of Internal Affairs at `mup.gov.rs/`.
- All endpoints were locally probed from the API container and returned HTTPS 200 responses with usable immigration, residence, border-control or foreigner-related content. Luxembourg and North Macedonia required source-monitor allowlist remediation for canonical redirects (`www.guichet.lu` -> `guichet.public.lu` and `www.mvr.gov.mk` -> `mvr.gov.mk`); TLS verification was not bypassed. The v10.22.18 evidence pack, SHA-256 receipt, and operations receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.17 (2026-07-18)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.17 adds the Europe coverage evidence tranche 1D for Spain (`ES`), Portugal (`PT`), Italy (`IT`), Slovenia (`SI`) and Croatia (`HR`). All five jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 50/243 to 55/243; the global coverage claim remains false.
- Spain's official source is the Ministry of Foreign Affairs, European Union and Cooperation portal at `exteriores.gob.es/`. Portugal's official source is the official government services portal at `eportugal.gov.pt/`, which redirects to `www.gov.pt/` and provides access to services including "Estrangeiros em Portugal" (Foreigners in Portugal). Italy's official source is the Ministry of the Interior at `interno.gov.it/`. Slovenia's official source is the Slovenian Government English portal at `gov.si/en/`. Croatia's official source is the Ministry of the Interior at `mup.gov.hr/`.
- All endpoints were locally probed from the API container and returned HTTPS 200 responses with usable foreigner, immigration, residence, work or migration content. Portugal's initial monitor fetch was blocked because the canonical `eportugal.gov.pt/` endpoint redirects to `www.gov.pt/`; the source monitor allowlist was remediated to include both domains without bypassing TLS verification. The v10.22.17 evidence pack, SHA-256 receipt, and operations receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.16 (2026-07-18)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.16 adds the Europe coverage evidence tranche 1C for Estonia (`EE`), Latvia (`LV`), Poland (`PL`), Czech Republic (`CZ`) and Greece (`GR`). All five jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 45/243 to 50/243; the global coverage claim remains false.
- Estonia's official source is the Police and Border Guard Board at `politsei.ee/en/`. Latvia's official source is the Office of Citizenship and Migration Affairs at `pmlp.gov.lv/en/`. Poland's official source is the Office for Foreigners at `gov.pl/web/udsc/`. Czech Republic's official source is the Ministry of the Interior at `mv.gov.cz/mvcren/`. Greece's official source is the Ministry of Migration and Asylum at `migration.gov.gr/`.
- All endpoints were locally probed from the API container and returned HTTPS 200 responses with usable migration, citizenship, asylum or residence content. The v10.22.16 evidence pack, SHA-256 receipt, and operations receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.15 (2026-07-18)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.15 adds the Europe coverage evidence tranche 1B for Denmark (`DK`), Netherlands (`NL`), Belgium (`BE`), France (`FR`) and Ireland (`IE`). All five jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 40/243 to 45/243; the global coverage claim remains false.
- Denmark's official source is the Danish Immigration Service portal at `nyidanmark.dk/en-GB/`. Netherlands's official source is the Immigration and Naturalisation Service (IND) at `ind.nl/en/`. Belgium's official source is the FPS Foreign Affairs at `diplomatie.belgium.be/en/`. France's official source is the Ministry for Europe and Foreign Affairs (France Diplomatie) at `diplomatie.gouv.fr/en/`. Ireland's official source is Immigration Service Delivery at `irishimmigration.ie/`.
- All endpoints were locally probed from the API container and returned HTTPS 200 responses with usable immigration, visa, residence or travel content. The v10.22.15 evidence pack, SHA-256 receipt, and operations receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.14 (2026-07-18)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.14 adds the Europe coverage evidence tranche 1A for Iceland (`IS`), Norway (`NO`), Switzerland (`CH`), Sweden (`SE`) and Finland (`FI`). All five jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 35/243 to 40/243; the global coverage claim remains false.
- Iceland's official source is the Directorate of Immigration page on the Icelandic government portal at `island.is/s/utlendingastofnun`. Norway's official source is the Norwegian Directorate of Immigration English portal at `udi.no/en/`. Switzerland's official source is the State Secretariat for Migration English portal at `sem.admin.ch/sem/en/home.html`. Sweden's official source is the Swedish Migration Agency English portal at `migrationsverket.se/en.html`. Finland's official source is the Finnish Immigration Service English portal at `migri.fi/en`.
- All endpoints were locally probed from the API container and returned HTTPS 200 responses with usable immigration and residence content. The v10.22.14 evidence pack, SHA-256 receipt, and operations receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.13 (2026-07-18)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.13 adds the Asia/MENA coverage evidence tranche 1A for Oman (`OM`), Bahrain (`BH`), Georgia (`GE`), Singapore (`SG`) and the United Arab Emirates (`AE`). All five jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 30/243 to 35/243; the global coverage claim remains false.
- Oman's official source is the Royal Oman Police eVisa portal at `evisa.rop.gov.om/`. Bahrain's official source is the Bahrain Electronic Visa Service at `evisa.gov.bh/`. Georgia's official source is the Ministry of Foreign Affairs e-VISA PORTAL at `evisa.gov.ge/GeoVisa/`. Singapore's official source is the Immigration and Checkpoints Authority portal at `ica.gov.sg/`. The UAE's official source is the Federal Authority for Identity, Citizenship, Customs and Port Security (ICP) English portal at `icp.gov.ae/en/`, which provides federal-level identity and residency content.
- All endpoints were locally probed from the API container and returned HTTPS 200 responses with usable English-language immigration, visa or residency content. The UAE ICP root path (`https://icp.gov.ae/`) was also reachable, but the English path (`/en/`) provides clearer federal service content, so it was selected as the monitored source.
- The v10.22.13 evidence pack, SHA-256 receipt, and operations receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.12 (2026-07-18)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.12 adds the Africa coverage evidence tranche 1H for South Africa (`ZA`) and Seychelles (`SC`). Both jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 28/243 to 30/243; the global coverage claim remains false. South Africa's official source is the Department of Home Affairs portal at `dha.gov.za`. Seychelles's official source is the Electronic Border System at `seychelles.govtas.com/en`, which identifies itself as the official government website. Both endpoints were locally probed from the API container and returned HTTPS 200 responses with usable immigration/entry content. Gabon (`GA`), Gambia (`GM`), Guinea-Bissau (`GW`), Democratic Republic of the Congo (`CD`), Nigeria (`NG`), South Sudan (`SS`), Tanzania (`TZ`), Togo (`TG`), Uganda (`UG`), and Zambia (`ZM`) remain blocked or deferred. The v10.22.12 evidence pack, SHA-256 receipt, and operations receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.11 (2026-07-17)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.11 adds the Africa coverage evidence tranche 1G for Mauritius (`MU`) and Zimbabwe (`ZW`). Both jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 26/243 to 28/243; the global coverage claim remains false. Mauritius's official source is the Passport and Immigration Office portal at `passport.govmu.org/passport`, which describes passport and immigration services under the Director General of Immigration. Zimbabwe's official source is the Zimbabwe eVisa portal at `evisa.gov.zw`, operated by the Zimbabwe Immigration Department. Both endpoints were locally probed from the API container and returned HTTPS 200 responses with usable immigration content. Gabon (`GA`), Gambia (`GM`), Guinea-Bissau (`GW`), Democratic Republic of the Congo (`CD`), and Zambia (`ZM`) remain blocked or deferred from earlier tranches. The v10.22.11 evidence pack, SHA-256 receipt, and operations receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.10 (2026-07-17)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.10 adds the Africa coverage evidence tranche 1F for Madagascar (`MG`), Malawi (`MW`), and Mozambique (`MZ`). All three jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 23/243 to 26/243; the global coverage claim remains false. Madagascar's official source is the eService of Tourism, Immigration and Emigration at `evisamada-mg.com/en/home`, which states it is the only official online visa application site of the Republic of Madagascar. Malawi's official source is the Malawi e-Visa System at `evisa.gov.mw`, operated by the Department of Immigration and Citizenship Services. Mozambique's official source is the eVisa and eTA portal at `evisa.gov.mz`, operated by the National Immigration Service. All endpoints were locally probed from the API container and returned HTTPS 200 responses with usable immigration/visa content. Gabon (`GA`), Gambia (`GM`), Guinea-Bissau (`GW`), and Democratic Republic of the Congo (`CD`) remain blocked or deferred from earlier tranches. The v10.22.10 evidence pack, SHA-256 receipt, and operations receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.9 (2026-07-17)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.9 adds the Africa coverage evidence tranche 1E for Kenya (`KE`) and Rwanda (`RW`). Both jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 21/243 to 23/243; the global coverage claim remains false. Kenya's official source is the Electronic Travel Authorization (eTA) portal at `evisa.go.ke`, operated by the Directorate of Immigration Services. Rwanda's official source is the Immigration and Emigration portal at `migration.gov.rw`, operated by the Rwanda Directorate General of Immigration and Emigration. Both endpoints were locally probed from the API container and returned HTTPS 200 responses with usable immigration content. The Democratic Republic of the Congo (`CD`) was deferred because the official `evisa.gouv.cd` page is a dynamic Inertia.js application with minimal generic-parser text extraction. Gabon (`GA`), Gambia (`GM`), and Guinea-Bissau (`GW`) remain blocked or deferred from earlier tranches. The v10.22.9 evidence pack, SHA-256 receipt, and operations receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.8 (2026-07-17)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.8 adds the Africa coverage evidence tranche 1D for Ghana (`GH`) and Guinea (`GN`). Both jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 19/243 to 21/243; the global coverage claim remains false. Ghana's official source is the Ghana Immigration Service e-Visa portal at `evisa.immigration.gov.gh`, which returned structured `GovernmentService` JSON-LD identifying the Ghana Immigration Service as the provider. Guinea's official source is the Police aux Frontieres (PAF) e-Visa page at `paf.gov.gn/visa`. Both endpoints were locally probed from the API container and returned HTTPS 200 responses with usable content. Gambia (`GM`) and Guinea-Bissau (`GW`) were deferred from this tranche because a confirmed reachable official source was not yet identified; Gabon (`GA`) remains blocked by TLS certificate validation from the previous tranche. The v10.22.8 evidence pack, SHA-256 receipt, and operations receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.7 (2026-07-17)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.7 adds the Africa coverage evidence tranche 1C for Djibouti (`DJ`), Egypt (`EG`), and Ethiopia (`ET`). All three jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 16/243 to 19/243; the global coverage claim remains false. Egypt required canonical-source remediation from `https://www.visa2egypt.gov.eg/` to `https://www.visa2egypt.gov.eg/eVisa/Home` because the root path only returned a meta-redirect with no usable text; the remediation was applied through the controlled source-remediation path and audited. Gabon (`GA`) was removed from the planned tranche because the official `evisa.dgdi.ga` endpoint fails TLS certificate-chain validation inside the API container; TLS verification was not bypassed. The v10.22.7 evidence pack, operations receipt, and SHA-256 receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.6 (2026-07-17)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.6 adds the Africa coverage evidence tranche 1B for Chad and Cote d'Ivoire. Both jurisdictions now have independently approved immigration assessments, approved source certifications, immutable baseline snapshots, and active verified rules. Coverage readiness moved from 14/243 to 16/243; the global coverage claim remains false. Algeria remains excluded because of a TLS certificate-chain validation failure; Comoros and Congo (Brazzaville) were deferred from the original plan because a confirmed official source was not yet identified. The v10.22.6 evidence pack, operations manifest, and SHA-256 receipt are stored in `knowledge/global_coverage/tranches/` and `coverage-operations-receipts/`.

## Delivery Status — v10.22.5 (2026-07-17)

Current database migration head: `0032_initial_rule_assertions`.

- v10.22.5 completes the Africa tranche 1A evidence review and initial-rule publication cycle for the British Indian Ocean Territory, Angola, Benin, Burkina Faso, Burundi, Cabo Verde, Cameroon, and Central African Republic. All nine tranche 1A jurisdictions now have independently approved assessments and source certifications, immutable baselines, and active verified rules. Coverage readiness moved from 6/243 to 14/243; the global coverage claim remains false.
- v10.22.1 corrects PowerShell-relative manifest and receipt path resolution in the tranche operations scripts. Paths now resolve from the active PowerShell provider location instead of a stale host-process working directory; no API, database, evidence, review, assertion, publication, snapshot, or coverage state is changed.
- v10.22 adds safe multi-batch tranche operations: read-only expansion planning, offline manifest validation, mandatory dry-run preflight, consolidated review/baseline/assertion/readiness receipts, and optional confirmation-gated queueing for explicitly selected approved baselines. It creates no review decision, assertion, publication, snapshot mutation, regulatory change, or coverage claim.
- v10.21.2 adds review-gated supplemental official sources for domains where the approved primary portal is unsuitable for monitoring. Supplemental approvals require the existing approved primary authority/source and relationship, never supersede the primary certification, and can supply fresh evidence for a snapshot-pinned assertion.
- v10.21.1 fixes the tranche-assistant draft handoff: copying a constrained draft now confirms success, scrolls to the existing initial-rule assertion form, and focuses the title field without submitting or persisting any record.
- v10.21 adds a feature-flagged coverage tranche assistant that prepares review packets, rejects navigation-heavy snapshots, extracts exact candidate evidence lines, and can selectively queue approved baseline captures. It creates no approvals, assertions, publications, snapshot mutations, regulatory changes, or coverage claims.
- v10.20 adds audited before/after jurisdiction coverage-readiness receipts, read-only reconciliation, dashboard count verification, and safer empty-by-default evidence JSON.
- v10.19 adds controlled initial verified-rule assertions from independently approved immutable baseline snapshots. Assertions are content-addressed, require a different reviewer, publish only through a separate explicit action, and project to the knowledge graph without fabricating a regulatory-change event.
- v10.18.2 fixes the canonical-source remediation helper's post-commit reporting path and makes reruns idempotent. An earlier run that committed the URL change but failed while printing detached ORM attributes can now be safely confirmed without a duplicate audit event.
- v10.18.1 corrects the Austria starter-tranche monitor to a canonical HTTPS endpoint after the upstream short URL redirected to HTTP. The retrieval security policy remains fail-closed; existing deployments use an audited same-host source-remediation script before retrying baseline capture.
- v10.18 adds controlled, idempotent baseline capture for independently approved evidence-batch sources. It pre-creates durable retrieval runs, queues the exact monitored source through Celery, records immutable snapshots, and never publishes a verified rule or coverage claim.
- v10.17 adds the first current official-evidence tranche for Austria, Germany, Canada, Australia, and New Zealand, plus offline validation and a PowerShell submission workflow. The linked assessment/certification records still require independent decisions before baseline capture is eligible.
- v10.16 extends coverage evidence batches with atomic authority, official-source, and monitor onboarding plus automatically linked pending primary-source certification proposals.
- v10.15.1 fixed PostgreSQL-safe compilation of the `0030` coverage-batch index names and added an offline PostgreSQL migration regression gate.

- Phase 7 regulatory-intelligence foundation is complete.
- Phase 8 universal profile, pathway catalogue, comparisons, and single-pathway timelines are complete.
- Phase 9 document intelligence is complete: extraction, profile/application validation,
  expiry reminders, missing-document and inconsistency detection, human-reviewed integrity
  indicators, and signed expiring document access with production storage controls.
- Phase 10A self-updating intelligence, controlled classification, relational knowledge
  graph, and pathway-impact linking are complete.
- Phase 10C dashboard filtering is complete across freshness, coverage, authority,
  confidence, materiality, and review state.
- Phase 10D is complete: explicit reassessment acceptance preserves pinned assessments,
  while immutable country-ranking assessments compare only human-published pathways,
  explain costs, trade-offs, long-term residence dependencies, and uncertainty, and preserve
  the Phase 10B global-coverage claim boundary.
- Phase 10E is complete: immutable, human-confirmed multi-year and multi-country scenarios
  model reviewed study, graduate-rights, work, settlement, permanent-residence, and
  citizenship-review transitions. Reviewed rule changes create a new scenario version and
  never rewrite the original plan.
- Phase 10B now has a prioritized evidence worklist and atomic, idempotent evidence batches
  for up to 50 jurisdictions. The same package can onboard authorities, official sources, and
  monitors, then create pending certification proposals while preserving the separate-reviewer
  requirement. Approved batch items can now queue controlled baseline retrieval and immutable
  source snapshots, while pending or rejected evidence remains ineligible. Reviewed baseline
  assertions can now publish the first verified rule without misclassifying a baseline as a
  detected change. A feature-flagged tranche assistant now prepares review packets, evaluates
  baseline content quality, extracts exact candidate evidence, and selectively queues approved
  baselines without creating legal decisions or persistent assertion drafts. Review-gated
  supplemental sources preserve approved primary certifications while narrower domain sources
  can provide monitored evidence. Multi-batch tranche operations now consolidate stage, blocker,
  review, baseline, draft, and readiness receipts without bypassing human decisions. The initial
  Austria, Germany, Canada, Australia, and New Zealand tranche has completed all gates, proving
  the workflow end to end while global coverage remains incomplete.
- The remaining Phase 10 delivery work is factual Phase 10B evidence collection and human
  approval across every required jurisdiction.
- Global coverage claims remain blocked until the authority, source, freshness,
  verified-rule, and jurisdiction-assessment gates are complete.

### Recommended execution order

1. Use v10.22 read-only expansion planning to select the next 10–25 evidence gaps without inferring authorities or relationships.
2. Research and independently verify each jurisdiction's relationship, authority, source, and evidence scope.
3. Submit reviewed source packages through the v10.16 atomic evidence-batch path; use v10.21.2 supplemental sources only where an approved primary portal is unsuitable for monitoring.
4. Use the v10.22 operations manifest to run mandatory dry-run preparation across existing batches and produce consolidated review, baseline, assertion, and readiness queues.
5. Complete assessment and certification decisions with separate reviewer identities.
6. Queue only explicitly selected approved baselines; inspect failures without weakening retrieval controls.
7. Draft, independently review, and explicitly publish snapshot-pinned initial rules through the existing v10.19 workflow.
8. Confirm readiness with v10.20 receipts and review later detected changes through the existing classification and publication gates.
9. Maintain fresh monitors and expand coverage without claiming global completeness until every required jurisdiction passes all Phase 10B gates.

### Remaining-work ledger

- **Phase 9:** complete.
- **Phase 10B:** software workflow complete; jurisdiction evidence onboarding and independent
  review remain operationally incomplete.
- **Phase 10C:** complete.
- **Phase 10D:** complete.
- **Phase 10E:** complete.
- **Phase 11:** complete; corporate mobility, entrepreneur dossiers, Business & Wealth advisory, governed investment programs, client readiness comparison, dedicated HNWI/family-office controls, governed tax/treaty intelligence, and the first independently published jurisdiction program are delivered. Further jurisdiction and treaty evidence onboarding remains ongoing operational expansion.
- **Phase 12:** in progress; secure responsive client, employer, and partner portals, stable account-scoped external APIs, the governed event/outbox automation foundation, credential-backed provider adapters with retry and scheduled delivery workers, authority appointment tracking, agency submission tracking, automation outbox bridge, external agency assignment tracking, authority submission checklists, and client portal PWA/mobile device-specific session controls are delivered. Remaining government and agency workflow depth and additional provider health/reconciliation tooling remain.
- **Phase 13:** not started; all listed capability groups remain future work.

## Current Baseline: MVP Phases 1-5

- Local/Docker FastAPI and Next.js platform
- CRM, public intake, client return, lead detail, and operator workbench
- Official-source Truth Engine and human review queues
- Documents, MinIO-ready storage, browser OCR, and verification actions
- Eligibility assessment and coaching
- Opportunity catalogue and deterministic matching
- Controlled agents and asynchronous batch execution
- Draft communications and trigger-based automatic communication records
- Audit, RBAC, demo/release checks, and Alembic foundation

## Phase 6: Foundation Alignment

- Make this roadmap and the product blueprint canonical
- Repair controlled-agent contract tests
- Complete migrations for every current SQLModel table
- Align public routes, browser sessions, local header authentication, and CORS
- Refresh architecture and operational documentation
- Keep frontend build, API tests, schema checks, and repository policy green

## Phase 7: Regulatory Intelligence Foundation

- [x] Add jurisdiction, immigration authority, and source schedule models
- [x] Support country, territory, and autonomous-jurisdiction identifiers
- [x] Ingest official-source content into immutable snapshots with hashes and timestamps
- [x] Compare snapshots and produce structured regulatory change sets
- [x] Queue every material change for human validation
- [x] Publish approved verified rules with evidence links and effective dates
- [x] Execute scheduled retrieval through controlled background workers
- [x] Add safe generic HTML, text, JSON, XML, and PDF parser routing
- [x] Add a Next.js regulatory operations workspace for health, review, publication, rules, and evidence
- [x] Add rule supersession and explicit retirement controls with audit history
- [x] Expose source-monitor freshness, due-state, errors, and retrieval failures
- [x] Add transactional jurisdiction, authority, source, and monitor onboarding with domain allowlists
- [x] Add coverage and freshness rollups by jurisdiction, authority, and regulatory domain
- [x] Add configurable authority-specific gazette and structured API parser profiles
- [x] Detect new, changed, and retired programs from structured authority catalogues

## Phase 8: Universal Mobility Profile and Pathways

- [x] Expand the profile across education, work, skills, languages, family,
  finances, goals, constraints, consent, and evidence
  - [x] Add immutable versions, supersession, completeness, and readiness stages
  - [x] Validate lead-owned document evidence and record purpose-limited consent
  - [x] Restrict eligibility and opportunity processing after consent withdrawal
  - [x] Persist profile-version provenance on eligibility conclusions
  - [x] Add the operator profile workspace and version history
- [x] Build a versioned pathway catalogue for study, work, visa, scholarship,
  settlement, family, and digital-nomad routes
  - [x] Add immutable draft, published, superseded, and retired versions
  - [x] Require official sources, immutable snapshots, verified rules, and human review for publication
  - [x] Add deterministic profile matching with consent enforcement and missing-evidence results
  - [x] Add the pathway governance workspace and version ledger
- [x] Connect eligibility conclusions to verified rules and source references
  - [x] Persist pathway, version, source, snapshot, and verified-rule provenance in assessment factors
- [x] Add cost, risk, alternative-pathway, and missing-evidence explanations
  - [x] Persist comparisons against exact profile and pathway versions
  - [x] Separate payable fees, recurring costs, and minimum-funds thresholds
  - [x] Explain declared, evidence-derived, and regulatory-freshness risks
  - [x] Rank alternatives with tradeoffs, benefits, gaps, and source provenance
  - [x] Add the Mobility Planning workspace and immutable comparison history
- [x] Build the multi-stage mobility timeline engine
  - [x] Generate deterministic profile-to-settlement stages from an immutable pathway comparison
  - [x] Enforce sequential dependencies, profile consent, and exact profile/pathway-version provenance
  - [x] Require audited human approval notes for eligibility, route, application, submission, and decision gates
  - [x] Keep application approval, authority decisions, and regulatory claims in their existing controlled systems
  - [x] Add the Mobility Timelines operator workspace with evidence, blockers, ownership, and due dates

## Phase 9: Document Intelligence

- [x] Server-side OCR/extraction jobs and structured document schemas
  - [x] Add Celery extraction jobs tied to immutable upload hashes and exact schema versions
  - [x] Extract text server-side from text files, PDF text layers, and Tesseract-supported images
  - [x] Publish baseline schemas for passports, CVs, degrees, transcripts, employment letters, and bank statements
  - [x] Require human approval or rejection without automatically verifying authenticity or mutating profile facts
  - [x] Add restricted document-intelligence APIs and an operator review workspace
- [x] Validation against profile and application facts
  - [x] Compare only human-approved extractions with exact immutable profile versions
  - [x] Snapshot lead identity and application facts inside every assessment
  - [x] Separate matches, mismatches, missing values, and semantically non-comparable facts
  - [x] Require human assessment review without overwriting documents, profiles, or applications
  - [x] Add consistency findings and immutable assessment history to the Document Intelligence workspace
- [x] Expiry monitoring and reminders
  - [x] Add deterministic 90, 30, 7-day, and expired urgency bands
  - [x] Create immutable, deduplicated reminder tasks from recorded document expiry metadata
  - [x] Supersede stale tasks when urgency increases or an expiry date changes
  - [x] Schedule controlled scans and expose lead-scoped manual scanning
  - [x] Require human review notes without sending uncontrolled external messages
  - [x] Add expiry metrics, task review, and audit history to Document Intelligence
- [x] Missing-document and inconsistency detection
  - [x] Resolve exact human-published pathway versions, eligibility assessments, or application-domain requirement snapshots
  - [x] Create immutable, content-addressed coverage assessments without creating or modifying source records
  - [x] Distinguish satisfied, missing, optional, expired, rejected, unverified, mismatch, and duplicate-conflict outcomes
  - [x] Reuse approved document-consistency findings as broader cross-document risk signals
  - [x] Add deduplicated scheduled and lead-scoped scans with mandatory human review and audit history
  - [x] Add requirement metrics, findings, provenance, and review actions to Document Intelligence
- [x] Human-reviewed fraud-risk indicators
  - [x] Create immutable, content-addressed integrity assessments with exact source provenance
  - [x] Detect exact-file reuse, approved identity/material mismatches, duplicate conflicts, rejected evidence, and hash-integrity failures
  - [x] Detect approved identifier reuse across leads while storing only hashes and masked values
  - [x] Require controlled human triage without declaring fraud or taking adverse action
  - [x] Add scheduled and lead-scoped scans, audit history, metrics, and review controls
- [x] Signed, expiring document access and production object-storage controls
  - [x] Issue short-lived, audited access grants instead of durable or direct object URLs
  - [x] Enforce authenticated role, lead ownership, document scope, and purpose on every grant
  - [x] Support local storage and MinIO without exposing storage credentials or unrestricted object keys
  - [x] Record grant creation, access, expiry, revocation, denial, and actor provenance
  - [x] Add explicit revocation and fail-closed handling for expired, altered, missing, or unauthorized objects
  - [x] Add production bucket privacy, TLS, encryption, retention/lifecycle, backup, and recovery guidance
  - [x] Add restricted operator controls and regression coverage without changing document verification state

## Phase 10: Global Self-Updating Mobility Intelligence — Highest Priority

### 10A. Self-Updating Visa Intelligence Engine

- [x] Continuously schedule controlled retrieval from allowlisted government, authority, and gazette sources
- [x] Detect immutable source changes through content hashes and snapshot comparison
- [x] Extract generic HTML, text, JSON, XML, PDF, gazette, and structured programme catalogues
- [x] Classify new programmes, removals, rule changes, salary thresholds, age limits,
  occupation lists, quotas, processing times, and policy changes
- [x] Route every material change through human validation before verified-rule publication
- [x] Refresh relational intelligence and dashboards from reviewed changes and verified rules
- [x] Add controlled model-assisted classification proposals with confidence, evidence, and deterministic fallback
- [x] Add a provenance-preserving regulatory knowledge graph updated only from human-published rules
- [x] Link graph updates to affected pathway versions without silently changing client assessments

Target pipeline:

```text
Government website / official API / gazette
  -> controlled crawler
  -> immutable snapshot and extraction
  -> structured classification proposal
  -> deterministic comparison
  -> human validation when material
  -> verified rule and knowledge-graph update
  -> global dashboard refresh
```

Delivered classification governance: every detected change receives a persisted
deterministic proposal tied to exact snapshots and diff evidence. Operators can
request configured model assistance; invalid, unavailable, or disabled model
execution falls back deterministically with a visible reason. A human must
accept one proposal before the separate regulatory-change review and verified-
rule publication gates can proceed. See
`docs/CONTROLLED_REGULATORY_CLASSIFICATION_V10_4.md`.

Delivered graph governance: human-published verified rules now transactionally
project typed jurisdiction, domain, authority, source, snapshot, change, and
rule nodes with per-edge rule/change/snapshot provenance. Supersession and
retirement preserve history, while controlled synchronization ignores
unpublished rules. See `docs/REGULATORY_KNOWLEDGE_GRAPH_V10_5.md`.

Delivered pathway-impact governance: rule publication, supersession, and
retirement now create idempotent, review-gated links to exact currently
published pathway versions using jurisdiction, domain, source, and direct-rule
evidence. Existing pathway criteria, comparisons, timelines, and client
conclusions remain immutable; resolving an impact requires an explicitly
published newer pathway version. See
`docs/PATHWAY_REGULATORY_IMPACT_LINKS_V10_6.md`.

### 10B. Global Country and Immigration-Jurisdiction Coverage

- [x] Support country, territory, and autonomous-immigration-jurisdiction types
- [x] Support parent jurisdictions, authorities, official sources, domains, and independent schedules
- [x] Seed and version a canonical registry covering every UN member/observer state and ISO 3166-1 entry
- [x] Register autonomous jurisdictions and territories without inferring their immigration-rule relationship
- [x] Add evidence-backed proposal, separate-reviewer approval, rejection, and supersession for immigration-rule relationships
- [x] Add a prioritized region/gap worklist for the remaining jurisdiction evidence programme
- [x] Add atomic, idempotent evidence batches that create pending proposals only
- [x] Add atomic batch onboarding for authorities, official sources, and source monitors
- [x] Automatically link onboarded sources to pending primary-source certification proposals
- [x] Preserve independent review and immutable batch provenance at scale
- [x] Capture immutable baselines only after both jurisdiction and primary-source reviews pass
- [x] Create independently reviewed initial verified-rule assertions without fabricating source-change events
- [x] Reconcile verified-rule publication into audited jurisdiction coverage-readiness receipts and live dashboard counts
- [x] Add feature-flagged tranche preparation that rejects weak snapshots and never auto-approves or publishes legal evidence
- [x] Add multi-batch tranche operations planning, manifest validation, and consolidated dry-run receipts without automatic legal decisions
- [ ] Complete reviewed independent, inherited, shared, or not-applicable assessments for every required jurisdiction
- [x] Add separate-reviewer certification for each jurisdiction's primary immigration authority and official source
- [ ] Establish at least one reviewed primary immigration authority and official source per jurisdiction
- [x] Track country-level source, authority, freshness, verified-rule, and immigration-rule-assessment gaps
- [x] Prevent “global coverage” claims unless registry and source-coverage release gates pass

Delivered registry foundation: immutable dataset-hashed releases from the fixed
UN M49 source with ISO 3166-1 scope reconciliation, 249 active entries, a
reproducible import command, coverage-gap API, release gate, and operator ledger.
Territories remain `unassessed` for independent immigration rules until reviewed;
their presence in the registry is not treated as verified immigration coverage.

Initial named coverage includes Austria, Germany, Canada, UAE, Singapore, Japan,
New Zealand, South Korea, Brazil, South Africa, Qatar, Oman, Saudi Arabia, and
all remaining registry jurisdictions—not only this example list.

Delivered v10.15 coverage operations: a prioritized release-derived worklist and
immutable SHA-256-keyed evidence batches for up to 50 jurisdictions. Batches are
atomic, create only pending assessment/certification proposals, and never bypass
the separate-reviewer or global-coverage release gates. See
`docs/GLOBAL_COVERAGE_EVIDENCE_OPERATIONS_V10_15.md`.

Delivered v10.16 source onboarding: the same atomic evidence package can create or update
a registry-bound regulatory authority, HTTPS official source, allowlisted source monitor,
and pending primary-source certification. Any invalid row rolls back the entire package;
source ownership conflicts and unsafe URLs still fail closed. Certification remains subject
to an independent reviewer and does not establish coverage by itself. See
`docs/GLOBAL_COVERAGE_SOURCE_ONBOARDING_V10_16.md`.

Delivered v10.19 initial-rule governance: an approved batch item with an immutable baseline
snapshot can create a content-addressed assertion tied to the exact jurisdiction, source,
snapshot hash, domain, statement, excerpt, rationale, and confidence. The proposer cannot
review or publish it; independent approval and a separate explicit publication action create
a verified rule. Knowledge-graph provenance records the initial assertion rather than a
fictional regulatory change, and the Opportunity Radar remains change-event-only. See
`docs/INITIAL_RULE_ASSERTIONS_V10_19.md`.

Delivered v10.20 readiness reconciliation: assertion-backed rule publication now returns and
audits the exact jurisdiction evidence-gate state before and after publication. Read-only
receipts expose remaining gaps and registry-wide counts; repeated publication is idempotent.
The Coverage workspace displays whether publication completed jurisdiction readiness, while
detected-change and Opportunity Radar counts remain event-only. Placeholder evidence JSON is
no longer preloaded. See `docs/COVERAGE_READINESS_RECEIPTS_V10_20.md`.

Delivered v10.21 tranche preparation: a disabled-by-default assistant assembles review packets,
scores immutable baseline content, rejects navigation-heavy pages, extracts exact candidate
evidence lines, and offers constrained assertion suggestions for human editing. It never creates
or approves review records, persists assertions, publishes rules, changes snapshots, or makes
coverage claims. Apply mode can only queue explicitly selected approved baseline captures. See
`docs/COVERAGE_TRANCHE_ASSISTANT_V10_21.md`.

Delivered v10.21.2 supplemental-source governance: an independently approved primary source and
authority can be preserved while a narrower `supplemental_<domain>` source enters its own
pending-review, baseline, assertion, and publication sequence. Supplemental approvals never
supersede the primary certification, and coverage freshness may use either approved source while
primary authority/source gates remain primary-only. See
`docs/SUPPLEMENTAL_OFFICIAL_SOURCES_V10_21_2.md`.

Delivered v10.22 tranche operations: read-only expansion planning converts the prioritized
coverage worklist into blank human-research plans. Offline manifest validation and a mandatory
dry-run preflight can prepare multiple existing evidence batches, then emit consolidated JSON
and CSV receipts for blockers, review queues, baseline states, candidate drafts, and readiness.
Optional apply mode can only queue explicitly selected API-eligible baselines and cannot review,
submit assertions, publish rules, mutate snapshots, create regulatory changes, or make coverage
claims. See `docs/COVERAGE_TRANCHE_OPERATIONS_V10_22.md`.

Delivered v10.17 official evidence starter: a validated, content-addressed pack prepares
Austria, Germany, Canada, Australia, and New Zealand for review using current official
authority and immigration portal evidence. Submission creates five pending immigration-rule
assessments and five pending primary-source certifications; it creates no approvals, source
snapshots, verified rules, or coverage claim. Combined rows link each assessment to the exact
newly onboarded official source. See
`docs/GLOBAL_COVERAGE_OFFICIAL_EVIDENCE_STARTER_V10_17.md`.

Delivered v10.18 controlled baseline capture: independently approved batch items can create
durable queued retrieval runs and dispatch the exact allowlisted monitors through the existing
controlled Celery worker. Existing snapshots and queued/running work are not duplicated; failed
runs remain visible for deliberate retry. The workflow captures evidence only and cannot publish
a verified rule or satisfy the global-coverage gate by itself. See
`docs/CONTROLLED_COVERAGE_BASELINE_CAPTURE_V10_18.md`.

### 10C. Live Global Intelligence Dashboard

- [x] New Visa Programmes dashboard with introductions, removals, provenance, and visible review state
- [x] Immigration Changes dashboard with countries and changes updated today
- [x] Processing-Time dashboard with windowed change history and visible review state
- [x] Skilled-Occupation dashboard with shortage/eligible-list changes
- [x] Salary and Investment Threshold dashboard
- [x] Global country activity heatmap across onboarded jurisdictions
- [x] Evidence-based Opportunity Radar calculated only from human-published events
- [x] Freshness, coverage, authority, confidence, materiality, and review-state filters
  - [x] Apply one evidence scope consistently to counts, change feeds, heatmaps, and Opportunity Radar
  - [x] Expose verified-rule or classification-proposal confidence provenance without inventing confidence
  - [x] Preserve pending-review visibility while keeping the Opportunity Radar human-published-only
- [x] Explicitly label activity signals as evidence summaries—not predictions or visa recommendations

Delivered foundation: `GET /api/v1/global-intelligence/dashboard` and the
`/global-intelligence` operator workspace. The dashboard deliberately displays
an onboarded-coverage warning until the Phase 10B global registry release gate passes.

### 10D. Global User Intelligence Engine

- [x] Maintain one immutable universal profile across education, experience,
  skills, languages, family, finances, goals, constraints, consent, and evidence
- [x] Rank published pathways with risks, costs, evidence gaps, alternatives, and provenance
- [x] Generate dependency-controlled operational case timelines
- [x] Rank best-fit countries across the complete reviewed global catalogue
  - [x] Persist immutable, content-addressed country-ranking assessments against an exact profile and published pathway-version set
  - [x] Require explicit user acceptance and human review before generating a new country-ranking assessment
  - [x] Preserve the Phase 10B release gate by labelling incomplete scope as reviewed-published-catalogue-only
- [x] Explain country-level tradeoffs, long-term goals, PR/citizenship dependencies, and uncertainty
  - [x] Derive ranking scores deterministically from profile fit, confidence, and reviewed pathway risk
  - [x] Surface costs, processing ranges, evidence gaps, coverage posture, and route alternatives by country
  - [x] Read permanent-residence and citizenship dependencies only from human-published pathway metadata and never infer missing rules
  - [x] Add uncertainty scoring and explicit non-recommendation/non-guarantee labels
- [x] Reassess only when the user explicitly accepts a new profile or reviewed regulatory version

### 10E. Multi-Year Global Mobility Timeline

- [x] Generate operational profile-to-settlement milestones for one selected pathway
- [x] Model versioned transitions across study, graduate rights, work permits,
  skilled migration, settlement, permanent residence, and citizenship eligibility
- [x] Support dated multi-country scenarios such as Austria study (2026), graduate
  permit (2028), RWR Card (2029), RWR Plus (2031), permanent residence (2034),
  and citizenship-eligibility review (2035)
- [x] Recalculate downstream stages when verified rules change while preserving the original scenario
- [x] Never present future eligibility dates as guarantees; require reviewed rules and human confirmation


Delivered country-ranking governance: explicit user acceptance creates an immutable
assessment tied to the exact profile version, published pathway versions, and registry
release posture. Countries are grouped and ranked only from human-published pathway
evidence. Permanent-residence and citizenship dependencies are surfaced only when they
exist in reviewed pathway metadata; missing data becomes visible uncertainty, never an
inference. Until Phase 10B passes, every response is labelled
`reviewed_published_catalogue_only` and cannot claim complete global ranking coverage. See
`docs/REVIEWED_GLOBAL_COUNTRY_RANKING_V10_13.md`.

Delivered multi-year scenario governance: explicit user acceptance and human review create
an immutable scenario version from exact published pathway versions, verified rules, source
snapshots, operator-confirmed durations, and dated dependencies. Reviewed pathway-impact
replacements can create a new scenario version; the prior scenario and all of its dates and
evidence remain unchanged. Every stage states that future eligibility is not guaranteed and
must be re-verified before action. See `docs/MULTI_YEAR_MOBILITY_SCENARIOS_V10_14.md`.

Historical and predictive analytics remain gated until sufficient verified history exists.

## Phase 11: Business and Wealth Mobility — Complete

- [x] Corporate account and review-gated employee mobility-case foundation
- [x] Dedicated dependant relationships, sponsor entities, and compliance calendars
- [x] Relocation task orchestration
- [x] Entrepreneur and startup mobility
- [x] Evidence-grounded Business & Wealth advisory with feasibility scoring, ranked lawful strategies, blockers, next actions, and independent  human review
- [x] Governed residency/citizenship-by-investment and investor-entrepreneur catalogue with source-pinned versioning and independent publication
- [x] Independently verified jurisdiction program onboarding
- [x] Jurisdiction program onboarding readiness, blocker diagnosis, and domain-isolated source controls
- [x] Begin official-source jurisdiction onboarding with Austria evidence and a pending-review pathway draft
- [x] Immutable source-pinned investment-rule proposals with independent approve/reject decisions and no automatic pathway publication
- [x] Client-specific investment-mobility readiness and program comparison with evidence, currency, family, risk, and independent-review controls
- [x] HNWI and family-office mobility with ownership, wealth-evidence, screening, governance, specialist, banking, succession, route-grounding, and independent-review controls
- [x] Tax residency and treaty intelligence with specialist-review controls

## Phase 12: Channels, Ecosystem, and Automation — In Progress

- [x] Dedicated responsive client web portal with expiring lead-scoped access, a client-safe dashboard, revocation, and audit
- [x] Native/mobile application and device-specific secure session controls
- [x] Employer and partner portal with account-derived tenant isolation, expiring access, minimized projections, revocation, and audit
- [x] Versioned public/partner APIs with stable projections, account-derived tenancy, scoped expiring credentials, revocation, pagination, and audit
- [x] Email, messaging, calendar, CRM, and case-event automation
  - [x] Account-scoped idempotent event ledger, rule matching, minimized multichannel outbox, independent review, dispatch receipts, audit, and Automation Hub
  - [x] Credential-backed email, messaging, calendar, and CRM provider adapters with retry, dead-letter, reconciliation, and scheduled delivery workers
- [x] Government and mobility-agency workflows
  - [x] Authority appointment scheduling and status tracking
  - [x] Agency submission tracking
  - [x] External agency assignment lifecycle and SLA tracking
  - [x] Authority submission checklist templates and per-application checklists
  - [x] Client portal visibility for appointments, submissions, assignments, and checklists
  - [x] Reminder automation for appointments and pending checklist items

## Phase 13: Global Scale Platform — Not Started

- [ ] Progressive coverage of all recognized countries and independent jurisdictions
- [ ] OpenSearch/Elasticsearch when validated search requirements exceed PostgreSQL
- [ ] Neo4j when validated graph traversal requires a dedicated graph store
- [ ] Durable event streaming and Temporal-class workflows when scale requires them
- [ ] OpenTelemetry, Prometheus, Grafana, Loki, tracing, SLOs, backups, and DR exercises
- [ ] Kubernetes and AWS/Azure/GCP/on-premise deployment profiles when operationally justified

## Delivery Rules

Every phase must include:

- Source provenance and Truth Engine integration for regulated claims
- Controlled agent permissions and human-review defaults
- Audit events for sensitive actions and state transitions
- Database migration and rollback paths
- Backend tests and frontend type/build validation
- Security, privacy, consent, retention, and operational notes
- Documentation updates and coverage-ledger status changes
## v10.22.5 — Africa tranche 1A completion

- Completes independent assessment and source-certification review for the British Indian Ocean Territory (`IO`), Angola (`AO`), Benin (`BJ`), Burkina Faso (`BF`), Burundi (`BI`), Cabo Verde (`CV`), Cameroon (`CM`), and Central African Republic (`CF`).
- Publishes narrow, snapshot-pinned initial verified rules for all eight jurisdictions through the separate proposer/reviewer/publisher identities.
- Moves coverage readiness from 6/243 to 14/243 and verified-rule count from 6 to 14.
- Keeps the global coverage claim false because 229 required jurisdictions remain incomplete.
- Algeria (`DZ`) remains blocked by official-endpoint TLS validation; TLS verification was not bypassed.
- Adds v10.22.4 regression tests in `apps/api/tests/test_coverage_v10_22_4_reconciliation.py` covering source-only supplemental assessment reuse, local pending/rejected assessment precedence, mandatory source certification, and snapshot provenance.
- Replaces deprecated `session.query()` usage in `apps/api/tests/test_eligibility.py` with `session.exec()`.
- Adds `.gitattributes` for LF/CRLF normalization to reduce line-ending noise on Windows.
- Makes `apps/api/tests/conftest.py` robust to shallow Docker container directory structures.
- Updates `docs/ROADMAP.md` and records the operational receipts in the local `coverage-operations-receipts/` folder.
- No database migration, automatic evidence approval, snapshot mutation, regulatory-change claim, or global coverage claim.

## v10.22.4 — Supplemental baseline assessment reconciliation

- Baseline eligibility may reuse the latest independently approved jurisdiction assessment when a source-only supplemental batch intentionally omits a duplicate assessment.
- Supplemental reconciliation preserves explicit supplemental certification scope and also recognizes source-only batches through the intentional absence of a batch-local assessment.
- A batch-local pending or rejected assessment continues to take precedence and is never bypassed.
- The supplemental source certification remains batch-item-specific and must be independently approved.
- Initial-rule assertion proposals use the same controlled reconciliation for source-only supplemental items while continuing to require the item's own approved source certification and immutable baseline snapshot.
- No database migration, automatic evidence approval, rule publication, snapshot mutation, or coverage claim.
