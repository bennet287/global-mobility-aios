# Versioned Pathway Catalogue v8.1

## Purpose

The pathway catalogue turns mobility programs into governed, evidence-backed
records that can be matched against a Universal Mobility Profile. It implements
the second Phase 8 capability in
[`GLOBAL_MOBILITY_AIOS_VISION_V1.md`](GLOBAL_MOBILITY_AIOS_VISION_V1.md).

Supported domains are:

- study
- work
- visa
- scholarship
- settlement
- family
- digital nomad

The catalogue does not authorize an application or promise eligibility. Every
regulated conclusion remains subject to the Truth Engine, current official
evidence, deterministic assessment, and human review.

## Data model

`MobilityPathway` is the stable catalogue identity: key, name, country,
jurisdiction, domain, description, and catalogue status.

`MobilityPathwayVersion` is an immutable criteria snapshot containing:

- official source and immutable source snapshot
- active verified-rule references
- deterministic eligibility criteria
- required documents and evidence types
- cost and processing-time structures
- benefits, risks, and effective dates
- draft/published/superseded/retired lifecycle
- creator, reviewer, review notes, and publication timestamp

A new version never updates an older version. Publishing a draft supersedes the
previous published version while preserving its evidence and criteria.

## Governance lifecycle

1. An operator creates a catalogue entry and draft version.
2. Draft evidence can be completed without exposing the route to matching.
3. Publication requires all of the following:
   - an active official source for the same country;
   - an immutable snapshot belonging to that source;
   - at least one active verified rule for the country and a relevant domain;
   - authenticated operator review notes.
4. Publication activates the pathway and records the reviewer.
5. A later draft can be published only through the same evidence gate.
6. Retirement removes every active/draft version from matching and writes an
   audited reason.

Audit actions are `mobility_pathway_created`,
`mobility_pathway_version_created`, `mobility_pathway_version_published`, and
`mobility_pathway_retired`.

## API

- `POST /api/v1/pathways` creates a stable pathway and draft version 1.
- `GET /api/v1/pathways` lists/filter catalogue entries.
- `GET /api/v1/pathways/{pathway_id}` returns immutable version history.
- `POST /api/v1/pathways/{pathway_id}/versions` creates the next draft.
- `POST /api/v1/pathways/versions/{version_id}/publish` performs the evidence
  and human-review publication gate.
- `POST /api/v1/pathways/{pathway_id}/retire` retires a catalogue entry.
- `POST /api/v1/pathways/match/{lead_id}` matches published pathways against the
  current consented profile.

All mutation endpoints use existing RBAC middleware and authenticated actor
attribution.

## Deterministic matching

Only active catalogue entries with a currently effective published version are
considered. Matching currently evaluates:

- target country and mobility-goal domain
- minimum years of experience
- required skills
- qualification keywords
- required languages
- minimum funds
- uploaded evidence document types

Responses include profile ID/version, consent state, match score, confidence,
reasons, missing evidence, and verified-rule IDs. Withdrawn profile consent
returns no matches.

Eligibility assessments use catalogue matches when available. Their factor
record persists pathway/version IDs, official source ID, source snapshot ID,
verified-rule IDs, and match score. The prior deterministic country/domain
fallback remains only where no published catalogue record exists.

## Operator workspace

The Next.js `/pathways` workspace provides:

- catalogue coverage metrics and lifecycle filters
- structured drafting without raw JSON editing
- official source, snapshot, and verified-rule selection
- eligibility, evidence, cost, timing, benefit, and risk fields
- a separate human-review publication action
- immutable version history and retirement controls

## Security and operational notes

- Draft versions never enter matching.
- Evidence relationships are validated server-side; UI selection is not trusted.
- Inactive or jurisdiction/domain-mismatched rules block publication.
- Effective date bounds are enforced at match time.
- Pathway matching consumes only permitted profile facts and honors withdrawn
  consent.
- Client-facing use still requires the existing controlled-agent and human-review
  rules. Publication makes a route eligible for internal assessment, not direct
  client delivery.
- Source-monitor updates do not silently rewrite pathway criteria. A new pathway
  version must be created and reviewed after regulatory change publication.

## Database and rollback

Migration `0012_versioned_pathway_catalogue` creates `mobility_pathways` and
`mobility_pathway_versions`, including source/snapshot foreign keys, immutable
version numbering, lifecycle indexes, and rollback that removes both tables.
SQLite fresh upgrade/downgrade/re-upgrade and PostgreSQL upgrade are part of the
release verification.

## Next Phase 8 increment

The next increment expands cost, risk, alternative-pathway, and missing-evidence
explanations into a dedicated comparison layer before the multi-stage mobility
timeline engine.
