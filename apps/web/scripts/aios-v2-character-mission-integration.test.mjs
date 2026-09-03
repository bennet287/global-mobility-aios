import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const adapter = await readFile(new URL("../lib/v2/character-mission-presentation.ts", import.meta.url), "utf8");
const registry = await readFile(new URL("../lib/v2/character-presentation.ts", import.meta.url), "utf8");
const miniature = await readFile(new URL("../components/v2/V2CharacterMiniature.tsx", import.meta.url), "utf8");
const missionRoom = await readFile(new URL("../components/v2/V2MissionRoomPanel.tsx", import.meta.url), "utf8");
const inspector = await readFile(new URL("../components/v2/V2EmployeeInspector.tsx", import.meta.url), "utf8");
const styles = await readFile(new URL("../styles/v2/foundation.css", import.meta.url), "utf8");

test("character adapter resolves presentation from canonical identity without writing canonical state", () => {
  assert.match(adapter, /getPreferredCharacterPresentation/);
  assert.match(adapter, /positionKey: identity\.positionKey/);
  assert.match(adapter, /roleFamily: roleFamilyHint/);
  assert.match(adapter, /presentationOnly: true/);
  assert.match(adapter, /presenceClaimed: false/);
  assert.match(adapter, /canonicalStateWritable: false/);
  assert.match(adapter, /semanticAnimationActive: false/);
  assert.doesNotMatch(adapter, /Math\.random|Date\.now/);
  assert.doesNotMatch(adapter, /POST|PUT|PATCH|DELETE/);
});

test("presentation family inference is deterministic and explicitly presentation-only", () => {
  assert.match(adapter, /Presentation-only family hint/);
  assert.match(adapter, /regulatory-compliance/);
  assert.match(adapter, /operations/);
  assert.match(adapter, /security/);
  assert.match(adapter, /technology-leadership/);
  assert.match(adapter, /executive/);
  assert.match(adapter, /not canonical organization classification/);
});

test("accepted registry identity boundary remains exact-position then family then neutral", () => {
  assert.match(registry, /canonicalPositionKey: "ceo"/);
  assert.match(registry, /canonicalPositionKey: "cto"/);
  assert.match(registry, /canonicalPositionKey: null/);
  assert.match(registry, /presentationPositionKey: "role-family:regulatory-compliance"/);
  assert.match(registry, /presentationPositionKey: "role-family:operations"/);
  assert.match(registry, /getPreferredCharacterPresentation/);
});

test("Mission Room participant selection renders a character presentation miniature", () => {
  assert.match(missionRoom, /V2CharacterMiniature/);
  assert.match(missionRoom, /participant\.positionKey/);
  assert.match(missionRoom, /participant\.title/);
  assert.match(missionRoom, /participant\.department/);
  assert.match(missionRoom, /character is presentation only/);
});

test("Employee Inspector exposes the selected employee character without a presence claim", () => {
  assert.match(inspector, /V2CharacterMiniature/);
  assert.match(inspector, /employee\.position_key/);
  assert.match(inspector, /employee\.title/);
  assert.match(inspector, /employee\.department/);
  assert.match(inspector, /data-presence-claimed="false"/);
});

test("miniature renderer exposes presentation metadata but never activates semantic motion", () => {
  assert.match(miniature, /data-presentation-only="true"/);
  assert.match(miniature, /data-presence-claimed="false"/);
  assert.match(miniature, /data-canonical-state-writable="false"/);
  assert.match(miniature, /data-semantic-animation-active="false"/);
  assert.match(miniature, /data-rig-class/);
  assert.match(miniature, /data-lod-class/);
  assert.match(miniature, /data-animation-set/);
  assert.doesNotMatch(miniature, /data-semantic-animation-active="true"/);
});

test("ambient miniature motion has a reduced-motion equivalent", () => {
  assert.match(styles, /@keyframes aios-v2-character-breathe/);
  assert.match(styles, /@media \(prefers-reduced-motion: reduce\)/);
  assert.match(styles, /\.aios-v2-character-form\s*\{\s*animation: none/);
  assert.doesNotMatch(styles, /aios-v2-character-(walk|handoff|conversation)-semantic/);
});
