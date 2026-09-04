import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import {
  ALLOWED_AMBIENT_RENDERER_ACTION_KEYS,
  AMBIENT_RENDERER_CONTRACT,
  FORBIDDEN_AMBIENT_RENDERER_ACTION_KEYS,
  PHASE_SLOT_OFFSETS_MS,
  buildV2AmbientCharacterRenderer,
} from "../lib/v2/ambient-character-renderer.ts";
import { buildV2AmbientCharacterBehavior } from "../lib/v2/character-ambient-behavior.ts";
import { resolveV2CharacterPresentation } from "../lib/v2/character-mission-presentation.ts";

const LIB_PATH = fileURLToPath(new URL("../lib/v2/ambient-character-renderer.ts", import.meta.url));
const COMPONENT_PATH = fileURLToPath(new URL("../components/v2/V2AmbientCharacterSurface.tsx", import.meta.url));
const CSS_PATH = fileURLToPath(new URL("../components/v2/V2AmbientCharacterSurface.module.css", import.meta.url));
const libSource = readFileSync(LIB_PATH, "utf8");
const componentSource = readFileSync(COMPONENT_PATH, "utf8");
const cssSource = readFileSync(CSS_PATH, "utf8");

function stripComments(source) {
  return source
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/(^|[^:])\/\/.*$/gm, "$1");
}

function behaviorFor(positionKey, title, department, options = {}) {
  const presentation = resolveV2CharacterPresentation({ positionKey, title, department });
  return buildV2AmbientCharacterBehavior({
    presentation,
    reducedMotion: options.reducedMotion ?? false,
    density: options.density ?? "normal",
  });
}

const BEHAVIORS = {
  ceo: behaviorFor("ceo", "Chief Executive Officer", "executive-office"),
  cto: behaviorFor("cto", "Chief Technology Officer", "technology-platform"),
  regulatory: behaviorFor(
    "regulatory-specialist-1",
    "Regulatory Evidence Specialist",
    "regulatory-compliance",
  ),
  operations: behaviorFor(
    "ops-coordinator-1",
    "Mobility Case Operations Coordinator",
    "operations",
  ),
  neutral: behaviorFor("unregistered-role-1", "Neutral Professional", "unassigned"),
};

