import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import {
  buildLatestV2VisibleHandoff,
  buildV2VisibleHandoffVisualization,
  isSupportedV2HandoffCoverage,
} from "../lib/v2/visible-handoff.ts";

const REAL_HANDOFF_COVERAGE = "organization_work_assigned_activity_v1";

const canonicalHandoff = Object.freeze({
  activity_id: "act-phase7a-handoff-001",
  work_item_id: "wi-phase7a-001",
  previous_position_key: "ceo",
  assigned_position_key: "cto",
  status: "assigned",
  occurred_at: "2026-09-07T12:40:00Z",
  causation_activity_id: "act-phase7a-cause-001",
  canonical_basis: "OrganizationActivity:act-phase7a-handoff-001",
});

const employees = Object.freeze([
  Object.freeze({
    position_key: "ceo",
    title: "Chief Executive Officer",
    department: "Executive",
    reports_to_position_key: null,
    authority_level: "executive",
    organization_status: "active",
    work_item_id: null,
    work_status: null,
    semantic_state: "working",
    presence_state: "not_asserted",
    state_reason: "Canonical roster fixture",
  }),
  Object.freeze({
    position_key: "cto",
    title: "Chief Technology Officer",
    department: "Technology",
    reports_to_position_key: "ceo",
    authority_level: "executive",
    organization_status: "active",
    work_item_id: canonicalHandoff.work_item_id,
    work_status: "assigned",
    semantic_state: "working",
    presence_state: "not_asserted",
    state_reason: "Canonical roster fixture",
  }),
]);

function build(overrides = {}) {
  return buildLatestV2VisibleHandoff({
    handoffs: [canonicalHandoff],
    employees,
    coverageState: REAL_HANDOFF_COVERAGE,
    ...overrides,
  });
}

function assertDeepFrozen(value, path = "value") {
  if (value === null || typeof value !== "object") return;
  assert.equal(Object.isFrozen(value), true, `${path} must be deeply frozen`);
  for (const [key, child] of Object.entries(value)) {
    assertDeepFrozen(child, `${path}.${key}`);
  }
}

test("the current live handoff coverage adapter is explicitly supported", () => {
  assert.equal(isSupportedV2HandoffCoverage(REAL_HANDOFF_COVERAGE), true);
  assert.equal(isSupportedV2HandoffCoverage("covered"), true);
  for (const unsupported of ["unavailable", "partial", "unknown", "", "not_asserted"]) {
    assert.equal(isSupportedV2HandoffCoverage(unsupported), false, unsupported);
  }
});

test("real live coverage maps the latest canonical event through sealed Phase 2E and Phase 2O contracts", () => {
  const model = build();
  assert.ok(model);
  assert.equal(model.canonicalHandoff.activity_id, canonicalHandoff.activity_id);
  assert.equal(model.canonicalHandoff.work_item_id, canonicalHandoff.work_item_id);
  assert.equal(model.canonicalHandoff.status, canonicalHandoff.status);
  assert.equal(model.canonicalHandoff.occurred_at, canonicalHandoff.occurred_at);
  assert.equal(model.truth.canonicalCoverageState, REAL_HANDOFF_COVERAGE);
  assert.equal(model.truth.canonicalCoverageSupported, true);
  assert.equal(model.semanticAnimationSupported, true);

  const full = buildV2VisibleHandoffVisualization(model, false);
  assert.ok(full);
  assert.equal(full.supported, true);
  assert.equal(full.mode, "bounded-transfer-sequence");
  assert.deepEqual(full.steps.map((step) => step.key), [
    "sender-emphasis",
    "work-object-activate",
    "bounded-transfer-path",
    "receiver-emphasis",
    "settle",
  ]);

  const reduced = buildV2VisibleHandoffVisualization(model, true);
  assert.ok(reduced);
  assert.equal(reduced.supported, true);
  assert.equal(reduced.mode, "static-relation");
  assert.deepEqual(reduced.steps.map((step) => step.key), [
    "sender-emphasis",
    "static-relation",
    "receiver-emphasis",
  ]);
  assertDeepFrozen(model);
});

test("unsupported or unavailable coverage never produces a current canonical handoff signal", () => {
  for (const coverageState of ["unavailable", "partial", "unknown", "not_asserted"]) {
    assert.equal(build({ coverageState }), null, coverageState);
  }
});

