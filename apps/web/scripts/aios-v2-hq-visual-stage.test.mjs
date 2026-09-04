import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { test } from "node:test";

const here = path.dirname(fileURLToPath(import.meta.url));
const libPath = path.resolve(here, "..", "lib", "v2", "hq-visual-presentation.ts");
const componentPath = path.resolve(here, "..", "components", "v2", "V2LivingHqVisualStage.tsx");
const cssPath = path.resolve(here, "..", "components", "v2", "V2LivingHqVisualStage.module.css");

const [libSource, componentSource, cssSource] = await Promise.all([
  readFile(libPath, "utf8"),
  readFile(componentPath, "utf8"),
  readFile(cssPath, "utf8"),
]);

const {
  HQ_VISUAL_PRESENTATION_CONTRACT,
  getWingOrder,
  resolveHqVisualStageLayout,
} = await import(pathToFileURL(libPath).href);

function stripComments(source) {
  return source
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/^\s*\/\/.*$/gm, "");
}

const executableLibSource = stripComments(libSource);
const executableComponentSource = stripComments(componentSource);

const baseMetrics = Object.freeze([
  Object.freeze({
    wingKey: "executive",
    departmentCount: 1,
    employeeCount: 1,
    workItemCount: 1,
    activeBlockerCount: 0,
  }),
  Object.freeze({
    wingKey: "atrium",
    departmentCount: 2,
    employeeCount: 3,
    workItemCount: 4,
    activeBlockerCount: 1,
  }),
]);

const placedCharacters = Object.freeze([
  Object.freeze({
    positionKey: "ceo",
    title: "Chief Executive Officer",
    department: "Executive Office",
    presentationWing: "executive",
  }),
  Object.freeze({
    positionKey: "cto",
    title: "Chief Technology Officer",
    department: "Technology Platform",
    presentationWing: "technology",
  }),
]);

test("stable architectural wing ordering", () => {
  assert.deepEqual([...getWingOrder()], [
    "executive",
    "regulatory",
    "atrium",
    "technology",
    "operations",
  ]);
});

test("identical input produces deeply equal deterministic output", () => {
  const input = { metrics: baseMetrics, characters: placedCharacters };
  assert.deepEqual(resolveHqVisualStageLayout(input), resolveHqVisualStageLayout(input));
});

test("visual adapter deeply freezes every exported result layer", () => {
  const mutableCharacter = {
    positionKey: "ceo",
    title: "Chief Executive Officer",
    department: "Executive Office",
    presentationWing: "executive",
  };
  const output = resolveHqVisualStageLayout({ metrics: baseMetrics, characters: [mutableCharacter] });

  assert.ok(Object.isFrozen(HQ_VISUAL_PRESENTATION_CONTRACT));
  assert.ok(Object.isFrozen(output));
  assert.ok(Object.isFrozen(output.zones));
  assert.ok(Object.isFrozen(output.hubZone));
  assert.ok(Object.isFrozen(output.unplacedCharacters));
  for (const zone of output.zones) {
    assert.ok(Object.isFrozen(zone));
    assert.ok(Object.isFrozen(zone.characters));
    for (const character of zone.characters) assert.ok(Object.isFrozen(character));
  }

  mutableCharacter.title = "mutated outside output";
  assert.equal(
    output.zones.find((zone) => zone.wingKey === "executive").characters[0].title,
    "Chief Executive Officer",
  );
});

test("unknown or explicitly unplaced character remains unplaced", () => {
  const output = resolveHqVisualStageLayout({
    characters: [
      { positionKey: "unknown", title: "Unknown", department: "Unmapped", presentationWing: null },
      { positionKey: "runtime-invalid", title: "Runtime invalid", department: "Unmapped", presentationWing: "not-a-wing" },
    ],
  });

  assert.equal(output.totalCharacterCount, 0);
  assert.equal(output.totalUnplacedCharacterCount, 2);
  assert.deepEqual(output.unplacedCharacters.map((item) => item.positionKey), ["runtime-invalid", "unknown"]);
  for (const item of output.unplacedCharacters) {
    assert.equal(item.presentationWing, null);
    assert.equal(item.presentationOnly, true);
    assert.equal(item.physicalLocationClaimed, false);
    assert.equal(item.presenceClaimed, false);
    assert.ok(Object.isFrozen(item));
  }
});

