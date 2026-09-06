import { expect, test } from "@playwright/test";

const scene = {
  contract_version: "living-organization-scene.v5",
  generated_at: "2026-09-06T02:00:00Z",
  scope: "fixture",
  root_work_item_id: "work:root",
  objective_key: "fixture",
  truth: { scene_authoritative: false, renderer_authoritative: false, scene_mutations_allowed: false, canonical_authority: "Fixture canonical source", prediction_authoritative: false, environmental_authoritative: false },
  coverage: { departments: "fixture", missions: "fixture", conversations: "unavailable", handoffs: "fixture", blockers: "fixture", human_actions: "unavailable", risk_escalations: "unavailable", incidents: "unavailable", smart_objects: "unavailable", runtime_costs: "unavailable", presence: "not_asserted" },
  deterministic: { canonical_projection: true, authoritative: false, departments: [{ department_key: "Operations", label: "Operations", employee_count: 2, work_item_count: 2, active_blocker_count: 2, canonical_basis: "fixture" }], missions: [{ mission_key: "mission:a", objective_key: "fixture", root_work_item_id: "work:root", title: "Austria filing", state: "running", phase_key: "review", participant_position_keys: ["ops"], work_item_ids: ["work:root"], blocker_count: 1, decision_count: 1, projection_only: true, canonical_basis: "fixture" }], employees: [], work_items: [], conversations: [], handoffs: [], blockers: [], decisions: [], human_actions: [], risk_escalations: [], incidents: [], smart_objects: [], rooms: [], relationships: [] },
  predictive: { enabled: false, canonical_projection: false, authoritative: false, status: "unsupported", items: [] },
  environmental: { enabled: false, canonical_projection: false, authoritative: false, status: "unsupported", items: [] },
};

const snapshot = {
  generated_at: "2026-09-06T02:00:00Z", root_work_item_id: "work:root", objective_key: "fixture", owner_position_key: "ceo", root_status: "running", cycle_status: "running", owner_synthesis_state: "pending", ready_for_owner_synthesis: false, readiness_reasons: [], authority_level: "L3", authority_posture: "recorded", autonomy_profile_state: null, provider_model_authority: false, external_action_authorized: false,
  specialist_outputs: [{ position_key: "regulatory", work_item_id: "work:reg", status: "completed", evidence_valid: true, evidence_reason: "Fixture evidence validated", action_output_id: null, execution_attempt_id: null, agent_run_id: null, context_hash: null, runtime_binding_hash: null, latency_ms: 10, retry_count: 0, confidence: null, provider_model_authority: false, external_action_authorized: false, runtime_quality: { contract_version: "v1", execution_mode: "fixture", provider_outcome: "ok", configured_provider: null, configured_model: null, response_provider: null, response_model: null, configured_runtime_matches_binding: null, provider_egress_occurred: null, fallback_to_template: false, prompt_tokens: null, completion_tokens: null, total_tokens: null, estimated_cost_usd: null, grounding_state: "grounded", evidence_ref_count: 2, verified_rule_ref_count: 1, source_snapshot_ref_count: 1, fresh_retrieval_provenance_present: true, provider_model_authority: false, warnings: [] } }],
  owner_synthesis: null, blockers: [], total_latency_ms: 10, max_latency_ms: 10, total_retry_count: 0, activity_count: 0, activities: [], domain_evidence_refs: ["evidence:a", "evidence:b"], verified_rule_refs: ["rule:a"], source_snapshot_refs: ["snapshot:a"],
};

const memory = {
  contract_version: "memory.v1", generated_at: "2026-09-06T02:02:00Z", scope: "fixture", root_work_item_id: "work:root", objective_key: "fixture", source_contract_version: "replay.v1", canonical_projection: true, authoritative: false, predictive: false, mutations_allowed: false, visualization_only: true, window_event_count: 9, window_start: "2026-09-05T00:00:00Z", window_end: "2026-09-06T00:00:00Z", coverage: { activity_history_basis: "fixture", activity_history_established: true, activity_history_coverage_start: "2026-09-05T00:00:00Z", pre_epoch_history: "partial", bounded_replay_window: "fixture", replay_truncated: false, path_history: "covered" }, kind_aggregates: [{ event_kind: "handoff", event_count: 4 }], path_frequencies: [{ previous_position_key: "regulatory", assigned_position_key: "ops", handoff_count: 2, work_item_count: 2, first_occurred_at: "2026-09-05T00:00:00Z", last_occurred_at: "2026-09-06T00:00:00Z", coverage_state: "covered" }], heat_cells: [], timeline: [{ bucket_start: "2026-09-06T00:00:00Z", event_count: 9, handoff_count: 2, blocker_count: 1, decision_count: 1, conversation_count: 0, coverage_state: "covered" }], unsupported_dimensions: ["presence"],
};

