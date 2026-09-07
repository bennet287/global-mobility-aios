import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const model = await readFile(new URL("../lib/v2/mission-room-inspector.ts", import.meta.url), "utf8");
const hook = await readFile(new URL("../hooks/useV2MissionRoomInspector.ts", import.meta.url), "utf8");
const missionRoom = await readFile(new URL("../components/v2/V2MissionRoomPanel.tsx", import.meta.url), "utf8");
const inspector = await readFile(new URL("../components/v2/V2EmployeeInspector.tsx", import.meta.url), "utf8");
const missionStrip = await readFile(new URL("../components/v2/V2MissionStrip.tsx", import.meta.url), "utf8");
const workspace = await readFile(new URL("../components/v2/V2OrganizationWorkspace.tsx", import.meta.url), "utf8");

test("Mission Room and employee inspector are read-only canonical projections", () => {
  assert.match(model, /buildV2MissionRoomModel/);
  assert.match(model, /buildV2EmployeeInspectorModel/);
  assert.match(model, /presenceClaimed: false/);
  assert.match(model, /locomotionClaimed: false/);
  assert.match(model, /scene_mutations_allowed/);
  assert.doesNotMatch(model, /Math\.random\(/);
});

test("Mission Room derives only supported participants and linked entities", () => {
  assert.match(model, /participant_position_keys/);
  assert.match(model, /mission\.work_item_ids/);
  assert.match(model, /deterministic\.blockers/);
  assert.match(model, /deterministic\.decisions/);
  assert.match(model, /deterministic\.handoffs/);
  assert.match(model, /must not fabricate a Mission Room/);
});

test("Employee Inspector does not convert roster, Mission membership, governed coordination or risk routing into physical truth", () => {
  assert.match(model, /Mission membership is topology scope only/);
  assert.match(model, /governed coordination requires exact conversation participation/);
  assert.match(model, /risk escalation is shown only for an exact accountable or escalated-to position key/);
  assert.match(model, /No celebration, active collaboration, Board meeting, approval, physical presence, locomotion or live speech is asserted/);
  assert.match(model, /Completion\/resolution evidence is scoped only by exact assigned WorkItem or exact linked WorkItem identity/);
  assert.match(model, /visibleOwnerBoardEscalationsForPosition/);
  assert.match(model, /must not fabricate an employee/);
  assert.match(inspector, /data-presence-claimed="false"/);
  assert.match(inspector, /data-locomotion-claimed="false"/);
  assert.match(inspector, /data-live-speech-claimed="false"/);
  assert.match(inspector, /data-transcript-claimed="false"/);
  assert.match(inspector, /data-active-collaboration-claimed="false"/);
  assert.match(inspector, /data-board-meeting-claimed="false"/);
  assert.match(inspector, /data-explicit-completion-resolution-claimed/);
  assert.match(inspector, /data-completion-inferred-from-animation="false"/);
  assert.match(inspector, /data-physical-celebration-claimed="false"/);
  assert.match(inspector, /Risk escalation routing claimed/);
  assert.match(inspector, /Roster identity is not physical presence/);
});

test("Mission Room UI exposes topology, governed coordination and attention evidence without inventing physical activity", () => {
  assert.match(missionRoom, /Mission topology participants/);
  assert.match(missionRoom, /Topology membership only/);
  assert.match(missionRoom, /Canonical links/);
  assert.match(missionRoom, /Governed Mission coordination/);
  assert.match(missionRoom, /Governed conversations/);
  assert.match(missionRoom, /governed coordination, Owner \/ Board attention and explicit completion\/resolution remain evidence, not physical activity/);
  assert.match(missionRoom, /AIOS will not infer collaboration from Mission membership or shared topology/);
  assert.match(missionRoom, /Owner \/ Board attention/);
  assert.match(missionRoom, /Completed \/ resolved evidence/);
  assert.match(missionRoom, /data-canonical-completion-resolution="true"/);
  assert.match(missionRoom, /no completion inferred from settled character state, animation, elapsed time or missing markers/);
  assert.match(missionRoom, /AIOS will not infer Board attention from severity, Mission membership or room placement/);
  assert.match(missionRoom, /no Board meeting · no approval inferred · no physical attendance or movement/);
  assert.match(missionRoom, /data-active-collaboration-claimed="false"/);
  assert.match(missionRoom, /data-board-meeting-claimed="false"/);
  assert.match(missionRoom, /data-live-speech-claimed="false"/);
  assert.match(missionRoom, /data-transcript-claimed="false"/);
  assert.match(missionRoom, /Authority effect: none · transcript not persisted/);
  assert.match(missionRoom, /No linked handoff events/);
});

test("Mission selection is view-only and drives the inspector workspace", () => {
  assert.match(missionStrip, /onSelectMission/);
  assert.match(missionStrip, /aria-pressed/);
  assert.match(workspace, /selectedMissionKey/);
  assert.match(workspace, /selectedPositionKey/);
  assert.match(workspace, /V2MissionRoomPanel/);
  assert.match(workspace, /V2EmployeeInspector/);
  assert.match(workspace, /V2CanonicalCompletionResolutionSignal/);
  assert.match(workspace, /buildV2VisibleCompletionResolution/);
});

test("Mission Room data hook reads Mission topology and the governed Living Organization scene", () => {
  assert.match(hook, /getLatestAustriaLivingScene/);
  assert.match(hook, /deterministic\.missions/);
  assert.match(hook, /coverage\.missions/);
  assert.match(hook, /deterministic\.human_actions/);
  assert.match(hook, /deterministic\.risk_escalations/);
  assert.match(hook, /coverage\.human_actions/);
  assert.match(hook, /coverage\.risk_escalations/);
  assert.match(hook, /buildV2MissionRoomModel/);
  assert.match(hook, /buildV2EmployeeInspectorModel/);
  assert.doesNotMatch(hook, /POST|PUT|PATCH|DELETE/);
});
