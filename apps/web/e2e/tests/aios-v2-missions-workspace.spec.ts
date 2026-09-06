import { expect, test } from "@playwright/test";

const scene = {
  contract_version: "living-organization-scene.v5",
  generated_at: "2026-09-06T01:00:00Z",
  scope: "fixture",
  root_work_item_id: "work:alpha",
  objective_key: "fixture",
  truth: { scene_authoritative: false, renderer_authoritative: false, scene_mutations_allowed: false, canonical_authority: "Fixture canonical source", prediction_authoritative: false, environmental_authoritative: false },
  coverage: { departments: "fixture", missions: "fixture", conversations: "unavailable", handoffs: "fixture", blockers: "fixture", human_actions: "unavailable", risk_escalations: "unavailable", incidents: "unavailable", smart_objects: "unavailable", runtime_costs: "unavailable", presence: "not_asserted" },
  deterministic: {
    canonical_projection: true,
    authoritative: false,
    departments: [{ department_key: "Executive", label: "Executive", employee_count: 3, work_item_count: 2, active_blocker_count: 1, canonical_basis: "Fixture department" }],
    missions: [
      { mission_key: "mission:alpha", objective_key: "fixture-alpha", root_work_item_id: "work:alpha", title: "Alpha evidence review", state: "awaiting_owner", phase_key: "review", participant_position_keys: ["ceo", "cto"], work_item_ids: ["work:alpha"], blocker_count: 1, decision_count: 1, projection_only: true, canonical_basis: "Fixture Mission alpha" },
      { mission_key: "mission:beta", objective_key: "fixture-beta", root_work_item_id: "work:beta", title: "Beta filing", state: "queued", phase_key: null, participant_position_keys: ["ops"], work_item_ids: ["work:beta"], blocker_count: 0, decision_count: 0, projection_only: true, canonical_basis: "Fixture Mission beta" },
    ],
    employees: [
      { position_key: "ceo", title: "Chief Executive", department: "Executive", reports_to_position_key: null, authority_level: "L3", organization_status: "active", work_item_id: "work:alpha", work_status: "running", semantic_state: "awaiting_owner", presence_state: "not_asserted", state_reason: "Fixture" },
      { position_key: "cto", title: "Technical Officer", department: "Technology", reports_to_position_key: "ceo", authority_level: "L2", organization_status: "active", work_item_id: "work:alpha", work_status: "running", semantic_state: "working", presence_state: "not_asserted", state_reason: "Fixture" },
      { position_key: "ops", title: "Operations Officer", department: "Operations", reports_to_position_key: "ceo", authority_level: "L1", organization_status: "active", work_item_id: "work:beta", work_status: "queued", semantic_state: "queued", presence_state: "not_asserted", state_reason: "Fixture" },
    ],
    work_items: [], conversations: [], handoffs: [], blockers: [], decisions: [], human_actions: [], risk_escalations: [], incidents: [], smart_objects: [], rooms: [], relationships: [],
  },
  predictive: { enabled: false, canonical_projection: false, authoritative: false, status: "unsupported", items: [] },
  environmental: { enabled: false, canonical_projection: false, authoritative: false, status: "unsupported", items: [] },
};

for (const width of [1280, 390]) test(`Q5 Missions stays read-only and responsive at ${width}px`, async ({ page }) => {
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
    if (path.endsWith("/scene/austria/latest")) { await route.fulfill({ status: 200, headers, contentType: "application/json", body: JSON.stringify({ established: true, scene }) }); return; }
    await route.fulfill({ status: 503, headers, contentType: "application/json", body: JSON.stringify({ detail: "Fixture source intentionally unavailable" }) });
  });

  await page.goto("/cockpit/v2/missions");
  await expect(page.getByRole("heading", { name: "Missions", level: 1 })).toBeVisible();
  await expect(page.getByRole("link", { name: "Missions" })).toHaveAttribute("aria-current", "page");
  await expect(page.getByRole("link", { name: "History" })).toHaveAttribute("href", "/cockpit/v2/history");
  await expect(page.getByText("Alpha evidence review")).toBeVisible();
  await expect(page.getByText("Beta filing")).toBeVisible();
  await expect(page.getByLabel("Mission portfolio readout")).toContainText("Rostered participants");
  await expect(page.getByText("Partial Owner source coverage")).toBeVisible();

  const alpha = page.getByRole("button", { name: /Alpha evidence review/ });
  await alpha.click();
  await expect(page.getByRole("heading", { name: "Alpha evidence review" })).toBeVisible();
  const provenance = page.getByText("Mission provenance", { exact: true });
  await provenance.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByText("work:alpha")).toBeVisible();
  await expect(page.getByText("Fixture Mission alpha")).toBeVisible();
  await page.getByRole("button", { name: "Close Alpha evidence review" }).click();

  const beta = page.getByRole("button", { name: /Beta filing/ });
  await beta.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { name: "Beta filing" })).toBeVisible();

  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth && document.body.scrollWidth <= window.innerWidth)).toBe(true);
  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);
});
