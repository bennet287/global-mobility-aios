import { expect, test } from "@playwright/test";

const ZOOM_EQUIVALENT_WIDTH = 640;
const ROOT_ID = "11111111-1111-4111-8111-111111111111";
const FIRST_ACTIVITY = "00000000-0000-0000-0000-000000000001";
const SECOND_ACTIVITY = "00000000-0000-0000-0000-000000000002";
const LONG_EVIDENCE_REF = "evidence:zoom:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const LONG_FINGERPRINT = "fp:q14:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const DECISION_TITLE = "Austria filing authority with extended owner-review provenance";
const backgrounds = ["canvas", "canvas-soft", "surface", "surface-raised", "surface-inset"] as const;
const foregrounds = ["text", "text-muted", "text-soft", "accent", "technology", "regulatory", "operations", "security", "success", "warning", "critical", "info"] as const;

const scene = {
  contract_version: "living-organization-scene.v5",
  generated_at: "2026-09-07T03:00:00Z",
  scope: "austria_mobility",
  root_work_item_id: ROOT_ID,
  objective_key: "q14_zoom_contrast",
  truth: { scene_authoritative: false, renderer_authoritative: false, scene_mutations_allowed: false, canonical_authority: "Q14 accepted-fixture projection", prediction_authoritative: false, environmental_authoritative: false },
  coverage: { departments: "canonical_fixture_projection", missions: "canonical_fixture_projection", conversations: "unavailable", handoffs: "unavailable", blockers: "canonical_fixture_projection", human_actions: "unavailable", risk_escalations: "unavailable", incidents: "unavailable", smart_objects: "unavailable", runtime_costs: "unavailable", presence: "not_asserted" },
  deterministic: {
    canonical_projection: true,
    authoritative: false,
    departments: [{ department_key: "Global Mobility Operations", label: "Global Mobility Operations", employee_count: 1, work_item_count: 1, active_blocker_count: 0, canonical_basis: "OrganizationPosition.department + OrganizationalWorkItem.department" }],
    missions: [{ mission_key: `objective:${ROOT_ID}`, objective_key: "q14_zoom_contrast", root_work_item_id: ROOT_ID, title: "Structured fallback proof mission with a deliberately long governed title", state: "running", phase_key: "Q14", participant_position_keys: ["mobility_operations_lead"], work_item_ids: [ROOT_ID], blocker_count: 0, decision_count: 1, projection_only: true, canonical_basis: "OrganizationalWorkItem objective_key/parent topology" }],
    employees: [{ position_key: "mobility_operations_lead", title: "Mobility Operations Lead", department: "Global Mobility Operations", reports_to_position_key: "ceo", authority_level: "L2", organization_status: "active", work_item_id: ROOT_ID, work_status: "running", semantic_state: "working", presence_state: "not_asserted", state_reason: "Canonical work is active; physical presence is not asserted." }],
    work_items: [{ work_item_id: ROOT_ID, parent_work_item_id: null, title: "Structured fallback proof mission with a deliberately long governed title", objective_key: "q14_zoom_contrast", phase_key: "Q14", status: "running", priority: "normal", risk_level: "routine", assigned_position_key: "mobility_operations_lead", department: "Global Mobility Operations", authority_level: "L2", created_at: "2026-09-07T01:00:00Z", updated_at: "2026-09-07T03:00:00Z", due_at: null, completed_at: null, elapsed_seconds: 7200, overdue: false, specialist_evidence_valid: null, specialist_evidence_reason: null }],
    conversations: [], handoffs: [], blockers: [], human_actions: [], risk_escalations: [], incidents: [], smart_objects: [], rooms: [], relationships: [],
    decisions: [
      { decision_id: "decision:current", decision_key: "filing-authority-q14", title: DECISION_TITLE, question: "Should the filing route proceed to owner review after the recorded evidence posture is inspected?", recommendation: "Proceed to owner review after the recorded evidence posture is inspected; this long recommendation must reflow without changing authority semantics.", status: "awaiting_owner", authority_level: "L3", decision_owner_position: "ceo", work_item_id: ROOT_ID, evidence_items: [{ ref: LONG_EVIDENCE_REF }], record_fingerprint: LONG_FINGERPRINT, source_object_type: "WorkItem", source_object_id: ROOT_ID, source_object_version: "2", supersedes_decision_id: "decision:old", superseded_by_decision_id: null, is_current: true, required_owner_action: true, decided_at: null, created_at: "2026-09-07T02:30:00Z", superseded_by_created_at: null, superseded_in_projection_week: false },
      { decision_id: "decision:old", decision_key: "filing-authority-q14-old", title: "Earlier filing authority", question: "Earlier question", recommendation: "Earlier recommendation", status: "superseded", authority_level: "L2", decision_owner_position: "ceo", work_item_id: ROOT_ID, evidence_items: [], record_fingerprint: "fp:q14:old", source_object_type: "WorkItem", source_object_id: ROOT_ID, source_object_version: "1", supersedes_decision_id: null, superseded_by_decision_id: "decision:current", is_current: false, required_owner_action: false, decided_at: "2026-09-06T03:00:00Z", created_at: "2026-09-06T02:00:00Z", superseded_by_created_at: "2026-09-07T02:30:00Z", superseded_in_projection_week: true },
    ],
  },
  predictive: { enabled: false, canonical_projection: false, authoritative: false, status: "disabled_in_q14_fixture", items: [] },
  environmental: { enabled: false, canonical_projection: false, authoritative: false, status: "disabled_in_q14_fixture", items: [] },
};

