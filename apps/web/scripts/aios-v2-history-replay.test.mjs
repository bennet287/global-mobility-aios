import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import {
  buildV2HistoryPortfolio,
  historyEventDestination,
  replayDiffGroups,
  replayStateGroups,
  selectV2HistoryEvent,
  summarizeV2ReplayState,
} from "../lib/v2/history-replay.ts";
import { navigationCommands, ownerNavigation } from "../lib/v2/navigation.ts";

const events = [
  { activity_id: "00000000-0000-0000-0000-000000000001", event_kind: "work_created", coverage_state: "pre_epoch_partial", stream_sequence: 1, activity_class: "work", activity_type: "work.created", title: "Work created", summary: "Recorded work creation", actor_type: "human", actor_id: "owner", department: "Executive", position_key: "ceo", authority_level: "L3", work_item_id: "work:root", source_object_type: "WorkItem", source_object_id: "work:root", source_object_version: "1", correlation_key: null, causation_activity_id: null, supersedes_activity_id: null, occurred_at: "2026-09-05T08:00:00Z" },
  { activity_id: "00000000-0000-0000-0000-000000000002", event_kind: "handoff", coverage_state: "covered", stream_sequence: 2, activity_class: "assignment", activity_type: "work.assigned", title: "Assignment recorded", summary: "Recorded assignment transition", actor_type: "agent", actor_id: "system", department: "Operations", position_key: "ops", authority_level: "L1", work_item_id: "work:root", source_object_type: "WorkItem", source_object_id: "work:root", source_object_version: "2", correlation_key: "corr:1", causation_activity_id: "00000000-0000-0000-0000-000000000001", supersedes_activity_id: null, occurred_at: "2026-09-05T09:00:00Z" },
];

const latest = {
  established: true,
  replay: {
    contract_version: "organization-replay.v1",
    generated_at: "2026-09-06T02:00:00Z",
    scope: "fixture",
    root_work_item_id: "work:root",
    objective_key: "fixture",
    work_item_ids: ["work:root"],
    canonical_projection: true,
    authoritative: false,
    mutations_allowed: false,
    coverage: { activity_history_basis: "semantic Activity", activity_history_established: true, activity_history_coverage_start: "2026-09-05T08:30:00Z", pre_epoch_history: "partial", evidence_history: "partial", risk_escalation_history: "unsupported", source_snapshot_history: "partial", conversation_history: "unsupported" },
    total_events: 5,
    returned_events: 2,
    truncated: true,
    events,
  },
};

const state = {
  contract_version: "organization-replay-state.v1", generated_at: "2026-09-06T02:01:00Z", scope: "fixture", root_work_item_id: "work:root", objective_key: "fixture", cursor_activity_id: events[1].activity_id, cursor_occurred_at: events[1].occurred_at, cursor_coverage_state: "covered", reconstruction_posture: "bounded_semantic_activity", canonical_projection: true, authoritative: false, mutations_allowed: false,
  supported_dimensions: ["work_items", "blockers", "decisions"], unsupported_dimensions: ["presence"], unapplied_transition_count: 1,
  work_items: [{ work_item_id: "work:root", status: "running", priority: "normal", department: "Operations", assigned_position_key: "ops", parent_work_item_id: null, coverage_state: "covered", known_from_activity_id: events[0].activity_id, last_activity_id: events[1].activity_id, last_occurred_at: events[1].occurred_at }],
  blockers: [], decisions: [], human_requests: [], conversations: [],
};

const diff = {
  contract_version: "organization-replay-state-diff.v1", generated_at: "2026-09-06T02:02:00Z", scope: "fixture", root_work_item_id: "work:root", objective_key: "fixture", comparison_basis: "semantic Activity cursor state", from_cursor: { activity_id: events[0].activity_id, occurred_at: events[0].occurred_at, coverage_state: "pre_epoch_partial", reconstruction_posture: "partial", unapplied_transition_count: 0 }, to_cursor: { activity_id: events[1].activity_id, occurred_at: events[1].occurred_at, coverage_state: "covered", reconstruction_posture: "bounded", unapplied_transition_count: 1 }, comparison_posture: "bounded_field_delta", canonical_projection: true, authoritative: false, mutations_allowed: false, supported_dimensions: ["work_items"], unsupported_dimensions: ["presence"], unchanged_entities_omitted: true, changed_entity_count: 1,
  work_items: [{ entity_id: "work:root", change_kind: "changed", changed_fields: ["assigned_position_key"], before: null, after: state.work_items[0] }], blockers: [], decisions: [], human_requests: [], conversations: [],
};