function render(behavior, phaseSlot = 0) {
  return buildV2AmbientCharacterRenderer({ ambientBehavior: behavior, phaseSlot });
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

const TRUTH = {
  semanticAnimationActive: false,
  canonicalStateWritable: false,
  physicalPresenceClaimed: false,
  physicalLocationClaimed: false,
  physicalTravelClaimed: false,
  conversationClaimed: false,
  collaborationClaimed: false,
  workActivityClaimed: false,
  completionClaimed: false,
  handoffClaimed: false,
  blockerResolutionClaimed: false,
};

test("real Phase 2K descriptors map to renderer descriptors without inventing identity", () => {
  const ceo = render(BEHAVIORS.ceo);
  const operations = render(BEHAVIORS.operations);
  assert.equal(ceo.kind, "ambient-character-renderer");
  assert.equal(ceo.mode, "ambient");
  assert.equal(ceo.presentationKey, "ceo");
  assert.equal(operations.presentationKey, "role-family:operations");
  assert.ok(ceo.actions.length > 0);
  assert.ok(operations.actions.length > 0);
});

test("the actual Phase 2K profile action sets are preserved", () => {
  assert.deepEqual(BEHAVIORS.ceo.actions.map((a) => a.action), [
    "blink", "breathing", "gaze-shift", "device-idle",
  ]);
  assert.deepEqual(BEHAVIORS.operations.actions.map((a) => a.action), [
    "blink", "breathing", "micro-posture", "device-idle",
  ]);
  assert.deepEqual(
    render(BEHAVIORS.operations).actions.map((a) => a.key),
    BEHAVIORS.operations.actions.map((a) => a.action),
  );
});

test("identical input is deterministic and output is deeply frozen", () => {
  const first = render(BEHAVIORS.cto, 2);
  const second = render(
    behaviorFor("cto", "Chief Technology Officer", "technology-platform"),
    2,
  );
  assert.deepEqual(first, second);
  assert.notEqual(first, second);
  for (const value of [
    first,
    first.contract,
    first.truth,
    first.actions,
    first.reducedMotion,
    first.limitations,
    ...first.actions,
  ]) {
    assert.ok(Object.isFrozen(value));
  }
});

test("truth posture is invariant across real profiles and phase slots", () => {
  for (const behavior of Object.values(BEHAVIORS)) {
    for (const phaseSlot of [0, 1, 2, 3]) {
      const descriptor = render(behavior, phaseSlot);
      assert.equal(descriptor.presentationOnly, true);
      assert.deepEqual(descriptor.truth, TRUTH);
    }
  }
});

test("forged top-level Phase 2K truth fails closed", () => {
  const forged = clone(BEHAVIORS.cto);
  forged.canonicalStateWritable = true;
  const descriptor = render(forged, 1);
  assert.equal(descriptor.mode, "static");
  assert.deepEqual(descriptor.actions, []);
  assert.ok(descriptor.limitations.includes("fail-closed-truth-canonicalStateWritable"));
  assert.deepEqual(descriptor.truth, TRUTH);
});

test("missing top-level truth property fails closed", () => {
  const broken = clone(BEHAVIORS.ceo);
  delete broken.handoffClaimed;
  const descriptor = render(broken);
  assert.equal(descriptor.mode, "static");
  assert.deepEqual(descriptor.actions, []);
  assert.ok(descriptor.limitations.includes("fail-closed-truth-handoffClaimed"));
});

test("wrong Phase 2K contract identity fails closed", () => {
  const forged = clone(BEHAVIORS.ceo);
  forged.contract.registryId = "not-phase-2k";
  const descriptor = render(forged);
  assert.equal(descriptor.mode, "static");
  assert.deepEqual(descriptor.actions, []);
  assert.ok(descriptor.limitations.includes("fail-closed-invalid-source-contract"));
});

test("reduced-motion envelope mismatch fails closed", () => {
  const forged = clone(BEHAVIORS.ceo);
  forged.mode = "reduced-motion";
  forged.reducedMotion.enabled = false;
  const descriptor = render(forged);
  assert.equal(descriptor.mode, "static");
  assert.ok(descriptor.limitations.includes("fail-closed-reduced-motion-mode-mismatch"));
});

test("unsupported semantic action is ignored while valid safe actions remain", () => {
  const tampered = clone(BEHAVIORS.operations);
  tampered.actions.push({
    action: "coffee-drink",
    motionClass: "opacity",
    durationMs: 500,
    minIntervalMs: 5000,
    weight: 1,
    tier: 2,
    presentationOnly: true,
  });
  const descriptor = render(tampered);
  assert.equal(descriptor.mode, "ambient");
  assert.ok(descriptor.limitations.includes("unsupported-ambient-action-ignored"));
  assert.ok(!descriptor.actions.some((action) => action.key === "coffee-drink"));
  assert.ok(descriptor.actions.some((action) => action.key === "blink"));
});

test("malformed allowed action is ignored rather than repaired", () => {
  const tampered = clone(BEHAVIORS.ceo);
  tampered.actions.push({
    action: "selection-emphasis",
    motionClass: "transform",
    durationMs: -1,
    minIntervalMs: "fast",
    presentationOnly: true,
  });
  const descriptor = render(tampered);
  assert.ok(descriptor.limitations.includes("malformed-ambient-action-ignored"));
  assert.ok(!descriptor.actions.some((action) => action.key === "selection-emphasis"));
});

test("duplicate safe action is ignored deterministically", () => {
  const tampered = clone(BEHAVIORS.ceo);
  tampered.actions.push(clone(tampered.actions[0]));
  const descriptor = render(tampered);
  assert.ok(descriptor.limitations.includes("duplicate-ambient-action-ignored"));
  assert.equal(descriptor.actions.filter((action) => action.key === "blink").length, 1);
});

test("renderer never emits forbidden semantic action keys", () => {
  for (const behavior of Object.values(BEHAVIORS)) {
    const descriptor = render(behavior, 3);
    for (const action of descriptor.actions) {
      assert.ok(ALLOWED_AMBIENT_RENDERER_ACTION_KEYS.includes(action.key));
      assert.ok(!FORBIDDEN_AMBIENT_RENDERER_ACTION_KEYS.includes(action.key));
    }
  }
});

test("selection emphasis is rendered only when explicitly present in the Phase 2K-shaped plan", () => {
  const base = render(BEHAVIORS.operations);
  assert.ok(!base.actions.some((action) => action.key === "selection-emphasis"));

  const explicit = clone(BEHAVIORS.operations);
  explicit.actions.push({
    action: "selection-emphasis",
    motionClass: "opacity",
    durationMs: 320,
    minIntervalMs: 5000,
    weight: 1,
    tier: 2,
    presentationOnly: true,
  });
  const descriptor = render(explicit);
  assert.ok(descriptor.actions.some((action) => action.key === "selection-emphasis"));
});

test("Phase 2K timing metadata is preserved rather than silently clamped", () => {
  const source = BEHAVIORS.ceo.actions.find((action) => action.action === "breathing");
  const rendered = render(BEHAVIORS.ceo).actions.find((action) => action.key === "breathing");
  assert.ok(source);
  assert.ok(rendered);
  assert.equal(rendered.durationMs, source.durationMs);
  assert.equal(rendered.minIntervalMs, source.minIntervalMs);
});

test("phase slots 0-3 are deterministic and invalid slots normalize to zero", () => {
  assert.deepEqual([...PHASE_SLOT_OFFSETS_MS], [0, 140, 280, 420]);
  for (const slot of [0, 1, 2, 3]) {
    const descriptor = render(BEHAVIORS.regulatory, slot);
    assert.equal(descriptor.phaseSlot, slot);
    assert.ok(descriptor.actions.every((action) => action.phaseOffsetMs === PHASE_SLOT_OFFSETS_MS[slot]));
  }
  for (const bad of [7, -1, 1.5, "2", true, {}]) {
    const descriptor = render(BEHAVIORS.ceo, bad);
    assert.equal(descriptor.phaseSlot, 0);
    assert.ok(descriptor.limitations.includes("invalid-phase-slot-normalized-to-zero"));
  }
});

test("omitted phase slot defaults to zero without a limitation", () => {
  const descriptor = buildV2AmbientCharacterRenderer({ ambientBehavior: BEHAVIORS.ceo });
  assert.equal(descriptor.phaseSlot, 0);
  assert.ok(!descriptor.limitations.includes("invalid-phase-slot-normalized-to-zero"));
});

test("reduced-motion Phase 2K plans omit transform actions and preserve opacity-safe cues", () => {
  const behavior = behaviorFor(
    "ceo",
    "Chief Executive Officer",
    "executive-office",
    { reducedMotion: true },
  );
  const descriptor = render(behavior, 1);
  assert.equal(descriptor.mode, "reduced-motion");
  assert.equal(descriptor.reducedMotion.enabled, true);
  assert.ok(descriptor.actions.every((action) => action.transformAllowed === false));
  assert.ok(descriptor.actions.some((action) => action.key === "blink"));
  assert.ok(descriptor.actions.some((action) => action.key === "device-idle"));
  assert.ok(!descriptor.actions.some((action) => action.key === "breathing"));
});

test("static source mode never renders actions even when a forged static plan carries them", () => {
  const staticPlan = clone(BEHAVIORS.ceo);
  staticPlan.mode = "static";
  const descriptor = render(staticPlan);
  assert.equal(descriptor.mode, "static");
  assert.deepEqual(descriptor.actions, []);
  assert.ok(descriptor.limitations.includes("static-mode-actions-omitted"));
});

test("renderer never mutates the Phase 2K descriptor", () => {
  const snapshot = JSON.stringify(BEHAVIORS.cto);
  render(BEHAVIORS.cto, 3);
  assert.equal(JSON.stringify(BEHAVIORS.cto), snapshot);
});

test("runtime export surface contains only builder and frozen constants", async () => {
  const mod = await import("../lib/v2/ambient-character-renderer.ts");
  assert.deepEqual(Object.keys(mod).sort(), [
    "ALLOWED_AMBIENT_RENDERER_ACTION_KEYS",
    "AMBIENT_RENDERER_CONTRACT",
    "FORBIDDEN_AMBIENT_RENDERER_ACTION_KEYS",
    "PHASE_SLOT_OFFSETS_MS",
    "buildV2AmbientCharacterRenderer",
  ]);
  for (const [key, value] of Object.entries(mod)) {
    if (key !== "buildV2AmbientCharacterRenderer") assert.ok(Object.isFrozen(value));
  }
});

test("adapter source contains no clock random timer network DOM or framework machinery", () => {
  const source = stripComments(libSource);
  for (const token of [
    "Math.random", "Date.now", "new Date", "performance.now",
    "setTimeout", "setInterval", "requestAnimationFrame",
    "fetch(", "WebSocket", "XMLHttpRequest", "localStorage",
    "document.", "window.", "React", "canvas", "WebGL", "Three.js",
  ]) {
    assert.ok(!source.includes(token), `forbidden adapter token: ${token}`);
  }
  const runtimeImports = source
    .split("\n")
    .filter((line) => line.trim().startsWith("import ") && !line.trim().startsWith("import type"));
  assert.deepEqual(runtimeImports, []);
});

test("component consumes only the prepared descriptor and uses the real lib path", () => {
  const source = stripComments(componentSource);
  assert.ok(source.includes('from "../../lib/v2/ambient-character-renderer"'));
  assert.ok(source.includes('from "./V2AmbientCharacterSurface.module.css"'));
  assert.ok(source.includes("{children}"));
  for (const token of [
    "buildV2AmbientCharacterBehavior", "resolveV2CharacterPresentation",
    "useEffect", "useState", "useRef", "requestAnimationFrame",
    "setInterval", "setTimeout", "fetch(", "WebSocket", "cloneElement",
    "canvas", "WebGL", "Three.js",
  ]) {
    assert.ok(!source.includes(token), `forbidden component token: ${token}`);
  }
  assert.ok(!source.includes("aria-hidden"));
});

test("component mirrors the no-truth-claim posture as data attributes", () => {
  for (const marker of [
    "data-presentation-only",
    "data-semantic-animation-active",
    "data-canonical-state-writable",
    "data-physical-presence-claimed",
    "data-physical-location-claimed",
    "data-physical-travel-claimed",
    "data-conversation-claimed",
    "data-collaboration-claimed",
    "data-work-activity-claimed",
    "data-completion-claimed",
    "data-handoff-claimed",
    "data-blocker-resolution-claimed",
  ]) {
    assert.ok(componentSource.includes(marker), `missing marker ${marker}`);
  }
});

test("component derives CSS cycle variables from source timing without timers", () => {
  assert.ok(componentSource.includes("Math.max(action.durationMs, action.minIntervalMs)"));
  for (const variable of [
    "--amb-blink-cycle", "--amb-breath-cycle", "--amb-posture-cycle",
    "--amb-drift-cycle", "--amb-device-cycle",
  ]) {
    assert.ok(componentSource.includes(variable), `missing timing variable ${variable}`);
    assert.ok(cssSource.includes(variable), `CSS missing timing variable ${variable}`);
  }
});

test("CSS is locally scoped, complete and contains no corrupted control bytes", () => {
  const source = stripComments(cssSource);
  assert.ok(source.includes(".root {"));
  assert.ok(!source.includes(":root"));
  assert.ok(!/--(?!amb-)[a-zA-Z-]+\s*:/.test(source));
  assert.doesNotMatch(cssSource, /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/);

  for (const className of [
    "root", "modeAmbient", "modeReducedMotion", "modeStatic",
    "phaseSlot0", "phaseSlot1", "phaseSlot2", "phaseSlot3",
    "breathLayer", "postureLayer", "driftLayer",
    "ambientBlink", "ambientBreathing", "ambientMicroPosture",
    "ambientGazeShift", "ambientFocusGlow", "ambientDeviceIdle",
    "ambientPropIdle", "ambientSelectionEmphasis",
  ]) {
    assert.ok(source.includes(`.${className}`), `missing CSS class .${className}`);
  }
});

test("reduced-motion and static gates cover both root and descendant animation carriers", () => {
  for (const selector of [
    ".modeReducedMotion.ambientBlink",
    ".modeReducedMotion.ambientDeviceIdle::before",
    ".modeReducedMotion .ambientBreathing",
    ".modeStatic.ambientBlink",
    ".modeStatic.ambientDeviceIdle::before",
    ".root.ambientBlink",
    ".root.ambientDeviceIdle::before",
    ".root .ambientBreathing",
  ]) {
    assert.ok(cssSource.includes(selector), `missing motion gate ${selector}`);
  }
  assert.ok(cssSource.includes("@media (prefers-reduced-motion: reduce)"));
});

test("CSS motion stays inside the Phase 2M micro-motion envelope", () => {
  const source = stripComments(cssSource);
  assert.ok(!source.includes("scale("));
  assert.ok(!source.includes("translate3d"));
  const translateValues = [...source.matchAll(/translate[XY]\((-?\d+(?:\.\d+)?)px\)/g)]
    .map((match) => Math.abs(Number(match[1])));
  const rotateValues = [...source.matchAll(/rotate\((-?\d+(?:\.\d+)?)deg\)/g)]
    .map((match) => Math.abs(Number(match[1])));
  assert.ok(translateValues.every((value) => value <= 1.2));
  assert.ok(rotateValues.every((value) => value <= 0.45));
});

test("CSS contains no semantic locomotion renderer dependency", () => {
  const source = stripComments(cssSource);
  for (const token of [
    "walk", "travel", "conversation", "handoff", "completion",
    "celebrat", "canvas", "WebGL", "Three.js",
  ]) {
    assert.ok(!source.includes(token), `forbidden CSS token: ${token}`);
  }
});
