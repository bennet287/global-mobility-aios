import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import {
  ALLOWED_AMBIENT_ACTION_KEYS,
  AMBIENT_ACTION_TIMING,
  AMBIENT_BEHAVIOR_MODES,
  AMBIENT_CHARACTER_BEHAVIOR_CONTRACT,
  AMBIENT_DENSITY_MODES,
  FORBIDDEN_AMBIENT_ACTION_KEYS,
  buildV2AmbientCharacterBehavior,
} from "../lib/v2/character-ambient-behavior.ts";
import { getPreferredCharacterPresentation } from "../lib/v2/character-presentation.ts";

const source = readFileSync(
  fileURLToPath(new URL("../lib/v2/character-ambient-behavior.ts", import.meta.url)),
  "utf8",
);
const executableSource = source
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .replace(/^\s*\/\/.*$/gm, "");

const identities = Object.freeze({
  ceo: Object.freeze({ positionKey: "ceo", title: "Chief Executive Officer", department: "Executive Office" }),
  cto: Object.freeze({ positionKey: "cto", title: "Chief Technology Officer", department: "Technology Platform" }),
  regulatory: Object.freeze({ positionKey: "regulatory-specialist-1", title: "Regulatory Evidence Specialist", department: "Regulatory Compliance" }),
  operations: Object.freeze({ positionKey: "operations-coordinator-1", title: "Mobility Operations Coordinator", department: "Operations" }),
  neutral: Object.freeze({ positionKey: "unregistered-role-1", title: "Neutral Professional", department: "Unassigned" }),
});

const roleFamilies = Object.freeze({
  ceo: null,
  cto: null,
  regulatory: "regulatory-compliance",
  operations: "operations",
  neutral: null,
});

function presentationKeyFor(record) {
  if (record.registration.kind === "exact-position") {
    return record.registration.canonicalPositionKey;
  }
  if (record.registration.kind === "role-family-fallback") {
    return record.registration.presentationPositionKey;
  }
  return "neutral-professional";
}

function registryBackedResolution(identity, roleFamily = null) {
  const frozenIdentity = Object.freeze({
    positionKey: identity.positionKey,
    title: identity.title,
    department: identity.department,
  });
  const presentation = getPreferredCharacterPresentation({
    positionKey: frozenIdentity.positionKey,
    roleFamily,
  });
  return Object.freeze({
    identity: frozenIdentity,
    roleFamilyHint: roleFamily,
    presentationKey: presentationKeyFor(presentation),
    resolutionKind: presentation.registration.kind,
    resolutionReason: "Test fixture resolved directly from the Character Presentation Registry.",
    presentation,
    presentationOnly: true,
    presenceClaimed: false,
    canonicalStateWritable: false,
    semanticAnimationActive: false,
  });
}

const presentations = Object.freeze(
  Object.fromEntries(
    Object.entries(identities).map(([key, identity]) => [
      key,
      registryBackedResolution(identity, roleFamilies[key]),
    ]),
  ),
);

const expectedProfiles = Object.freeze({
  ceo: "ceo",
  cto: "cto",
  regulatory: "regulatory-compliance",
  operations: "operations",
  neutral: "neutral",
});

const expectedNormalActions = Object.freeze({
  ceo: ["blink", "breathing", "gaze-shift", "device-idle"],
  cto: ["blink", "breathing", "device-idle", "focus-glow", "micro-posture"],
  regulatory: ["blink", "breathing", "device-idle", "gaze-shift", "focus-glow"],
  operations: ["blink", "breathing", "micro-posture", "device-idle"],
  neutral: ["blink", "breathing"],
});

const truthFlags = Object.freeze({
  presentationOnly: true,
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
});

function build(presentation, options = {}) {
  return buildV2AmbientCharacterBehavior({
    presentation,
    reducedMotion: options.reducedMotion ?? false,
    density: options.density ?? "normal",
  });
}

function assertTruth(plan) {
  for (const [key, value] of Object.entries(truthFlags)) {
    assert.equal(plan[key], value, key);
  }
}

test("registry preconditions resolve expected presentation keys", () => {
  assert.equal(presentations.ceo.presentationKey, "ceo");
  assert.equal(presentations.cto.presentationKey, "cto");
  assert.equal(presentations.regulatory.presentationKey, "role-family:regulatory-compliance");
  assert.equal(presentations.operations.presentationKey, "role-family:operations");
  assert.equal(presentations.neutral.presentationKey, "neutral-professional");
});

