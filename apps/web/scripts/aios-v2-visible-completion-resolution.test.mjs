import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import {
  V2_COMPLETION_RESOLUTION_TRUTH,
  buildV2VisibleBlockerResolutions,
  buildV2VisibleCompletionResolution,
  buildV2VisibleDecisionOutcomes,
  buildV2VisibleWorkCompletions,
  visibleCompletionResolutionForPosition,
  visibleCompletionResolutionForWorkItems,
} from "../lib/v2/visible-completion-resolution.ts";

function work(overrides = {}) {
  return {
    work_item_id: "work-1",
    parent_work_item_id: null,
    title: "Canonical work",
    objective_key: "objective-1",
    phase_key: null,
    status: "completed",
    priority: "normal",
    risk_level: "low",
    assigned_position_key: "cto",
    department: "Technology",
    authority_level: "L2",
    created_at: "2026-09-07T20:00:00Z",
    updated_at: "2026-09-07T20:30:00Z",
    due_at: null,
    completed_at: "2026-09-07T20:30:00Z",
    elapsed_seconds: 1800,
    overdue: false,
    specialist_evidence_valid: false,
    specialist_evidence_reason: "K.1 evidence not established",
    ...overrides,
  };
}

function blocker(overrides = {}) {
  return {
    blocker_id: "blocker-1",
    work_item_id: "work-1",
    blocker_type: "dependency",
    title: "Canonical blocker",
    description: "Blocked by dependency.",
    severity: "high",
    status: "resolved",
    accountable_position_key: "cto",
    decision_id: null,
    risk_escalation_id: null,
    requires_human_action: false,
    opened_at: "2026-09-07T19:00:00Z",
    due_at: null,
    open_elapsed_seconds: 3600,
    overdue: false,
    resolved_at: "2026-09-07T20:00:00Z",
    resolution_summary: "Dependency evidence supplied.",
    resolving_actor_type: "human",
    resolving_actor_id: "owner-1",
    waived_at: null,
    waived_by_human_id: null,
    waiver_reason: null,
    ...overrides,
  };
}

function decision(overrides = {}) {
  return {
    decision_id: "decision-1",
    decision_key: "decision-key-1",
    title: "Governed decision",
    question: "Proceed?",
    recommendation: "Proceed after review.",
    status: "approved",
    authority_level: "L4",
    decision_owner_position: "board",
    work_item_id: "work-1",
    evidence_items: [],
    record_fingerprint: "fingerprint",
    source_object_type: "work_item",
    source_object_id: "work-1",
    source_object_version: "1",
    supersedes_decision_id: null,
    superseded_by_decision_id: null,
    is_current: true,
    required_owner_action: false,
    decided_at: "2026-09-07T20:45:00Z",
    created_at: "2026-09-07T20:15:00Z",
    superseded_by_created_at: null,
    superseded_in_projection_week: false,
    ...overrides,
  };
}

test("Phase 7G requires completed status and a canonical completion timestamp", () => {
  assert.equal(buildV2VisibleWorkCompletions([work()]).length, 1);
  assert.equal(buildV2VisibleWorkCompletions([work({ completed_at: null })]).length, 0);
  assert.equal(buildV2VisibleWorkCompletions([work({ status: "running" })]).length, 0);
  assert.equal(buildV2VisibleWorkCompletions([work({ completed_at: "not-a-date" })]).length, 0);
});

test("Phase 7G does not promote structural completion into execution-evidence success", () => {
  const [completion] = buildV2VisibleWorkCompletions([
    work({ specialist_evidence_valid: false, specialist_evidence_reason: "K.1 durable output missing" }),
  ]);
  assert.equal(completion.kind, "work_completed");
  assert.equal(completion.canonicalBasis, "OrganizationalWorkItem.status+completed_at");
  assert.equal("evidenceValid" in completion, false);
});

test("Phase 7G requires the full canonical blocker resolution tuple", () => {
  const [resolved] = buildV2VisibleBlockerResolutions([blocker()]);
  assert.equal(resolved.kind, "blocker_resolved");
  assert.equal(resolved.outcomeSummary, "Dependency evidence supplied.");
  assert.equal(resolved.resolverLabel, "human:owner-1");

  for (const overrides of [
    { resolved_at: null },
    { resolution_summary: "" },
    { resolving_actor_type: null },
    { resolving_actor_id: null },
    { status: "mitigated" },
  ]) {
    assert.deepEqual(buildV2VisibleBlockerResolutions([blocker(overrides)]), []);
  }
});

