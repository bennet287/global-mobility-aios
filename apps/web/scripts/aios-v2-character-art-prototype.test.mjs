/**
 * AIOS V2 — Phase 2J — Character Art Prototype contract tests.
 *
 * Run with:
 *   node --experimental-strip-types --test scripts/aios-v2-character-art-prototype.test.mjs
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  CHARACTER_ART_ACCENT_PALETTE,
  CHARACTER_ART_PROTOTYPE_CONTRACT,
  getKnownArtPrototypeKeys,
  hasDedicatedArtArchetype,
  resolveCharacterArtPrototype,
} from "../lib/v2/character-art-prototype.ts";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const repoRoot = resolve(__dirname, "..", "..", "..");
const componentPath = resolve(repoRoot, "apps/web/components/v2/V2CharacterArtPrototype.tsx");
const moduleCssPath = resolve(repoRoot, "apps/web/components/v2/V2CharacterArtPrototype.module.css");
const libPath = resolve(repoRoot, "apps/web/lib/v2/character-art-prototype.ts");

const componentSrc = readFileSync(componentPath, "utf8");
const moduleCssSrc = readFileSync(moduleCssPath, "utf8");
const libSrc = readFileSync(libPath, "utf8");

function stripComments(source) {
  return source
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/(^|[^:])\/\/.*$/gm, "$1");
}

const productionSrc = stripComments(`${libSrc}\n${componentSrc}\n${moduleCssSrc}`);

const KEYS = Object.freeze([
  "ceo",
  "cto",
  "role-family:regulatory-compliance",
  "role-family:operations",
  "neutral-professional",
]);

test("exact CEO presentation maps to CEO art archetype", () => {
  assert.equal(resolveCharacterArtPrototype({ presentationKey: "ceo" }).archetype, "ceo");
});

test("exact CTO presentation maps to CTO art archetype", () => {
  assert.equal(resolveCharacterArtPrototype({ presentationKey: "cto" }).archetype, "cto");
});

test("regulatory family maps correctly", () => {
  assert.equal(
    resolveCharacterArtPrototype({ presentationKey: "role-family:regulatory-compliance" }).archetype,
    "regulatory-compliance",
  );
});

test("operations family maps correctly", () => {
  assert.equal(
    resolveCharacterArtPrototype({ presentationKey: "role-family:operations" }).archetype,
    "operations",
  );
});

test("neutral presentation maps correctly", () => {
  assert.equal(
    resolveCharacterArtPrototype({ presentationKey: "neutral-professional" }).archetype,
    "neutral-professional",
  );
});

test("unknown presentation keys fall back deterministically to neutral", () => {
  const model = resolveCharacterArtPrototype({ presentationKey: "unknown-xyz" });
  assert.equal(model.archetype, "neutral-professional");
  assert.equal(model.presentationKey, "neutral-professional");
});

test("mapping is deterministic and deeply equal for identical inputs", () => {
  for (const presentationKey of KEYS) {
    const a = resolveCharacterArtPrototype({ presentationKey });
    const b = resolveCharacterArtPrototype({ presentationKey });
    assert.deepEqual(a, b);
  }
});

test("returned models and exported registries are runtime immutable", () => {
  const model = resolveCharacterArtPrototype({ presentationKey: "ceo" });
  assert.equal(Object.isFrozen(model), true);
  assert.equal(Object.isFrozen(CHARACTER_ART_PROTOTYPE_CONTRACT), true);
  assert.equal(Object.isFrozen(CHARACTER_ART_ACCENT_PALETTE), true);
  for (const paletteEntry of Object.values(CHARACTER_ART_ACCENT_PALETTE)) {
    assert.equal(Object.isFrozen(paletteEntry), true);
  }
  assert.equal(Object.isFrozen(getKnownArtPrototypeKeys()), true);
  assert.throws(() => {
    model.archetype = "cto";
  }, TypeError);
});

test("contract truth posture is presentation-only and non-authoritative", () => {
  assert.deepEqual(CHARACTER_ART_PROTOTYPE_CONTRACT, {
    contractId: "aios-v2.character-art-prototype",
    contractVersion: "1.0.0",
    presentationOnly: true,
    physicalPresenceClaimed: false,
    physicalLocationClaimed: false,
    canonicalStateWritable: false,
    semanticAnimationActive: false,
  });
});

test("every resolved archetype preserves the truth posture", () => {
  for (const presentationKey of KEYS) {
    const model = resolveCharacterArtPrototype({ presentationKey });
    assert.equal(model.presentationOnly, true);
    assert.equal(model.physicalPresenceClaimed, false);
    assert.equal(model.physicalLocationClaimed, false);
    assert.equal(model.canonicalStateWritable, false);
    assert.equal(model.semanticAnimationActive, false);
  }
});

test("only exact presentation keys select dedicated art archetypes", () => {
  assert.deepEqual([...getKnownArtPrototypeKeys()].sort(), [...KEYS].sort());
  for (const key of KEYS) assert.equal(hasDedicatedArtArchetype(key), true);
  assert.equal(hasDedicatedArtArchetype("CEO"), false);
  assert.equal(hasDedicatedArtArchetype("chief executive officer"), false);
  assert.equal(hasDedicatedArtArchetype("technology"), false);
});

test("title-like and authority-like extra inputs cannot influence resolution", () => {
  const forgedCeo = resolveCharacterArtPrototype({
    presentationKey: "unknown",
    title: "CEO",
    authority: "L4",
  });
  assert.equal(forgedCeo.archetype, "neutral-professional");

  const exactCto = resolveCharacterArtPrototype({
    presentationKey: "cto",
    title: "Operations Specialist",
    authority: "none",
  });
  assert.equal(exactCto.archetype, "cto");
});

test("neutral fallback is intentionally less role-specific than CEO and CTO", () => {
  const neutral = resolveCharacterArtPrototype({ presentationKey: "neutral-professional" });
  const ceo = resolveCharacterArtPrototype({ presentationKey: "ceo" });
  const cto = resolveCharacterArtPrototype({ presentationKey: "cto" });
  assert.equal(neutral.prop, "none");
  assert.equal(neutral.detailDensity, "minimal");
  assert.equal(ceo.detailDensity, "rich");
  assert.equal(cto.detailDensity, "rich");
  assert.notEqual(neutral.silhouette, ceo.silhouette);
  assert.notEqual(neutral.silhouette, cto.silhouette);
});

test("no randomness, wall clock, timers, or network machinery exists in production source", () => {
  assert.doesNotMatch(productionSrc, /\bMath\.random\b/);
  assert.doesNotMatch(productionSrc, /\bDate\.now\b|\bnew Date\s*\(/);
  assert.doesNotMatch(productionSrc, /\bperformance\.now\b/);
  assert.doesNotMatch(productionSrc, /\bsetTimeout\b|\bsetInterval\b|\brequestAnimationFrame\b/);
  assert.doesNotMatch(productionSrc, /\bfetch\s*\(|XMLHttpRequest|WebSocket|EventSource/);
});

test("no backend, API, or database dependency exists", () => {
  assert.doesNotMatch(
    stripComments(`${libSrc}\n${componentSrc}`),
    /from\s+["'][^"']*(?:\/api\/|backend|server|database|prisma|sqlite|sqlmodel)[^"']*["']/i,
  );
});

test("component supports compact and inspector variants", () => {
  assert.match(componentSrc, /"compact"\s*\|\s*"inspector"/);
  assert.match(componentSrc, /variant === "inspector"/);
});

test("component contains structural role differentiation beyond color", () => {
  assert.match(componentSrc, /function JacketShape/);
  assert.match(componentSrc, /function HeadShape/);
  assert.match(componentSrc, /function HairShape/);
  assert.match(componentSrc, /function PropShape/);
  for (const archetype of ["ceo", "cto", "regulatory-compliance", "operations"]) {
    assert.match(componentSrc, new RegExp(`case "${archetype}"`));
  }
  assert.match(componentSrc, /data-silhouette/);
  assert.match(componentSrc, /data-wardrobe/);
  assert.match(componentSrc, /data-prop/);
});

test("component exposes explicit non-authoritative truth data attributes", () => {
  assert.match(componentSrc, /data-presentation-only="true"/);
  assert.match(componentSrc, /data-physical-presence-claimed="false"/);
  assert.match(componentSrc, /data-physical-location-claimed="false"/);
  assert.match(componentSrc, /data-canonical-state-writable="false"/);
  assert.match(componentSrc, /data-semantic-animation-active="false"/);
});

test("component accessibility description is exposed without duplicated hidden copy", () => {
  assert.match(componentSrc, /aria-label=\{labelledBy \? undefined : model\.accessibilityDescription\}/);
  assert.match(componentSrc, /aria-labelledby=\{labelledBy\}/);
  assert.match(componentSrc, /aria-hidden="true"/);
  assert.doesNotMatch(componentSrc, /screenReaderDescription/);
});

test("SVG paint IDs use React useId rather than archetype-only IDs", () => {
  assert.match(componentSrc, /useId\(\)/);
  assert.match(componentSrc, /cap-plinth-/);
  assert.match(componentSrc, /cap-jacket-/);
  assert.match(componentSrc, /cap-surface-/);
  assert.doesNotMatch(componentSrc, /id=\{`(?:plinth|jacket|skin)-\$\{model\.archetype\}`\}/);
});

test("prototype uses a neutral figurine surface material rather than role-specific skin mapping", () => {
  assert.match(componentSrc, /cap-surface-/);
  assert.doesNotMatch(componentSrc, /skin-\$\{model\.archetype\}/);
});

test("component does not fetch organization data or import existing canonical hooks", () => {
  assert.doesNotMatch(componentSrc, /\bfetch\s*\(/);
  assert.doesNotMatch(componentSrc, /useV2OwnerOrganization|useBackendStatus|loadV2OwnerOrganization/);
});

test("CSS variables are locally scoped to the prototype root", () => {
  assert.doesNotMatch(moduleCssSrc, /(^|\n)\s*:root\s*\{/);
  assert.match(moduleCssSrc, /\.root\s*\{[\s\S]*--cap-stage-bg:/);
});

test("reduced motion disables all prototype animation", () => {
  assert.match(moduleCssSrc, /@media\s*\(prefers-reduced-motion:\s*reduce\)/);
  assert.match(moduleCssSrc, /\.characterSvg,[\s\S]*\.eyeGroup,[\s\S]*\.propIdle[\s\S]*animation:\s*none\s*!important/);
  assert.match(moduleCssSrc, /\.figureStage,[\s\S]*\.root:hover \.figureStage[\s\S]*transition:\s*none\s*!important/);
});

test("ambient motion stays presentation-only and does not implement semantic behaviors", () => {
  assert.match(moduleCssSrc, /@keyframes cap-breathe/);
  assert.match(moduleCssSrc, /@keyframes cap-blink/);
  assert.match(moduleCssSrc, /@keyframes cap-prop-idle/);
  const stripped = stripComments(`${componentSrc}\n${moduleCssSrc}`);
  assert.doesNotMatch(stripped, /\bwalk(?:ing)?\b/i);
  assert.doesNotMatch(stripped, /\bconversation\b|\bchat\b|\bspeak(?:ing)?\b/i);
  assert.doesNotMatch(stripped, /\bhandoff\b/i);
});

test("prototype uses no Three.js, WebGL, canvas, or remote media", () => {
  assert.doesNotMatch(productionSrc, /@react-three|\bthree\b|\bWebGL\b|<canvas/i);
  assert.doesNotMatch(productionSrc, /https?:\/\/[^\s"'`]+\.(?:png|jpe?g|gif|svg|webp|glb|gltf)/i);
});

test("production source contains no copyrighted character references", () => {
  assert.doesNotMatch(
    stripComments(`${componentSrc}\n${libSrc}`),
    /\bboss baby\b|\bfunko\b|\bpixar\b|\bdisney\b|\bmario\b|\bgoku\b|\bnaruto\b/i,
  );
});

test("the static CTO tablet transform is isolated from prop idle animation", () => {
  assert.match(componentSrc, /<g transform="rotate\(-8 92 110\)">[\s\S]*<g className=\{styles\.propIdle\}>/);
});

test("blink and prop transforms use SVG-local transform boxes", () => {
  assert.match(moduleCssSrc, /\.eyeGroup\s*\{[\s\S]*transform-box:\s*fill-box/);
  assert.match(moduleCssSrc, /\.propIdle\s*\{[\s\S]*transform-box:\s*fill-box/);
});
