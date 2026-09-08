import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, test, type Page } from "@playwright/test";

const ROOT_ID = "11111111-1111-4111-8111-111111111111";
const FIRST_ACTIVITY = "00000000-0000-0000-0000-000000000001";
const SECOND_ACTIVITY = "00000000-0000-0000-0000-000000000002";
const EVIDENCE_REF = "evidence:visual:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FINGERPRINT = "fp:q15:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";

const scene = {
  contract_version: "living-organization-scene.v5",
  generated_at: "2026-09-07T03:00:00Z",
  scope: "austria_mobility",
  root_work_item_id: ROOT_ID,
  objective_key: "q15_visual_regression",
  truth: { scene_authoritative: false, renderer_authoritative: false, scene_mutations_allowed: false, canonical_authority: "Q15 frozen visual fixture", prediction_authoritative: false, environmental_authoritative: false },
  coverage: { departments: "canonical_fixture_projection", missions: "canonical_fixture_projection", conversations: "organization_activity_conversation_lifecycle_v1", handoffs: "unavailable", blockers: "canonical_fixture_projection", human_actions: "unavailable", risk_escalations: "unavailable", incidents: "unavailable", smart_objects: "unavailable", runtime_costs: "unavailable", presence: "not_asserted" },
  deterministic: {
    canonical_projection: true,
    authoritative: false,
    departments: [{ department_key: "Global Mobility Operations", label: "Global Mobility Operations", employee_count: 1, work_item_count: 1, active_blocker_count: 0, canonical_basis: "OrganizationPosition.department + OrganizationalWorkItem.department" }],
    missions: [{ mission_key: `objective:${ROOT_ID}`, objective_key: "q15_visual_regression", root_work_item_id: ROOT_ID, title: "Austria mobility filing readiness with owner review", state: "running", phase_key: "Q15", participant_position_keys: ["mobility_operations_lead"], work_item_ids: [ROOT_ID], blocker_count: 0, decision_count: 1, projection_only: true, canonical_basis: "OrganizationalWorkItem objective_key/parent topology" }],
    employees: [{ position_key: "mobility_operations_lead", title: "Mobility Operations Lead", department: "Global Mobility Operations", reports_to_position_key: "ceo", authority_level: "L2", organization_status: "active", work_item_id: ROOT_ID, work_status: "running", semantic_state: "working", presence_state: "not_asserted", state_reason: "Canonical work is active; physical presence is not asserted." }],
    work_items: [{ work_item_id: ROOT_ID, parent_work_item_id: null, title: "Austria mobility filing readiness with owner review", objective_key: "q15_visual_regression", phase_key: "Q15", status: "running", priority: "normal", risk_level: "routine", assigned_position_key: "mobility_operations_lead", department: "Global Mobility Operations", authority_level: "L2", created_at: "2026-09-07T01:00:00Z", updated_at: "2026-09-07T03:00:00Z", due_at: null, completed_at: null, elapsed_seconds: 7200, overdue: false, specialist_evidence_valid: null, specialist_evidence_reason: null }],
    conversations: [], handoffs: [], blockers: [], human_actions: [], risk_escalations: [], incidents: [], smart_objects: [], rooms: [], relationships: [],
    decisions: [{ decision_id: "decision:q15", decision_key: "filing-authority-q15", title: "Austria filing authority", question: "Should the filing route proceed to owner review?", recommendation: "Proceed to owner review after the recorded evidence posture is inspected.", status: "awaiting_owner", authority_level: "L3", decision_owner_position: "ceo", work_item_id: ROOT_ID, evidence_items: [{ ref: EVIDENCE_REF }], record_fingerprint: FINGERPRINT, source_object_type: "WorkItem", source_object_id: ROOT_ID, source_object_version: "2", supersedes_decision_id: null, superseded_by_decision_id: null, is_current: true, required_owner_action: true, decided_at: null, created_at: "2026-09-07T02:30:00Z", superseded_by_created_at: null, superseded_in_projection_week: false }],
  },
  predictive: { enabled: false, canonical_projection: false, authoritative: false, status: "disabled_in_q15_fixture", items: [] },
  environmental: { enabled: false, canonical_projection: false, authoritative: false, status: "disabled_in_q15_fixture", items: [] },
};

