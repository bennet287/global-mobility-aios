# Reviewed Global Country Ranking v10.13

## Purpose

This Phase 10D increment produces an immutable internal country-fit assessment from the
current consented Universal Mobility Profile and the exact set of current human-published
pathway versions. It does not predict approval, declare eligibility, or recommend a
destination without human review.

## Coverage boundary

The ranking service always reads the Phase 10B jurisdiction release gate. Until every
required jurisdiction has reviewed authority, source, freshness, verified-rule, and
immigration-rule-relationship coverage, the response scope is
`reviewed_published_catalogue_only`.

A country absent from the ranking may simply lack a human-published pathway version. The
system never interprets absence as poor fit, no route, or no immigration requirements.
Only after the release gate passes may the response use `complete_global_catalogue`.

## Immutable assessment

Each `CountryRankingAssessment` records:

- lead and exact profile ID/version;
- the complete set of published pathway-version IDs used;
- registry release version and coverage-gate snapshot;
- deterministic ranked-country payload;
- explicit user attestation and operator notes;
- input SHA-256, actor, generation time, and human-review requirement.

Identical inputs and attestations are idempotent. A changed profile, catalogue release,
coverage posture, attestation, or country limit creates a new immutable assessment.
Historical pathway comparisons and timelines are not changed.

## Deterministic ranking

Every current human-published pathway is matched against the same profile. Pathways are
grouped by country, and the leading route determines the country score from:

- deterministic profile fit;
- deterministic match confidence;
- reviewed declared, evidence, and regulatory risk.

Coverage completeness is displayed but does not become a country-quality score. This
prevents incomplete onboarding from being interpreted as negative country evidence.

## Trade-offs and long-term dependencies

Each country response includes:

- leading and alternative reviewed pathways;
- payable costs and minimum-funds thresholds;
- processing ranges, evidence gaps, benefits, and risks;
- country coverage posture;
- permanent-residence and citizenship dependencies;
- explicit uncertainty factors.

Long-term dependencies are read only from metadata on a human-published pathway version.
When permanent-residence or citizenship data is absent, the output says `not_recorded`
and makes no inference about eligibility, timing, or availability.

## Consent and human control

Generation requires current profile consent plus explicit user acceptance, a user
attestation, and operator notes. Every output remains `human_review_required=true`.
The service writes `country_ranking_generated` audit events and does not mutate profiles,
pathways, comparisons, timelines, applications, or communications.

## API and workspace

- `POST /api/v1/pathways/country-rankings/{lead_id}`
- `GET /api/v1/pathways/country-rankings/{lead_id}/latest`
- `GET /api/v1/pathways/country-rankings/{lead_id}`
- `/planning` now includes reviewed country-fit generation, coverage warnings, ranked
  country cards, long-term dependency summaries, uncertainty, and history metrics.

## Migration and verification

Migration `0028_country_ranking_assessments` creates the immutable assessment table and
query indexes. Downgrade removes only this table. Release checks cover fresh migration,
downgrade/re-upgrade, metadata parity, API regression tests, repository policy, and the
Next.js production build.
