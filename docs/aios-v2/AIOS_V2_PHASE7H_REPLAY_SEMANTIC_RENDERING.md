# AIOS V2 Phase 7H — Replay Semantic Rendering

Phase 7H closes the Living Organization semantic-integration sequence by rendering the sealed replay-state contract as historical cursor truth.

## Truth contract

Replay semantic labels describe reconstructed state **at the selected Activity cursor** only. They never claim the same state is true now.

Supported lifecycle semantics include WorkItem status/assignment, blocker lifecycle, decision lifecycle, human-request lifecycle, and conversation lifecycle when those dimensions are returned by the canonical replay-state contract.

Examples such as `Completed at this cursor`, `Resolved at this cursor`, `Approved at this cursor`, `Rejected at this cursor`, request lifecycle labels, and conversation lifecycle labels are presentation of canonical replay reconstruction only.

Semantic promotion is exact-status only. Phase 7H does not treat colloquial or legacy-looking aliases as canonical terminal states. In particular, WorkItem completion is promoted only from exact `completed`; blocker resolution only from exact `resolved` (`mitigated` is not resolution, while `waived` remains a distinct waiver); decision outcomes only from exact `approved` / `rejected`; HumanActionRequest completion only from exact `completed`; and conversation lifecycle uses exact `open` / `closed`. Unknown values remain literal historical labels and fail closed.

Phase 7H must not infer or claim:

- present/current organization state from historical state;
- physical presence, co-location, locomotion, celebration, or live speech;
- quality, success, improvement, deterioration, urgency, or causality from status or cursor order;
- authority beyond canonical replay fields;
- conversation transcript content when transcript history is unsupported;
- risk-escalation history when that replay dimension is unsupported;
- canonical mutation from any History UI interaction.

Partial reconstruction posture, coverage boundaries, unapplied transitions, and unsupported dimensions remain visible and fail closed.

## Acceptance

Phase 7H requires source-level semantic tests, TypeScript/build proof, responsive/reduced-motion browser proof, explicit no-write verification, a dedicated review screenshot artifact, Q15 baseline inspection for intentional History changes, and final exact-head Repository Policy + V12 acceptance before merge.
