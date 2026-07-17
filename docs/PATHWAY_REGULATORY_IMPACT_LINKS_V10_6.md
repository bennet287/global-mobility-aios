# Pathway Regulatory Impact Links v10.6

## Outcome

Human-published regulatory graph updates now create immutable, review-gated
impact records for exact currently published pathway versions that may be
affected. The impact layer is an operational queue, not an automatic pathway
editor or client reassessment engine.

The following records remain unchanged when a new rule is published,
superseded, or retired:

- the affected `MobilityPathwayVersion` criteria and evidence snapshot;
- existing `PathwayComparisonAssessment` records;
- existing `MobilityTimeline` records; and
- prior eligibility or client-facing conclusions.

## Deterministic affected-version matching

An impact is created only when all of the following are true:

1. the regulatory event comes from a human-published verified rule and reviewed
   regulatory change;
2. the rule has already been projected into the provenance-preserving graph;
3. a pathway version is currently `published`;
4. the pathway matches the rule jurisdiction, with normalized country fallback
   only for legacy pathways without a jurisdiction link;
5. the rule domain is relevant to the pathway domain; and
6. the rule publication or retirement event occurred on or after the exact
   pathway version was published.

Each impact records its match basis, including direct verified-rule reference,
superseded-rule reference, official-source match, jurisdiction/country match,
and regulatory-domain match. This prevents a graph synchronization from
creating false impacts for pathway versions published after an older rule event.

## Immutable provenance

`PathwayRegulatoryImpact` stores:

- stable idempotency key;
- pathway and exact pathway-version IDs;
- verified rule and optional superseded-rule IDs;
- reviewed regulatory change and immutable source-snapshot IDs;
- projected verified-rule graph-node ID and graph projection version;
- impact type, materiality, event time, and deterministic match basis;
- pathway/rule/change context captured at detection time;
- counts of pinned primary comparisons and timelines at detection time;
- human-review status, reviewer, notes, and time; and
- optional newer human-published pathway version used to resolve the impact.

The graph and impact records are derived from governed evidence. Neither is an
independent truth source.

## Review lifecycle

Every new record starts as `pending_review`. A permitted operator can record one
of these decisions:

- `acknowledged` — reviewed, with follow-up still open;
- `no_change_required` — reviewed evidence does not require a pathway change;
- `new_version_required` — a new immutable pathway draft must be created through
  the existing pathway catalogue workflow; or
- `resolved` — a newer version of the same pathway has completed human-reviewed
  publication and is explicitly linked as the resolution.

Resolution rejects draft or unrelated pathway versions. Review decisions never
create, publish, supersede, or retire a pathway version automatically.

## Rule lifecycle behavior

- A newly published rule creates `rule_published` impacts.
- A replacement rule creates one `rule_supersession` impact and records the
  superseded rule so direct references are visible.
- Explicit rule retirement creates `rule_retired` impacts.
- Knowledge-graph synchronization is idempotent and repairs missing graph-node
  links without duplicating or resetting reviewed impacts.

## API and operator workspace

- `GET /api/v1/pathways/regulatory-impacts`
  - filters: status, pathway, pathway version, verified rule, impact type, limit
  - returns queue counts, exact provenance, pinned-record counts, and the
    `client_assessments_unchanged` safety flag
- `POST /api/v1/pathways/regulatory-impacts/{impact_id}/review`
  - records an explicit human decision and optional published replacement version

The `/pathways` workspace includes pending-impact metrics, provenance and match
basis, pinned comparison/timeline counts, review notes, and controlled actions.
It never edits pathway criteria from the impact panel.

## Migration and verification

Migration `0022_pathway_regulatory_impacts` creates the impact ledger and its
provenance, lifecycle, and query indexes. Downgrade removes only the derived
impact table.

Automated tests verify supersession and retirement impacts, idempotent graph
synchronization, replacement-version validation, audit history, and byte-for-byte
preservation of pinned comparison, timeline, and pathway-version records.
