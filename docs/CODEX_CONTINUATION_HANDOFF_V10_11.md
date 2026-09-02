# Codex Continuation Handoff v10.11

## Completed increment

Phase 10C Global Intelligence evidence filters are complete.

The dashboard API and operator workspace now filter one consistent evidence set by
freshness, coverage, authority, confidence, materiality, and review state. Change payloads
include governed authority, monitor, registry, and confidence provenance. Headline counts,
change feeds, country heatmap totals, and Opportunity Radar evidence all use the same
scope, while the Radar remains limited to human-published events.

## Files of interest

- `apps/api/app/services/live_intelligence.py`
- `apps/api/app/routers/live_intelligence.py`
- `apps/api/tests/test_live_intelligence.py`
- `apps/web/app/global-intelligence/page.tsx`
- `apps/web/lib/api.ts`
- `apps/web/app/globals.css`
- `docs/GLOBAL_INTELLIGENCE_FILTERS_V10_11.md`
- `docs/ROADMAP.md`

## Release state

- Product continuation: v10.11
- Database head: `0026_document_access_grants` (unchanged)
- Backend: 198 tests passed, 2 warnings
- Frontend: production build passed all 21 routes
- Local repository policy, migration, Docker-profile, and schema checks passed

## Safety boundary

The filter layer is read-only. It does not publish pending changes, infer confidence,
change coverage status, rewrite verified rules, alter pathways, or trigger client
reassessment.

## Recommended next bounded increment

Implement Phase 10D explicit reassessment acceptance controls so a new universal profile
version or reviewed regulatory version cannot refresh a client assessment until an
operator records the user's explicit acceptance. Continue Phase 10B jurisdiction evidence
onboarding in parallel.
