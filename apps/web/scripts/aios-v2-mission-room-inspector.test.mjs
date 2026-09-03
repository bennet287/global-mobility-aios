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

test("Employee Inspector does not convert roster identity into presence truth", () => {
  assert.match(model, /Roster identity and semantic state do not assert physical presence or locomotion/);
  assert.match(model, /must not fabricate an employee/);
  assert.match(inspector, /data-presence-claimed="false"/);
  assert.match(inspector, /data-locomotion-claimed="false"/);
  assert.match(inspector, /Roster identity is not physical presence/);
});

test("Mission Room UI exposes supported signals without inventing conversation", () => {
  assert.match(missionRoom, /Rostered Mission participants/);
  assert.match(missionRoom, /Canonical links/);
  assert.match(missionRoom, /No linked handoff events/);
  assert.match(missionRoom, /no inferred conversation or presence/);
  assert.doesNotMatch(missionRoom, /transcript|spoken words/i);
});

test("Mission selection is view-only and drives the inspector workspace", () => {
  assert.match(missionStrip, /onSelectMission/);
  assert.match(missionStrip, /aria-pressed/);
  assert.match(workspace, /selectedMissionKey/);
  assert.match(workspace, /selectedPositionKey/);
  assert.match(workspace, /V2MissionRoomPanel/);
  assert.match(workspace, /V2EmployeeInspector/);
});

test("Mission Room data hook reads the governed Living Organization scene", () => {
  assert.match(hook, /getLatestAustriaLivingScene/);
  assert.match(hook, /buildV2MissionRoomModel/);
  assert.match(hook, /buildV2EmployeeInspectorModel/);
  assert.doesNotMatch(hook, /POST|PUT|PATCH|DELETE/);
});
