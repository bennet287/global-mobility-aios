import { expect, test } from "@playwright/test";

const firstActivity = "00000000-0000-0000-0000-000000000001";
const secondActivity = "00000000-0000-0000-0000-000000000002";
const rootWorkItem = "10000000-0000-0000-0000-000000000001";

const replay = {
  contract_version: "organization-replay.v1",
  generated_at: "2026-09-06T03:00:00Z",
  scope: "fixture",
  root_work_item_id: rootWorkItem,
  objective_key: "fixture",
  work_item_ids: [rootWorkItem],
  canonical_projection: true,
  authoritative: false,
  mutations_allowed: false,
  coverage: {
    activity_history_basis: "persisted semantic Activity",
    activity_history_established: true,
    activity_history_coverage_start: "2026-09-05T08:30:00Z",
    pre_epoch_history: "partial",
    evidence_history: "partial",
    risk_escalation_history: "unsupported",
    source_snapshot_history: "partial",
    conversation_history: "unsupported",
  },
  total_events: 5,
  returned_events: 2,
  truncated: true,
  events: [
    {
      activity_id: firstActivity,
      event_kind: "work_created",
      coverage_state: "pre_epoch_partial",
      stream_sequence: 1,
      activity_class: "work",
      activity_type: "work.created",
      title: "Work created",
      summary: "Recorded creation before the established coverage epoch",
      actor_type: "human",
      actor_id: "owner",
      department: "Executive",
      position_key: "ceo",
      authority_level: "L3",
      work_item_id: rootWorkItem,
      source_object_type: "WorkItem",
      source_object_id: rootWorkItem,
      source_object_version: "1",
      correlation_key: null,
      causation_activity_id: null,
      supersedes_activity_id: null,
      occurred_at: "2026-09-05T08:00:00Z",
    },
    {
      activity_id: secondActivity,
      event_kind: "decision",
      coverage_state: "covered",
      stream_sequence: 2,
      activity_class: "decision",
      activity_type: "decision.recorded",
      title: "Owner review recorded",
      summary: "Recorded Decision state transition",
      actor_type: "human",
      actor_id: "owner",
      department: "Executive",
      position_key: "ceo",
      authority_level: "L3",
      work_item_id: rootWorkItem,
      source_object_type: "ExecutiveDecision",
      source_object_id: "20000000-0000-0000-0000-000000000001",
      source_object_version: "2",
      correlation_key: "corr:fixture",
      causation_activity_id: firstActivity,
      supersedes_activity_id: null,
      occurred_at: "2026-09-05T09:00:00Z",
    },
  ],
};

const stateFor = (activityId: string) => ({
  contract_version: "organization-replay-state.v1",
  generated_at: "2026-09-06T03:01:00Z",
  scope: "fixture",
  root_work_item_id: rootWorkItem,
  objective_key: "fixture",
  cursor_activity_id: activityId,
  cursor_occurred_at: activityId === firstActivity ? "2026-09-05T08:00:00Z" : "2026-09-05T09:00:00Z",
  cursor_coverage_state: activityId === firstActivity ? "pre_epoch_partial" : "covered",
  reconstruction_posture: activityId === firstActivity ? "partial_pre_epoch" : "bounded_semantic_activity",
  canonical_projection: true,
  authoritative: false,
  mutations_allowed: false,
  supported_dimensions: ["work_items", "decisions"],
  unsupported_dimensions: ["presence", "evidence_history"],
  unapplied_transition_count: activityId === firstActivity ? 1 : 0,
  work_items: [{
    work_item_id: rootWorkItem,
    status: activityId === firstActivity ? "queued" : "running",
    priority: "normal",
    department: "Executive",
    assigned_position_key: "ceo",
    parent_work_item_id: null,
    coverage_state: activityId === firstActivity ? "pre_epoch_partial" : "covered",
    known_from_activity_id: firstActivity,
    last_activity_id: activityId,
    last_occurred_at: activityId === firstActivity ? "2026-09-05T08:00:00Z" : "2026-09-05T09:00:00Z",
  }],
  blockers: [],
  decisions: activityId === secondActivity ? [{
    decision_id: "20000000-0000-0000-0000-000000000001",
    work_item_id: rootWorkItem,
    status: "awaiting_owner",
    decision_type: "filing_authority",
    authority_level: "L3",
    coverage_state: "covered",
    known_from_activity_id: secondActivity,
    last_activity_id: secondActivity,
    last_occurred_at: "2026-09-05T09:00:00Z",
  }] : [],
  human_requests: [],
  conversations: [],
});

