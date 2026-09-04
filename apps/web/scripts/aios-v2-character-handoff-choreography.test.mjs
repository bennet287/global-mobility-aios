import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

import { buildV2HandoffChoreography } from "../lib/v2/character-handoff-choreography.ts";
import { buildV2HandoffMotionDescriptor } from "../lib/v2/character-semantic-motion.ts";
import {
  getCharacterPresentationForPosition,
  getCharacterPresentationForRoleFamily,
  createNeutralPresentationFallback,
} from "../lib/v2/character-presentation.ts";

const here = path.dirname(fileURLToPath(import.meta.url));
const source = readFileSync(path.join(here, "..", "lib", "v2", "character-handoff-choreography.ts"), "utf8");

function resolutionFor(presentation, positionKey, title, department) {
  const registration = presentation.registration;
  const presentationKey = registration.kind === "exact-position"
    ? registration.canonicalPositionKey
    : registration.kind === "role-family-fallback"
      ? registration.presentationPositionKey
      : "neutral-professional";
  return Object.freeze({
    identity: Object.freeze({ positionKey, title, department }),
    roleFamilyHint: presentation.roleFamily,
    presentationKey,
    resolutionKind: registration.kind,
    resolutionReason: "test-fixture",
    presentation,
    presentationOnly: true,
    presenceClaimed: false,
    canonicalStateWritable: false,
    semanticAnimationActive: false,
  });
}

const ceo = resolutionFor(getCharacterPresentationForPosition("ceo"), "ceo", "CEO", "Executive");
const cto = resolutionFor(getCharacterPresentationForPosition("cto"), "cto", "CTO", "Technology");
const regulatory = resolutionFor(getCharacterPresentationForRoleFamily("regulatory-compliance"), "regulatory-intelligence", "Regulatory", "Compliance");
const operations = resolutionFor(getCharacterPresentationForRoleFamily("operations"), "operations-coordinator", "Operations", "Operations");
const neutral = resolutionFor(createNeutralPresentationFallback("ceo"), "ceo", "CEO", "Executive");

const CEO_CTO = Object.freeze({
  activity_id: "act-1", work_item_id: "wi-1", previous_position_key: "ceo", assigned_position_key: "cto",
  status: "assigned", occurred_at: "2026-09-03T12:00:00.000Z", causation_activity_id: "cause-1", canonical_basis: "basis-1",
});
const REG_OPS = Object.freeze({
  activity_id: "act-2", work_item_id: "wi-2", previous_position_key: "regulatory-intelligence", assigned_position_key: "operations-coordinator",
  status: "assigned", occurred_at: "2026-09-03T12:05:00.000Z", causation_activity_id: null, canonical_basis: "basis-2",
});

const ceoDescriptor = buildV2HandoffMotionDescriptor({ handoff: CEO_CTO, sender: ceo, receiver: cto });
const familyDescriptor = buildV2HandoffMotionDescriptor({ handoff: REG_OPS, sender: regulatory, receiver: operations });
const neutralDescriptor = buildV2HandoffMotionDescriptor({ handoff: CEO_CTO, sender: neutral, receiver: cto });
const swappedDescriptor = buildV2HandoffMotionDescriptor({ handoff: CEO_CTO, sender: cto, receiver: ceo });

const freezeWalk = value => {
  if (value === null || typeof value !== "object") return;
  assert.ok(Object.isFrozen(value));
  for (const child of Object.values(value)) freezeWalk(child);
};

const falseFlags = result => {
  for (const key of ["semanticAnimationActive","canonicalStateWritable","physicalPresenceClaimed","physicalTravelClaimed","conversationClaimed","workCompletionClaimed","dependencyResolutionClaimed","roomTraversalClaimed","pathfindingRequired"]) {
    assert.equal(result[key], false, key);
  }
  for (const key of ["canonicalStateWritable","physicalPresenceClaimed","physicalTravelClaimed","roomTraversalClaimed","pathfindingRequired","conversationClaimed","spokenWordsClaimed","transcriptClaimed","physicalObjectTransferClaimed","workCompletionClaimed","dependencyResolutionClaimed","authorityChangeClaimed","approvalOrRejectionClaimed"]) {
    assert.equal(result.truth[key], false, `truth.${key}`);
  }
};

