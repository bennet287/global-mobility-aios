import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";

const root = process.cwd();
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");

const layout = read("app/layout.tsx");
const loader = read("components/AgentChatWidgetLoader.tsx");
const widget = read("components/AgentChatWidget.tsx");
const e2e = read("e2e/tests/aios-v2-consultant-asset-optimization.spec.ts");
const pkg = JSON.parse(read("package.json"));
const workflow = read("../../.github/workflows/v12-production-proof.yml");

test("Q18 root layout mounts only the lightweight consultant loader", () => {
  assert.match(layout, /import \{ AgentChatWidgetLoader \} from "\.\.\/components\/AgentChatWidgetLoader";/);
  assert.match(layout, /<AgentChatWidgetLoader \/>/);
  assert.doesNotMatch(layout, /import \{ AgentChatWidget \} from "\.\.\/components\/AgentChatWidget";/);
  assert.doesNotMatch(layout, /<AgentChatWidget \/>/);
});

test("Q18 consultant code enters the client graph only after explicit user intent", () => {
  assert.match(loader, /await import\("\.\/AgentChatWidget"\)/);
  assert.doesNotMatch(loader, /^import .*AgentChatWidget/m);
  assert.doesNotMatch(loader, /next\/dynamic/);
  assert.match(loader, /onClick=\{loadConsultant\}/);
  assert.match(loader, /aria-label=\{accessibleLabel\}/);
  assert.match(loader, /aria-busy=\{loading \|\| undefined\}/);
  assert.match(loader, /<Consultant initiallyOpen \/>/);
  assert.doesNotMatch(loader, /\.\.\/lib\/api/);
});

test("Q18 keeps client-facing route suppression in the lightweight layer", () => {
  for (const route of ["/portal", "/return", "/partner-portal"]) {
    assert.ok(loader.includes(`pathname.startsWith("${route}")`), `${route} must remain suppressed before loading the consultant`);
  }
  assert.match(loader, /if \(isClientFacingRoute\(pathname\)\) return null;/);
});

test("Q18 loaded consultant preserves first-click open behavior without changing chat authority", () => {
  assert.match(widget, /initiallyOpen\?: boolean/);
  assert.match(widget, /useState\(initiallyOpen\)/);
  assert.match(widget, /chatWithAgent/);
  assert.match(widget, /runControlledAgent/);
  assert.match(widget, /aria-label=\{open \? "Close consultant chat" : "Open consultant chat"\}/);
});

test("Q18 browser proof measures actual lazy asset delta without inventing budgets", () => {
  assert.match(e2e, /aios-v2-consultant-assets\.v1/);
  assert.match(e2e, /newScriptUrls/);
  assert.match(e2e, /scriptTransferBytes/);
  assert.match(e2e, /hardBudgetsEnforced: false/);
  assert.match(e2e, /Open consultant chat/);
  assert.match(e2e, /In-House Consultant/);
  assert.match(e2e, /writes/);
  assert.doesNotMatch(e2e, /toBeLessThan\(/);
  assert.doesNotMatch(e2e, /MAX_.*(?:MS|BYTES)/);
});

test("Q18 regression is wired into package and V12 production proof", () => {
  assert.ok(pkg.scripts["test:design-foundation"].includes("aios-v2-consultant-asset-optimization.test.mjs"));
  assert.equal(pkg.scripts["test:consultant-assets"], "node --experimental-strip-types --test scripts/aios-v2-consultant-asset-optimization.test.mjs");
  assert.match(workflow, /Measure Q18 intent-lazy consultant assets/);
  assert.match(workflow, /tests\/aios-v2-consultant-asset-optimization\.spec\.ts/);
  assert.match(workflow, /q18-consultant-asset-profile/);
  assert.match(workflow, /aios-v2-consultant-assets\.json/);
});