const snapshot = {
  generated_at: "2026-09-07T03:00:00Z", root_work_item_id: ROOT_ID, objective_key: "q15_visual_regression", owner_position_key: "ceo", root_status: "running", cycle_status: "running", owner_synthesis_state: "pending", ready_for_owner_synthesis: false, readiness_reasons: [], authority_level: "L3", authority_posture: "recorded", autonomy_profile_state: null, provider_model_authority: false, external_action_authorized: false,
  specialist_outputs: [{ position_key: "regulatory", work_item_id: ROOT_ID, status: "completed", evidence_valid: true, evidence_reason: "Fixture evidence validated without asserting legal validity", action_output_id: null, execution_attempt_id: null, agent_run_id: null, context_hash: null, runtime_binding_hash: null, latency_ms: 10, retry_count: 0, confidence: null, provider_model_authority: false, external_action_authorized: false, runtime_quality: { contract_version: "v1", execution_mode: "fixture", provider_outcome: "ok", configured_provider: null, configured_model: null, response_provider: null, response_model: null, configured_runtime_matches_binding: null, provider_egress_occurred: null, fallback_to_template: false, prompt_tokens: null, completion_tokens: null, total_tokens: null, estimated_cost_usd: null, grounding_state: "grounded", evidence_ref_count: 1, verified_rule_ref_count: 1, source_snapshot_ref_count: 1, fresh_retrieval_provenance_present: true, provider_model_authority: false, warnings: [] } }],
  owner_synthesis: null, blockers: [], total_latency_ms: 10, max_latency_ms: 10, total_retry_count: 0, activity_count: 0, activities: [], domain_evidence_refs: [EVIDENCE_REF], verified_rule_refs: ["rule:q15:frozen-visual"], source_snapshot_refs: ["snapshot:q15:frozen-visual"],
};

const replay = {
  contract_version: "organization-replay.v1", generated_at: "2026-09-07T03:00:00Z", scope: "fixture", root_work_item_id: ROOT_ID, objective_key: "q15_visual_regression", work_item_ids: [ROOT_ID], canonical_projection: true, authoritative: false, mutations_allowed: false,
  coverage: { activity_history_basis: "persisted semantic Activity", activity_history_established: true, activity_history_coverage_start: "2026-09-06T08:30:00Z", pre_epoch_history: "partial", evidence_history: "partial", risk_escalation_history: "unsupported", source_snapshot_history: "partial", conversation_history: "unsupported" },
  total_events: 2, returned_events: 2, truncated: false,
  events: [
    { activity_id: FIRST_ACTIVITY, event_kind: "work_created", coverage_state: "pre_epoch_partial", stream_sequence: 1, activity_class: "work", activity_type: "work.created", title: "Work created", summary: "Recorded creation before established historical coverage.", actor_type: "human", actor_id: "owner", department: "Executive", position_key: "ceo", authority_level: "L3", work_item_id: ROOT_ID, source_object_type: "WorkItem", source_object_id: ROOT_ID, source_object_version: "1", correlation_key: null, causation_activity_id: null, supersedes_activity_id: null, occurred_at: "2026-09-06T08:00:00Z" },
    { activity_id: SECOND_ACTIVITY, event_kind: "decision", coverage_state: "covered", stream_sequence: 2, activity_class: "decision", activity_type: "decision.recorded", title: "Owner review recorded", summary: "Recorded decision transition with bounded semantic Activity evidence.", actor_type: "human", actor_id: "owner", department: "Executive", position_key: "ceo", authority_level: "L3", work_item_id: ROOT_ID, source_object_type: "ExecutiveDecision", source_object_id: "20000000-0000-0000-0000-000000000001", source_object_version: "2", correlation_key: "corr:q15", causation_activity_id: FIRST_ACTIVITY, supersedes_activity_id: null, occurred_at: "2026-09-06T09:00:00Z" },
  ],
};

