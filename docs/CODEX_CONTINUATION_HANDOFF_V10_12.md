# Codex Continuation Handoff v10.12

## Completed increment

Phase 10D explicit reassessment acceptance controls are complete.

New profile versions and resolved regulatory replacements are surfaced as reassessment
candidates but cannot refresh a pathway comparison through the ordinary compare endpoint.
An operator must record the user's explicit acceptance and then execute that acceptance as
a separate action. The new comparison uses the accepted profile and exact pinned or
replacement pathway versions; all historical comparisons and timelines remain unchanged.

## Files of interest

- `apps/api/alembic/versions/0027_reassessment_acceptances.py`
- `apps/api/app/models/domain.py`
- `apps/api/app/services/reassessment_acceptance.py`
- `apps/api/app/services/pathway_catalogue.py`
- `apps/api/app/routers/pathways.py`
- `apps/api/tests/test_reassessment_acceptance.py`
- `apps/web/app/planning/page.tsx`
- `apps/web/lib/api.ts`
- `docs/REASSESSMENT_ACCEPTANCE_CONTROLS_V10_12.md`
- `docs/ROADMAP.md`

## Release state

- Product continuation: v10.12
- Database head: `0027_reassessment_acceptances`
- Backend: 200 tests passed
- Frontend: compilation, type checking, and all 21 static pages completed; the sandbox
  terminated during final build-trace collection after producing a valid BUILD_ID
- Repository policy, migration, Docker-profile, and local schema checks passed

## Recommended next bounded increment

Implement Phase 10D reviewed global country ranking and country-level trade-off
explanations, while preserving the Phase 10B global-coverage release gate.
