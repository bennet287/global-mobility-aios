# Changelog

## 2026-07-14 — Global intelligence evidence filters v10.11

- Added API filters for source freshness, jurisdiction coverage, regulatory authority, evidence confidence, materiality, and review state.
- Added source-monitor freshness, registry coverage posture, authority provenance, and verified-rule/classification-proposal confidence to every dashboard change record.
- Applied the selected evidence scope consistently to metrics, change feeds, country heatmap totals, and the human-published-only Opportunity Radar.
- Added filter option counts, matched-versus-available evidence totals, clear-filter controls, and responsive operator UI.
- Added regression coverage for combined filters, stale/fresh monitoring, coverage posture, authority scoping, confidence provenance, and invalid filter rejection.
- Kept the database migration head at `0026_document_access_grants`; this increment is query and presentation logic only.

## 2026-07-14 — Signed document access v9.5 / product continuation v10.10

- Added migration `0026_document_access_grants` and a short-lived, use-limited access ledger.
- Added HMAC-signed tokens bound to actor, role, lead, document, purpose, and expiry, with raw tokens returned only once and stored only as SHA-256 hashes.
- Added local/MinIO content access with immutable hash and size validation, revocation, expiry reconciliation, and fail-closed denial for missing or altered objects.
- Removed raw storage keys from operator-facing document API payloads and disabled direct object URLs.
- Added strict production posture checks for MinIO TLS, non-default credentials, private pre-provisioned buckets, signing secrets, retention, backup, and recovery records.
- Added Document Intelligence secure-download controls, active-grant metrics, access ledger, and audit provenance without changing document verification state.
- Added regression coverage for one-use consumption, delegated role scope, expiry, revocation, tamper denial, public policy detection, and audit events.

## v6.4 - Next.js Operator Workspace Completion

- Added In-House Consultant Agent (`agents/role_cards/inhouse_consultant.md`, `app/services/inhouse_consultant.py`, `app/routers/agent_chat.py`) with LLM-powered routing and deterministic fallback.
- Added floating chat widget (`apps/web/components/AgentChatWidget.tsx`) integrated into the root layout.
- Added Next.js Agent Console (`apps/web/app/agents/console/page.tsx`) for single and batch controlled-agent runs.
- Added Next.js Agent Review Queue (`apps/web/app/agents/review/page.tsx`) with filters, bulk actions, and run detail view.
- Added `GET /api/v1/agent-output-reviews/runs/{run_id}` endpoint and audit history schema.
- Enriched `GET /api/v1/leads/{id}/detail` with documents and applications; redesigned Next.js lead detail page with tabs, profiles, source references, and actions.
- Added Next.js Client Communication Drafts workspace (`apps/web/app/communications/*`) backed by existing `/api/v1/client-communications` endpoints.
- Updated sidebar navigation with active states for Agents and Communications.

## v6.3 - GitHub Release Prep

- Added `scripts/check_github_release_ready.py`.
- Added release-readiness checks for required tags, clean Git state, release notes, and the v6.2 archive manifest.
- Added `docs/RELEASE_NOTES_MVP_V6_2.md`.
- Added `docs/GITHUB_RELEASE_PREP_V6_3.md`.
- Included the GitHub release readiness checker in local compile coverage.

## v6.2 - MVP Release Archive Export

- Added `scripts/export_mvp_release_archive.py`.
- Added ignored release archive zip output under `release_exports/`.
- Added archive manifest metadata with bundle status, safety rules, tags, and included files.
- Added tests for archive path handling, manifest content, and zip contents.
- Added `docs/MVP_RELEASE_ARCHIVE_V6_2.md`.
- Included the archive exporter in local compile coverage.

## v6.1 - MVP Release Bundle Export

- Added `scripts/export_mvp_release_bundle.py`.
- Added ignored `release_exports/` output storage.
- Added bundle tests for Markdown content, JSON structure, and ignored export paths.
- Added `docs/MVP_RELEASE_BUNDLE_EXPORT_V6_1.md`.
- Included the bundle exporter in local compile coverage.

## v6.0 - MVP Release Hardening

