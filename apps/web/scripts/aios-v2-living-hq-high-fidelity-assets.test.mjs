import test from "node:test";
import assert from "node:assert/strict";
import {
  LIVING_HQ_HIGH_FIDELITY_ASSETS,
  LIVING_HQ_HIGH_FIDELITY_BUDGET,
  chooseLivingHQHighFidelityMode,
  totalOptionalTransferBudget,
} from "../lib/living-hq-high-fidelity-assets.ts";

test("high-fidelity pack stays inside optional transfer budget", () => {
  assert.ok(totalOptionalTransferBudget() <= LIVING_HQ_HIGH_FIDELITY_BUDGET.maximumOptionalTransferBytes);
  assert.ok(LIVING_HQ_HIGH_FIDELITY_ASSETS.every((asset) => asset.optional));
  assert.ok(LIVING_HQ_HIGH_FIDELITY_ASSETS.every((asset) => asset.uri.endsWith(".glb")));
});

test("runtime degrades visuals before execution or canonical truth", () => {
  assert.equal(chooseLivingHQHighFidelityMode({ rendererReady: false, reducedMotion: false, saveData: false, assetPackAvailable: true }), "css-fallback");
  assert.equal(chooseLivingHQHighFidelityMode({ rendererReady: true, reducedMotion: false, saveData: true, assetPackAvailable: true }), "css-fallback");
  assert.equal(chooseLivingHQHighFidelityMode({ rendererReady: true, reducedMotion: true, saveData: false, assetPackAvailable: true }), "three-procedural");
  assert.equal(chooseLivingHQHighFidelityMode({ rendererReady: true, reducedMotion: false, saveData: false, assetPackAvailable: false }), "three-procedural");
  assert.equal(chooseLivingHQHighFidelityMode({ rendererReady: true, reducedMotion: false, saveData: false, assetPackAvailable: true }), "three-assets");
});