const snapshot = {
  generated_at: "2026-09-07T03:00:00Z", root_work_item_id: ROOT_ID, objective_key: "q14_zoom_contrast", owner_position_key: "ceo", root_status: "running", cycle_status: "running", owner_synthesis_state: "pending", ready_for_owner_synthesis: false, readiness_reasons: [], authority_level: "L3", authority_posture: "recorded", autonomy_profile_state: null, provider_model_authority: false, external_action_authorized: false,
  specialist_outputs: [{ position_key: "regulatory", work_item_id: ROOT_ID, status: "completed", evidence_valid: true, evidence_reason: "Fixture evidence validated without asserting legal validity", action_output_id: null, execution_attempt_id: null, agent_run_id: null, context_hash: null, runtime_binding_hash: null, latency_ms: 10, retry_count: 0, confidence: null, provider_model_authority: false, external_action_authorized: false, runtime_quality: { contract_version: "v1", execution_mode: "fixture", provider_outcome: "ok", configured_provider: null, configured_model: null, response_provider: null, response_model: null, configured_runtime_matches_binding: null, provider_egress_occurred: null, fallback_to_template: false, prompt_tokens: null, completion_tokens: null, total_tokens: null, estimated_cost_usd: null, grounding_state: "grounded", evidence_ref_count: 1, verified_rule_ref_count: 1, source_snapshot_ref_count: 1, fresh_retrieval_provenance_present: true, provider_model_authority: false, warnings: [] } }],
  owner_synthesis: null, blockers: [], total_latency_ms: 10, max_latency_ms: 10, total_retry_count: 0, activity_count: 0, activities: [], domain_evidence_refs: [LONG_EVIDENCE_REF], verified_rule_refs: ["rule:q14:long-reference-proof"], source_snapshot_refs: ["snapshot:q14:long-reference-proof"],
};