const stateFor = (activityId: string) => ({ contract_version: "organization-replay-state.v1", generated_at: "2026-09-07T03:01:00Z", scope: "fixture", root_work_item_id: ROOT_ID, objective_key: "q15_visual_regression", cursor_activity_id: activityId, cursor_occurred_at: activityId === FIRST_ACTIVITY ? "2026-09-06T08:00:00Z" : "2026-09-06T09:00:00Z", cursor_coverage_state: activityId === FIRST_ACTIVITY ? "pre_epoch_partial" : "covered", reconstruction_posture: activityId === FIRST_ACTIVITY ? "partial_pre_epoch" : "bounded_semantic_activity", canonical_projection: true, authoritative: false, mutations_allowed: false, supported_dimensions: ["work_items", "decisions"], unsupported_dimensions: ["presence", "evidence_history"], unapplied_transition_count: 0, work_items: [{ work_item_id: ROOT_ID, status: activityId === FIRST_ACTIVITY ? "queued" : "running", priority: "normal", department: "Executive", assigned_position_key: "ceo", parent_work_item_id: null, coverage_state: activityId === FIRST_ACTIVITY ? "pre_epoch_partial" : "covered", known_from_activity_id: FIRST_ACTIVITY, last_activity_id: activityId, last_occurred_at: activityId === FIRST_ACTIVITY ? "2026-09-06T08:00:00Z" : "2026-09-06T09:00:00Z" }], blockers: [], decisions: [], human_requests: [], conversations: [] });

async function installFixture(page: Page, writes: string[]) {
  await page.route("http://127.0.0.1:8000/**", async (route) => {
    const request = route.request(); const path = new URL(request.url()).pathname;
    const headers = { "access-control-allow-origin": request.headers().origin || "http://127.0.0.1:3000", "access-control-allow-credentials": "true", "access-control-allow-headers": "content-type,x-gmai-role,x-gmai-user", "access-control-allow-methods": "GET,OPTIONS" };
    if (request.method() === "OPTIONS") { await route.fulfill({ status: 204, headers, body: "" }); return; }
    if (request.method() !== "GET") writes.push(`${request.method()} ${request.url()}`);
    const json = async (body: unknown) => route.fulfill({ status: 200, headers, contentType: "application/json", body: JSON.stringify(body) });
    if (path === "/health") return json({ status: "ok", service: "fixture", environment: "test" });
    if (path.endsWith("/scene/austria/latest")) return json({ established: true, scene });
    if (path.endsWith("/live-organization/austria/latest")) return json({ established: true, snapshot });
    if (path.endsWith("/replay/austria/latest")) return json({ established: true, replay });
    if (path.endsWith(`/replay/austria/latest/state/${FIRST_ACTIVITY}`)) return json(stateFor(FIRST_ACTIVITY));
    if (path.endsWith(`/replay/austria/latest/state/${SECOND_ACTIVITY}`)) return json(stateFor(SECOND_ACTIVITY));
    await route.fulfill({ status: 503, headers, contentType: "application/json", body: JSON.stringify({ detail: "Q15 frozen fixture leaves unrelated governed sources unavailable" }) });
  });
}

async function freezePresentation(page: Page) {
  await page.clock.setFixedTime(new Date("2026-09-07T03:00:00Z"));
  await page.emulateMedia({ colorScheme: "dark", reducedMotion: "reduce" });
  await page.addInitScript(() => window.localStorage.clear());
}

const screenshotOptions = { animations: "disabled" as const, caret: "hide" as const, maxDiffPixels: 0 };

async function baseline(page: Page, name: string, fullPage = true) {
  await expect(page).toHaveScreenshot(name, { ...screenshotOptions, fullPage });
}

