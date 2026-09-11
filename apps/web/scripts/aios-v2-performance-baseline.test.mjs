import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const spec = await readFile(new URL("../e2e/tests/aios-v2-performance-baseline.spec.ts", import.meta.url), "utf8");
const workflow = await readFile(new URL("../../../.github/workflows/v12-production-proof.yml", import.meta.url), "utf8");
const packageJson = await readFile(new URL("../package.json", import.meta.url), "utf8");
const assetRenderer = await readFile(new URL("../components/LivingHQAssetBackedCanvas.tsx", import.meta.url), "utf8");

test("Q17 profiles the production V2 runtime across the master-plan measurement dimensions", () => {
  assert.match(spec, /Performance\.getMetrics/);
  assert.match(spec, /JSHeapUsedSize/);
  assert.match(spec, /JSHeapTotalSize/);
  assert.match(spec, /Nodes/);
  assert.match(spec, /LayoutCount/);
  assert.match(spec, /RecalcStyleCount/);
  assert.match(spec, /requestAnimationFrame/);
  assert.match(spec, /PerformanceObserver\.supportedEntryTypes\.includes\("longtask"\)/);
  assert.match(spec, /homeReadyMs/);
  assert.match(spec, /commandOpenMs/);
  assert.match(spec, /homeToOrganizationMs/);
  assert.match(spec, /organizationStageReadyMs/);
  assert.match(spec, /resourceSummary/);
});

test("Q17 labels low-power measurement as a synthetic proxy rather than hardware truth", () => {
  assert.match(spec, /Emulation\.setCPUThrottlingRate/);
  assert.match(spec, /rate: 4/);
  assert.match(spec, /reducedMotion: "reduce"/);
  assert.match(spec, /Chromium 4x CPU throttling \+ reduced motion/);
  assert.match(spec, /lowPowerProxy/);
});

test("Q17 emits a machine-readable profile but deliberately does not invent hard timing budgets", () => {
  assert.match(spec, /aios-v2-performance-baseline\.v1/);
  assert.match(spec, /performance-results\/aios-v2-performance-baseline\.json/);
  assert.match(spec, /hardBudgetsEnforced: false/);
  assert.match(spec, /evidence for later budget setting/);
  assert.doesNotMatch(spec, /toBeLessThan(?:OrEqual)?\s*\(/);
  assert.doesNotMatch(spec, /PERFORMANCE_BUDGET|MAX_[A-Z_]*_MS|BUDGET_[A-Z_]*_MS/);
});

test("Q17 preserves read-only product truth and does not claim GPU memory for the current DOM/CSS stage", () => {
  assert.match(spec, /not a WebGL\/GPU memory claim/);
  assert.match(spec, /writes\)\.toEqual\(\[\]\)/);
  assert.doesNotMatch(spec, /\bPOST\b|\bPUT\b|\bPATCH\b|\bDELETE\b/);
  assert.doesNotMatch(spec, /physicalPresence\s*=\s*true|presence_state:\s*"present"/);
});

test("Q17 profiling is wired into package scripts and V12 with a retained JSON artifact", () => {
  assert.match(packageJson, /scripts\/aios-v2-performance-baseline\.test\.mjs/);
  assert.match(packageJson, /test:performance-baseline/);
  assert.match(workflow, /tests\/aios-v2-performance-baseline\.spec\.ts/);
  assert.match(workflow, /q17-v2-performance-profile/);
  assert.match(workflow, /performance-results\/aios-v2-performance-baseline\.json/);
  assert.match(workflow, /actions\/upload-artifact@v4/);
  assert.match(workflow, /if-no-files-found: error/);
});

test("13G.1I asset-backed realism is lazy, on-demand, and independent from canonical refresh churn", () => {
  assert.match(assetRenderer, /new IntersectionObserver/);
  assert.match(assetRenderer, /lazyLoadMarginPx/);
  assert.match(assetRenderer, /data\.renderCadence = "on-demand"/);
  assert.match(assetRenderer, /modelRef\.current = renderModel/);
  assert.match(assetRenderer, /data\.assetPipelineBudgeted = "true"/);
  assert.match(assetRenderer, /document\.visibilityState === "visible"/);
  assert.match(assetRenderer, /Math\.min\(window\.devicePixelRatio \|\| 1, LIVING_HQ_HIGH_FIDELITY_BUDGET\.maximumDevicePixelRatio\)/);
  assert.doesNotMatch(assetRenderer, /requestAnimationFrame/);
});

test("13G.1I live canonical updates refresh renderer metadata without rebuilding the asset scene", () => {
  assert.match(assetRenderer, /data\.canonicalEmployeeCount/);
  assert.match(assetRenderer, /data\.canonicalActiveEmployees/);
  assert.match(assetRenderer, /data\.canonicalBlockedEmployees/);
  assert.match(assetRenderer, /renderRef\.current\?\.\(\)/);
  assert.match(assetRenderer, /\}, \[\]\);/);
  assert.match(assetRenderer, /\}, \[renderModel\]\);/);
});
