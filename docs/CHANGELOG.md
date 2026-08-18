# Global Mobility AIOS — Active Changelog

This is the current changelog from the post-`f0688a8` baseline onward. The complete historical changelog through the sealed
Phase 13.16.7 baseline is preserved byte-for-byte at
[archive/CHANGELOG_THROUGH_F0688A8_2026-08-17.md](archive/CHANGELOG_THROUGH_F0688A8_2026-08-17.md).

## 2026-08-18 - Phase 13.16.8 COMPLETE / PASS - Governed Professional / Operator experience

- Refined the existing `/` Operations Workspace and `/leads/[id]` native case workspace instead of creating a parallel
  professional dashboard. The Global Mobility AIOS Cockpit and secure Mobility User experience remain distinct role surfaces.
- Restored `/eligibility` as a first-class Professional / Operator navigation destination while preserving the rule that
  navigation is presentation context only and backend authorization remains authoritative.
- Established the professional reading order as **decision/context → blockers & uncertainty → governed next actions →
  supporting evidence & review state → technical provenance**.
- Composed existing persisted reads for latest eligibility, latest pathway comparison, mobility timelines,
  document-requirement assessments, and application-scoped authority operations. No new backend endpoint or API contract was required.
- Corrected the context-alignment boundary before acceptance: the persisted PathwayComparison is the current-decision anchor;
  timeline/document-assessment records may contribute to current blockers/evidence/journey state only when their persisted
  profile/pathway/version context aligns. Historical, unassigned, and mismatched records remain inspectable but are excluded from current conclusions.
- Kept latest EligibilityAssessment explicitly separate where the contract cannot prove full comparison/profile/pathway
  alignment; absence of an alignment pin is never converted into alignment or clearance.
- Labeled appointments, submissions, external-agency assignments, and authority checklist rows as **case operations**, not
  selected-pathway evidence unless an explicit aligned relationship is persisted.
- Preserved the reliance boundary: opening a case does not evaluate eligibility, generate a comparison, create/activate a
  timeline, certify evidence, submit to an authority, send an authority outcome, or bypass required human review.
- Added premium responsive Professional/Operator case-workbench styling and extended the design-foundation regression to lock
  role separation, Eligibility navigation, exact read bindings, context-alignment filtering, visible mismatch state,
  truthful sparse state, native technical provenance, and no read-surface mutation.

### Acceptance

- design foundation: **25/25 PASS**;
- request/auth regression: **4/4 PASS**;
- Next.js 15.2.4 production build: **PASS**, **41/41 static pages**;
- repository policy: **PASS**;
- release consistency: **PASS** at `0076_organization_position_active_identity`;
- Docker production profile: **PASS**;
- database migration/schema consistency: **PASS** at Alembic `0076_organization_position_active_identity`;
- local physical-schema parity: **PASS** — 118 registered model tables / 118 actual model tables / 119 physical tables including only `alembic_version` infrastructure;
- complete API regression: **811 passed / 5 skipped / 0 failed**; carried forward because the accepted alignment correction is frontend/test-only and no backend/API/model/schema/Alembic file changed;
- `git diff --check`: **PASS**;
- browser/runtime semantic acceptance: **PASS** for aligned data-rich, deliberate context-mismatch, and sparse/uncertain cases;
- browser-open fixture traffic: **GET/HEAD/OPTIONS only**, with no mutation;
- human visual review: **PASS** across all three full-page Professional case captures;
- preserved `gmai.db`: SHA256 `23FC012AF3FA89804A84A9C8DD75C0C68515B23AEF1813CC5460D6D73808CD31`, unchanged and re-verified before seal.

### Boundary

Exact delivery boundary at seal is seven tracked files:

- `apps/web/app/globals.css`
- `apps/web/app/leads/[id]/page.tsx`
- `apps/web/app/page.tsx`
- `apps/web/lib/workspace-navigation.ts`
- `apps/web/scripts/design-foundation.test.mjs`
- `docs/CHANGELOG.md`
- `docs/ROADMAP.md`

