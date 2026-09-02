# Immutable Multi-Year Mobility Scenarios v10.14

## Purpose

This Phase 10E increment extends the operational single-pathway timeline into a reviewed,
versioned planning scenario across multiple countries and long-term mobility stages. It is a
planning and provenance record, not an authority prediction, eligibility guarantee, or
substitute for the existing application, decision, and Truth Engine controls.

## Immutable scenario versions

Each `MobilityScenario` stores the exact lead, current consented profile ID/version, optional
baseline timeline, human attestation, reviewer notes, start date, countries, published pathway
versions, verified rules, source snapshots, and regulatory impacts used to generate it.

Each `MobilityScenarioStage` stores a dated transition with:

- study, graduate-rights, work-permit, skilled-migration, settlement, permanent-residence,
  or citizenship-review type;
- exact country, pathway, published pathway version, verified rules, and source snapshots;
- operator-confirmed duration and gap assumptions;
- deterministic start/end dates and dependencies;
- an explicit uncertainty payload stating that future eligibility is not guaranteed.

Submitting the same reviewed input is idempotent. Recalculation never updates an existing
scenario. It creates the next version and links it through `supersedes_scenario_id`.

## Evidence and human-control gate

Scenario creation requires:

1. current granted profile consent;
2. explicit user acceptance and a specific attestation;
3. human review notes;
4. an active pathway with a currently published version for every stage;
5. reviewed official-source and immutable snapshot provenance;
6. at least one active, human-published verified rule with a source snapshot for every stage.

The schedule uses operator-confirmed durations. Published processing-time data is retained as
context, but the engine does not convert it into an authority-outcome prediction.

## Reviewed rule-change recalculation

The recalculation-candidate endpoint finds only human-resolved `PathwayRegulatoryImpact`
records that point to a published replacement pathway version. No recalculation occurs
automatically. A reviewer must select the impacts, confirm user acceptance, and supply notes.
The new scenario version uses replacement pathway versions only for affected stages; all
other stage inputs are preserved.

The original scenario, stage dates, pathway versions, rules, and evidence remain unchanged
and queryable.

## API and workspace

- `POST /api/v1/mobility-timelines/scenarios`
- `GET /api/v1/mobility-timelines/scenarios?lead_id={lead_id}`
- `GET /api/v1/mobility-timelines/scenarios/{scenario_id}`
- `GET /api/v1/mobility-timelines/scenarios/{scenario_id}/recalculation-candidate`
- `POST /api/v1/mobility-timelines/scenarios/{scenario_id}/recalculate`

The `/timelines` workspace now includes a stage builder, dated scenario ledger, immutable
version history, evidence badges, and reviewed-rule recalculation controls.

## Safety boundaries

- Future dates are estimates, not guarantees.
- Residence accrual, permanent residence, and citizenship conditions are never inferred from
  elapsed time alone.
- Every stage must be re-verified against rules effective at the time of action.
- The Phase 10B global-coverage release gate remains authoritative.
- No scenario creates, submits, approves, or changes an application or authority decision.

## Migration and verification

Migration `0029_multi_year_mobility_scenarios` creates scenario and stage tables. Downgrade
removes stages before scenarios. Tests cover explicit acceptance, multi-country dates,
idempotency, reviewed evidence gates, recalculation, audit events, and byte-for-byte
preservation of the original scenario.
