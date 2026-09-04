import assert from "node:assert/strict";
import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { test } from "node:test";

const here = path.dirname(fileURLToPath(import.meta.url));
const manifestPath = path.resolve(here, "..", "lib", "v2", "character-asset-manifest.ts");
const registryPath = path.resolve(here, "..", "lib", "v2", "character-presentation.ts");
const manifestSource = await readFile(manifestPath, "utf8");
const miniatureSource = await readFile(path.resolve(here, "..", "components", "v2", "V2CharacterMiniature.tsx"), "utf8");

const executableManifestSource = manifestSource.replace(
  'from "./character-presentation";',
  `from "${pathToFileURL(registryPath).href}";`,
);
assert.notEqual(executableManifestSource, manifestSource, "manifest import rewrite must be applied");

const tempDir = await mkdtemp(path.join(tmpdir(), "aios-v2-character-assets-"));
const executableManifestPath = path.join(tempDir, "character-asset-manifest.ts");
await writeFile(executableManifestPath, executableManifestSource, "utf8");

const {
  CHARACTER_ASSET_MANIFEST_CONTRACT,
  characterAssetManifest,
  getCharacterAssetManifestEntry,
  getCharacterPresentationKey,
  resolveCharacterAssetBinding,
} = await import(pathToFileURL(executableManifestPath).href);

const {
  getCharacterPresentationForPosition,
  getCharacterPresentationForRoleFamily,
} = await import(pathToFileURL(registryPath).href);

test("asset manifest is presentation-only and never claims presence or canonical writes", () => {
  assert.equal(CHARACTER_ASSET_MANIFEST_CONTRACT.presentationOnly, true);
  assert.equal(CHARACTER_ASSET_MANIFEST_CONTRACT.presenceClaimed, false);
  assert.equal(CHARACTER_ASSET_MANIFEST_CONTRACT.canonicalStateWritable, false);
  assert.equal(CHARACTER_ASSET_MANIFEST_CONTRACT.missingAssetPolicy, "structured-css-miniature-fallback");
  assert.equal(characterAssetManifest.presentationOnly, true);
});

test("initial asset manifest covers the five current presentation keys deterministically", () => {
  const keys = characterAssetManifest.entries.map((entry) => entry.presentationKey);
  assert.deepEqual(keys, [
    "ceo",
    "cto",
    "role-family:regulatory-compliance",
    "role-family:operations",
    "neutral-professional",
  ]);
  assert.equal(new Set(keys).size, keys.length);
});

test("manifest does not fabricate GLB availability before real assets are integrated", () => {
  for (const entry of characterAssetManifest.entries) {
    assert.equal(entry.model.format, "glb");
    assert.equal(entry.model.availability, "not-integrated");
    assert.equal(entry.model.uri, null);
    assert.equal(entry.model.assetVersion, null);
    assert.equal(entry.model.contentHash, null);
    assert.equal(entry.fallback.renderer, "css-miniature");
    assert.equal(entry.fallback.requiredWhenModelUnavailable, true);
    assert.equal(entry.fallback.mayClaimCanonicalPresence, false);
    assert.equal(entry.fallback.mayActivateSemanticAnimation, false);
  }
});

test("CEO and CTO presentations resolve to compatible CSS fallbacks until verified GLBs exist", () => {
  for (const key of ["ceo", "cto"]) {
    const presentation = getCharacterPresentationForPosition(key);
    const binding = resolveCharacterAssetBinding(presentation);
    assert.equal(binding.presentationKey, key);
    assert.equal(binding.compatible, true);
    assert.equal(binding.modelAvailable, false);
    assert.equal(binding.rendererMode, "css-miniature");
    assert.equal(binding.modelUri, null);
    assert.equal(binding.presentationOnly, true);
    assert.equal(binding.presenceClaimed, false);
    assert.equal(binding.canonicalStateWritable, false);
    assert.equal(binding.semanticAnimationActive, false);
  }
});

test("registered family presentations resolve to compatible family manifest entries", () => {
  const regulatory = getCharacterPresentationForRoleFamily("regulatory-compliance");
  const operations = getCharacterPresentationForRoleFamily("operations");

  assert.equal(getCharacterPresentationKey(regulatory), "role-family:regulatory-compliance");
  assert.equal(getCharacterPresentationKey(operations), "role-family:operations");

  for (const presentation of [regulatory, operations]) {
    const binding = resolveCharacterAssetBinding(presentation);
    assert.equal(binding.compatible, true);
    assert.equal(binding.modelAvailable, false);
    assert.equal(binding.rendererMode, "css-miniature");
  }
});