test("closed ambient vocabulary and contract posture", () => {
  assert.equal(AMBIENT_CHARACTER_BEHAVIOR_CONTRACT.registryId, "aios-v2.character-ambient-behavior");
  assert.equal(AMBIENT_CHARACTER_BEHAVIOR_CONTRACT.presentationOnly, true);
  assert.equal(AMBIENT_CHARACTER_BEHAVIOR_CONTRACT.presenceClaimed, false);
  assert.deepEqual([...AMBIENT_DENSITY_MODES], ["low", "normal", "high"]);
  assert.deepEqual([...AMBIENT_BEHAVIOR_MODES], ["standard", "reduced-motion", "static"]);
  for (const key of ["walk", "conversation", "coffee-drink", "handoff", "complete"]) {
    assert.ok(FORBIDDEN_AMBIENT_ACTION_KEYS.includes(key));
    assert.ok(!ALLOWED_AMBIENT_ACTION_KEYS.includes(key));
  }
});

for (const [key, presentation] of Object.entries(presentations)) {
  test(`${key} ambient profile is deterministic`, () => {
    const first = build(presentation);
    const second = build(presentation);
    assert.equal(first.ambientProfile, expectedProfiles[key]);
    assert.deepEqual(first.actions.map((action) => action.action), expectedNormalActions[key]);
    assert.deepEqual(first, second);
    assertTruth(first);
  });
}

test("all descriptor layers are deeply frozen", () => {
  const plan = build(presentations.cto);
  assert.ok(Object.isFrozen(plan));
  assert.ok(Object.isFrozen(plan.contract));
  assert.ok(Object.isFrozen(plan.actions));
  assert.ok(Object.isFrozen(plan.timing));
  assert.ok(Object.isFrozen(plan.timing.entries));
  assert.ok(Object.isFrozen(plan.reducedMotion));
  assert.ok(Object.isFrozen(plan.reducedMotion.excludedActionKeys));
  assert.ok(Object.isFrozen(plan.limitations));
  for (const action of plan.actions) assert.ok(Object.isFrozen(action));
  for (const timing of Object.values(plan.timing.entries)) assert.ok(Object.isFrozen(timing));
});

test("truth posture is invariant across profiles, density and reduced motion", () => {
  for (const presentation of Object.values(presentations)) {
    for (const density of AMBIENT_DENSITY_MODES) {
      assertTruth(build(presentation, { density }));
      assertTruth(build(presentation, { density, reducedMotion: true }));
    }
  }
});

test("density changes presentation subset/cadence only", () => {
  for (const presentation of Object.values(presentations)) {
    const low = build(presentation, { density: "low" });
    const normal = build(presentation, { density: "normal" });
    const high = build(presentation, { density: "high" });
    assert.ok(low.actions.length <= normal.actions.length);
    assert.ok(normal.actions.length <= high.actions.length);
    assert.equal(low.timing.densityAffectsPresentationOnly, true);
    assert.equal(low.timing.densityMayChangeActionSubset, true);
    assert.equal(low.timing.densityNeverChangesTruth, true);
    assert.equal(normal.presentationKey, high.presentationKey);
    assert.equal(normal.ambientProfile, high.ambientProfile);
  }
});

test("reduced motion removes transform actions and preserves presentation identity", () => {
  for (const presentation of Object.values(presentations)) {
    const standard = build(presentation);
    const reduced = build(presentation, { reducedMotion: true });
    assert.equal(reduced.presentationKey, standard.presentationKey);
    assert.equal(reduced.ambientProfile, standard.ambientProfile);
    assert.equal(reduced.presentationBasis, standard.presentationBasis);
    assert.equal(reduced.reducedMotion.informationLoss, false);
    assert.ok(reduced.actions.every((action) => action.motionClass === "opacity"));
    assert.ok(!reduced.actions.some((action) => ["breathing", "micro-posture", "gaze-shift"].includes(action.action)));
  }
});

test("timing uses bounded constants independent of canonical time", () => {
  for (const entry of Object.values(AMBIENT_ACTION_TIMING)) {
    assert.ok(Number.isInteger(entry.durationMs));
    assert.ok(Number.isInteger(entry.minIntervalMs));
    assert.ok(entry.durationMs > 0 && entry.durationMs <= 6000);
    assert.ok(entry.minIntervalMs > 0 && entry.minIntervalMs <= 20000);
  }
  const plan = build(presentations.ceo);
  assert.equal(plan.timing.source, "bounded-presentation-constants");
  assert.equal(plan.timing.independentOfCanonicalTime, true);
});

test("presentation title cannot change a coherent exact-position ambient identity", () => {
  const normal = registryBackedResolution(
    { ...identities.ceo, title: "Chief Executive Officer" },
    roleFamilies.ceo,
  );
  const altered = registryBackedResolution(
    { ...identities.ceo, title: "Junior Assistant" },
    roleFamilies.ceo,
  );
  assert.deepEqual(build(normal), build(altered));
});