test("title never determines presentation wing", () => {
  const output = resolveHqVisualStageLayout({
    characters: [{
      positionKey: "ceo-title-probe",
      title: "Chief Executive Officer",
      department: "Executive Office",
      presentationWing: null,
    }],
  });
  assert.equal(output.totalCharacterCount, 0);
  assert.equal(output.unplacedCharacters[0].positionKey, "ceo-title-probe");
});

test("authority-like extra data never determines presentation wing", () => {
  const output = resolveHqVisualStageLayout({
    characters: [{
      positionKey: "authority-probe",
      title: "Officer",
      department: "Executive Office",
      authorityLevel: "board",
      presentationWing: null,
    }],
  });
  assert.equal(output.totalCharacterCount, 0);
  assert.equal(output.unplacedCharacters[0].positionKey, "authority-probe");
});

test("explicit presentation wing is the only character placement input", () => {
  const output = resolveHqVisualStageLayout({
    characters: [{
      positionKey: "ceo-in-ops-probe",
      title: "Chief Executive Officer",
      department: "Executive Office",
      presentationWing: "operations",
    }],
  });
  assert.equal(output.zones.find((zone) => zone.wingKey === "operations").characters[0].positionKey, "ceo-in-ops-probe");
  assert.equal(output.zones.find((zone) => zone.wingKey === "executive").characters.length, 0);
});

test("numeric presentation metrics are sanitized without clocks or randomness", () => {
  const output = resolveHqVisualStageLayout({
    metrics: [{
      wingKey: "executive",
      departmentCount: -4,
      employeeCount: Number.NaN,
      workItemCount: 2.9,
      activeBlockerCount: Number.POSITIVE_INFINITY,
    }],
  });
  const executive = output.zones.find((zone) => zone.wingKey === "executive");
  assert.equal(executive.departmentCount, 0);
  assert.equal(executive.employeeCount, 0);
  assert.equal(executive.workItemCount, 2);
  assert.equal(executive.activeBlockerCount, 0);
});

test("truth posture is explicit and immutable", () => {
  const output = resolveHqVisualStageLayout({});
  assert.equal(output.presentationOnly, true);
  assert.equal(output.physicalLocationClaimed, false);
  assert.equal(output.presenceClaimed, false);
  assert.equal(output.canonicalStateWritable, false);
  assert.equal(HQ_VISUAL_PRESENTATION_CONTRACT.presentationOnly, true);
  assert.equal(HQ_VISUAL_PRESENTATION_CONTRACT.physicalLocationClaimed, false);
  assert.equal(HQ_VISUAL_PRESENTATION_CONTRACT.presenceClaimed, false);
  assert.equal(HQ_VISUAL_PRESENTATION_CONTRACT.canonicalStateWritable, false);
});

