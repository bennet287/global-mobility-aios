import { expect, test } from "@playwright/test";

// Synthetic UI fixture, never professional evidence or a production seed.
const scene = {
  contract_version: "living-organization-scene.v5", generated_at: "2026-09-06T00:00:00Z", scope: "fixture", root_work_item_id: "work-1", objective_key: "fixture",
  truth: { scene_authoritative: false, renderer_authoritative: false, scene_mutations_allowed: false, canonical_authority: "Fixture records", prediction_authoritative: false, environmental_authoritative: false },
  coverage: { departments: "fixture", missions: "fixture", conversations: "unavailable", handoffs: "fixture", blockers: "fixture", human_actions: "fixture", risk_escalations: "fixture", incidents: "unavailable", smart_objects: "fixture", runtime_costs: "unavailable", presence: "not_asserted" },
  deterministic: {
    canonical_projection: true, authoritative: false,
    departments: [{ department_key: "Executive", label: "Executive", employee_count: 1, work_item_count: 1, active_blocker_count: 0, canonical_basis: "Fixture department" }],
    missions: [{ mission_key: "mission-1", objective_key: "fixture", root_work_item_id: "work-1", title: "Review fixture mission", state: "awaiting_owner", phase_key: null, participant_position_keys: ["ceo"], work_item_ids: ["work-1"], blocker_count: 0, decision_count: 0, projection_only: true, canonical_basis: "Fixture work" }],
    employees: [{ position_key: "ceo", title: "Chief Executive", department: "Executive", reports_to_position_key: null, authority_level: "L3", organization_status: "active", work_item_id: "work-1", work_status: "running", semantic_state: "awaiting_owner", presence_state: "not_asserted", state_reason: "Recorded fixture state only." }],
    work_items: [], conversations: [], handoffs: [], blockers: [], decisions: [], human_actions: [], risk_escalations: [], incidents: [], smart_objects: [], rooms: [], relationships: [],
  },
  predictive: { enabled: false, canonical_projection: false, authoritative: false, status: "unsupported", items: [] },
  environmental: { enabled: false, canonical_projection: false, authoritative: false, status: "unsupported", items: [] },
};

for (const width of [1280, 390]) test(`shared Mission and Employee primitives preserve truth and selection at ${width}px`, async ({ page }, testInfo) => {
  await page.setViewportSize({ width, height: 844 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  const writes: string[] = []; const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("http://127.0.0.1:8000/**", async (route) => {
    const request = route.request(); const path = new URL(request.url()).pathname;
    const headers = { "access-control-allow-origin": request.headers().origin || "http://127.0.0.1:3000", "access-control-allow-credentials": "true", "access-control-allow-headers": "content-type,x-gmai-role,x-gmai-user", "access-control-allow-methods": "GET,OPTIONS" };
    if (request.method() === "OPTIONS") { await route.fulfill({ status: 204, headers, body: "" }); return; }
    if (request.method() !== "GET") writes.push(request.method());
    const body = path === "/health" ? { status: "ok" } : path.endsWith("/scene/austria/latest") ? { established: true, scene } : { detail: "Unrelated fixture source unavailable" };
    await route.fulfill({ status: "detail" in body ? 503 : 200, headers, contentType: "application/json", body: JSON.stringify(body) });
  });
  await page.goto("/cockpit/v2/organization");
  await page.getByRole("button", { name: /Review fixture mission/ }).click();
  const room = page.locator(".aios-v2-mission-room");
  await expect(room.getByRole("heading", { name: "Review fixture mission" })).toBeVisible();
  await room.getByRole("button", { name: /Chief Executive/ }).click();
  const inspector = page.locator('.aios-v2-employee-inspector[data-presence-claimed="false"]');
  await expect(inspector.getByRole("heading", { name: "Chief Executive" })).toBeVisible();
  await expect(inspector.getByText("Recorded authority: L3")).toBeVisible();
  await expect(inspector.getByText("Recorded fixture state only.")).toBeVisible();
  const disclosure = inspector.locator("details");
  await expect(disclosure).not.toHaveAttribute("open", "");
  await disclosure.locator("summary").focus(); await page.keyboard.press("Enter");
  await expect(disclosure).toHaveAttribute("open", "");
  await expect(disclosure.getByText("Mutation: disabled")).toBeVisible();
  const close = inspector.getByRole("button", { name: "Close", exact: true });
  const closeBounds = await close.boundingBox();
  expect(closeBounds?.height).toBeGreaterThanOrEqual(44);
  await inspector.screenshot({ path: testInfo.outputPath(`q4-inspector-detail-${width}.png`) });
  await page.screenshot({ path: testInfo.outputPath(`q4-inspector-${width}.png`), fullPage: true });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await inspector.getByRole("button", { name: "Close", exact: true }).click();
  await expect(page.getByText("Select a rostered Mission participant to inspect canonical employee state.")).toBeVisible();
  expect(errors).toEqual([]); expect(writes).toEqual([]);
});
