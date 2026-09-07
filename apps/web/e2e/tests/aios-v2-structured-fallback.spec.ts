import { expect, test } from "@playwright/test";

const ROOT_ID = "11111111-1111-4111-8111-111111111111";
const SCENE_PATH = "/api/v1/organization/transparency/live-organization/scene/austria/latest";

function livingSceneFixture() {
  return {
    established: true,
    scene: {
      contract_version: "living-organization-scene.v5",
      generated_at: "2026-09-07T02:00:00Z",
      scope: "austria_mobility",
      root_work_item_id: ROOT_ID,
      objective_key: "q13_structured_fallback",
      coverage: {
        departments: "canonical_fixture_projection",
        missions: "canonical_fixture_projection",
        conversations: "unavailable_in_q13_fixture",
        handoffs: "unavailable_in_q13_fixture",
        blockers: "canonical_fixture_projection",
        human_actions: "canonical_fixture_projection",
        risk_escalations: "canonical_fixture_projection",
        incidents: "unavailable_no_canonical_incident_model",
        smart_objects: "canonical_fixture_projection",
        runtime_costs: "unavailable_no_canonical_organization_cost_ledger",
        presence: "not_asserted",
      },
      deterministic: {
        departments: [
          {
            department_key: "Global Mobility Operations",
            label: "Global Mobility Operations",
            employee_count: 1,
            work_item_count: 1,
            active_blocker_count: 0,
            canonical_basis: "OrganizationPosition.department + OrganizationalWorkItem.department",
          },
        ],
        missions: [
          {
            mission_key: `objective:${ROOT_ID}`,
            objective_key: "q13_structured_fallback",
            root_work_item_id: ROOT_ID,
            title: "Structured fallback proof mission",
            state: "running",
            phase_key: "Q13",
            participant_position_keys: ["mobility_operations_lead"],
            work_item_ids: [ROOT_ID],
            blocker_count: 0,
            decision_count: 0,
            projection_only: true,
            canonical_basis: "OrganizationalWorkItem objective_key/parent topology",
          },
        ],
        canonical_projection: true,
        authoritative: false,
        employees: [
          {
            position_key: "mobility_operations_lead",
            title: "Mobility Operations Lead",
            department: "Global Mobility Operations",
            reports_to_position_key: "ceo",
            authority_level: "L2",
            organization_status: "active",
            work_item_id: ROOT_ID,
            work_status: "running",
            semantic_state: "working",
            presence_state: "not_asserted",
            state_reason: "Canonical work is active; physical presence is not asserted.",
          },
        ],
        work_items: [
          {
            work_item_id: ROOT_ID,
            parent_work_item_id: null,
            title: "Structured fallback proof mission",
            objective_key: "q13_structured_fallback",
            phase_key: "Q13",
            status: "running",
            priority: "normal",
            risk_level: "routine",
            assigned_position_key: "mobility_operations_lead",
            department: "Global Mobility Operations",
            authority_level: "L2",
            created_at: "2026-09-07T01:00:00Z",
            updated_at: "2026-09-07T02:00:00Z",
            due_at: null,
            completed_at: null,
            elapsed_seconds: 3600,
            overdue: false,
            specialist_evidence_valid: null,
            specialist_evidence_reason: null,
          },
        ],
        conversations: [],
        handoffs: [],
        blockers: [],
        decisions: [],
        human_actions: [],
        risk_escalations: [],
        incidents: [],
        smart_objects: [],
        rooms: [],
        relationships: [],
      },
      predictive: {
        enabled: false,
        canonical_projection: false,
        authoritative: false,
        status: "disabled_in_q13_fixture",
        items: [],
      },
      environmental: {
        enabled: false,
        canonical_projection: false,
        authoritative: false,
        status: "disabled_in_q13_fixture",
        items: [],
      },
      truth: {
        canonical_authority: "AIOS canonical records and accepted projections",
        scene_authoritative: false,
        renderer_authoritative: false,
        prediction_authoritative: false,
        environmental_authoritative: false,
        scene_mutations_allowed: false,
      },
    },
  };
}

