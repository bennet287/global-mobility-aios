import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import {
  buildV2HqAtmospherePresentation,
  HQ_ATMOSPHERE_CONTRACT,
  HQ_ATMOSPHERE_DECORATIVE_FIELDS,
  HQ_ATMOSPHERE_EMPHASIS_MODES,
  HQ_ATMOSPHERE_THEMES,
  HQ_ATMOSPHERE_ZONES,
} from "../lib/v2/hq-atmosphere-presentation.ts";

const LIB_PATH = fileURLToPath(new URL("../lib/v2/hq-atmosphere-presentation.ts", import.meta.url));
const COMPONENT_PATH = fileURLToPath(new URL("../components/v2/V2HqAtmosphereLayer.tsx", import.meta.url));
const CSS_PATH = fileURLToPath(new URL("../components/v2/V2HqAtmosphereLayer.module.css", import.meta.url));
const libSource = readFileSync(LIB_PATH, "utf8");
const componentSource = readFileSync(COMPONENT_PATH, "utf8");
const cssSource = readFileSync(CSS_PATH, "utf8");

function stripComments(source) {
  return source
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/(^|[^:])\/\/.*$/gm, "$1");
}

function build(overrides = {}) {
  return buildV2HqAtmospherePresentation({
    theme: "neutral",
    selectedZone: null,
    emphasis: "balanced",
    reducedMotion: false,
    ...overrides,
  });
}

const TRUTH = {
  canonicalStateWritable: false,
  physicalPresenceClaimed: false,
  physicalLocationClaimed: false,
  workActivityClaimed: false,
  urgencyClaimed: false,
  collaborationClaimed: false,
  conversationClaimed: false,
  semanticAnimationActive: false,
};

test("closed vocabulary matches the five real Phase 2I selectable wings", () => {
  assert.equal(HQ_ATMOSPHERE_CONTRACT.contractVersion, "1.1.0");
  assert.deepEqual([...HQ_ATMOSPHERE_ZONES], [
    "executive", "regulatory", "atrium", "technology", "operations",
  ]);
  assert.deepEqual([...HQ_ATMOSPHERE_DECORATIVE_FIELDS], [
    "decision-chamber", "collaboration-deck",
  ]);
});

test("identical input produces deeply equal deterministic output", () => {
  const first = build({ selectedZone: "technology", emphasis: "defined" });
  const second = build({ selectedZone: "technology", emphasis: "defined" });
  assert.deepEqual(first, second);
  assert.notEqual(first, second);
});

test("all themes remain deterministic and presentation-only", () => {
  for (const theme of HQ_ATMOSPHERE_THEMES) {
    const first = build({ theme });
    assert.deepEqual(first, build({ theme }));
    assert.equal(first.presentationOnly, true);
  }
});

test("selection follows explicit five-wing input only", () => {
  const descriptor = build({ selectedZone: "operations" });
  assert.equal(descriptor.selectedZone, "operations");
  assert.deepEqual(
    descriptor.zones.filter((zone) => zone.selected).map((zone) => zone.zone),
    ["operations"],
  );
});

test("null selection selects nothing and does not default the atrium", () => {
  const descriptor = build({ selectedZone: null });
  assert.equal(descriptor.selectedZone, null);
  assert.ok(descriptor.zones.every((zone) => !zone.selected));
});

test("unknown or decorative selection input is ignored instead of guessed", () => {
  for (const selectedZone of ["board", "collaboration", "decision-chamber", "holodeck"]) {
    const descriptor = build({ selectedZone });
    assert.equal(descriptor.selectedZone, null);
    assert.ok(descriptor.zones.every((zone) => !zone.selected));
    assert.ok(descriptor.limitations.includes("unknown-selected-zone-ignored"));
  }
});

test("decorative architectural fields are permanently non-selectable", () => {
  const descriptor = build({ selectedZone: "atrium", emphasis: "defined" });
  assert.deepEqual(
    descriptor.decorativeFields.map((field) => field.field),
    [...HQ_ATMOSPHERE_DECORATIVE_FIELDS],
  );
  for (const field of descriptor.decorativeFields) {
    assert.equal(field.selected, false);
    assert.equal(field.selectionEligible, false);
  }
});

test("title authority department and employee name cannot determine selection", () => {
  const bare = build();
  const decorated = build({
    title: "Chief Executive Officer",
    authority: "board",
    department: "executive-office",
    employeeName: "Example",
  });
  assert.deepEqual(decorated, bare);
});

test("emphasis changes visual intensity without changing truth", () => {
  for (const emphasis of HQ_ATMOSPHERE_EMPHASIS_MODES) {
    const descriptor = build({ emphasis });
    assert.deepEqual(descriptor.truth, TRUTH);
  }
});

test("descriptor and all nested structures are deeply frozen", () => {
  const descriptor = build({ selectedZone: "regulatory", reducedMotion: true });
  for (const value of [
    descriptor,
    descriptor.contract,
    descriptor.truth,
    descriptor.environment,
    descriptor.zones,
    descriptor.decorativeFields,
    descriptor.motion,
    descriptor.reducedMotion,
    descriptor.limitations,
    ...descriptor.zones,
    ...descriptor.decorativeFields,
  ]) {
    assert.ok(Object.isFrozen(value));
  }
});

test("truth flags are invariant across theme emphasis selection and reduced motion", () => {
  for (const theme of HQ_ATMOSPHERE_THEMES) {
    for (const emphasis of HQ_ATMOSPHERE_EMPHASIS_MODES) {
      for (const selectedZone of [null, "executive"]) {
        for (const reducedMotion of [false, true]) {
          const descriptor = build({ theme, emphasis, selectedZone, reducedMotion });
          assert.equal(descriptor.presentationOnly, true);
          assert.deepEqual(descriptor.truth, TRUTH);
        }
      }
    }
  }
});