const diff = {
  contract_version: "organization-replay-state-diff.v1",
  generated_at: "2026-09-06T03:02:00Z",
  scope: "fixture",
  root_work_item_id: rootWorkItem,
  objective_key: "fixture",
  comparison_basis: "semantic Activity cursor state",
  from_cursor: { activity_id: firstActivity, occurred_at: "2026-09-05T08:00:00Z", coverage_state: "pre_epoch_partial", reconstruction_posture: "partial_pre_epoch", unapplied_transition_count: 1 },
  to_cursor: { activity_id: secondActivity, occurred_at: "2026-09-05T09:00:00Z", coverage_state: "covered", reconstruction_posture: "bounded_semantic_activity", unapplied_transition_count: 0 },
  comparison_posture: "bounded_field_delta",
  canonical_projection: true,
  authoritative: false,
  mutations_allowed: false,
  supported_dimensions: ["work_items", "decisions"],
  unsupported_dimensions: ["presence"],
  unchanged_entities_omitted: true,
  changed_entity_count: 2,
  work_items: [{ entity_id: rootWorkItem, change_kind: "changed", changed_fields: ["status"], before: null, after: stateFor(secondActivity).work_items[0] }],
  blockers: [],
  decisions: [{ entity_id: "20000000-0000-0000-0000-000000000001", change_kind: "added", changed_fields: ["status", "authority_level"], before: null, after: stateFor(secondActivity).decisions[0] }],
  human_requests: [],
  conversations: [],
};

for (const width of [1280, 390]) test(`Q8 History stays read-only and responsive at ${width}px`, async ({ page }) => {
  await page.setViewportSize({ width, height: 844 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));

  await page.route("http://127.0.0.1:8000/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const headers = { "access-control-allow-origin": request.headers().origin || "http://127.0.0.1:3000", "access-control-allow-credentials": "true", "access-control-allow-headers": "content-type,x-gmai-role,x-gmai-user", "access-control-allow-methods": "GET,OPTIONS" };
    if (request.method() === "OPTIONS") { await route.fulfill({ status: 204, headers, body: "" }); return; }
    if (request.method() !== "GET") writes.push(request.method());
    if (path === "/health") { await route.fulfill({ status: 200, headers, contentType: "application/json", body: JSON.stringify({ status: "ok", service: "fixture", environment: "test" }) }); return; }
    if (path.endsWith("/replay/austria/latest")) { await route.fulfill({ status: 200, headers, contentType: "application/json", body: JSON.stringify({ established: true, replay }) }); return; }
    if (path.endsWith(`/replay/austria/latest/state/${firstActivity}`)) { await route.fulfill({ status: 200, headers, contentType: "application/json", body: JSON.stringify(stateFor(firstActivity)) }); return; }
    if (path.endsWith(`/replay/austria/latest/state/${secondActivity}`)) { await route.fulfill({ status: 200, headers, contentType: "application/json", body: JSON.stringify(stateFor(secondActivity)) }); return; }
    if (path.endsWith(`/replay/austria/latest/diff/${firstActivity}/${secondActivity}`)) { await route.fulfill({ status: 200, headers, contentType: "application/json", body: JSON.stringify(diff) }); return; }
    await route.fulfill({ status: 503, headers, contentType: "application/json", body: JSON.stringify({ detail: "Fixture source intentionally unavailable" }) });
  });

  await page.goto("/cockpit/v2/history");
  await expect(page.getByRole("heading", { name: "History", level: 1 })).toBeVisible();
  await expect(page.getByRole("link", { name: "History" })).toHaveAttribute("aria-current", "page");
  await expect(page.getByLabel("History replay readout")).toContainText("Returned events");
  await expect(page.getByText("Bounded replay window", { exact: true })).toBeVisible();
  await expect(page.getByText("pre_epoch_partial", { exact: true })).toBeVisible();

  const current = page.getByRole("button", { name: /Owner review recorded/ });
  await current.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { name: "Owner review recorded" })).toBeVisible();
  await expect(page.getByText("Historical reconstruction", { exact: true })).toBeVisible();
  await expect(page.getByLabel("As-of state readout")).toContainText("Work items");
  await page.getByText("Reconstruction posture", { exact: true }).click();
  await expect(page.getByText("bounded_semantic_activity", { exact: false })).toBeVisible();

  await page.getByLabel("Compare from Activity").selectOption(firstActivity);
  await expect(page.getByRole("heading", { name: "Cursor comparison" })).toBeVisible();
  await expect(page.getByLabel("Replay comparison readout")).toContainText("Changed entities");
  await page.getByText("Comparison posture", { exact: true }).click();
  await expect(page.getByText("bounded_field_delta", { exact: true })).toBeVisible();
  await expect(page.getByText("Q8 reports only the backend-proven field deltas.", { exact: false })).toBeVisible();

  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth && document.body.scrollWidth <= window.innerWidth)).toBe(true);
  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);
});