test("latest event selection is deterministic by canonical occurrence time then activity id", () => {
  const earlier = {
    ...canonicalHandoff,
    activity_id: "act-phase7a-handoff-000",
    occurred_at: "2026-09-07T12:39:00Z",
  };
  const sameTimeLaterId = {
    ...canonicalHandoff,
    activity_id: "act-phase7a-handoff-999",
  };
  const model = build({ handoffs: [sameTimeLaterId, earlier, canonicalHandoff] });
  assert.ok(model);
  assert.equal(model.canonicalHandoff.activity_id, sameTimeLaterId.activity_id);
});

test("a malformed newest event fails closed instead of falling back to an older prettier event", () => {
  const older = {
    ...canonicalHandoff,
    activity_id: "act-phase7a-handoff-older",
    occurred_at: "2026-09-07T12:39:00Z",
  };
  const malformedNewest = {
    ...canonicalHandoff,
    activity_id: "act-phase7a-handoff-newest",
    occurred_at: "2026-09-07T12:41:00Z",
    canonical_basis: "",
  };
  assert.equal(build({ handoffs: [older, malformedNewest] }), null);
});

test("an unorderable handoff record makes the latest claim fail closed", () => {
  const unorderable = {
    ...canonicalHandoff,
    activity_id: "act-phase7a-unorderable",
    occurred_at: "",
  };
  assert.equal(build({ handoffs: [canonicalHandoff, unorderable] }), null);
});

test("missing or ambiguous roster endpoints preserve the canonical relation but disable character semantic motion", () => {
  const missingReceiver = build({ employees: [employees[0]] });
  assert.ok(missingReceiver);
  assert.equal(missingReceiver.receiver, null);
  assert.equal(missingReceiver.semanticAnimationSupported, false);
  assert.equal(missingReceiver.limitation, "receiver-employee-unavailable");
  assert.equal(buildV2VisibleHandoffVisualization(missingReceiver, false), null);

  const duplicateSender = build({ employees: [employees[0], employees[0], employees[1]] });
  assert.ok(duplicateSender);
  assert.equal(duplicateSender.sender, null);
  assert.equal(duplicateSender.semanticAnimationSupported, false);
  assert.equal(duplicateSender.limitation, "sender-employee-unavailable");
});

test("visible model cannot claim physical travel, presence, conversation, completion or canonical mutation", () => {
  const model = build();
  assert.ok(model);
  for (const key of [
    "canonicalStateWritable",
    "physicalPresenceClaimed",
    "physicalLocationClaimed",
    "physicalTravelClaimed",
    "conversationClaimed",
    "completionClaimed",
  ]) {
    assert.equal(model.truth[key], false, `truth.${key}`);
  }
  assert.equal(model.truth.presentationOnly, true);
  assert.equal(model.truth.canonicalEvent, true);
});

test("the pure selector contains no random, clock, network, DOM or mutation machinery", () => {
  const source = readFileSync(
    fileURLToPath(new URL("../lib/v2/visible-handoff.ts", import.meta.url)),
    "utf8",
  );
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
});

test("visible choreography consumes centralized motion tokens and never loops semantic transfer indefinitely", () => {
  const css = readFileSync(
    fileURLToPath(new URL("../components/v2/V2CanonicalHandoffSignal.module.css", import.meta.url)),
    "utf8",
  );
  const tokens = readFileSync(
    fileURLToPath(new URL("../styles/v2/tokens.css", import.meta.url)),
    "utf8",
  );
  assert.match(tokens, /--aios-v2-motion-duration-semantic-handoff:\s*1280ms/);
  assert.match(tokens, /--aios-v2-motion-ease-emphasis:/);
  assert.match(css, /var\(--aios-v2-motion-duration-semantic-handoff\)/);
  assert.match(css, /var\(--aios-v2-motion-ease-emphasis\)/);
  assert.doesNotMatch(css, /\b\d+ms\b/);
  assert.doesNotMatch(css, /animation\s*:[^;]*\binfinite\b/i);
  assert.match(css, /prefers-reduced-motion:\s*reduce/);
  assert.match(css, /\.traveler\s*\{\s*display:\s*none;/s);
});
