# Multi-Stage Mobility Timeline Engine v8.3

## Purpose

This final Phase 8 increment turns one immutable pathway comparison into an
audited operational plan. It coordinates work from profile readiness through
settlement while preserving the project boundaries around human application
approval, external authority decisions, and regulated claims.

Dates are planning estimates. The timeline never predicts an authority outcome
and never replaces the application lifecycle or authority-decision controls.

## Immutable planning basis

Every `MobilityTimeline` records the exact lead, profile ID/version, comparison
assessment, primary pathway, and published pathway version used to generate it.
Generation is idempotent per comparison: the same comparison cannot create
multiple divergent timelines. A new profile or comparison produces a new plan.

The schedule records its deterministic basis, published maximum processing
window, optional target date, and an explicit authority-timing warning.

## Stages and dependencies

The engine creates eleven sequential milestones:

1. profile readiness
2. evidence collection
3. human eligibility review
4. route-specific prerequisite
5. application preparation
6. human application review
7. submission to authority
8. authority processing
9. authority decision
10. relocation
11. settlement and integration

The fourth stage adapts to study, work, scholarship, family, settlement,
digital-nomad, or general visa routes. Evidence collection combines pathway
required documents with comparison evidence gaps. A milestone becomes ready
only after all dependencies are completed.

## Human control and consent

Eligibility review, the route-specific prerequisite, application review,
submission, and authority decision require a named operator and an approval
note. These approvals record timeline progress only; operators must still use
the dedicated application and authority controls for the underlying action.

Current profile consent is checked at generation, activation, and every
transition. Missing or withdrawn consent restricts an existing timeline and
blocks further transitions. Generation also rejects a comparison whose profile
version is no longer current.

## States and audit

Timelines move from `draft` to `active`, then `completed`; consent loss moves a
timeline to `restricted`. Milestones support `pending`, `ready`, `in_progress`,
`blocked`, and `completed`. Blockers require a reason and all mutations produce
audit events:

- `mobility_timeline_generated`
- `mobility_timeline_activated`
- `mobility_timeline_restricted`
- `mobility_timeline_milestone_transitioned`

## API and workspace

- `POST /api/v1/mobility-timelines/from-comparison/{assessment_id}`
- `GET /api/v1/mobility-timelines?lead_id={lead_id}`
- `GET /api/v1/mobility-timelines/{timeline_id}`
- `POST /api/v1/mobility-timelines/{timeline_id}/activate`
- `POST /api/v1/mobility-timelines/{timeline_id}/milestones/{milestone_id}/transition`

The `/timelines` workspace exposes provenance, progress, due dates, owners,
evidence, blockers, approval notes, and controlled transition actions.

## Database and rollback

Migration `0014_mobility_timeline_engine` creates timeline and milestone tables,
foreign keys, and query indexes. Downgrade removes milestones before timelines.
Fresh SQLite upgrade/downgrade/re-upgrade and live PostgreSQL upgrade remain
release gates.

## Next phase

Phase 9 begins with server-side document extraction jobs and structured schemas,
then connects extracted facts to profile and application validation.
