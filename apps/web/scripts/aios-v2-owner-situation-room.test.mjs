import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const ownerHome = await readFile(new URL("../components/v2/V2OwnerHomePrototype.tsx", import.meta.url), "utf8");
const situationRoom = await readFile(new URL("../components/v2/V2OwnerSituationRoom.tsx", import.meta.url), "utf8");
const situationModel = await readFile(new URL("../lib/v2/owner-situation.ts", import.meta.url), "utf8");
const styles = await readFile(new URL("../components/v2/V2OwnerSituationRoom.module.css", import.meta.url), "utf8");
const packageJson = await readFile(new URL("../package.json", import.meta.url), "utf8");

test("Owner Home delegates presentation to the Q3 Situation Room without adding a second data source", () => {
  assert.match(ownerHome, /useV2OwnerOrganization\(\)/);
  assert.match(ownerHome, /<V2OwnerSituationRoom/);
  assert.doesNotMatch(ownerHome, /fetch\(/);
  assert.doesNotMatch(ownerHome, /listOrganization|getBoardPacket|getLatestAustriaLivingScene/);
});

test("Situation Room follows the locked Owner priority order", () => {
  const attention = situationRoom.indexOf("1 · Needs attention");
  const missions = situationRoom.indexOf("2 · Mission condition");
  const organization = situationRoom.indexOf("3 · Organization condition");
  const activity = situationRoom.indexOf("4 · Significant change");

  assert.ok(attention >= 0);
  assert.ok(missions > attention);
  assert.ok(organization > missions);
  assert.ok(activity > organization);
  assert.match(situationRoom, /Decision awareness/);
});

test("Situation summary derives only from existing Owner organization data", () => {
  assert.match(situationModel, /data\.attention/);
  assert.match(situationModel, /data\.missions/);
  assert.match(situationModel, /mission\.blockerCount > 0/);
  assert.match(situationModel, /item\.kind === "decision"/);
  assert.match(situationModel, /data\.organization\.employeeRosterCount/);
  assert.match(situationModel, /zone\.activeBlockerCount/);
  assert.match(situationModel, /data\.recentChanges/);
  assert.doesNotMatch(situationModel, /Math\.random|Date\.now|fetch\(|localStorage|sessionStorage/);
});

test("Situation Room keeps source coverage and zero-state language explicit", () => {
  assert.match(situationRoom, /Partial source coverage/);
  assert.match(situationRoom, /will not infer missing records/);
  assert.match(situationRoom, /governed signals returned/);
  assert.match(situationRoom, /Mission records with linked blockers/);
  assert.match(situationRoom, /No Mission projection is established/);
  assert.match(situationRoom, /No Activity records were returned/);
});

test("Situation Room preserves presentation-only truth boundaries", () => {
  assert.match(situationRoom, /roster counts rather than presence claims/);
  assert.match(situationRoom, /has no mutation authority/);
  assert.doesNotMatch(situationRoom, /physicalPresence\s*=\s*true/);
  assert.doesNotMatch(situationRoom, /walking|coffee break|spoken words|conversation transcript/i);
  assert.doesNotMatch(situationRoom, /onClick=.*approve|onClick=.*reject|onClick=.*submit/i);
});

test("Q3 layout remains bounded and responsive", () => {
  assert.match(styles, /\.priorityGrid/);
  assert.match(styles, /\.contextGrid/);
  assert.match(styles, /@media \(max-width: 1040px\)/);
  assert.match(styles, /@media \(max-width: 760px\)/);
  assert.match(styles, /@media \(max-width: 460px\)/);
  assert.match(styles, /@media \(prefers-reduced-motion: reduce\)/);
});

test("Q3 Situation Room test stays wired into the design-foundation gate", () => {
  assert.match(packageJson, /scripts\/aios-v2-owner-situation-room\.test\.mjs/);
});
