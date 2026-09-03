import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const adapter = await readFile(new URL("../lib/v2/owner-organization.ts", import.meta.url), "utf8");
const organization = await readFile(new URL("../components/v2/V2OrganizationBlockout.tsx", import.meta.url), "utf8");
const workspace = await readFile(new URL("../components/v2/V2OrganizationWorkspace.tsx", import.meta.url), "utf8");
const route = await readFile(new URL("../app/cockpit/v2/organization/page.tsx", import.meta.url), "utf8");

test("V2 Owner Home adapter reads only governed existing sources", () => {
  for (const source of [
    "getBoardPacket",
    "listOrganizationHumanActionRequests",
    "listOrganizationBlockers",
    "listOrganizationActivities",
    "getLatestAustriaLivingScene",
  ]) {
    assert.match(adapter, new RegExp(source));
  }

  assert.doesNotMatch(adapter, /Math\.random\(/);
  assert.doesNotMatch(adapter, /mock|fixture|placeholder/i);
});

test("architectural wing placement is explicitly presentation mapping, not canonical topology", () => {
  assert.match(adapter, /wingForDepartment/);
  assert.match(organization, /data-presentation-topology="aios-v2-office-bible\.v1"/);
  assert.match(organization, /mapped departments/);
  assert.match(organization, /presentation zone/);
});

test("V2 organization blockout preserves non-authority and no-mutation posture", () => {
  assert.match(organization, /data-scene-authoritative/);
  assert.match(organization, /data-renderer-authoritative/);
  assert.match(organization, /data-mutations-allowed/);
  assert.match(organization, /View focus only · no AIOS mutation/);
  assert.match(organization, /rostered positions/);
  assert.match(organization, /not presence claims|No Living Organization scene is established/);
});

test("Organization workspace always includes a structured accessible equivalent", () => {
  assert.match(workspace, /Structured organization/);
  assert.match(workspace, /Available independently of the spatial renderer/);
  assert.match(workspace, /No canonical department mapped/);
});

test("V2 Organization route is isolated under the V2 cockpit namespace", () => {
  assert.match(route, /V2OrganizationWorkspace/);
  assert.match(route, /AiosV2OrganizationPage/);
});
