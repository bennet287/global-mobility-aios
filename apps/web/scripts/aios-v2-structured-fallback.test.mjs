import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const read = (relative) => readFile(new URL(`../${relative}`, import.meta.url), "utf8");

const [workspace, styles, packageJson, workflow, browserProof] = await Promise.all([
  read("components/v2/V2OrganizationWorkspace.tsx"),
  read("components/v2/V2OrganizationWorkspace.module.css"),
  read("package.json"),
  read("../../.github/workflows/v12-production-proof.yml"),
  read("e2e/tests/aios-v2-structured-fallback.spec.ts"),
]);

test("Q13 exposes native spatial and structured representation controls", () => {
  assert.match(workspace, /type OrganizationRepresentation = "spatial" \| "structured"/);
  assert.match(workspace, /useState<OrganizationRepresentation>\("spatial"\)/);
  assert.match(workspace, /<legend>Organization representation<\/legend>/);
  assert.match(workspace, /type="radio"[\s\S]*value="spatial"/);
  assert.match(workspace, /type="radio"[\s\S]*value="structured"/);
  assert.match(workspace, /Local view preference only · no canonical mutation · Structured mode does not mount the Living HQ stage/);
});

test("Q13 structured mode does not mount the Living HQ stage", () => {
  assert.match(workspace, /representation === "spatial" \? \([\s\S]*<V2LivingHqVisualStage/);
  assert.match(workspace, /\) : structuredOrganization\}/);
  assert.match(workspace, /\{representation === "spatial" \? structuredOrganization : null\}/);
  assert.doesNotMatch(workspace, /display:\s*none[\s\S]*V2LivingHqVisualStage/);
});

test("Q13 structured representation preserves navigation and employee inspection", () => {
  assert.match(workspace, /onClick=\{\(\) => openWing\(zone\.wingKey\)\}/);
  assert.match(workspace, /onClick=\{\(\) => selectEmployee\(placement\.positionKey\)\}/);
  assert.match(workspace, /hqCharacterLayout\.unplaced\.map/);
  assert.match(workspace, /onClick=\{\(\) => selectEmployee\(employee\.positionKey\)\}/);
  assert.match(workspace, /presentation mapping only/);
  assert.match(workspace, /Wing mapping is not physical location, roster identity is not presence/);
});

test("Q13 structured fallback uses semantic headings and touch-safe controls", () => {
  assert.match(workspace, /<h2 className=\{styles\.sectionTitle\} id="aios-v2-structured-title">Structured organization<\/h2>/);
  assert.match(workspace, /<h3>\{zone\.label\}<\/h3>/);
  assert.match(styles, /\.representationOptions label \{[\s\S]*min-height: 44px/);
  assert.match(styles, /\.zoneHeader button \{[\s\S]*min-height: 44px/);
  assert.match(styles, /\.employeeButton \{[\s\S]*min-height: 44px/);
  assert.match(styles, /@media \(forced-colors: active\)/);
});

test("Q13 representation switching is local presentation state only", () => {
  assert.doesNotMatch(workspace, /localStorage|sessionStorage/);
  assert.doesNotMatch(workspace, /fetch\(|method:\s*["'](?:POST|PUT|PATCH|DELETE)["']/);
  assert.match(workspace, /setRepresentation\("spatial"\)/);
  assert.match(workspace, /setRepresentation\("structured"\)/);
});

test("Q13 browser proof exercises populated structured navigation and employee inspection", () => {
  assert.match(browserProof, /SCENE_PATH/);
  assert.match(browserProof, /Operations Studio/);
  assert.match(browserProof, /Mobility Operations Lead/);
  assert.match(browserProof, /data-presence-claimed/);
  assert.match(browserProof, /Open details/);
  assert.match(browserProof, /toBeGreaterThanOrEqual\(44\)/);
  assert.match(browserProof, /organization\\\/wing\\\/operations/);
});

test("Q13 static and browser fallback proofs are wired into CI", () => {
  assert.match(packageJson, /scripts\/aios-v2-structured-fallback\.test\.mjs/);
  assert.match(packageJson, /"test:structured-fallback"/);
  assert.match(workflow, /tests\/aios-v2-structured-fallback\.spec\.ts/);
});