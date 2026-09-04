import assert from "node:assert/strict";
import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { test } from "node:test";

const here = path.dirname(fileURLToPath(import.meta.url));
const layoutPath = path.resolve(here, "..", "lib", "v2", "hq-character-layout.ts");
const hookPath = path.resolve(here, "..", "hooks", "useV2MissionRoomInspector.ts");
const blockoutPath = path.resolve(here, "..", "components", "v2", "V2OrganizationBlockout.tsx");
const workspacePath = path.resolve(here, "..", "components", "v2", "V2OrganizationWorkspace.tsx");
const stylesPath = path.resolve(here, "..", "components", "v2", "V2OrganizationBlockout.module.css");

const layoutSource = await readFile(layoutPath, "utf8");
const hookSource = await readFile(hookPath, "utf8");
const blockoutSource = await readFile(blockoutPath, "utf8");
const workspaceSource = await readFile(workspacePath, "utf8");
const stylesSource = await readFile(stylesPath, "utf8");

// The layout module imports only TypeScript types. Remove those imports in the
// direct Node test copy so native type stripping can execute the pure functions
// without relying on application bundler resolution.
const executableLayoutSource = layoutSource
  .replace(/import type \{ LivingSceneEmployee \} from "\.\.\/live-organization";\n/, "")
  .replace(/import type \{[\s\S]*?\} from "\.\/owner-organization";\n/, "");

const tempDir = await mkdtemp(path.join(tmpdir(), "aios-v2-hq-layout-"));
const executableLayoutPath = path.join(tempDir, "hq-character-layout.ts");
await writeFile(executableLayoutPath, executableLayoutSource, "utf8");

const {
  buildV2HqCharacterLayout,
  getV2HqPlacementsForWing,
} = await import(pathToFileURL(executableLayoutPath).href);

function department(key, label) {
  return {
    key,
    label,
    employeeRosterCount: 1,
    workItemCount: 0,
    activeBlockerCount: 0,
    canonicalBasis: `Department:${key}`,
  };
}

const zones = [
  {
    wingKey: "executive",
    label: "Executive Terrace",
    departments: [department("executive_office", "Executive Office")],
    employeeRosterCount: 1,
    workItemCount: 0,
    activeBlockerCount: 0,
  },
  {
    wingKey: "technology",
    label: "Technology & Security",
    departments: [department("technology_platform", "Technology Platform")],
    employeeRosterCount: 1,
    workItemCount: 0,
    activeBlockerCount: 0,
  },
  {
    wingKey: "operations",
    label: "Operations Studio",
    departments: [department("operations_coordination", "Operations Coordination")],
    employeeRosterCount: 1,
    workItemCount: 0,
    activeBlockerCount: 0,
  },
];

function employee(positionKey, title, departmentName) {
  return {
    position_key: positionKey,
    title,
    department: departmentName,
    reports_to_position_key: null,
    authority_level: "team",
    organization_status: "active",
    work_item_id: null,
    work_status: null,
    semantic_state: "queued",
    presence_state: "unsupported",
    state_reason: "fixture",
  };
}

test("HQ character layout maps only normalized exact canonical department key/label matches", () => {
  const layout = buildV2HqCharacterLayout(
    [
      employee("ceo", "Chief Executive Officer", "Executive Office"),
      employee("cto", "Chief Technology Officer", "technology_platform"),
      employee("ops", "Operations Coordinator", "Operations Coordination"),
    ],
    zones,
  );

  assert.equal(layout.placements.length, 3);
  assert.equal(layout.unplaced.length, 0);
  assert.deepEqual(
    layout.placements.map((item) => [item.positionKey, item.wingKey]),
    [
      ["ceo", "executive"],
      ["cto", "technology"],
      ["ops", "operations"],
    ],
  );
});

test("title never causes a guessed HQ room when canonical department mapping is absent", () => {
  const layout = buildV2HqCharacterLayout(
    [employee("fake-ceo-probe", "Chief Executive Officer", "Unmapped Department")],
    zones,
  );

  assert.equal(layout.placements.length, 0);
  assert.equal(layout.unplaced.length, 1);
  assert.equal(layout.unplaced[0].positionKey, "fake-ceo-probe");
  assert.equal(layout.unplaced[0].reason, "unmapped-department");
  assert.match(layout.unplaced[0].limitation, /will not invent a spatial room/i);
});

test("ambiguous department-to-zone mapping remains unplaced instead of choosing the first room", () => {
  const ambiguousZones = [
    ...zones,
    {
      wingKey: "regulatory",
      label: "Regulatory Wing",
      departments: [department("duplicate_ops", "Operations Coordination")],
      employeeRosterCount: 1,
      workItemCount: 0,
      activeBlockerCount: 0,
    },
  ];
  const layout = buildV2HqCharacterLayout(
    [employee("ops", "Operations Coordinator", "Operations Coordination")],
    ambiguousZones,
  );

  assert.equal(layout.placements.length, 0);
  assert.equal(layout.unplaced.length, 1);
  assert.equal(layout.unplaced[0].reason, "ambiguous-department-mapping");
  assert.match(layout.unplaced[0].limitation, /ambiguous mapping/i);
});

