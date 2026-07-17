# Codex Continuation Handoff v10.14

## Completed increment

Phase 10E immutable multi-year and multi-country mobility scenarios are complete.

Human-confirmed scenarios now model dated study, graduate-rights, work-permit,
skilled-migration, settlement, permanent-residence, and citizenship-review transitions from
exact published pathway versions, verified rules, and source snapshots. Reviewed regulatory
replacements create a new scenario version only after explicit acceptance; original scenario
rows and dates are never changed.

## Files of interest

- `apps/api/alembic/versions/0029_multi_year_mobility_scenarios.py`
- `apps/api/app/models/domain.py`
- `apps/api/app/services/mobility_scenarios.py`
- `apps/api/app/routers/mobility_timelines.py`
- `apps/api/app/schemas.py`
- `apps/api/tests/test_mobility_scenarios.py`
- `apps/web/app/timelines/ScenarioWorkspace.tsx`
- `apps/web/app/timelines/page.tsx`
- `apps/web/lib/api.ts`
- `docs/MULTI_YEAR_MOBILITY_SCENARIOS_V10_14.md`
- `docs/ROADMAP.md`

## Release state

- Product continuation: v10.14
- Database head: `0029_multi_year_mobility_scenarios`
- Phase 10E: complete
- Remaining Phase 10 work: Phase 10B jurisdiction relationship and primary authority/source evidence completion
- Global coverage claims remain blocked until the Phase 10B release gate passes

## Recommended next bounded increment

Continue Phase 10B with a coverage-operations batch workflow that prioritizes required
jurisdictions, records reviewed immigration-rule relationships, and certifies one primary
authority/source pair per jurisdiction without weakening separate-reviewer controls.
