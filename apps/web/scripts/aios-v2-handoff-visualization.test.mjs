import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { resolveV2CharacterPresentation } from "../lib/v2/character-mission-presentation.ts";
import { buildV2HandoffMotionDescriptor } from "../lib/v2/character-semantic-motion.ts";
import {
  HANDOFF_VISUALIZATION_CONTRACT,
  buildV2HandoffVisualization,
} from "../lib/v2/handoff-visualization.ts";

const SOURCE_PATH = fileURLToPath(new URL("../lib/v2/handoff-visualization.ts", import.meta.url));
const source = readFileSync(SOURCE_PATH, "utf8");

const canonicalHandoff = Object.freeze({
  activity_id: "act-handoff-2o-001",
  work_item_id: "wi-2o-001",
  previous_position_key: "ceo",
  assigned_position_key: "cto",
  status: "assigned",
  occurred_at: "2026-09-04T13:30:00Z",
  causation_activity_id: "act-cause-2o-001",
  canonical_basis: "living_scene.handoff:act-handoff-2o-001",
});

function realMotion() {
  const sender = resolveV2CharacterPresentation({
    positionKey: "ceo",
    title: "Chief Executive Officer",
    department: "executive",
  });
  const receiver = resolveV2CharacterPresentation({
    positionKey: "cto",
    title: "Chief Technology Officer",
    department: "technology",
  });
  return buildV2HandoffMotionDescriptor({ handoff: canonicalHandoff, sender, receiver });
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function assertDeepFrozen(value, path = "descriptor") {
  if (value === null || typeof value !== "object") return;
  assert.ok(Object.isFrozen(value), `${path} must be frozen`);
  for (const [key, child] of Object.entries(value)) {
    assertDeepFrozen(child, `${path}.${key}`);
  }
}

test("contract is presentation-only and non-authoritative", () => {
  assert.equal(HANDOFF_VISUALIZATION_CONTRACT.registryId, "aios-v2.canonical-handoff-visualization");
  assert.equal(HANDOFF_VISUALIZATION_CONTRACT.contractVersion, "1.0.0");
  assert.equal(HANDOFF_VISUALIZATION_CONTRACT.presentationOnly, true);
  assert.equal(HANDOFF_VISUALIZATION_CONTRACT.canonicalStateWritable, false);
  assert.equal(HANDOFF_VISUALIZATION_CONTRACT.semanticAnimationActive, false);
});

test("real canonical CEO to CTO handoff maps to the bounded visual grammar", () => {
  const descriptor = buildV2HandoffVisualization({ motion: realMotion(), reducedMotion: false });
  assert.equal(descriptor.supported, true);
  assert.equal(descriptor.limitation, null);
  assert.equal(descriptor.mode, "bounded-transfer-sequence");
  assert.deepEqual(descriptor.steps.map((step) => step.key), [
    "sender-emphasis",
    "work-object-activate",
    "bounded-transfer-path",
    "receiver-emphasis",
    "settle",
  ]);
});

test("canonical identifiers and occurrence time are preserved exactly", () => {
  const descriptor = buildV2HandoffVisualization({ motion: realMotion(), reducedMotion: false });
  assert.equal(descriptor.activityId, canonicalHandoff.activity_id);
  assert.equal(descriptor.workItemId, canonicalHandoff.work_item_id);
  assert.equal(descriptor.fromPositionKey, canonicalHandoff.previous_position_key);
  assert.equal(descriptor.toPositionKey, canonicalHandoff.assigned_position_key);
  assert.equal(descriptor.occurredAt, canonicalHandoff.occurred_at);
  assert.equal(descriptor.canonicalBasis, canonicalHandoff.canonical_basis);
  assert.equal(descriptor.handoffStatus, canonicalHandoff.status);
});

test("visual sequence never claims physical travel, location, presence or collaboration", () => {
  const descriptor = buildV2HandoffVisualization({ motion: realMotion(), reducedMotion: false });
  for (const key of [
    "canonicalStateWritable",
    "physicalPresenceClaimed",
    "physicalLocationClaimed",
    "physicalTravelClaimed",
    "physicalTransferDurationClaimed",
    "roomTraversalClaimed",
    "conversationClaimed",
    "transcriptClaimed",
    "spokenWordsClaimed",
    "collaborationClaimed",
    "workCompletionClaimed",
    "dependencyResolutionClaimed",
    "authorityChangeClaimed",
    "approvalOrRejectionClaimed",
    "presentationTimingIsCanonical",
    "visualPathIsPhysicalRoute",
  ]) {
    assert.equal(descriptor.truth[key], false, `truth.${key} must be false`);
  }
  assert.ok(descriptor.steps.every((step) => step.physicalMotionClaimed === false));
});

test("reduced motion uses only static relation plus brief endpoint emphasis", () => {
  const descriptor = buildV2HandoffVisualization({ motion: realMotion(), reducedMotion: true });
  assert.equal(descriptor.supported, true);
  assert.equal(descriptor.mode, "static-relation");
  assert.deepEqual(descriptor.steps.map((step) => step.key), [
    "sender-emphasis",
    "static-relation",
    "receiver-emphasis",
  ]);
  assert.equal(descriptor.reducedMotion.mode, "static-relation-brief-emphasis");
  assert.equal(descriptor.reducedMotion.longTravelAnimationAllowed, false);
  assert.ok(!descriptor.steps.some((step) => step.key === "bounded-transfer-path"));
});

test("presentation timing is tokenized and never derived from canonical occurred_at", () => {
  const descriptor = buildV2HandoffVisualization({ motion: realMotion(), reducedMotion: false });
  assert.deepEqual(
    descriptor.steps.map((step) => step.timingToken),
    ["micro", "standard", "spatial-focus", "standard", "standard"],
  );
  for (const step of descriptor.steps) {
    assert.equal(typeof step.timingToken, "string");
    assert.equal("durationMs" in step, false);
    assert.equal("occurredAt" in step, false);
  }
});

test("unsupported Phase 2E source descriptor fails closed", () => {
  const sender = resolveV2CharacterPresentation({
    positionKey: "unknown-sender",
    title: "Neutral Professional",
    department: "unassigned",
  });
  const receiver = resolveV2CharacterPresentation({
    positionKey: "unknown-receiver",
    title: "Neutral Professional",
    department: "unassigned",
  });
  const motion = buildV2HandoffMotionDescriptor({
    handoff: {
      ...canonicalHandoff,
      previous_position_key: "unknown-sender",
      assigned_position_key: "unknown-receiver",
    },
    sender,
    receiver,
  });
  assert.equal(motion.supported, false);
  const descriptor = buildV2HandoffVisualization({ motion, reducedMotion: false });
  assert.equal(descriptor.supported, false);
  assert.equal(descriptor.mode, "unsupported");
  assert.equal(descriptor.limitation, "source-motion-unsupported");
  assert.deepEqual(descriptor.steps, []);
});

test("forged source truth fails closed instead of being repaired", () => {
  const forged = clone(realMotion());
  forged.truth.physicalTravelClaimed = true;
  const descriptor = buildV2HandoffVisualization({ motion: forged, reducedMotion: false });
  assert.equal(descriptor.supported, false);
  assert.equal(descriptor.mode, "unsupported");
  assert.equal(descriptor.limitation, "source-motion-truth-invalid");
  assert.equal(descriptor.activityId, "");
  assert.deepEqual(descriptor.steps, []);
});

test("replay visualization requires supported coverage and the matching canonical event", () => {
  const descriptor = buildV2HandoffVisualization({
    motion: realMotion(),
    reducedMotion: false,
    context: {
      mode: "replay",
      coverageSupported: true,
      cursorActivityId: canonicalHandoff.activity_id,
    },
  });
  assert.equal(descriptor.supported, true);
  assert.equal(descriptor.replay.mode, "replay");
  assert.equal(descriptor.replay.coverageSupported, true);
  assert.equal(descriptor.replay.cursorMatchesActivity, true);
  assert.equal(descriptor.replay.activationAllowedByReplayContext, true);
  assert.equal(descriptor.replay.historicalInferenceAllowed, false);
});

test("replay without supported coverage fails closed", () => {
  const descriptor = buildV2HandoffVisualization({
    motion: realMotion(),
    reducedMotion: false,
    context: {
      mode: "replay",
      coverageSupported: false,
      cursorActivityId: canonicalHandoff.activity_id,
    },
  });
  assert.equal(descriptor.supported, false);
  assert.equal(descriptor.limitation, "replay-coverage-unsupported");
  assert.deepEqual(descriptor.steps, []);
});

test("replay at a different event cursor fails closed", () => {
  const descriptor = buildV2HandoffVisualization({
    motion: realMotion(),
    reducedMotion: false,
    context: {
      mode: "replay",
      coverageSupported: true,
      cursorActivityId: "act-other",
    },
  });
  assert.equal(descriptor.supported, false);
  assert.equal(descriptor.limitation, "replay-cursor-mismatch");
  assert.equal(descriptor.replay.cursorMatchesActivity, false);
});

test("live mode does not require replay evidence", () => {
  const descriptor = buildV2HandoffVisualization({ motion: realMotion(), reducedMotion: false });
  assert.equal(descriptor.replay.mode, "live");
  assert.equal(descriptor.replay.coverageSupported, null);
  assert.equal(descriptor.replay.cursorActivityId, null);
  assert.equal(descriptor.replay.cursorMatchesActivity, null);
  assert.equal(descriptor.replay.activationAllowedByReplayContext, true);
});

test("identical inputs are deterministic and outputs are deeply frozen", () => {
  const first = buildV2HandoffVisualization({ motion: realMotion(), reducedMotion: false });
  const second = buildV2HandoffVisualization({ motion: realMotion(), reducedMotion: false });
  assert.deepEqual(first, second);
  assert.notEqual(first, second);
  assertDeepFrozen(first);
});

test("source contains no random, clock, scheduling, network, DOM or mutation machinery", () => {
  for (const forbidden of [
    "Math.random",
    "Date.now",
    "new Date(",
    "setTimeout",
    "setInterval",
    "requestAnimationFrame",
    "fetch(",
    "XMLHttpRequest",
    "WebSocket",
    "document.",
    "window.",
    "localStorage",
    "sessionStorage",
  ]) {
    assert.equal(source.includes(forbidden), false, `source must not contain ${forbidden}`);
  }
  assert.equal(/export\s+(async\s+)?function\s+(set|update|write|mutate|delete|save)/i.test(source), false);
});
