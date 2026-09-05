import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const stagePath = fileURLToPath(
  new URL("../components/v2/V2LivingHqVisualStage.tsx", import.meta.url),
);
const focusPanelPath = fileURLToPath(
  new URL("../components/v2/V2WingFocusPanel.tsx", import.meta.url),
);
const workspacePath = fileURLToPath(
  new URL("../components/v2/V2OrganizationWorkspace.tsx", import.meta.url),
);
const wingWorkspacePath = fileURLToPath(
  new URL("../components/v2/V2OrganizationWingWorkspace.tsx", import.meta.url),
);
const wingRoutePath = fileURLToPath(
  new URL("../app/cockpit/v2/organization/wing/[wingKey]/page.tsx", import.meta.url),
);
const hookPath = fileURLToPath(new URL("../hooks/useReducedMotion.ts", import.meta.url));
const packagePath = fileURLToPath(new URL("../package.json", import.meta.url));

const stage = readFileSync(stagePath, "utf8");
const focusPanel = readFileSync(focusPanelPath, "utf8");
const workspace = readFileSync(workspacePath, "utf8");
const wingWorkspace = readFileSync(wingWorkspacePath, "utf8");
const wingRoute = readFileSync(wingRoutePath, "utf8");
const reducedMotionHook = readFileSync(hookPath, "utf8");
const packageJson = JSON.parse(readFileSync(packagePath, "utf8"));

function includesAll(source, fragments, label) {
  for (const fragment of fragments) {
    assert.ok(source.includes(fragment), `${label} must include ${fragment}`);
  }
}

test("Living HQ composes the accepted character-art and ambient renderer stack", () => {
  includesAll(
    stage,
    [
      "resolveV2CharacterPresentation",
      "buildV2AmbientCharacterBehavior",
      "buildV2AmbientCharacterRenderer",
      "V2AmbientCharacterSurface",
      "V2CharacterArtPrototype",
    ],
    "Living HQ stage",
  );
});