const replay = {
  contract_version: "organization-replay.v1", generated_at: "2026-09-07T03:00:00Z", scope: "fixture", root_work_item_id: ROOT_ID, objective_key: "q14_zoom_contrast", work_item_ids: [ROOT_ID], canonical_projection: true, authoritative: false, mutations_allowed: false,
  coverage: { activity_history_basis: "persisted semantic Activity", activity_history_established: true, activity_history_coverage_start: "2026-09-06T08:30:00Z", pre_epoch_history: "partial", evidence_history: "partial", risk_escalation_history: "unsupported", source_snapshot_history: "partial", conversation_history: "unsupported" },
  total_events: 2, returned_events: 2, truncated: false,
  events: [
    { activity_id: FIRST_ACTIVITY, event_kind: "work_created", coverage_state: "pre_epoch_partial", stream_sequence: 1, activity_class: "work", activity_type: "work.created", title: "Work created", summary: "Recorded creation before the established coverage epoch with a long but truthful summary that must reflow.", actor_type: "human", actor_id: "owner", department: "Executive", position_key: "ceo", authority_level: "L3", work_item_id: ROOT_ID, source_object_type: "WorkItem", source_object_id: ROOT_ID, source_object_version: "1", correlation_key: null, causation_activity_id: null, supersedes_activity_id: null, occurred_at: "2026-09-06T08:00:00Z" },
    { activity_id: SECOND_ACTIVITY, event_kind: "decision", coverage_state: "covered", stream_sequence: 2, activity_class: "decision", activity_type: "decision.recorded", title: "Owner review recorded", summary: "Recorded Decision state transition with bounded semantic Activity evidence.", actor_type: "human", actor_id: "owner", department: "Executive", position_key: "ceo", authority_level: "L3", work_item_id: ROOT_ID, source_object_type: "ExecutiveDecision", source_object_id: "20000000-0000-0000-0000-000000000001", source_object_version: "2", correlation_key: "corr:q14:long-correlation-key-proof", causation_activity_id: FIRST_ACTIVITY, supersedes_activity_id: null, occurred_at: "2026-09-06T09:00:00Z" },
  ],
};

const stateFor = (activityId: string) => ({
  contract_version: "organization-replay-state.v1", generated_at: "2026-09-07T03:01:00Z", scope: "fixture", root_work_item_id: ROOT_ID, objective_key: "q14_zoom_contrast", cursor_activity_id: activityId, cursor_occurred_at: activityId === FIRST_ACTIVITY ? "2026-09-06T08:00:00Z" : "2026-09-06T09:00:00Z", cursor_coverage_state: activityId === FIRST_ACTIVITY ? "pre_epoch_partial" : "covered", reconstruction_posture: activityId === FIRST_ACTIVITY ? "partial_pre_epoch" : "bounded_semantic_activity", canonical_projection: true, authoritative: false, mutations_allowed: false, supported_dimensions: ["work_items", "decisions"], unsupported_dimensions: ["presence", "evidence_history"], unapplied_transition_count: activityId === FIRST_ACTIVITY ? 1 : 0,
  work_items: [{ work_item_id: ROOT_ID, status: activityId === FIRST_ACTIVITY ? "queued" : "running", priority: "normal", department: "Executive", assigned_position_key: "ceo", parent_work_item_id: null, coverage_state: activityId === FIRST_ACTIVITY ? "pre_epoch_partial" : "covered", known_from_activity_id: FIRST_ACTIVITY, last_activity_id: activityId, last_occurred_at: activityId === FIRST_ACTIVITY ? "2026-09-06T08:00:00Z" : "2026-09-06T09:00:00Z" }], blockers: [], decisions: [], human_requests: [], conversations: [],
});

