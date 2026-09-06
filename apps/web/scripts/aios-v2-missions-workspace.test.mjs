import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import {
  buildV2MissionPortfolio,
  filterMissionSummaries,
  missionDestination,
  missionSourceUnavailable,
  selectMissionSummary,
} from "../lib/v2/missions-workspace.ts";
import { navigationCommands, ownerNavigation } from "../lib/v2/navigation.ts";

const mission = (missionKey, overrides = {}) => ({
  missionKey,
  title: missionKey === "mission:alpha" ? "Alpha evidence review" : "Beta filing",
  state: missionKey === "mission:alpha" ? "awaiting_owner" : "queued",
  phaseKey: missionKey === "mission:alpha" ? "review" : null,
  participantCount: missionKey === "mission:alpha" ? 2 : 1,
  blockerCount: missionKey === "mission:alpha" ? 1 : 0,
  decisionCount: missionKey === "mission:alpha" ? 1 : 0,
  rootWorkItemId: `work:${missionKey.split(":")[1]}`,
  canonicalBasis: `Mission:${missionKey}`,
  ...overrides,
});

const ownerData = (overrides = {}) => ({
  loadedAt: "2026-09-06T01:00:00Z",
  partial: false,
  unavailableSources: [],
  attention: [],
  missions: [mission("mission:alpha")],
  recentChanges: [],
  boardGeneratedAt: null,
  organization: {
    established: true,
    generatedAt: "2026-09-06T00:59:00Z",
    scope: "fixture",
    contractVersion: "living-organization-scene.v5",
    sceneAuthoritative: false,
    rendererAuthoritative: false,
    mutationsAllowed: false,
    canonicalAuthority: "Fixture canonical source",
    missions: [mission("mission:alpha"), mission("mission:beta")],
    zones: [],
    employeeRosterCount: 3,
    departmentCount: 1,
    missionCount: 2,
    coverage: { missions: "fixture" },
  },
  ...overrides,
});

test("Q5 derives literal portfolio metrics from the full organization Mission collection", () => {
  const portfolio = buildV2MissionPortfolio(ownerData());
  assert.equal(portfolio.returnedMissionCount, 2);
  assert.equal(portfolio.missionsWithBlockers, 1);
  assert.equal(portfolio.missionsWithDecisions, 1);
  assert.equal(portfolio.rosteredParticipants, 3);
  assert.deepEqual(portfolio.missions.map((item) => item.missionKey), ["mission:alpha", "mission:beta"]);
});

test("Q5 uses organization.missions rather than the five-item Owner Home slice and adds no read path", () => {
  const helper = readFileSync(new URL("../lib/v2/missions-workspace.ts", import.meta.url), "utf8");
  const component = readFileSync(new URL("../components/v2/V2MissionsWorkspace.tsx", import.meta.url), "utf8");
  assert.match(helper, /data\.organization\.missions/);
  assert.doesNotMatch(helper, /data\.missions/);
  assert.match(component, /useV2OwnerOrganization/);
  assert.doesNotMatch(component + helper, /getLatestAustriaLivingScene|fetch\(/);
});

test("Q5 distinguishes unavailable Living Organization source from an established empty portfolio", () => {
  assert.equal(missionSourceUnavailable(ownerData({ partial: true, unavailableSources: ["Living Organization scene"] })), true);
  const empty = ownerData({ organization: { ...ownerData().organization, missions: [], missionCount: 0 } });
  assert.equal(missionSourceUnavailable(empty), false);
  assert.equal(buildV2MissionPortfolio(empty).returnedMissionCount, 0);
});

test("Q5 filters supplied states and opaque identities without inventing ranking", () => {
  const missions = ownerData().organization.missions;
  assert.deepEqual(filterMissionSummaries(missions, "ALPHA review", "awaiting_owner").map((item) => item.missionKey), ["mission:alpha"]);
  assert.deepEqual(filterMissionSummaries(missions, "Alpha", "queued"), []);
  assert.equal(selectMissionSummary(missions, "mission:beta")?.state, "queued");
  const opaque = "mission:AT /?ref=%23#alpha";
  assert.equal(new URL(missionDestination(opaque), "http://test").searchParams.get("mission"), opaque);
});

test("Q5 keeps Missions enabled as later Owner domains are introduced incrementally", () => {
  const missions = ownerNavigation.find((item) => item.label === "Missions");
  assert.equal(missions?.enabled, true);
  assert.equal(missions?.href, "/cockpit/v2/missions");
  assert.equal(navigationCommands.filter((item) => item.href === "/cockpit/v2/missions").length, 1);
  const history = ownerNavigation.find((candidate) => candidate.label === "History");
  assert.equal(history?.enabled, false);
  assert.equal(history?.href, null);
});

test("Q5 selection remains inspection-only and loaded-record search performs no fetch", () => {
  const component = readFileSync(new URL("../components/v2/V2MissionsWorkspace.tsx", import.meta.url), "utf8");
  assert.match(component, /useV2SearchItems/);
  assert.match(component, /V2Inspector/);
  assert.doesNotMatch(component, />\s*(Start Mission|Pause Mission|Complete Mission|Assign employee|Approve|Reject|Resolve blocker|Escalate)\s*</i);
  assert.doesNotMatch(component, /\b(POST|PUT|PATCH|DELETE)\b/);
  assert.match(component, /Roster counts are not physical presence/);
  assert.match(component, /No progress percentage, completion, urgency, authority or next action is inferred/);
});