async function installFixture(page, writes: string[]) {
  await page.route("http://127.0.0.1:8000/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const headers = { "access-control-allow-origin": request.headers().origin || "http://127.0.0.1:3000", "access-control-allow-credentials": "true", "access-control-allow-headers": "content-type,x-gmai-role,x-gmai-user", "access-control-allow-methods": "GET,OPTIONS" };
    if (request.method() === "OPTIONS") { await route.fulfill({ status: 204, headers, body: "" }); return; }
    if (request.method() !== "GET") writes.push(request.method());
    if (path === "/health") { await route.fulfill({ status: 200, headers, contentType: "application/json", body: JSON.stringify({ status: "ok", service: "fixture", environment: "test" }) }); return; }
    if (path.endsWith("/environmental-memory/austria/latest")) { await route.fulfill({ status: 200, headers, contentType: "application/json", body: JSON.stringify({ established: true, memory }) }); return; }
    if (path.endsWith("/scene/austria/latest")) { await route.fulfill({ status: 200, headers, contentType: "application/json", body: JSON.stringify({ established: true, scene }) }); return; }
    if (path.endsWith("/live-organization/austria/latest")) { await route.fulfill({ status: 200, headers, contentType: "application/json", body: JSON.stringify({ established: true, snapshot }) }); return; }
    await route.fulfill({ status: 503, headers, contentType: "application/json", body: JSON.stringify({ detail: "Fixture source intentionally unavailable" }) });
  });
}

for (const width of [1280, 390]) {
  test(`Q6 Evidence remains inspection-only at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await page.emulateMedia({ reducedMotion: "reduce" });
    const writes: string[] = []; const pageErrors: string[] = [];
    page.on("pageerror", (error) => pageErrors.push(error.message));
    await installFixture(page, writes);
    await page.goto("/cockpit/v2/evidence");
    await expect(page.getByRole("heading", { name: "Evidence", level: 1 })).toBeVisible();
    await expect(page.getByRole("link", { name: "Evidence" })).toHaveAttribute("aria-current", "page");
    await expect(page.getByRole("link", { name: "History" })).toHaveAttribute("href", "/cockpit/v2/history");
    await expect(page.getByLabel("Evidence ledger readout")).toContainText("Domain evidence refs");
    await expect(page.getByText("evidence:a", { exact: true })).toBeVisible();
    const reference = page.getByRole("button", { name: /evidence:a/ });
    await reference.focus(); await page.keyboard.press("Enter");
    await expect(page.getByRole("heading", { name: "Domain evidence" })).toBeVisible();
    const disclosure = page.getByText("Reference identity", { exact: true });
    await disclosure.focus(); await page.keyboard.press("Enter");
    await expect(page.getByText("No source text, approval, freshness or legal conclusion is inferred")).toBeVisible();
    await expect(page.getByText("evidence_valid=true")).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth && document.body.scrollWidth <= window.innerWidth)).toBe(true);
    expect(writes).toEqual([]); expect(pageErrors).toEqual([]);
  });

  test(`Q6 Intelligence separates current signals from aggregate memory at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await page.emulateMedia({ reducedMotion: "reduce" });
    const writes: string[] = []; const pageErrors: string[] = [];
    page.on("pageerror", (error) => pageErrors.push(error.message));
    await installFixture(page, writes);
    await page.goto("/cockpit/v2/intelligence");
    await expect(page.getByRole("heading", { name: "Intelligence", level: 1 })).toBeVisible();
    await expect(page.getByRole("link", { name: "Intelligence" })).toHaveAttribute("aria-current", "page");
    await expect(page.getByText("Partial current-source coverage")).toBeVisible();
    await expect(page.getByLabel("Current intelligence readout")).toContainText("Projected Missions");
    await expect(page.getByText("Aggregate memory", { exact: true })).toBeVisible();
    await expect(page.getByLabel("Aggregate memory readout")).toContainText("Window events");
    await expect(page.getByText("handoff", { exact: true })).toBeVisible();
    const posture = page.getByText("Aggregate-memory truth posture", { exact: true });
    await posture.focus(); await page.keyboard.press("Enter");
    await expect(page.getByText("This is assignment lineage, not physical movement.")).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth && document.body.scrollWidth <= window.innerWidth)).toBe(true);
    expect(writes).toEqual([]); expect(pageErrors).toEqual([]);
  });
}