test("Phase 7G requires exact human waiver evidence", () => {
  const waived = blocker({
    status: "waived",
    resolved_at: null,
    resolution_summary: null,
    resolving_actor_type: null,
    resolving_actor_id: null,
    waived_at: "2026-09-07T20:10:00Z",
    waived_by_human_id: "human-owner",
    waiver_reason: "Owner accepted the governed exception.",
  });
  const [projection] = buildV2VisibleBlockerResolutions([waived]);
  assert.equal(projection.kind, "blocker_waived");
  assert.equal(projection.resolverLabel, "human:human-owner");

  assert.deepEqual(
    buildV2VisibleBlockerResolutions([waived, { ...waived, blocker_id: "b2", waiver_reason: "" }]),
    [projection],
  );
});

test("Phase 7G decision outcome requires approved/rejected plus decided_at", () => {
  assert.equal(buildV2VisibleDecisionOutcomes([decision()]).length, 1);
  assert.equal(buildV2VisibleDecisionOutcomes([decision({ status: "rejected" })])[0].status, "rejected");
  assert.deepEqual(buildV2VisibleDecisionOutcomes([decision({ status: "pending_board" })]), []);
  assert.deepEqual(buildV2VisibleDecisionOutcomes([decision({ decided_at: null })]), []);
});

test("Phase 7G builds a deterministic newest-first canonical transition timeline", () => {
  const timeline = buildV2VisibleCompletionResolution({
    workItems: [work()],
    blockers: [blocker()],
    decisions: [decision()],
  });
  assert.deepEqual(timeline.map((item) => item.kind), [
    "decision_outcome",
    "work_completed",
    "blocker_resolved",
  ]);
});

test("Phase 7G scopes Mission and employee evidence without inferring unrelated outcomes", () => {
  const timeline = buildV2VisibleCompletionResolution({
    workItems: [
      work(),
      work({ work_item_id: "work-2", title: "Other work", assigned_position_key: "ops", completed_at: "2026-09-07T21:00:00Z" }),
    ],
    blockers: [blocker(), blocker({ blocker_id: "blocker-2", work_item_id: "work-2" })],
    decisions: [decision(), decision({ decision_id: "decision-2", work_item_id: "work-2" })],
  });

  const mission = visibleCompletionResolutionForWorkItems(timeline, new Set(["work-1"]));
  assert.equal(mission.length, 3);
  assert.equal(mission.every((item) => item.kind === "work_completed" ? item.workItemId === "work-1" : item.workItemId === "work-1"), true);

  const employee = visibleCompletionResolutionForPosition({
    items: timeline,
    positionKey: "cto",
    workItemIds: new Set(["work-1"]),
  });
  assert.equal(employee.length, 3);
  assert.equal(employee.some((item) => item.kind === "work_completed" && item.assignedPositionKey === "ops"), false);
});

test("Phase 7G presentation signal keeps completion evidence distinct from celebration or physical activity", () => {
  const signal = readFileSync(
    new URL("../components/v2/V2CanonicalCompletionResolutionSignal.tsx", import.meta.url),
    "utf8",
  );
  assert.match(signal, /data-aios-v2-completion-resolution="canonical-evidence"/);
  assert.match(signal, /data-completion-inferred-from-animation="false"/);
  assert.match(signal, /data-physical-celebration-claimed="false"/);
  assert.match(signal, /data-physical-presence-claimed="false"/);
  assert.match(signal, /data-locomotion-claimed="false"/);
  assert.match(signal, /Explicit canonical transition evidence only · no celebration, travel or physical presence · no completion inferred from animation or elapsed time/);
});

test("Phase 7G presentation truth forbids physical or animation-derived completion claims", () => {
  assert.equal(V2_COMPLETION_RESOLUTION_TRUTH.presentationOnly, true);
  assert.equal(V2_COMPLETION_RESOLUTION_TRUTH.physicalCelebrationClaimed, false);
  assert.equal(V2_COMPLETION_RESOLUTION_TRUTH.physicalPresenceClaimed, false);
  assert.equal(V2_COMPLETION_RESOLUTION_TRUTH.locomotionClaimed, false);
  assert.equal(V2_COMPLETION_RESOLUTION_TRUTH.canonicalMutationAllowed, false);
  assert.equal(V2_COMPLETION_RESOLUTION_TRUTH.inferredFromAnimation, false);
  assert.equal(V2_COMPLETION_RESOLUTION_TRUTH.inferredFromElapsedTime, false);
});