test("authority fields cannot change ambient identity", () => {
  const forged = { ...presentations.cto, authority: "board-supreme", decisionRights: ["all"] };
  assert.deepEqual(build(forged), build(presentations.cto));
});

test("department cannot override exact canonical presentation identity", () => {
  const normal = registryBackedResolution(
    { ...identities.ceo, department: "Executive Office" },
    roleFamilies.ceo,
  );
  const altered = registryBackedResolution(
    { ...identities.ceo, department: "Technology Platform" },
    roleFamilies.ceo,
  );
  assert.deepEqual(build(normal), build(altered));
});

test("neutral presentation never gains role-specific actions", () => {
  for (const density of AMBIENT_DENSITY_MODES) {
    const plan = build(presentations.neutral, { density });
    assert.equal(plan.ambientProfile, "neutral");
    assert.deepEqual(plan.actions.map((action) => action.action), ["blink", "breathing"]);
  }
});

test("presentationKey alone cannot unlock role-specific ambient behavior", () => {
  const forged = {
    ...presentations.neutral,
    presentationKey: "ceo",
  };
  const plan = build(forged);
  assert.equal(plan.mode, "static");
  assert.equal(plan.presentationKey, "unavailable");
  assert.deepEqual(plan.actions, []);
  assert.ok(plan.limitations.includes("presentation-resolution-missing-or-inconsistent"));
});

test("mismatched exact-position registration and key are rejected", () => {
  const forged = { ...presentations.ceo, presentationKey: "neutral-professional" };
  const plan = build(forged);
  assert.equal(plan.mode, "static");
  assert.deepEqual(plan.actions, []);
});

test("mismatched role-family registration and key are rejected", () => {
  const forged = {
    ...presentations.operations,
    presentationKey: "role-family:regulatory-compliance",
  };
  const plan = build(forged);
  assert.equal(plan.mode, "static");
  assert.deepEqual(plan.actions, []);
});

test("unsafe resolution envelope is rejected", () => {
  const forged = { ...presentations.ceo, canonicalStateWritable: true };
  const plan = build(forged);
  assert.equal(plan.mode, "static");
  assert.deepEqual(plan.actions, []);
  assertTruth(plan);
});

test("selection emphasis is never scheduled without explicit selection truth", () => {
  for (const density of AMBIENT_DENSITY_MODES) {
    assert.ok(!build(presentations.operations, { density }).actions.some(
      (action) => action.action === "selection-emphasis",
    ));
  }
});

test("malformed input degrades to safe static presentation", () => {
  for (const malformed of [null, undefined, {}, { presentation: null }, { presentation: {} }]) {
    const plan = buildV2AmbientCharacterBehavior(malformed);
    assert.equal(plan.mode, "static");
    assert.equal(plan.ambientProfile, "neutral");
    assert.deepEqual(plan.actions, []);
    assert.ok(plan.limitations.includes("presentation-resolution-missing-or-inconsistent"));
    assertTruth(plan);
  }
});

test("planner does not mutate its input", () => {
  const input = presentations.regulatory;
  const before = JSON.stringify(input);
  build(input, { density: "high", reducedMotion: true });
  assert.equal(JSON.stringify(input), before);
});

test("source has no random, clock, timer, network, renderer, or mutation machinery", () => {
  const banned = [
    "Math.random",
    "Date.now",
    "new Date",
    "performance.now",
    "setTimeout",
    "setInterval",
    "requestAnimationFrame",
    "fetch(",
    "WebSocket",
    "XMLHttpRequest",
    "EventSource",
    "localStorage",
    "sessionStorage",
    "document.",
    "window.",
    "React",
    "WebGL",
    "Three.js",
  ];
  for (const token of banned) {
    assert.ok(!executableSource.includes(token), token);
  }
});

test("module exports no mutation API and frozen constants stay frozen", async () => {
  const mod = await import("../lib/v2/character-ambient-behavior.ts");
  const expected = [
    "ALLOWED_AMBIENT_ACTION_KEYS",
    "AMBIENT_ACTION_TIMING",
    "AMBIENT_BEHAVIOR_MODES",
    "AMBIENT_CHARACTER_BEHAVIOR_CONTRACT",
    "AMBIENT_DENSITY_MODES",
    "FORBIDDEN_AMBIENT_ACTION_KEYS",
    "buildV2AmbientCharacterBehavior",
  ].sort();
  assert.deepEqual(Object.keys(mod).sort(), expected);
  for (const key of expected) {
    if (key !== "buildV2AmbientCharacterBehavior") assert.ok(Object.isFrozen(mod[key]));
  }
});
