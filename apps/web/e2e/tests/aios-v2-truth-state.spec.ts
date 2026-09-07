import { expect, test, type Page } from "@playwright/test";

const EMPTY_SCENE = {
  contract_version: "living-organization-scene.v5",
  generated_at: "2026-09-07T10:00:00Z",
  scope: "q16_truth_fixture",
  root_work_item_id: "11111111-1111-4111-8111-111111111111",
  objective_key: "q16_truth_fixture",
  truth: {
    scene_authoritative: false,
    renderer_authoritative: false,
    scene_mutations_allowed: false,
    canonical_authority: "Q16 truth fixture",
    prediction_authoritative: false,
    environmental_authoritative: false,
  },
  coverage: {
    departments: "covered",
    missions: "covered",
    conversations: "unavailable",
    handoffs: "unavailable",
    blockers: "covered",
    human_actions: "unavailable",
    risk_escalations: "unavailable",
    incidents: "unavailable",
    smart_objects: "unavailable",
    runtime_costs: "unavailable",
    presence: "not_asserted",
  },
  deterministic: {
    canonical_projection: true,
    authoritative: false,
    departments: [],
    missions: [],
    employees: [],
    work_items: [],
    conversations: [],
    handoffs: [],
    blockers: [],
    human_actions: [],
    risk_escalations: [],
    incidents: [],
    smart_objects: [],
    rooms: [],
    relationships: [],
    decisions: [],
  },
  predictive: { enabled: false, canonical_projection: false, authoritative: false, status: "disabled", items: [] },
  environmental: { enabled: false, canonical_projection: false, authoritative: false, status: "disabled", items: [] },
};

async function installOwnerFixture(
  page: Page,
  writes: string[],
  options: { boardAvailable: boolean; activityAvailable: boolean; sceneEstablished?: boolean },
) {
  await page.route("http://127.0.0.1:8000/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const headers = {
      "access-control-allow-origin": request.headers().origin || "http://127.0.0.1:3000",
      "access-control-allow-credentials": "true",
      "access-control-allow-headers": "content-type,x-gmai-role,x-gmai-user",
      "access-control-allow-methods": "GET,OPTIONS",
    };
    if (request.method() === "OPTIONS") {
      await route.fulfill({ status: 204, headers, body: "" });
      return;
    }
    if (request.method() !== "GET") writes.push(`${request.method()} ${request.url()}`);
    const json = async (body: unknown) => route.fulfill({ status: 200, headers, contentType: "application/json", body: JSON.stringify(body) });
    const unavailable = async () => route.fulfill({ status: 503, headers, contentType: "application/json", body: JSON.stringify({ detail: "Q16 intentional source outage" }) });

    if (path === "/health") return json({ status: "ok", service: "fixture", environment: "test" });
    if (path === "/api/v1/organization/board-packet") {
      return options.boardAvailable
        ? json({ generated_at: "2026-09-07T10:00:00Z", pending_decisions: [], open_risks: [], recent_packets: [] })
        : unavailable();
    }
    if (path === "/api/v1/organization/human-action-requests") return json({ data: [] });
    if (path === "/api/v1/organization/blockers") return json({ data: [] });
    if (path === "/api/v1/organization/activities") return options.activityAvailable ? json({ data: [] }) : unavailable();
    if (path.endsWith("/scene/austria/latest")) {
      return options.sceneEstablished === false ? json({ established: false, scene: null }) : json({ established: true, scene: EMPTY_SCENE });
    }
    await unavailable();
  });
}

function scanMetric(page: Page, label: string) {
  return page.locator('section[aria-label="Owner five-second scan"] > div').filter({ hasText: label });
}

function intelligenceMetric(page: Page, label: string) {
  return page.getByLabel("Current intelligence readout").locator("div").filter({ hasText: label }).first();
}

test("Q16 partial source coverage never renders unknown Owner metrics as zero", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  const writes: string[] = [];
  await installOwnerFixture(page, writes, { boardAvailable: false, activityAvailable: false });
  await page.goto("/cockpit/v2");

  await expect(page.getByText("Partial source coverage", { exact: true })).toBeVisible();
  await expect(scanMetric(page, "Owner attention").getByText("Unknown", { exact: true })).toBeVisible();
  await expect(scanMetric(page, "Mission blockers").getByText("0", { exact: true })).toBeVisible();
  await expect(scanMetric(page, "Decision awareness").getByText("Unavailable", { exact: true })).toBeVisible();
  await expect(scanMetric(page, "Recent Activity").getByText("Unavailable", { exact: true })).toBeVisible();
  await expect(page.getByText("Attention coverage is incomplete.", { exact: true })).toBeVisible();
  await expect(page.getByText("Activity source unavailable. No zero-Activity conclusion is made.", { exact: true })).toBeVisible();
  expect(writes).toEqual([]);
});

test("Q16 Intelligence carries the same coverage truth without false zero metrics", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  const writes: string[] = [];
  await installOwnerFixture(page, writes, { boardAvailable: false, activityAvailable: false });
  await page.goto("/cockpit/v2/intelligence");

  await expect(page.getByText("Partial current-source coverage", { exact: true })).toBeVisible();
  await expect(intelligenceMetric(page, "Attention records").getByText("Unknown", { exact: true })).toBeVisible();
  await expect(intelligenceMetric(page, "Projected Missions").getByText("0", { exact: true })).toBeVisible();
  await expect(intelligenceMetric(page, "Department blocker entries").getByText("0", { exact: true })).toBeVisible();
  await expect(intelligenceMetric(page, "Recent Activity records").getByText("Unavailable", { exact: true })).toBeVisible();
  await expect(page.getByText("Owner-attention coverage incomplete", { exact: true })).toBeVisible();
  await expect(page.getByText("Activity source unavailable", { exact: true })).toBeVisible();
  expect(writes).toEqual([]);
});

test("Q16 available empty sources still render legitimate canonical zero", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  const writes: string[] = [];
  await installOwnerFixture(page, writes, { boardAvailable: true, activityAvailable: true });
  await page.goto("/cockpit/v2");

  await expect(page.getByText("Connected source coverage", { exact: true })).toBeVisible();
  await expect(scanMetric(page, "Owner attention").getByText("0", { exact: true })).toBeVisible();
  await expect(scanMetric(page, "Decision awareness").getByText("0", { exact: true })).toBeVisible();
  await expect(scanMetric(page, "Recent Activity").getByText("0", { exact: true })).toBeVisible();
  await expect(page.getByText("No current attention item was returned.", { exact: true })).toBeVisible();
  await expect(page.getByText("The available bounded Activity read returned zero recent records.", { exact: true })).toBeVisible();
  expect(writes).toEqual([]);
});

test("Q16 non-established Living Organization is not rendered as zero Missions", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  const writes: string[] = [];
  await installOwnerFixture(page, writes, { boardAvailable: true, activityAvailable: true, sceneEstablished: false });
  await page.goto("/cockpit/v2");

  await expect(scanMetric(page, "Mission blockers").getByText("Not established", { exact: true })).toBeVisible();
  await expect(page.getByText("No Mission projection is established for the connected Living Organization scene.", { exact: true })).toBeVisible();
  expect(writes).toEqual([]);
});