There is **no backend/model/Alembic/preserved-database/Austria-safety/Technology-Radar runtime semantic change** in this slice.
AIOS Coworker remains a future UX seam only; no speculative OpenWorker/runtime dependency is introduced.

Phase 13.16.9 Evidence and provenance UX consolidation is now **UNLOCKED / NEXT**.

## 2026-08-18 - Technology Radar V1.1 / Platform Evolution architecture checkpoint

- Promoted `docs/TECHNOLOGY_RADAR_V1_1.md` as the active canonical platform-evolution radar while preserving frozen
  `docs/TECHNOLOGY_RADAR_V1.md` as historical evidence.
- Added strategic fit tiers and recorded OpenWorker (`andrewyng/openworker`) as **A+ / STRATEGIC REFERENCE / CONTROLLED
  PILOT** for the future AIOS Coworker / finished-work execution plane; existing specialist candidates remain independently
  evaluated.
- Established the AIOS-owned **AIOS Coworker** capability boundary: third-party coworker/runtime implementations may
  execute files/tools/connectors and produce deliverables behind AIOS-owned contracts, but may not define WorkItem,
  authority, evidence/legal truth, Activity, Contribution, certification, publication, or business outcome semantics.
- Added the **Internal Learning & Quality Principle** and separated operational intelligence, evaluation/quality, and
  permitted training/optimization. Professional corrections, approvals/rejections, OCR fixes, and workflow outcomes are
  future traceable learning signals rather than implicit mutations of authoritative records.
- Added training/evaluation lineage direction plus a future `AIOSDataUsagePolicy` boundary so service, analytics,
  evaluation, improvement, human-review, and internal-model-training uses can be allowed/conditional/excluded with purpose,
  lawful-basis/compatibility, sensitivity, retention, provenance, and lineage metadata.
- Recorded the EU compliance direction as compliance-aware lawful learning: GDPR processing-purpose/legal-basis,
  special-category, minimisation, transparency, retention/security, and other applicable safeguards must be resolved for
  each production regime; future EU AI Act/GPAI provider obligations remain separately assessed if AIOS later becomes a
  model provider.
- Updated Platform Evolution waves: Wave 1 quality/safety (Promptfoo/OpenTelemetry/ClamAV), Wave 2 document/privacy
  intelligence, Wave 3 regulatory monitoring, Wave 4 AI runtime/retrieval/quality, Wave 5 AIOS Coworker + durable
  organization execution, Wave 6 professional output.
- Updated `docs/THIRD_PARTY_PLATFORM_ADOPTION_PRINCIPLES.md` to V1.1 while preserving AIOS Semantic Sovereignty,
  adapter-first integration, provider replacement, and evidence/authority boundaries.
- Reorganized the active `docs/ROADMAP.md` and `docs/CHANGELOG.md` into current-state documents while preserving their exact
  pre-checkpoint contents under `docs/archive/`. This keeps ongoing sessions focused without deleting historical Phase-13
  evidence.
- Corrected roadmap status so 13.16.8 Professional / Operator experience is consistently **UNLOCKED / NEXT** after accepted
  13.16.7; product sequencing itself is unchanged.
- Documentation/architecture checkpoint only: **no runtime dependency, package, model/table change, migration, container,
  feature flag, provider interface, preserved-database mutation, authorization expansion, publication/certification
  change, human-review weakening, production training regime, or Austria legal-safety change**. Phase 13.16.8 remains the
  active product slice.

### Verification in the documentation-preparation environment

- repository policy: **PASS**;
- release consistency: **PASS** at `0076_organization_position_active_identity`;
- UTF-8 / markdown-fence / relative-reference / trailing-whitespace integrity: **PASS**;
- database-migration checker: **not executed successfully in this environment** because the isolated runtime does not
  include `sqlmodel`; this is recorded as an environment limitation, not a PASS or product failure.
- no frontend build, complete API regression, browser/runtime acceptance, database mutation, or migration execution is
  claimed for this docs-only architecture checkpoint.