test("Q15 desktop dark visual baselines are deterministic", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  const writes: string[] = [];
  await freezePresentation(page); await installFixture(page, writes);

  await page.goto("/cockpit/v2");
  await page.getByLabel("AIOS V2 theme").selectOption("dark");
  await baseline(page, "owner-home-dark-1280.png");

  await page.goto("/cockpit/v2/organization");
  await page.getByRole("radio", { name: "Structured" }).check();
  await page.getByRole("button", { name: /Mobility Operations Lead/ }).click();
  await page.getByRole("button", { name: "Close" }).scrollIntoViewIfNeeded();
  await baseline(page, "organization-structured-dark-1280.png", false);

  await page.goto("/cockpit/v2/missions");
  await page.getByRole("button", { name: /Austria mobility filing readiness/ }).click();
  const missionInspector = page.getByRole("complementary", { name: "Austria mobility filing readiness with owner review" });
  await expect(missionInspector).toBeVisible();
  await expect(missionInspector).toHaveScreenshot("missions-inspector-dark-1280.png", screenshotOptions);

  await page.goto("/cockpit/v2/evidence");
  await page.getByRole("button", { name: /evidence:visual:/ }).click();
  const evidenceInspector = page.getByRole("complementary", { name: "Domain evidence" });
  await expect(evidenceInspector).toBeVisible();
  await expect(evidenceInspector).toHaveScreenshot("evidence-inspector-dark-1280.png", screenshotOptions);

  await page.goto("/cockpit/v2/history");
  const stateResponse = page.waitForResponse((response) => response.url().endsWith(`/replay/austria/latest/state/${SECOND_ACTIVITY}`) && response.status() === 200);
  await page.getByRole("button", { name: /Owner review recorded/ }).click();
  await stateResponse;
  const historyInspector = page.getByRole("complementary", { name: "Owner review recorded" });
  await expect(historyInspector.getByText("Reconstruction posture", { exact: true })).toBeVisible();
  await expect(historyInspector.locator('[data-replay-semantic-rendering="historical-cursor"]')).toBeVisible();
  await page.waitForLoadState("networkidle");
  await page.setViewportSize({ width: 1280, height: 1600 });
  const historyBounds = await historyInspector.boundingBox();
  expect(historyBounds).not.toBeNull();
  const historyClip = {
    x: Math.floor(historyBounds!.x),
    y: Math.floor(historyBounds!.y),
    width: Math.ceil(historyBounds!.x + historyBounds!.width) - Math.floor(historyBounds!.x),
    height: Math.ceil(historyBounds!.y + historyBounds!.height) - Math.floor(historyBounds!.y),
  };
  const historyActualPath = testInfo.outputPath("history-replay-dark-1280-actual.png");
  const historyScreenshot = await page.screenshot({ animations: "disabled", caret: "hide", clip: historyClip, path: historyActualPath });
  const historyDigestPath = resolve(process.cwd(), "tests", "aios-v2-visual-regression.spec.ts-snapshots", "history-replay-dark-1280-chromium-linux.sha256");
  const expectedHistoryDigest = readFileSync(historyDigestPath, "utf8").trim();
  const actualHistoryDigest = createHash("sha256").update(historyScreenshot).digest("hex");
  expect(actualHistoryDigest, "History screenshot SHA-256 must match committed Linux visual baseline digest").toBe(expectedHistoryDigest);

  expect(writes).toEqual([]);
});

test("Q15 desktop light decision baseline is deterministic", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  const writes: string[] = [];
  await freezePresentation(page); await installFixture(page, writes);
  await page.goto("/cockpit/v2/decisions");
  await page.getByLabel("AIOS V2 theme").selectOption("light");
  await page.getByRole("button", { name: /Austria filing authority/ }).click();
  const decisionInspector = page.getByRole("complementary", { name: "Austria filing authority" });
  await expect(decisionInspector.getByText("Recorded recommendation", { exact: true })).toBeVisible();
  await expect(decisionInspector).toHaveScreenshot("decisions-inspector-light-1280.png", screenshotOptions);
  expect(writes).toEqual([]);
});

test("Q15 phone Owner Home baseline is deterministic", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const writes: string[] = [];
  await freezePresentation(page); await installFixture(page, writes);
  await page.goto("/cockpit/v2");
  await page.getByLabel("AIOS V2 theme").selectOption("dark");
  await baseline(page, "owner-home-dark-390.png");
  expect(writes).toEqual([]);
});