test("1-2 supported CEO→CTO and Regulatory→Operations produce standard choreography", () => {
  for (const descriptor of [ceoDescriptor, familyDescriptor]) {
    const result = buildV2HandoffChoreography({ descriptor });
    assert.equal(result.mode, "standard"); assert.equal(result.supported, true); assert.equal(result.limitation, null);
  }
});

test("3-4 standard stage order and duration are deterministic and bounded", () => {
  const a = buildV2HandoffChoreography({ descriptor: ceoDescriptor });
  const b = buildV2HandoffChoreography({ descriptor: ceoDescriptor });
  assert.deepEqual(a.stages.map(x => x.key), ["sender-emphasis","transfer-emphasis","receiver-emphasis","settle"]);
  assert.deepEqual(a.stages.map(x => x.durationMs), [180,260,180,160]);
  assert.equal(a.timing.totalDurationMs, 780); assert.ok(a.timing.totalDurationMs <= 900); assert.deepEqual(a, b);
});

test("5 occurredAt never controls duration", () => {
  const altered = buildV2HandoffMotionDescriptor({ handoff: { ...CEO_CTO, occurred_at: "1999-01-01T00:00:00Z" }, sender: ceo, receiver: cto });
  const a = buildV2HandoffChoreography({ descriptor: ceoDescriptor });
  const b = buildV2HandoffChoreography({ descriptor: altered });
  assert.deepEqual(a.stages, b.stages); assert.deepEqual(a.timing, b.timing);
  assert.equal(a.timing.timingCanonical, false); assert.equal(a.timing.occurredAtControlsDuration, false); assert.equal(a.timing.derivesFromCanonicalTimestamp, false);
});

test("6 identical input returns deeply equal output", () => {
  assert.deepEqual(buildV2HandoffChoreography({ descriptor: ceoDescriptor }), buildV2HandoffChoreography({ descriptor: ceoDescriptor }));
});

test("7 unsupported Phase 2E descriptor has unsupported mode and no stages", () => {
  const result = buildV2HandoffChoreography({ descriptor: neutralDescriptor });
  assert.equal(result.mode, "unsupported"); assert.deepEqual(result.stages, []); assert.equal(result.limitation, "phase2e-descriptor-unsupported");
});

test("8-11 identity and capability gate failures block choreography", () => {
  for (const [field, limitation] of [
    ["senderIdentityMatchesCanonicalHandoff","phase2e-sender-identity-mismatch"],
    ["receiverIdentityMatchesCanonicalHandoff","phase2e-receiver-identity-mismatch"],
    ["senderCapabilitySupported","phase2e-sender-capability-unsupported"],
    ["receiverCapabilitySupported","phase2e-receiver-capability-unsupported"],
  ]) {
    const result = buildV2HandoffChoreography({ descriptor: { ...ceoDescriptor, [field]: false } });
    assert.equal(result.mode, "unsupported"); assert.deepEqual(result.stages, []); assert.equal(result.limitation, limitation);
  }
});

test("12-20 truth boundaries remain false in standard/reduced/unsupported modes", () => {
  falseFlags(buildV2HandoffChoreography({ descriptor: ceoDescriptor }));
  falseFlags(buildV2HandoffChoreography({ descriptor: ceoDescriptor, reducedMotion: true }));
  falseFlags(buildV2HandoffChoreography({ descriptor: neutralDescriptor }));
});

