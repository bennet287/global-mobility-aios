import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { replayDiffGroups, replayDiffSemantic } from "../lib/v2/history-replay.ts";

const base = {
  coverage_state: "covered",
  known_from_activity_id: "activity:known",
  last_activity_id: "activity:last",
  last_occurred_at: "2026-09-08T12:00:00Z",
};

const beforeWork = {
  ...base,
  work_item_id: "work-1",
  status: "running",
  priority: "normal",
  department: "Operations",
  assigned_position_key: "ops",
  parent_work_item_id: null,
};
const afterWork = { ...beforeWork, status: "completed", last_activity_id: "activity:to" };

const diff = {
  contract_version: "organization-replay-state-diff.v1",
  generated_at: "2026-09-08T12:01:00Z",
  scope: "fixture",
  root_work_item_id: "work-root",
  objective_key: "fixture",
  comparison_basis: "semantic Activity cursor state",
  from_cursor: { activity_id: "activity:from", occurred_at: "2026-09-08T11:00:00Z", coverage_state: "covered", reconstruction_posture: "bounded", unapplied_transition_count: 0 },
  to_cursor: { activity_id: "activity:to", occurred_at: "2026-09-08T12:00:00Z", coverage_state: "covered", reconstruction_posture: "bounded", unapplied_transition_count: 0 },
  comparison_posture: "bounded_field_delta",
  canonical_projection: true,
  authoritative: false,
  mutations_allowed: false,
  supported_dimensions: ["work_items", "blockers", "decisions", "human_requests", "conversations"],
  unsupported_dimensions: ["presence"],
  unchanged_entities_omitted: true,
  changed_entity_count: 4,
  work_items: [{ entity_id: "work-1", change_kind: "changed", changed_fields: ["status"], before: beforeWork, after: afterWork }],
  blockers: [{ entity_id: "blocker-1", change_kind: "added", changed_fields: [], before: null, after: { ...base, blocker_id: "blocker-1", status: "open" } }],
  decisions: [{ entity_id: "decision-1", change_kind: "removed", changed_fields: [], before: { ...base, decision_id: "decision-1", status: "pending" }, after: null }],
  human_requests: [{ entity_id: "request-1", change_kind: "reindexed", changed_fields: ["status"], before: null, after: null }],
  conversations: [],
};

test("7I renders exact status deltas as cursor-interval truth", () => {
  const semantic = replayDiffSemantic(diff.work_items[0]);
  assert.deepEqual(semantic, {
    kind: "changed",
    label: "Status running → completed between these cursors",
    truthScope: "cursor_interval",
  });
});

test("7I does not overclaim creation or deletion from bounded appearance changes", () => {
  assert.equal(replayDiffSemantic(diff.blockers[0]).label, "Appeared between these cursors");
  assert.equal(replayDiffSemantic(diff.decisions[0]).label, "Not represented at the later cursor");
  assert.doesNotMatch(replayDiffSemantic(diff.blockers[0]).label, /created|born|started/i);
  assert.doesNotMatch(replayDiffSemantic(diff.decisions[0]).label, /deleted|destroyed|ended/i);
});

test("7I fails closed for unknown change kinds", () => {
  const semantic = replayDiffSemantic(diff.human_requests[0]);
  assert.equal(semantic.kind, "neutral");
  assert.equal(semantic.label, "reindexed between these cursors");
  assert.equal(semantic.truthScope, "cursor_interval");
});

test("7I preserves raw backend change kind while rendering semantic comparison labels", () => {
  const groups = replayDiffGroups(diff);
  const work = groups.find((group) => group.label === "Work items")?.items[0];
  assert.equal(work?.rawChangeKind, "changed");
  assert.equal(work?.changeKind, "Status running → completed between these cursors");
  assert.equal(work?.semantic.truthScope, "cursor_interval");
});

test("7I remains read-only and makes no present-state, quality, causal, urgency or authority inference", () => {
  const source = readFileSync(new URL("../lib/v2/history-replay.ts", import.meta.url), "utf8");
  const workspace = readFileSync(new URL("../components/v2/V2HistoryWorkspace.tsx", import.meta.url), "utf8");
  assert.doesNotMatch(source, /currently|now improved|worse because|caused by|urgent because|authority increased/i);
  assert.doesNotMatch(source + workspace, /\b(POST|PUT|PATCH|DELETE)\b/);
  assert.match(workspace, /does not infer improvement, deterioration, causality, urgency or authority/);
});
