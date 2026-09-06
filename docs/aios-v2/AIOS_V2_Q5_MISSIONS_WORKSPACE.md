# AIOS V2 Q5 — Missions Workspace V1

Status: reconstructed implementation candidate; not sealed or merged.

Accepted base: `d4fe450927d218d01fd2ee93babd5336ef9c8268` (Q4 merge).

Q5 turns `/cockpit/v2/missions` into the first real successor workspace after Home and Organization. The page is a read-only operational portfolio over the existing governed Owner read path. It deliberately does not create a second Living Organization fetch, backend endpoint, write path or mission-management workflow.

## Recovery reconciliation

Two parallel workers stopped at quota limits and were preserved as recovery branches:

- Codex core: `83dd9141617fb76fc80873c1b56c476ebfc7da2b`.
- Kimi experience: `4c55db640f573388a4c6b06d5b423d0a03bd52d1`.

The recovery branches were treated as design/code input, not merge candidates. Codex's useful route, navigation, search and test ideas were retained, but its independent `getLatestAustriaLivingScene()` Mission hook and deep-scene detail expansion were rejected because Q5's agreed contract reuses `useV2OwnerOrganization()` and `data.organization.missions`. Kimi's useful missing metric primitive was completed with CSS and regression coverage; its unfinished deep-scene presentation model was not promoted into the bounded Q5 route.

## Experience

The workspace presents:

- a semantic page header and source posture;
- literal portfolio readouts for returned Missions, Missions with blockers, Missions with decisions and rostered participant relations;
- filtering over already-loaded Mission summaries;
- exact supplied Mission state, phase and literal counts;
- selection-only Mission inspection;
- technical identifiers and canonical basis behind provenance disclosure.

Selection changes view context only. The page exposes no Start, Pause, Complete, Assign, Approve, Reject, Resolve or Escalate control.

## Truth posture

The full portfolio comes from `V2OwnerOrganizationData.organization.missions`, not the five-item Owner Home slice. Missing Living Organization source coverage is unavailable, not zero. An unestablished scene is not an empty Mission collection. Only an established projection with an empty Mission array renders a genuine empty state.

No progress percentage, urgency, health, success, completion, authority, presence, conversation or collaboration is inferred. Participant counts are roster relations, not physical presence. Search registration uses only records already loaded by the page and creates no search-specific request.

## Responsive and accessibility posture

Desktop uses one composed portfolio/inspector workspace. Below 900px the inspector stacks after the portfolio; at 390px filters and provenance definitions become single-column. Shared object rows retain native button keyboard behavior, selected state and visible focus. Reduced motion is supported without motion-dependent comprehension.

## Candidate proof required

Before seal:

- `npm run test:design-foundation`
- `npm run test:request-auth`
- `npm run build`
- `npm run test:compiled-auth`
- focused Chromium Q5 browser proof at 1280 and 390 with reduced motion
- exact-head Woodpecker repository-policy, backend-sqlite, frontend and postgres-governance 4/4
- human visual acceptance of the Missions workspace

Q6–Q16 remain separate phases.