- Added `scripts/check_mvp_release.py`.
- Added release-hardening tests for git cleanliness, required demo tags, demo release status, and quality status.
- Added `docs/MVP_RELEASE_HARDENING_V6_0.md`.
- Included the MVP release checker in local compile coverage.

## v5.9 - Demo Release Status Sync

- Updated `scripts/check_demo_release.py` to validate the v5.8 release state.
- Added release coverage for v5.6 duplicate-output guard, v5.7 demo UX polish, and v5.8 export cleanup.
- Added export-cleanup checks for ignored local demo exports and local production env files.
- Added `docs/DEMO_RELEASE_STATUS_V5_9.md`.

## v5.5 - Demo Release Checkpoint

- Added `scripts/check_demo_release.py`.
- Added release tests for demo readiness, release artifacts, and safety state.
- Added `docs/DEMO_RELEASE_V5_5.md`.
- Added this changelog.
- Included the release checker in local compile coverage.

## v5.4 - Demo Readiness Banner

- Added readiness banner to `/admin/demo`.
- Added readiness banner to `/admin/v2`.
- Extended demo navigation JSON with readiness metadata.

## v5.3 - Demo Navigation Polish

- Added `/admin/demo`.
- Added `/api/v1/admin-demo/navigation`.
- Added a local demo command center with primary workflow links.

## v5.2 - Demo Snapshot Export

- Added JSON and Markdown demo snapshot export.
- Captured lead, agent, client draft, audit, URL, and safety state.

## v5.1 - Demo Release Runbook

- Added local demo runbook helper.
- Documented the safe agent-to-client-draft walkthrough.

## 2026-07-14 — Pathway regulatory impact links v10.6

- Added migration `0022_pathway_regulatory_impacts` and immutable impact ledger.
- Linked human-published graph/rule publication, supersession, and retirement
  events to exact affected published pathway versions.
- Added a review lifecycle that cannot mutate pathway versions, comparisons,
  timelines, or client conclusions.
- Added pathway impact APIs, operator workspace controls, audit events, and
  regression coverage for pinned-record immutability and idempotent graph sync.

## 2026-07-14 — Document expiry monitoring v9.2 / product continuation v10.7

- Added migration `0023_document_expiry_reminders` and the immutable reminder ledger.
- Added deterministic 90, 30, 7-day, and expired urgency scans with unique keys.
- Added stale-date and increasing-urgency supersession while preserving task history.
- Added six-hour Celery Beat scanning, lead-scoped manual scans, and restricted APIs.
- Added human acknowledgement, resolution, and dismissal with mandatory notes and audit events.
- Added the Document Intelligence expiry queue and explicit zero-external-message controls.
- Added regression coverage for deduplication, renewal, lifecycle review, and audit provenance.

## 2026-07-14 — Document requirement detection v9.3 / product continuation v10.8

- Added migration `0024_document_requirement_assessments` and an immutable, content-addressed requirement coverage ledger.
- Added exact requirement resolution from human-published pathway versions, persisted eligibility assessments, or application-domain baselines with visible provenance.
- Added deterministic satisfied, missing, optional, expired, rejected, unverified, fact-inconsistency, and duplicate-conflict findings.
- Added twelve-hour Celery Beat scanning, lead-scoped manual scans, idempotent regeneration, human approval/rejection, and audit history.
- Added the Document Intelligence requirement queue, gap metrics, source snapshots, and explicit non-mutation controls.
- Added regression coverage proving no documents are created and no profile, application, eligibility, pathway, or timeline record is rewritten.
## 2026-07-14 — Document fraud-risk indicators v9.4 / product continuation v10.9

- Added migration `0025_document_fraud_risk_assessments` and immutable integrity-assessment ledger.
- Added deterministic exact-file reuse, conflicting type, approved mismatch, duplicate-conflict, rejected-evidence, hash-integrity, and approved identifier-reuse indicators.
- Masked repeated identifiers and retained only SHA-256 comparison hashes in indicator evidence.
- Added twelve-hour Celery Beat scanning, lead-scoped manual scans, restricted APIs, and mandatory human review notes.
- Added Document Intelligence risk metrics and queue with explicit zero automated fraud determinations or adverse actions.
- Added regression tests for idempotency, source linkage, privacy masking, human review, and non-mutation.