test("adapter contains no randomness, clock, network, DOM or write machinery", () => {
  assert.doesNotMatch(executableLibSource, /Math\.random|Date\.now|new Date\s*\(|performance\.now|fetch\s*\(|XMLHttpRequest|WebSocket|requestAnimationFrame|setTimeout|setInterval/);
  assert.doesNotMatch(executableLibSource, /\bPOST\b|\bPUT\b|\bPATCH\b|\bDELETE\b|canonicalStateWritable:\s*true/);
});

test("component reuses V2CharacterMiniature and does not fetch organization truth", () => {
  assert.match(componentSource, /V2CharacterMiniature/);
  assert.doesNotMatch(executableComponentSource, /fetch\s*\(|useV2OwnerOrganization|useBackendStatus|getLatestAustriaLivingScene/);
});

test("component contains no backend, API, database, Three.js, canvas or WebGL integration", () => {
  const combined = `${executableComponentSource}\n${executableLibSource}`;
  assert.doesNotMatch(combined, /from\s+["'][^"']*(?:api|server|database|prisma|sqlite)[^"']*["']|three|@react-three|WebGL|<canvas|GLTFLoader/);
});

test("wing and character controls are native buttons only when callbacks exist", () => {
  assert.match(componentSource, /interactive=\{Boolean\(onSelectWing\)\}/);
  assert.match(componentSource, /onSelectCharacter\s*\?\s*\(/);
  assert.match(componentSource, /<button[\s\S]*?type="button"/);
});

test("component does not nest character buttons inside wing buttons", () => {
  const selectorStart = componentSource.indexOf("<SelectableSurface");
  const selectorEnd = componentSource.indexOf("</SelectableSurface>", selectorStart);
  const characterList = componentSource.indexOf("characterAnchorList", selectorEnd);
  assert.ok(selectorStart >= 0);
  assert.ok(selectorEnd > selectorStart);
  assert.ok(characterList > selectorEnd);
});

test("mission badge uses the missionCount prop rather than work-item totals", () => {
  assert.match(componentSource, /missionCount > 0/);
  assert.doesNotMatch(executableComponentSource, /totalWorkItemCount[^;\n]*missions|missions[^;\n]*totalWorkItemCount/);
});

test("null selectedWing does not fabricate a selected presentation wing", () => {
  assert.match(componentSource, /const activeWing[\s\S]*selectedWing !== null[\s\S]*:\s*null/);
  assert.doesNotMatch(executableComponentSource, /activeWing\s*\?\?\s*getHubWingKey|getHubWingKey\(\)/);
});

test("unplaced presentations are explicitly surfaced rather than silently dropped", () => {
  assert.match(componentSource, /layout\.unplacedCharacters/);
  assert.match(componentSource, /Unplaced presentations/);
  assert.match(componentSource, /does not infer one from title/);
});

test("empty/unestablished scene does not fabricate organization content", () => {
  assert.match(componentSource, /if \(!sceneEstablished\)/);
  assert.match(componentSource, /will not fabricate departments, missions, employees/);
});

test("CSS is locally scoped and contains responsive architectural fallbacks", () => {
  assert.doesNotMatch(cssSource, /^\s*:root\s*\{/m);
  assert.match(cssSource, /\.stageRoot\s*\{/);
  assert.match(cssSource, /@media \(max-width: 1200px\)/);
  assert.match(cssSource, /@media \(max-width: 980px\)/);
  assert.match(cssSource, /@media \(max-width: 760px\)/);
  assert.match(cssSource, /@media \(max-width: 520px\)/);
});

test("reduced motion disables ambient animation and interaction transitions", () => {
  assert.match(cssSource, /@media \(prefers-reduced-motion: reduce\)/);
  assert.match(cssSource, /\.lightPool,[\s\S]*?\.loadingOrb[\s\S]*?animation: none/);
  assert.match(cssSource, /\.wing,[\s\S]*?\.characterButton[\s\S]*?transition: none/);
});

test("ambient loops are presentation-only and not attention-demanding", () => {
  const outsideReducedMotion = cssSource.split("@media (prefers-reduced-motion: reduce)")[0];
  const durations = [...outsideReducedMotion.matchAll(/animation:\s*[^;]*?(\d+(?:\.\d+)?)s[^;]*?infinite/g)].map((match) => Number(match[1]));
  assert.ok(durations.length > 0);
  for (const duration of durations) assert.ok(duration >= 3, `ambient loop ${duration}s is too fast`);
});

test("component contains no walking, travel, conversation or semantic activation claims", () => {
  assert.doesNotMatch(executableComponentSource, /\bwalking\b|\bwalk-to\b|\bphysical travel\b|\bconversation\b|\bspoken words\b|semanticAnimationActive\s*=\s*true|semanticAnimationActive:\s*true/i);
});

test("auxiliary Decision Chamber and Collaboration Deck remain decorative architecture", () => {
  assert.match(componentSource, /Decision Chamber/);
  assert.match(componentSource, /Collaboration Deck/);
  assert.match(componentSource, /className=\{styles\.stageFloor\} aria-hidden="true"/);
});