test("Q8 preserves canonical replay order, literal counts and coverage posture", () => {
  const portfolio = buildV2HistoryPortfolio(latest);
  assert.equal(portfolio.established, true);
  assert.equal(portfolio.totalEvents, 5);
  assert.equal(portfolio.returnedEvents, 2);
  assert.equal(portfolio.truncated, true);
  assert.equal(portfolio.preEpochHistory, "partial");
  assert.deepEqual(portfolio.events.map((event) => event.activity_id), events.map((event) => event.activity_id));
  assert.equal(portfolio.events[0].coverage_state, "pre_epoch_partial");
});

test("Q8 selection and destinations preserve opaque Activity identity", () => {
  assert.equal(selectV2HistoryEvent(events, events[1].activity_id)?.title, "Assignment recorded");
  assert.equal(selectV2HistoryEvent(events, "missing"), null);
  const opaque = "activity:AT /?ref=%23#alpha";
  assert.equal(new URL(historyEventDestination(opaque), "http://test").searchParams.get("cursor"), opaque);
  const comparison = new URL(historyEventDestination(events[1].activity_id, events[0].activity_id), "http://test");
  assert.equal(comparison.searchParams.get("cursor"), events[1].activity_id);
  assert.equal(comparison.searchParams.get("from"), events[0].activity_id);
});

test("Q8 state and diff helpers report only returned reconstruction fields", () => {
  const summary = summarizeV2ReplayState(state);
  assert.equal(summary?.workItemCount, 1);
  assert.equal(summary?.unappliedTransitionCount, 1);
  assert.deepEqual(summary?.unsupportedDimensions, ["presence"]);
  assert.equal(replayStateGroups(state)[0].rows[0].id, "work:root");
  const groups = replayDiffGroups(diff);
  assert.equal(groups[0].items[0].entityId, "work:root");
  assert.deepEqual(groups[0].items[0].changedFields, ["assigned_position_key"]);
});

test("Q8 enables the seventh Owner domain and preserves the legacy replay destination", () => {
  const history = ownerNavigation.find((item) => item.label === "History");
  assert.equal(history?.enabled, true);
  assert.equal(history?.href, "/cockpit/v2/history");
  assert.equal(navigationCommands.filter((item) => item.href === "/cockpit/v2/history").length, 1);
  assert.equal(navigationCommands.filter((item) => item.href === "/cockpit/live-organization").length, 1);
});

test("Q8 reuses sealed replay/state/diff GET clients and introduces no write path", () => {
  const hook = readFileSync(new URL("../hooks/useV2HistoryReplay.ts", import.meta.url), "utf8");
  const component = readFileSync(new URL("../components/v2/V2HistoryWorkspace.tsx", import.meta.url), "utf8");
  const client = readFileSync(new URL("../lib/live-organization.ts", import.meta.url), "utf8");
  assert.match(hook, /getLatestAustriaOrganizationReplay/);
  assert.match(hook, /getLatestAustriaOrganizationReplayState/);
  assert.match(hook, /getLatestAustriaOrganizationReplayStateDiff/);
  assert.match(client, /\/replay\/austria\/latest/);
  assert.match(component, /V2TruthBadge kind="historical"/);
  assert.match(component, /does not infer improvement, deterioration, causality, urgency or authority/);
  assert.doesNotMatch(component + hook, /\b(POST|PUT|PATCH|DELETE)\b/);
  assert.doesNotMatch(component, /fetch\(/);
});

test("Q8 source contract remains wired into design-foundation", () => {
  const packageJson = readFileSync(new URL("../package.json", import.meta.url), "utf8");
  assert.match(packageJson, /scripts\/aios-v2-history-replay\.test\.mjs/);
});