test("HQ placement is presentation-only and never claims physical location or presence", () => {
  const layout = buildV2HqCharacterLayout(
    [employee("cto", "Chief Technology Officer", "Technology Platform")],
    zones,
  );
  const placement = layout.placements[0];

  assert.equal(layout.presentationOnly, true);
  assert.equal(layout.physicalLocationClaimed, false);
  assert.equal(layout.presenceClaimed, false);
  assert.equal(placement.presentationOnly, true);
  assert.equal(placement.physicalLocationClaimed, false);
  assert.equal(placement.presenceClaimed, false);
  assert.equal(placement.placementBasis, "canonical-department-zone-mapping");
});

test("HQ layout output is deterministic, sorted and runtime frozen", () => {
  const employees = [
    employee("z-position", "Z", "Operations Coordination"),
    employee("a-position", "A", "Executive Office"),
  ];
  const first = buildV2HqCharacterLayout(employees, zones);
  const second = buildV2HqCharacterLayout(employees, zones);

  assert.deepEqual(first, second);
  assert.deepEqual(first.placements.map((item) => item.positionKey), ["a-position", "z-position"]);
  assert.ok(Object.isFrozen(first));
  assert.ok(Object.isFrozen(first.placements));
  assert.ok(Object.isFrozen(first.unplaced));
  for (const item of first.placements) assert.ok(Object.isFrozen(item));
  for (const item of first.unplaced) assert.ok(Object.isFrozen(item));
});

test("wing selector returns only placements mapped to that presentation wing", () => {
  const layout = buildV2HqCharacterLayout(
    [
      employee("ceo", "CEO", "Executive Office"),
      employee("cto", "CTO", "Technology Platform"),
    ],
    zones,
  );
  const technology = getV2HqPlacementsForWing(layout, "technology");
  assert.deepEqual(technology.map((item) => item.positionKey), ["cto"]);
  assert.ok(Object.isFrozen(technology));
});

test("layout implementation does not infer room from title, authority, random state or network", () => {
  assert.match(layoutSource, /employee\.department/);
  assert.doesNotMatch(layoutSource, /employee\.title.*(?:match|test)|(?:match|test).*employee\.title/);
  assert.doesNotMatch(layoutSource, /authority_level.*(?:match|test)|(?:match|test).*authority_level/);
  assert.doesNotMatch(layoutSource, /Math\.random|Date\.now|performance\.now/);
  assert.doesNotMatch(layoutSource, /fetch\(|POST|PUT|PATCH|DELETE|requestAnimationFrame/);
});

test("Mission Room scene hook exposes the canonical employee roster read-only", () => {
  assert.match(hookSource, /scene\?\.deterministic\.employees/);
  assert.match(hookSource, /employees,/);
  assert.doesNotMatch(hookSource, /setEmployees/);
});

test("HQ blockout renders character presentations with explicit no-location/no-presence posture", () => {
  assert.match(blockoutSource, /V2CharacterMiniature/);
  assert.match(blockoutSource, /buildV2HqCharacterLayout/);
  assert.match(blockoutSource, /data-physical-location-claimed="false"/);
  assert.match(blockoutSource, /data-presence-claimed="false"/);
  assert.match(blockoutSource, /physical location not claimed/i);
  assert.match(blockoutSource, /spatially unplaced/i);
});

test("HQ roster selection synchronizes with the existing Employee Inspector selection key", () => {
  assert.match(workspaceSource, /employees: sceneEmployees/);
  assert.match(workspaceSource, /employees=\{sceneEmployees\}/);
  assert.match(workspaceSource, /onSelectEmployee=\{setSelectedPositionKey\}/);
  assert.match(workspaceSource, /selectedPositionKey=\{selectedPositionKey\}/);
});

test("Phase 2G styles are scoped and preserve reduced motion", () => {
  assert.match(blockoutSource, /V2OrganizationBlockout\.module\.css/);
  assert.match(stylesSource, /@media \(prefers-reduced-motion: reduce\)/);
  assert.match(stylesSource, /button\.rosterPerson\s*\{\s*transition: none/);
  assert.doesNotMatch(stylesSource, /animation:\s*[^;]*infinite/);
});

test("HQ roster presentation contains no walking, conversation or semantic animation activation", () => {
  const combined = `${layoutSource}\n${blockoutSource}\n${stylesSource}`;
  assert.doesNotMatch(combined, /semanticAnimationActive\s*=\s*true|semanticAnimationActive:\s*true/);
  assert.doesNotMatch(combined, /walk(?:ing)?-semantic|conversation-semantic|room-traversal/);
});
