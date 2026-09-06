# AIOS V2 Q8 — History / Replay

## Status

Provisional implementation on top of the current Q7 Decisions candidate. Q8 is not sealed or merged until Q7 is accepted and Q8 is reconstructed onto the accepted Q7 merge.

## Goal

Turn the final Owner navigation domain, `/cockpit/v2/history`, into a read-only temporal-transparency workspace over the already sealed M.8 replay contracts.

Q8 does not create a second history model. It consumes the existing board-transparent GET surfaces for:

- canonical semantic Activity replay;
- explicit as-of state reconstruction at one Activity cursor;
- explicit state diff between two Activity cursors.

## Existing source contracts reused

- `getLatestAustriaOrganizationReplay()`
- `getLatestAustriaOrganizationReplayState(activityId)`
- `getLatestAustriaOrganizationReplayStateDiff(fromActivityId, toActivityId)`

No backend endpoint, database model, migration, write command or parallel replay store is added by Q8.

## Information architecture

The workspace presents:

1. History source and coverage posture;
2. literal replay readout (`returned_events`, `total_events`, coverage established, truncation);
3. the backend-returned Activity sequence without re-ranking;
4. a selected Activity cursor inspector;
5. bounded as-of state reconstructed by the existing M.8.2 endpoint;
6. optional, explicit cursor-to-cursor field deltas from the existing M.8.3 endpoint.

Selection is inspection only. Comparison is inspection only.

## Coverage posture

Q8 keeps the replay coverage vocabulary visible, including:

- `activity_history_basis`;
- `activity_history_established`;
- `activity_history_coverage_start`;
- `pre_epoch_history`;
- event-level `coverage_state`;
- replay `truncated`;
- state `supported_dimensions` / `unsupported_dimensions`;
- reconstruction posture and unapplied-transition count.

An unestablished replay is unavailable, not an empty history. An established replay with zero returned semantic Activity events may use an empty state. A truncated replay is explicitly partial.

## Truth boundaries

Q8 must never infer from Activity ordering, timestamps, styling, state counts or field deltas:

- physical presence or location;
- travel or physical movement;
- conversation or collaboration;
- work completion beyond an exact supplied status;
- approval, legal validity or execution authority;
- urgency, success, health or productivity;
- causal explanation;
- improvement or deterioration.

Historical reconstruction does not replace current canonical organization state. `authoritative`, `canonical_projection` and `mutations_allowed` are displayed exactly as supplied.

## Command/search continuity

History becomes the seventh enabled V2 Owner domain. The existing legacy `Live Organization & Replay` destination remains available.

Already-loaded replay Activity records may register with the Q2 search registry as `Event` items using deterministic `Event:<activity_id>` identity. Search registration adds no request and no persistence.

## Responsive and accessibility posture

Desktop composes a replay timeline with a sticky inspection surface. At narrower widths the inspector stacks under the timeline rather than shrinking the desktop grid.

Activity rows remain native keyboard-reachable selection controls. The explicit comparison selector is at least 44px high. Reduced motion does not remove any historical meaning.

## Acceptance required

Before Q8 can be sealed:

- Q7 must first seal and merge;
- Q8 must be reconstructed directly onto the accepted Q7 merge;
- exact-head design-foundation, request-auth, production build/TypeScript and compiled-auth must pass;
- focused Chromium at 1280px and 390px must pass under reduced motion;
- human visual acceptance must pass;
- exact-head Woodpecker `repository-policy`, `backend-sqlite`, `frontend`, and `postgres-governance` must all pass.
