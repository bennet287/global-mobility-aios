import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { filterMissions, missionCoverageUnavailable, missionDestination, selectMission, validateMissionScene } from "../lib/v2/missions-workspace.ts";
import { navigationCommands, ownerNavigation } from "../lib/v2/navigation.ts";
const fixture = () => JSON.parse(readFileSync(new URL("./fixtures/v2-missions.json", import.meta.url), "utf8"));

test("Q5 joins Mission detail by exact work and participant identity", () => {
  const scene = fixture().scene; const detail = selectMission(scene, "mission:alpha");
  assert.deepEqual(detail.workItems.map((item) => item.work_item_id), ["work:alpha"]);
  assert.deepEqual(detail.participants.map((item) => item.position_key), ["employee:alpha"]);
  assert.deepEqual(detail.handoffs.map((item) => item.activity_id), ["handoff:alpha"]);
  assert.equal(detail.humanRequests[0].instructions, "Provide the missing fixture snapshot.");
  assert.equal(selectMission(scene, "mission:beta").blockers.length, 0);
  assert.equal(selectMission(scene, "missing"), null);
});
test("Q5 preserves missing linked records and contradictory coverage as incomplete", () => {
  const scene = fixture().scene; scene.deterministic.work_items = []; scene.deterministic.employees = []; scene.deterministic.blockers = [];
  const detail = selectMission(scene, "mission:alpha");
  assert.deepEqual(detail.missingWorkIds, ["work:alpha"]); assert.deepEqual(detail.missingParticipantKeys, ["employee:alpha"]);
  assert.ok(detail.unavailable.includes("complete blocker detail")); assert.equal(detail.mission.blocker_count, 1);
});
test("Q5 unavailable coverage is never global or canonical empty", () => {
  const scene = fixture().scene; scene.coverage.missions = "unavailable";
  assert.equal(missionCoverageUnavailable(scene), true);
  assert.ok(selectMission(scene, "mission:alpha").unavailable.includes("missions"));
});
test("Q5 filters exact states without invented progress or input mutation", () => {
  const missions = fixture().scene.deterministic.missions; const before = structuredClone(missions);
  assert.deepEqual(filterMissions(missions, "  ALPHA evidence ", "awaiting_owner").map((item) => item.mission_key), ["mission:alpha"]);
  assert.deepEqual(filterMissions(missions, "Alpha", "queued"), []);
  assert.deepEqual(missions, before);
});
test("Q5 encodes opaque Mission identities without losing characters", () => {
  const key = "objective:AT /?ref=%23#alpha";
  assert.equal(new URL(missionDestination(key), "http://test").searchParams.get("mission"), key);
});
test("Q5 validates non-authority and rejects ambiguous identities", () => {
  assert.equal(validateMissionScene({ established: false, scene: null }), null);
  const current = fixture(); assert.equal(validateMissionScene(current), current.scene);
  current.scene.truth.scene_mutations_allowed = true;
  assert.throws(() => validateMissionScene(current), /read-only/);
  const duplicate = fixture(); duplicate.scene.deterministic.missions.push(duplicate.scene.deterministic.missions[0]);
  assert.throws(() => validateMissionScene(duplicate), /ambiguous/);
  assert.throws(() => validateMissionScene({ established: true, scene: null }), /read-only/);
});
test("Q5 enables only Missions among unfinished Owner workspaces", () => {
  assert.equal(ownerNavigation.find((item) => item.label === "Missions").href, "/cockpit/v2/missions");
  assert.equal(navigationCommands.filter((item) => item.href === "/cockpit/v2/missions").length, 1);
  for (const label of ["Evidence", "Intelligence", "Decisions", "History"]) assert.equal(ownerNavigation.find((item) => item.label === label).enabled, false);
});