function luminance(hex: string): number {
  const raw = hex.trim().replace(/^#/, "");
  const normalized = raw.length === 3 ? raw.split("").map((channel) => channel + channel).join("") : raw;
  if (!/^[0-9a-f]{6}$/i.test(normalized)) throw new Error(`Q14 contrast helper expected 3- or 6-digit hex, received ${hex}`);
  const channels = normalized.match(/../g)!.map((channel) => parseInt(channel, 16) / 255);
  return channels.map((channel) => channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4).reduce((sum, channel, index) => sum + channel * [0.2126, 0.7152, 0.0722][index], 0);
}

function contrastRatio(a: string, b: string): number {
  const first = luminance(a); const second = luminance(b);
  return (Math.max(first, second) + 0.05) / (Math.min(first, second) + 0.05);
}

async function installReadOnlyFixture(page: import("@playwright/test").Page, writes: string[]) {
  await page.route("http://127.0.0.1:8000/**", async (route) => {
    const request = route.request(); const path = new URL(request.url()).pathname;
    const headers = { "access-control-allow-origin": request.headers().origin || "http://127.0.0.1:3000", "access-control-allow-credentials": "true", "access-control-allow-headers": "content-type,x-gmai-role,x-gmai-user", "access-control-allow-methods": "GET,OPTIONS" };
    if (request.method() === "OPTIONS") { await route.fulfill({ status: 204, headers, body: "" }); return; }
    if (request.method() !== "GET") writes.push(`${request.method()} ${request.url()}`);
    if (path === "/health") { await route.fulfill({ status: 200, headers, contentType: "application/json", body: JSON.stringify({ status: "ok", service: "fixture", environment: "test" }) }); return; }
    if (path.endsWith("/scene/austria/latest")) { await route.fulfill({ status: 200, headers, contentType: "application/json", body: JSON.stringify({ established: true, scene }) }); return; }
    if (path.endsWith("/live-organization/austria/latest")) { await route.fulfill({ status: 200, headers, contentType: "application/json", body: JSON.stringify({ established: true, snapshot }) }); return; }
    if (path.endsWith("/replay/austria/latest")) { await route.fulfill({ status: 200, headers, contentType: "application/json", body: JSON.stringify({ established: true, replay }) }); return; }
    if (path.endsWith(`/replay/austria/latest/state/${FIRST_ACTIVITY}`)) { await route.fulfill({ status: 200, headers, contentType: "application/json", body: JSON.stringify(stateFor(FIRST_ACTIVITY)) }); return; }
    if (path.endsWith(`/replay/austria/latest/state/${SECOND_ACTIVITY}`)) { await route.fulfill({ status: 200, headers, contentType: "application/json", body: JSON.stringify(stateFor(SECOND_ACTIVITY)) }); return; }
    await route.fulfill({ status: 503, headers, contentType: "application/json", body: JSON.stringify({ detail: "Q14 fixture intentionally leaves unrelated governed sources unavailable" }) });
  });
}

async function computedPalette(page: import("@playwright/test").Page) {
  return page.locator(".aios-v2-root").evaluate((element) => {
    const styles = getComputedStyle(element);
    const names = ["canvas", "canvas-soft", "surface", "surface-raised", "surface-inset", "text", "text-muted", "text-soft", "accent", "technology", "regulatory", "operations", "security", "success", "warning", "critical", "info"];
    return Object.fromEntries(names.map((name) => [name, styles.getPropertyValue(`--aios-v2-color-${name}`).trim().toLowerCase()]));
  });
}

async function expectNoPageOverflow(page: import("@playwright/test").Page) {
  const geometry = await page.evaluate(() => {
    const root = document.querySelector<HTMLElement>(".aios-v2-root"); const main = document.querySelector<HTMLElement>(".aios-v2-main");
    if (!root || !main) return null;
    const mainRect = main.getBoundingClientRect();
    return { viewport: window.innerWidth, documentWidth: document.documentElement.scrollWidth, bodyWidth: document.body.scrollWidth, rootWidth: root.scrollWidth, mainLeft: mainRect.left, mainRight: mainRect.right };
  });
  expect(geometry).not.toBeNull();
  expect(geometry!.documentWidth).toBeLessThanOrEqual(geometry!.viewport + 1);
  expect(geometry!.bodyWidth).toBeLessThanOrEqual(geometry!.viewport + 1);
  expect(geometry!.rootWidth).toBeLessThanOrEqual(geometry!.viewport + 1);
  expect(geometry!.mainLeft).toBeGreaterThanOrEqual(-1);
  expect(geometry!.mainRight).toBeLessThanOrEqual(geometry!.viewport + 1);
}

for (const theme of ["dark", "light"] as const) {
  test(`Q14 ${theme} palette and populated 200% browser zoom/reflow equivalent remain usable`, async ({ page }) => {
    // 1280px desktop at 200% browser zoom exposes roughly a 640 CSS-pixel layout width.
    // The 640px effective viewport exercises the same media-query/reflow pressure without CSS-transform approximations.
    await page.setViewportSize({ width: ZOOM_EQUIVALENT_WIDTH, height: 844 });
    await page.emulateMedia({ colorScheme: theme, reducedMotion: "reduce" });
    const writes: string[] = []; const pageErrors: string[] = [];
    page.on("pageerror", (error) => pageErrors.push(error.message));
    await installReadOnlyFixture(page, writes);

    await page.goto("/cockpit/v2");
    const root = page.locator(".aios-v2-root"); const themeControl = page.getByLabel("AIOS V2 theme");
    await themeControl.selectOption(theme); await expect(root).toHaveAttribute("data-theme", theme);
    const palette = await computedPalette(page);
    for (const foreground of foregrounds) for (const background of backgrounds) expect(contrastRatio(palette[foreground], palette[background]), `${theme} ${foreground} on ${background}`).toBeGreaterThanOrEqual(4.5);
    await expectNoPageOverflow(page);

    await page.goto("/cockpit/v2/organization");
    await page.getByRole("radio", { name: "Structured" }).check();
    const employee = page.getByRole("button", { name: /Mobility Operations Lead/ });
    await expect(employee).toBeVisible(); await employee.click();
    await expect(page.getByText("Roster identity is not physical presence.", { exact: true }).first()).toBeVisible();
    await expectNoPageOverflow(page);

    await page.goto("/cockpit/v2/missions");
    const mission = page.getByRole("button", { name: /Structured fallback proof mission/ });
    await expect(mission).toBeVisible(); await mission.click();
    const missionProvenance = page.getByText("Mission provenance", { exact: true });
    await missionProvenance.focus(); await page.keyboard.press("Enter");
    await expect(page.getByText(ROOT_ID, { exact: true })).toBeVisible();
    await expectNoPageOverflow(page);

    await page.goto("/cockpit/v2/evidence");
    await expect(page.getByText(LONG_EVIDENCE_REF, { exact: true })).toBeVisible();
    const evidence = page.getByRole("button", { name: /evidence:zoom:/ });
    await evidence.focus(); await page.keyboard.press("Enter");
    const identity = page.getByText("Reference identity", { exact: true });
    await identity.focus(); await page.keyboard.press("Enter");
    await expect(page.getByText(LONG_EVIDENCE_REF, { exact: true }).last()).toBeVisible();
    await expectNoPageOverflow(page);

    await page.goto("/cockpit/v2/decisions");
    const decision = page.getByRole("button", { name: /Austria filing authority/ });
    await expect(decision).toBeVisible(); await decision.click();
    const decisionProvenance = page.getByText("Decision provenance & supersession", { exact: true });
    await decisionProvenance.focus(); await page.keyboard.press("Enter");
    await expect(page.getByText(LONG_FINGERPRINT, { exact: true })).toBeVisible();
    await expectNoPageOverflow(page);

    await page.goto("/cockpit/v2/history");
    const event = page.getByRole("button", { name: /Owner review recorded/ });
    await expect(event).toBeVisible(); await event.click();
    await expect(page.getByText("Historical reconstruction", { exact: true })).toBeVisible();
    await expect(page.getByLabel("As-of state readout")).toContainText("Work items");
    await expectNoPageOverflow(page);

    expect(writes).toEqual([]); expect(pageErrors).toEqual([]);
  });
}
