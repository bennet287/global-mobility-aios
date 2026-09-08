import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { replaySemanticState, replayStateGroups } from "../lib/v2/history-replay.ts";

const base = {
  coverage_state: "covered",
  known_from_activity_id: "00000000-0000-0000-0000-000000000001",
  last_activity_id: "00000000-0000-0000-0000-000000000002",
  last_occurred_at: "2026-09-08T12:00:00Z",
};

const state = {
  contract_version: "organization-replay-state.v1",
  generated_at: "2026-09-08T12:01:00Z",
  scope: "fixture",
  root_work_item_id: "00000000-0000-0000-0000-000000000010",
  objective_key: "fixture",
  cursor_activity_id: "00000000-0000-0000-0000-000000000099",
  cursor_occurred_at: "2026-09-08T12:00:00Z",
  cursor_coverage_state: "covered",
  reconstruction_posture: "covered",
  canonical_projection: true,
  authoritative: false,
  mutations_allowed: false,
  supported_dimensions: ["work_item_status_assignment", "blocker_lifecycle", "decision_lifecycle", "human_request_lifecycle", "conversation_lifecycle"],
  unsupported_dimensions: ["risk_escalation_history"],
  unapplied_transition_count: 0,
  work_items: [{ ...base, work_item_id: "work-1", status: "completed", priority: "normal", department: "Operations", assigned_position_key: "ops", parent_work_item_id: null }],
  blockers: [{ ...base, blocker_id: "blocker-1", work_item_id: "work-1", status: "resolved", blocker_type: "dependency", severity: "high", requires_human_action: false }],
  decisions: [
    { ...base, decision_id: "decision-1", work_item_id: "work-1", status: "approved", decision_type: "governance", authority_level: "board" },
    { ...base, decision_id: "decision-2", work_item_id: "work-1", status: "rejected", decision_type: "governance", authority_level: "board" },
  ],
  human_requests: [{ ...base, request_id: "request-1", work_item_id: "work-1", status: "completed", request_type: "review", required_role: "owner" }],
  conversations: [{ ...base, conversation_id: "conversation-1", work_item_id: "work-1", status: "closed" }],
};

test("7H maps exact canonical reconstructed statuses to historical cursor semantics", () => {
  assert.deepEqual(replaySemanticState("Work items", "completed"), {
    kind: "completed",
    label: "Completed at this cursor",
    truthScope: "historical_cursor",
  });
  assert.equal(replaySemanticState("Blockers", "resolved").label, "Resolved at this cursor");
  assert.equal(replaySemanticState("Blockers", "waived").label, "Waived at this cursor");
  assert.equal(replaySemanticState("Blockers", "mitigated").kind, "active");
  assert.equal(replaySemanticState("Decisions", "approved").label, "Approved at this cursor");
  assert.equal(replaySemanticState("Decisions", "rejected").label, "Rejected at this cursor");
  assert.equal(replaySemanticState("Human requests", "completed").label, "Completed at this cursor");
  assert.equal(replaySemanticState("Human requests", "declined").kind, "closed");
  assert.equal(replaySemanticState("Conversations", "closed").label, "Closed at this cursor");
});

test("7H fails closed instead of promoting noncanonical aliases", () => {
  for (const [group, alias] of [
    ["Work items", "done"],
    ["Work items", "complete"],
    ["Blockers", "cleared"],
    ["Blockers", "closed"],
    ["Decisions", "accepted"],
    ["Decisions", "declined"],
    ["Human requests", "fulfilled"],
    ["Human requests", "resolved"],
  ]) {
    const semantic = replaySemanticState(group, alias);
    assert.equal(semantic.kind, "neutral", `${group}:${alias} must remain literal`);
    assert.equal(semantic.label, `${alias} at this cursor`);
  }
});

test("7H replay groups preserve canonical state identity and attach historical semantics", () => {
  const groups = replayStateGroups(state);
  const work = groups.find((group) => group.label === "Work items");
  const blockers = groups.find((group) => group.label === "Blockers");
  const decisions = groups.find((group) => group.label === "Decisions");
  assert.equal(work?.rows[0].id, "work-1");
  assert.equal(work?.rows[0].semantic.kind, "completed");
  assert.equal(blockers?.rows[0].semantic.kind, "resolved");
  assert.deepEqual(decisions?.rows.map((row) => row.semantic.kind), ["approved", "rejected"]);
  assert.ok(groups.flatMap((group) => group.rows).every((row) => row.semantic.truthScope === "historical_cursor"));
});

test("7H does not infer present truth, physical presence, movement, quality or causality", () => {
  const source = readFileSync(new URL("../lib/v2/history-replay.ts", import.meta.url), "utf8");
  assert.doesNotMatch(source, /currently completed|completed now|present in|physically present|walk(?:ing)? to|moved to|improved because|caused by/i);
  assert.match(source, /at this cursor/);
});

test("7H remains read-only and depends on the sealed replay state contract", () => {
  const workspace = readFileSync(new URL("../components/v2/V2HistoryWorkspace.tsx", import.meta.url), "utf8");
  const hook = readFileSync(new URL("../hooks/useV2HistoryReplay.ts", import.meta.url), "utf8");
  assert.match(hook, /getLatestAustriaOrganizationReplayState/);
  assert.doesNotMatch(workspace + hook, /\b(POST|PUT|PATCH|DELETE)\b/);
});
