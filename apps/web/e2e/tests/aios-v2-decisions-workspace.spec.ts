import { expect, test } from "@playwright/test";

const scene = {
  contract_version: "living-organization-scene.v5",
  generated_at: "2026-09-06T03:30:00Z",
  scope: "fixture",
  root_work_item_id: "work:root",
  objective_key: "fixture",
  truth: { scene_authoritative: false, renderer_authoritative: false, scene_mutations_allowed: false, canonical_authority: "Fixture canonical source", prediction_authoritative: false, environmental_authoritative: false },
  coverage: { departments: "fixture", missions: "fixture", conversations: "unavailable", handoffs: "fixture", blockers: "fixture", human_actions: "unavailable", risk_escalations: "unavailable", incidents: "unavailable", smart_objects: "unavailable", runtime_costs: "unavailable", presence: "not_asserted" },
  deterministic: {
    canonical_projection: true,
    authoritative: false,
    departments: [], missions: [], employees: [], work_items: [], conversations: [], handoffs: [], blockers: [], human_actions: [], risk_escalations: [], incidents: [], smart_objects: [], rooms: [], relationships: [],
    decisions: [
      {
        decision_id: "decision:current", decision_key: "filing-authority-v2", title: "Austria filing authority", question: "Should the filing route proceed to owner review?", recommendation: "Proceed to owner review after the recorded evidence posture is inspected.", status: "awaiting_owner", authority_level: "L3", decision_owner_position: "ceo", work_item_id: "work:root", evidence_items: [{ ref: "evidence:a" }, { ref: "rule:a" }], record_fingerprint: "fp:current", source_object_type: "WorkItem", source_object_id: "work:root", source_object_version: "2", supersedes_decision_id: "decision:old", superseded_by_decision_id: null, is_current: true, required_owner_action: true, decided_at: null, created_at: "2026-09-06T03:00:00Z", superseded_by_created_at: null, superseded_in_projection_week: false,
      },
      {
        decision_id: "decision:old", decision_key: "filing-authority-v1", title: "Earlier filing authority", question: "Earlier question", recommendation: "Earlier recommendation", status: "superseded", authority_level: "L2", decision_owner_position: "ceo", work_item_id: "work:root", evidence_items: [], record_fingerprint: "fp:old", source_object_type: "WorkItem", source_object_id: "work:root", source_object_version: "1", supersedes_decision_id: null, superseded_by_decision_id: "decision:current", is_current: false, required_owner_action: false, decided_at: "2026-09-05T03:00:00Z", created_at: "2026-09-05T02:00:00Z", superseded_by_created_at: "2026-09-06T03:00:00Z", superseded_in_projection_week: true,
      },
    ],
  },
  predictive: { enabled: false, canonical_projection: false, authoritative: false, status: "unsupported", items: [] },
  environmental: { enabled: false, canonical_projection: false, authoritative: false, status: "unsupported", items: [] },
};

for (const width of [1280, 390]) test(`Q7 Decisions remains read-only and responsive at ${width}px`, async ({ page }) => {
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

  await page.goto("/cockpit/v2/decisions");
  await expect(page.getByRole("heading", { name: "Decisions", level: 1 })).toBeVisible();
  await expect(page.getByRole("link", { name: "Decisions" })).toHaveAttribute("aria-current", "page");
  await expect(page.getByLabel("History (not yet available)")).toHaveAttribute("aria-disabled", "true");
  await expect(page.getByLabel("Decision portfolio readout")).toContainText("Owner action recorded");
  await expect(page.getByText("Austria filing authority")).toBeVisible();
  await expect(page.getByText("Earlier filing authority")).toBeVisible();

  const current = page.getByRole("button", { name: /Austria filing authority/ });
  await current.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { name: "Austria filing authority" })).toBeVisible();
  await expect(page.getByText("Recorded authority: L3")).toBeVisible();
  const inspector = page.getByLabel("Austria filing authority", { exact: true });
  await expect(inspector.locator('[data-tone="warning"]').filter({ hasText: "Owner action required" })).toBeVisible();
  await expect(page.getByText("Recorded recommendation", { exact: true })).toBeVisible();
  await expect(page.getByText("Proceed to owner review after the recorded evidence posture is inspected.")).toBeVisible();

  const provenance = page.getByText("Decision provenance & supersession", { exact: true });
  await provenance.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByText("decision:old", { exact: true })).toBeVisible();
  await expect(page.getByText("fp:current", { exact: true })).toBeVisible();
  await expect(page.getByText("No approval, legal validity, completion, urgency or execution authority is inferred from recommendation text, timestamps, evidence count or styling.")).toBeVisible();

  await page.getByRole("button", { name: "Close Austria filing authority" }).click();
  const old = page.getByRole("button", { name: /Earlier filing authority/ });
  await old.click();
  await expect(page.getByRole("heading", { name: "Earlier filing authority" })).toBeVisible();
  await expect(page.getByLabel("Selected Decision readout")).toContainText("Current recordNo");

  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth && document.body.scrollWidth <= window.innerWidth)).toBe(true);
  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);
});
