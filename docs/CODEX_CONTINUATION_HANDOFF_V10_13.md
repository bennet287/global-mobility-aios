# Codex Continuation Handoff v10.13

## Completed increment

Phase 10D reviewed global country ranking and country-level trade-off explanations are
complete.

Country rankings are immutable, explicit-acceptance assessments built only from the exact
current profile and human-published pathway versions. They expose costs, alternatives,
evidence gaps, coverage posture, long-term permanent-residence/citizenship dependencies,
and uncertainty. The Phase 10B release gate remains authoritative: incomplete scope is
labelled `reviewed_published_catalogue_only` and cannot be presented as a complete global
ranking.

## Files of interest

- `apps/api/alembic/versions/0028_country_ranking_assessments.py`
- `apps/api/app/models/domain.py`
- `apps/api/app/services/country_ranking.py`
- `apps/api/app/services/pathway_catalogue.py`
- `apps/api/app/routers/pathways.py`
- `apps/api/tests/test_country_ranking.py`
- `apps/web/app/planning/page.tsx`
- `apps/web/lib/api.ts`
- `docs/REVIEWED_GLOBAL_COUNTRY_RANKING_V10_13.md`
- `docs/ROADMAP.md`

## Release state

- Product continuation: v10.13
- Database head: `0028_country_ranking_assessments`
- Phase 10D: complete
- Phase 10B global coverage gate: still blocked until reviewed evidence onboarding is complete

## Recommended next bounded increment

Implement Phase 10E versioned multi-year mobility scenarios across study, graduate rights,
work, settlement, permanent residence, and citizenship-review stages while preserving
original scenarios and requiring reviewed rules plus human confirmation.
