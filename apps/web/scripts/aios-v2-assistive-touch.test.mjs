import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";

const root = process.cwd();
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");

const e2e = read("e2e/tests/aios-v2-assistive-touch.spec.ts");
const pkg = JSON.parse(read("package.json"));
const workflow = read("../../.github/workflows/v12-production-proof.yml");

test("Q19 provides an explicit automated accessibility-tree smoke", () => {
  assert.match(e2e, /ariaSnapshot\(\)/);
  for (const label of [
    "Know what needs you before you open the details.",
    "Authority & human review",
    "Living Organization",
    "Navigate AIOS",
    "Structured organization",
  ]) {
    assert.ok(e2e.includes(label), `accessibility-tree proof must cover ${label}`);
  }
});

test("Q19 executes real touch-input actions in a touch-enabled mobile context", () => {
  assert.match(e2e, /hasTouch:\s*true/);
  assert.match(e2e, /isMobile:\s*true/);
  assert.match(e2e, /navigator\.maxTouchPoints/);
  assert.ok((e2e.match(/\.tap\(/g) || []).length >= 4, "touch proof must execute multiple real tap actions");
  assert.match(e2e, /getByRole\("radio", \{ name: "Structured" \}\)/);
  assert.match(e2e, /structuredLabel\.tap/);
  assert.match(e2e, /getByLabel\("Missions", \{ exact: true \}\)/);
});

test("Q19 assistive/touch proof remains read-only and error-aware", () => {
  assert.match(e2e, /writes/);
  assert.match(e2e, /pageErrors/);
  assert.match(e2e, /expect\(writes\)\.toEqual\(\[\]\)/);
  assert.match(e2e, /expect\(pageErrors\)\.toEqual\(\[\]\)/);
});

test("Q19 is wired into design-foundation and the V12 Chromium lane", () => {
  assert.ok(pkg.scripts["test:design-foundation"].includes("aios-v2-assistive-touch.test.mjs"));
  assert.equal(pkg.scripts["test:assistive-touch"], "node --experimental-strip-types --test scripts/aios-v2-assistive-touch.test.mjs");
  assert.match(workflow, /tests\/aios-v2-assistive-touch\.spec\.ts/);
});