test("reduced motion preserves selected-zone identity with static truth", () => {
  const standard = build({ selectedZone: "technology" });
  const reduced = build({ selectedZone: "technology", reducedMotion: true });
  assert.equal(reduced.selectedZone, standard.selectedZone);
  assert.equal(reduced.reducedMotion.enabled, true);
  assert.equal(reduced.motion.ambientAnimation, "none");
  assert.equal(reduced.motion.parallax, false);
  assert.equal(reduced.motion.glowSweep, false);
});

test("low-stimulation plus reduced motion is fully static", () => {
  const descriptor = build({ theme: "low-stimulation", reducedMotion: true });
  assert.equal(descriptor.motion.mode, "static");
  assert.equal(descriptor.motion.hoverTransitionMs, 0);
  assert.equal(descriptor.motion.selectionTransitionMs, 0);
});

test("unknown theme and emphasis fail closed to restrained defaults", () => {
  const descriptor = build({ theme: "neon", emphasis: "maximum" });
  assert.equal(descriptor.theme, "neutral");
  assert.equal(descriptor.emphasis, "balanced");
  assert.ok(descriptor.limitations.includes("unknown-theme-treated-as-neutral"));
  assert.ok(descriptor.limitations.includes("unknown-emphasis-treated-as-balanced"));
});

test("planner never mutates its input", () => {
  const input = { theme: "focused", selectedZone: "atrium", emphasis: "calm", reducedMotion: false };
  const snapshot = JSON.stringify(input);
  buildV2HqAtmospherePresentation(input);
  assert.equal(JSON.stringify(input), snapshot);
});

test("planner exposes no mutation API and constants are frozen", async () => {
  const mod = await import("../lib/v2/hq-atmosphere-presentation.ts");
  assert.equal(typeof mod.buildV2HqAtmospherePresentation, "function");
  for (const [key, value] of Object.entries(mod)) {
    if (key !== "buildV2HqAtmospherePresentation") {
      assert.ok(Object.isFrozen(value), `${key} should be frozen`);
    }
  }
});

test("planner executable source is stochastic clock timer and network free", () => {
  const source = stripComments(libSource);
  for (const token of [
    "Math.random", "Date.now", "new Date", "performance.now", "setTimeout",
    "setInterval", "requestAnimationFrame", "fetch(", "WebSocket", "XMLHttpRequest",
    "localStorage", "document.", "window.",
  ]) {
    assert.ok(!source.includes(token), `forbidden executable token: ${token}`);
  }
});

test("component import points to the real lib path and consumes descriptor only", () => {
  const source = stripComments(componentSource);
  assert.ok(source.includes('from "../../lib/v2/hq-atmosphere-presentation"'));
  assert.ok(source.includes('from "./V2HqAtmosphereLayer.module.css"'));
  for (const token of [
    "fetch(", "useEffect", "useState", "useMemo", "Date.now", "Math.random",
    "requestAnimationFrame", "WebSocket", "canvas", "Three.js",
  ]) {
    assert.ok(!source.includes(token), `forbidden component token: ${token}`);
  }
});

test("component mirrors truth posture and is decorative", () => {
  assert.ok(componentSource.includes('aria-hidden="true"'));
  assert.ok(componentSource.includes("data-canonical-state-writable"));
  assert.ok(componentSource.includes("data-physical-presence-claimed"));
  assert.ok(componentSource.includes('data-selection-eligible="false"'));
});

test("CSS custom properties are locally scoped and prefixed", () => {
  const source = stripComments(cssSource);
  assert.ok(source.includes(".root {"));
  assert.ok(!source.includes(":root"));
  assert.ok(!/--(?!atmo-)[a-zA-Z-]+\s*:/.test(source));
});

test("CSS provides reduced-motion and responsive degradation", () => {
  assert.ok(cssSource.includes("@media (prefers-reduced-motion: reduce)"));
  assert.ok(cssSource.includes("@media (max-width: 1024px)"));
  assert.ok(cssSource.includes("@media (max-width: 768px)"));
});

test("CSS contains no looping animation or renderer dependency", () => {
  const source = stripComments(cssSource);
  for (const token of ["@keyframes", "animation:", "infinite", "canvas", "WebGL", "Three.js"]) {
    assert.ok(!source.includes(token), `forbidden CSS token: ${token}`);
  }
});

test("decorative fields and selectable zones have distinct renderer classes", () => {
  for (const className of [
    "zoneExecutive", "zoneRegulatory", "zoneAtrium", "zoneTechnology", "zoneOperations",
    "fieldDecisionChamber", "fieldCollaborationDeck", "decorativeField", "zoneGlowSelected",
  ]) {
    assert.ok(cssSource.includes(`.${className}`), `missing class ${className}`);
  }
});

test("CSS source contains no forbidden control bytes", () => {
  assert.doesNotMatch(cssSource, /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/);
});

test("atrium accent mapping resolves to the actual CSS module class", () => {
  assert.ok(componentSource.includes('"accent-balanced-central": "accentBalancedCentral"'));
  assert.ok(cssSource.includes(".accentBalancedCentral"));
  assert.ok(!componentSource.includes("acentBalancedCentral"));
});

test("critical atmosphere CSS expressions and motion classes are intact", () => {
  assert.ok(cssSource.includes("calc(var(--atmo-theme-vignette) * var(--atmo-contrast-vignette) * var(--atmo-response))"));
  for (const className of [
    "motionTransitionOnly", "motionOpacityOnly", "motionStatic", "reducedMotionActive",
    "intensityLow", "intensityMedium", "intensityHigh",
  ]) {
    assert.ok(cssSource.includes(`.${className}`), `missing class ${className}`);
  }
});
