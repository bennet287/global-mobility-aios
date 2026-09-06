# AIOS V2 Q6 — Evidence + Intelligence

Q6 turns the previously disabled **Evidence** and **Intelligence** domains into read-only Owner workspaces while preserving the accepted AIOS truth boundary.

## Evidence

Route: `/cockpit/v2/evidence`

The Evidence workspace reads the existing Austria live-organization transparency snapshot. It exposes only recorded identifiers and supplied specialist Evidence posture:

- domain Evidence references;
- verified-rule references;
- source-snapshot references;
- specialist `evidence_valid`, `evidence_reason`, grounding state, counts and warnings when supplied.

A reference row is an inspection target, not a claim that source text has been loaded. The inspector deliberately states that source contents, approval, freshness and legal conclusions are not inferred from an identifier.

No Evidence write/review/publish action is introduced.

## Intelligence

Route: `/cockpit/v2/intelligence`

The Intelligence workspace keeps two different truth surfaces visibly separate:

1. **Current governed signals** from the existing `useV2OwnerOrganization()` read path.
2. **Aggregate organization memory** from the existing environmental-memory transparency read.

Current readouts are literal returned counts: attention records, projected Missions, department blocker entries and recent Activity records.

Aggregate memory is explicitly labelled `Aggregate memory`. It is presented using its supplied truth flags (`authoritative`, `predictive`, `mutations_allowed`, `visualization_only`) and never promoted into current-state authority or prediction. Assignment relation frequencies are described as recorded handoff lineage, not physical movement.

## Navigation and search

Q6 enables only `Intelligence` and `Evidence` in addition to previously accepted Home, Organization and Missions. Decisions and History remain fail-closed.

The command palette receives workspace destinations plus only records already loaded by the active page:

- Evidence references register as `Evidence` records;
- recent Activity registers as `Event` records.

No search-specific fetch or persistence is added.

## Interaction and responsive posture

Selection is inspection-only. Desktop uses a bounded list/context composition; at narrower widths the inspector stacks into the reading order. Controls remain keyboard reachable and reduced-motion comprehension does not depend on animation.

## Permanent truth boundaries

Q6 does not infer or claim:

- source contents from a reference identifier;
- approval, legal validity or freshness from reference presence;
- physical presence, location or movement;
- conversations or collaboration;
- completion, urgency, health or success;
- authority from presentation styling;
- predictions from aggregate historical memory;
- canonical mutations or external action authority.

## Proof required before seal

- exact-head design-foundation tests;
- request-auth tests;
- production build / TypeScript;
- compiled-auth proof;
- focused Chromium proof at 1280 and 390 with reduced motion;
- human visual acceptance;
- Woodpecker repository-policy, backend-sqlite, frontend and postgres-governance 4/4 on the exact Q6 candidate.