test("21-23 reduced motion is first-class, static, and preserves canonical identity", () => {
  const standard = buildV2HandoffChoreography({ descriptor: ceoDescriptor });
  const reduced = buildV2HandoffChoreography({ descriptor: ceoDescriptor, reducedMotion: true });
  assert.equal(reduced.mode, "reduced-motion");
  assert.deepEqual(reduced.stages.map(x => x.key), ["static-relation","brief-target-emphasis","settle"]);
  assert.equal(reduced.stages.some(x => x.key === "transfer-emphasis" || x.visualIntent === "transfer-relation"), false);
  assert.deepEqual(reduced.handoff, standard.handoff); assert.equal(reduced.reducedMotion.preservesCanonicalIdentity, true);
});

test("24-27 result, stages, every stage, and nested metadata are deeply frozen", () => {
  for (const result of [buildV2HandoffChoreography({ descriptor: ceoDescriptor }), buildV2HandoffChoreography({ descriptor: ceoDescriptor, reducedMotion: true }), buildV2HandoffChoreography({ descriptor: neutralDescriptor })]) freezeWalk(result);
});

test("28-32 module has no randomness, clocks, timers, network, DOM, React or Three.js machinery", () => {
  const stripped = source.replace(/\/\*[\s\S]*?\*\//g, " ").replace(/^[^'"`]*\/\/.*$/gm, " ");
  for (const pattern of [/Math\.random/,/Date\.now/,/new\s+Date\b/,/performance\.now/,/setTimeout/,/setInterval/,/requestAnimationFrame/,/requestIdleCallback/,/\bfetch\b/,/XMLHttpRequest/,/WebSocket/,/\bwindow\b/,/\bdocument\b/,/from\s+["']react/,/from\s+["']three/,/GLTFLoader/,/@react-three/]) assert.doesNotMatch(stripped, pattern);
});

test("33 no mutation API is exported", async () => {
  const module = await import("../lib/v2/character-handoff-choreography.ts");
  assert.deepEqual(Object.keys(module).filter(key => typeof module[key] === "function"), ["buildV2HandoffChoreography"]);
});

test("34 choreography duration never derives from canonical timestamp", () => {
  const result = buildV2HandoffChoreography({ descriptor: ceoDescriptor });
  assert.equal(result.timing.totalDurationMs, result.stages.reduce((sum, x) => sum + x.durationMs, 0));
  assert.equal(result.timing.occurredAtControlsDuration, false);
});

test("35 swapped endpoints cannot create choreography", () => {
  const result = buildV2HandoffChoreography({ descriptor: swappedDescriptor });
  assert.equal(result.mode, "unsupported"); assert.deepEqual(result.stages, []); assert.equal(result.phase2eLimitation, "sender-and-receiver-presentation-identities-mismatch");
});

test("36 forged supported descriptor without canonical identity is rejected as malformed", () => {
  const forged = { kind: "handoff", supported: true, limitation: null, senderPresentationKey: "ceo", receiverPresentationKey: "cto", senderCapabilitySupported: true, receiverCapabilitySupported: true, senderIdentityMatchesCanonicalHandoff: true, receiverIdentityMatchesCanonicalHandoff: true, semanticAnimationActive: false, truth: { canonicalEvent: true } };
  const result = buildV2HandoffChoreography({ descriptor: forged });
  assert.equal(result.mode, "unsupported"); assert.deepEqual(result.stages, []); assert.equal(result.limitation, "phase2e-descriptor-missing-or-malformed");
  assert.equal(result.truth.canonicalEvent, false); assert.equal(result.reducedMotion.preservesCanonicalIdentity, false); assert.equal(result.reducedMotion.relation, "");
});

test("raw LivingSceneHandoff and already-active descriptors are rejected", () => {
  assert.equal(buildV2HandoffChoreography({ descriptor: CEO_CTO }).limitation, "phase2e-descriptor-missing-or-malformed");
  assert.equal(buildV2HandoffChoreography({ descriptor: { ...ceoDescriptor, semanticAnimationActive: true } }).limitation, "phase2e-descriptor-animation-already-active");
});