test("ambient behavior stays presentation-only with fixed normal density", () => {
  assert.match(stage, /buildV2AmbientCharacterBehavior\([\s\S]*?density:\s*"normal"/);
  assert.match(stage, /reducedMotion,\s*\n\s*density:\s*"normal"/);
});

test("ambient phase staggering is deterministic and bounded to four Phase 2M slots", () => {
  assert.match(stage, /characterIndex\s*%\s*4/);
  assert.doesNotMatch(stage, /Math\.random|Date\.now|performance\.now/);
});

test("Living HQ integrates the sealed atmosphere presentation and layer", () => {
  includesAll(
    stage,
    ["buildV2HqAtmospherePresentation", "V2HqAtmosphereLayer"],
    "Living HQ stage",
  );
  assert.match(stage, /theme:\s*"presentation"/);
  assert.match(stage, /emphasis:\s*"balanced"/);
  assert.match(stage, /selectedZone:\s*activeWing/);
});

test("reduced-motion preference reaches both ambient and atmosphere builders", () => {
  assert.ok(stage.includes("const reducedMotion = useReducedMotion()"));
  assert.ok(stage.match(/buildV2AmbientCharacterBehavior\([\s\S]*?reducedMotion/));
  assert.ok(stage.match(/buildV2HqAtmospherePresentation\([\s\S]*?reducedMotion/));
  includesAll(
    reducedMotionHook,
    ["prefers-reduced-motion: reduce", "window.matchMedia", "addEventListener", "removeEventListener"],
    "reduced-motion hook",
  );
});

test("wing focus context remains explicit presentation-only state", () => {
  includesAll(
    stage,
    [
      "const focusedZone =",
      "layout.zones.find((zone) => zone.wingKey === activeWing)",
      "<V2WingFocusPanel",
      "currently focused",
    ],
    "Living HQ stage",
  );
  includesAll(
    focusPanel,
    [
      'data-wing-focus="true"',
      'mode?: "focus" | "detail"',
      "Wing focus · presentation only",
      "Wing detail · presentation only",
      "No physical presence claimed",
      "No canonical state written",
    ],
    "wing focus panel",
  );
});

test("wing focus context is derived only from the resolved presentation zone", () => {
  includesAll(
    focusPanel,
    [
      "zone.departmentCount",
      "zone.employeeCount",
      "zone.workItemCount",
      "zone.activeBlockerCount",
      "zone.characters.length",
      "zone.isHub && missionCount > 0",
    ],
    "wing focus panel",
  );
  assert.doesNotMatch(focusPanel, /\bfetch\s*\(|use[A-Z].*Organization|setInterval|requestAnimationFrame/);
});

test("Organization workspace reuses the governed HQ character-layout adapter", () => {
  includesAll(
    workspace,
    ["buildV2HqCharacterLayout", "sceneEmployees", "data?.organization.zones ?? []"],
    "Organization workspace",
  );
});

test("placed and unplaced employees are explicitly adapted to the visual-stage DTO", () => {
  includesAll(
    workspace,
    [
      "positionKey: placement.positionKey",
      "presentationWing: placement.wingKey",
      "positionKey: employee.positionKey",
      "presentationWing: null",
    ],
    "Organization workspace",
  );
});

test("architecture zones are explicitly adapted to HQ wing metrics", () => {
  includesAll(
    workspace,
    [
      "departmentCount: zone.departments.length",
      "employeeCount: zone.employeeRosterCount",
      "workItemCount: zone.workItemCount",
      "activeBlockerCount: zone.activeBlockerCount",
    ],
    "Organization workspace",
  );
});

test("Living HQ is the primary Organization visualization without deleting the legacy component", () => {
  assert.ok(workspace.includes("<V2LivingHqVisualStage"));
  assert.doesNotMatch(workspace, /V2OrganizationBlockout/);
});

test("wing selection opens a dedicated governed detail route instead of ending at glow-only feedback", () => {
  includesAll(
    workspace,
    [
      'import { useRouter } from "next/navigation"',
      "const openWing = (wingKey: HqWingKey)",
      "router.push(`/cockpit/v2/organization/wing/${wingKey}`)",
      "onSelectWing={openWing}",
    ],
    "Organization workspace",
  );
  includesAll(
    wingRoute,
    [
      "isKnownWingKey",
      "notFound()",
      "V2OrganizationWingWorkspace",
      "params: Promise<{ wingKey: string }>",
    ],
    "wing detail route",
  );
  includesAll(
    wingWorkspace,
    [
      'href="/cockpit/v2/organization"',
      "Organization · governed wing detail",
      'mode="detail"',
      "Mapped departments",
      'wingKey === "atrium"',
      "V2MissionStrip",
    ],
    "wing detail workspace",
  );
});

test("employee selection remains synchronized through selectedPositionKey", () => {
  includesAll(
    workspace,
    [
      "const selectEmployee = (positionKey: string)",
      "setSelectedPositionKey(positionKey)",
      "onSelectEmployee={selectEmployee}",
      "employeeInspectorFor(selectedPositionKey)",
      "selectedPositionKey={selectedPositionKey}",
    ],
    "Organization workspace",
  );
});

test("structured accessible Organization representation remains independently present", () => {
  includesAll(
    workspace,
    ["aios-v2-structured-fallback", "Accessible equivalent", "Structured organization"],
    "Organization workspace",
  );
});

test("integration adds no direct mutation, clock, timer, rAF, or autonomous motion machinery", () => {
  const combined = `${stage}\n${focusPanel}\n${workspace}\n${wingWorkspace}\n${wingRoute}\n${reducedMotionHook}`;
  assert.doesNotMatch(combined, /from\s+["'][^"']*\/api["']/);
  assert.doesNotMatch(combined, /\bfetch\s*\(/);
  assert.doesNotMatch(combined, /Math\.random|Date\.now|setInterval|requestAnimationFrame/);
});

test("stage keeps explicit presentation-only truth attributes", () => {
  includesAll(
    stage,
    [
      'data-canonical-state-writable="false"',
      'data-physical-location-claimed="false"',
      'data-presence-claimed="false"',
      'data-presentation-only="true"',
    ],
    "Living HQ stage",
  );
});

test("Phase 2N test wiring preserves accepted Phase 2J/2K/2L/2M tests", () => {
  const command = packageJson.scripts["test:design-foundation"];
  includesAll(
    command,
    [
      "aios-v2-living-hq-character-integration.test.mjs",
      "aios-v2-character-art-prototype.test.mjs",
      "aios-v2-character-ambient-behavior.test.mjs",
      "aios-v2-hq-atmosphere-presentation.test.mjs",
      "aios-v2-ambient-character-renderer.test.mjs",
    ],
    "test:design-foundation",
  );
});