test("neutral character presentation resolves to the neutral fallback asset binding", () => {
  const neutral = getCharacterPresentationForPosition("unknown-asset-probe");
  const binding = resolveCharacterAssetBinding(neutral);
  assert.equal(getCharacterPresentationKey(neutral), "neutral-professional");
  assert.equal(binding.presentationKey, "neutral-professional");
  assert.equal(binding.compatible, true);
  assert.equal(binding.modelAvailable, false);
  assert.equal(binding.rendererMode, "css-miniature");
});

test("manifest compatibility rejects rig, LOD, or animation-set mismatches", () => {
  const ceo = getCharacterPresentationForPosition("ceo");

  const wrongRig = { ...ceo, rigClass: "rig-standard-humanoid-v1" };
  const wrongLod = { ...ceo, lodClass: "lod-standard" };
  const wrongAnimation = {
    ...ceo,
    animationSetKey: "aios-v2:animation-set:mismatch",
  };

  for (const presentation of [wrongRig, wrongLod, wrongAnimation]) {
    const binding = resolveCharacterAssetBinding(presentation);
    assert.equal(binding.compatible, false);
    assert.equal(binding.modelAvailable, false);
    assert.equal(binding.rendererMode, "css-miniature");
    assert.equal(binding.modelUri, null);
    assert.equal(binding.semanticAnimationActive, false);
  }
});

test("manifest entries and their nested model/fallback metadata are deeply frozen", () => {
  assert.ok(Object.isFrozen(characterAssetManifest));
  assert.ok(Object.isFrozen(characterAssetManifest.entries));
  for (const entry of characterAssetManifest.entries) {
    assert.ok(Object.isFrozen(entry));
    assert.ok(Object.isFrozen(entry.model));
    assert.ok(Object.isFrozen(entry.fallback));
  }
  const binding = resolveCharacterAssetBinding(getCharacterPresentationForPosition("ceo"));
  assert.ok(Object.isFrozen(binding));
});

test("asset binding resolution is deterministic", () => {
  const ceo = getCharacterPresentationForPosition("ceo");
  const first = resolveCharacterAssetBinding(ceo);
  const second = resolveCharacterAssetBinding(ceo);
  assert.deepEqual(first, second);
  assert.equal(first.manifestEntry, second.manifestEntry);
  assert.equal(getCharacterAssetManifestEntry("ceo"), first.manifestEntry);
});

test("asset manifest contains no loader, network, timing, randomness, or semantic activation machinery", () => {
  for (const forbidden of [
    "Math.random",
    "Date.now",
    "requestAnimationFrame",
    "setTimeout",
    "setInterval",
    "fetch(",
    "XMLHttpRequest",
    "WebSocket",
    "GLTFLoader",
    "THREE.",
    "semanticAnimationActive: true",
  ]) {
    assert.equal(manifestSource.includes(forbidden), false, `forbidden asset-manifest machinery: ${forbidden}`);
  }
});

test("asset manifest stores presentation compatibility only, not organization truth", () => {
  const serialized = JSON.stringify(characterAssetManifest).toLowerCase();
  for (const forbidden of [
    "authority_level",
    "reporting_line",
    "reports_to",
    "work_item_id",
    "semantic_state",
    "presence_state",
    "decision_owner",
  ]) {
    assert.equal(serialized.includes(forbidden), false, `canonical truth leaked into asset manifest: ${forbidden}`);
  }
});

test("V2CharacterMiniature consumes the manifest and exposes truthful asset state", () => {
  assert.match(miniatureSource, /resolveCharacterAssetBinding/);
  assert.match(miniatureSource, /data-asset-compatible/);
  assert.match(miniatureSource, /data-asset-model-available/);
  assert.match(miniatureSource, /data-asset-renderer-mode/);
  assert.match(miniatureSource, /assetBinding\.limitation/);
  assert.doesNotMatch(miniatureSource, /GLTFLoader|THREE\.|modelUri!/);
});