async function installReadOnlyFixture(page: import("@playwright/test").Page, writes: string[]) {
  await page.route("http://127.0.0.1:8000/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const origin = request.headers().origin || "http://127.0.0.1:3000";
    const headers = {
      "access-control-allow-origin": origin,
      "access-control-allow-credentials": "true",
      "access-control-allow-headers": "content-type,x-gmai-role,x-gmai-user",
      "access-control-allow-methods": "GET,OPTIONS",
    };

    if (request.method() === "OPTIONS") {
      await route.fulfill({ status: 204, headers, body: "" });
      return;
    }

    if (request.method() !== "GET") writes.push(`${request.method()} ${request.url()}`);

    if (url.pathname === "/health") {
      await route.fulfill({
        status: 200,
        headers,
        contentType: "application/json",
        body: JSON.stringify({ status: "ok", service: "fixture", environment: "test" }),
      });
      return;
    }

    if (url.pathname === SCENE_PATH) {
      await route.fulfill({
        status: 200,
        headers,
        contentType: "application/json",
        body: JSON.stringify(livingSceneFixture()),
      });
      return;
    }

    await route.fulfill({
      status: 503,
      headers,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Q13 fixture intentionally leaves unrelated governed sources unavailable" }),
    });
  });
}

for (const scenario of [
  { width: 1280, colorScheme: "dark" as const },
  { width: 390, colorScheme: "light" as const },
]) {
  test(`Q13 structured fallback preserves governed work without the renderer at ${scenario.width}px`, async ({ page }) => {
    await page.setViewportSize({ width: scenario.width, height: 844 });
    await page.emulateMedia({ colorScheme: scenario.colorScheme, reducedMotion: "reduce" });
    const writes: string[] = [];
    const pageErrors: string[] = [];
    page.on("pageerror", (error) => pageErrors.push(error.message));
    await installReadOnlyFixture(page, writes);

    await page.goto("/cockpit/v2/organization");

    const spatial = page.getByRole("radio", { name: "Spatial" });
    const structured = page.getByRole("radio", { name: "Structured" });
    const stage = page.getByLabel("Living HQ visual stage");
    const structuredView = page.locator('[data-v2-organization-representation="structured"]');

    await expect(spatial).toBeChecked();
    await expect(structured).not.toBeChecked();
    await expect(stage).toHaveCount(1);
    await expect(structuredView).toHaveCount(1);
    await expect(structuredView).toHaveAttribute("data-view-placement", "equivalent");

    await structured.check();
    await expect(structured).toBeChecked();
    await expect(stage).toHaveCount(0);
    await expect(structuredView).toHaveCount(1);
    await expect(structuredView).toHaveAttribute("data-view-placement", "primary");
    await expect(page.getByRole("heading", { level: 2, name: "Structured organization" })).toBeVisible();
    await expect(page.getByText("Structured mode does not mount the Living HQ stage.")).toBeVisible();

    const operationsHeading = structuredView.getByRole("heading", { level: 3, name: "Operations Studio" });
    await expect(operationsHeading).toBeVisible();
    const operationsZone = operationsHeading.locator("xpath=ancestor::section[1]");
    const detailButton = operationsZone.getByRole("button", { name: "Open details" });
    const employeeButton = operationsZone.getByRole("button", { name: /Mobility Operations Lead/ });
    await expect(detailButton).toBeVisible();
    await expect(employeeButton).toBeVisible();

    const detailBox = await detailButton.boundingBox();
    const employeeBox = await employeeButton.boundingBox();
    expect(detailBox?.height ?? 0).toBeGreaterThanOrEqual(44);
    expect(employeeBox?.height ?? 0).toBeGreaterThanOrEqual(44);

    await employeeButton.click();
    const inspector = page.locator('[data-presence-claimed="false"][data-locomotion-claimed="false"]');
    await expect(inspector).toBeVisible();
    await expect(inspector.getByText("mobility_operations_lead", { exact: true })).toBeVisible();
    await expect(inspector.getByText("Roster identity is not physical presence.", { exact: true }).first()).toBeVisible();

    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth && document.body.scrollWidth <= window.innerWidth)).toBe(true);

    await detailButton.click();
    await expect(page).toHaveURL(/\/cockpit\/v2\/organization\/wing\/operations$/);

    expect(writes).toEqual([]);
    expect(pageErrors).toEqual([]);

    await page.goto("/cockpit/v2/organization");
    await expect(page.getByRole("radio", { name: "Spatial" })).toBeChecked();
    await expect(page.getByLabel("Living HQ visual stage")).toHaveCount(1);
  });
}