import { mkdirSync } from "node:fs";
import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

const CEO_WORK_ITEM = "44444444-4444-4444-8444-444444444440";
const CTO_WORK_ITEM = "44444444-4444-4444-8444-444444444441";
const REG_WORK_ITEM = "44444444-4444-4444-8444-444444444442";

const employees = [
  {
    position_key: "ceo",
    title: "Chief Executive Officer",
    department: "Executive",
    reports_to_position_key: null,
    authority_level: "executive",
    organization_status: "active",
    work_item_id: CEO_WORK_ITEM,
    work_status: "running",
    semantic_state: "working",
    presence_state: "not_asserted",
    state_reason: "Phase 7E topology-only participant fixture",
  },
  {
    position_key: "cto",
    title: "Chief Technology Officer",
    department: "Technology",
    reports_to_position_key: "ceo",
    authority_level: "operational",
    organization_status: "active",
    work_item_id: CTO_WORK_ITEM,
    work_status: "running",
    semantic_state: "working",
    presence_state: "not_asserted",
    state_reason: "Phase 7E exact coordination participant fixture",
  },
  {
    position_key: "regulatory_lead",
    title: "Regulatory Lead",
    department: "Regulatory",
    reports_to_position_key: "ceo",
    authority_level: "operational",
    organization_status: "active",
    work_item_id: REG_WORK_ITEM,
    work_status: "running",
    semantic_state: "working",
    presence_state: "not_asserted",
    state_reason: "Phase 7E exact coordination participant fixture",
  },
];

function workItem(
  work_item_id: string,
  title: string,
  assigned_position_key: string,
  department: string,
) {
  return {
    work_item_id,
    parent_work_item_id: work_item_id === CEO_WORK_ITEM ? null : CEO_WORK_ITEM,
    title,
    objective_key: "phase7e_mission_coordination",
    phase_key: "phase7e",
    status: "running",
    priority: "high",
    risk_level: "low",
    assigned_position_key,
    department,
    authority_level: assigned_position_key === "ceo" ? "executive" : "operational",
    created_at: "2026-09-07T19:00:00Z",
    updated_at: "2026-09-07T19:30:00Z",
    due_at: null,
    completed_at: null,
    elapsed_seconds: 1800,
    overdue: false,
    specialist_evidence_valid: null,
    specialist_evidence_reason: null,
  };
}

function scene(
  missionCoverage = "workitem_objective_topology_projection",
  conversationCoverage = "organization_activity_conversation_lifecycle_v1",
) {
  return {
    contract_version: "living-organization-scene.v5",
    generated_at: "2026-09-07T19:30:00Z",
    scope: "phase7e_mission_coordination_browser_fixture",
    root_work_item_id: CEO_WORK_ITEM,
    objective_key: "phase7e_mission_coordination",
    coverage: {
      departments: "projected_from_canonical_positions_and_work",
      missions: missionCoverage,
      conversations: conversationCoverage,
      handoffs: "unavailable",
      blockers: "organization_blocker_canonical_records",
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
      departments: [
        { department_key: "executive", label: "Executive", employee_count: 1, work_item_count: 1, active_blocker_count: 0, canonical_basis: "Position.department" },
        { department_key: "technology", label: "Technology", employee_count: 1, work_item_count: 1, active_blocker_count: 0, canonical_basis: "Position.department" },
        { department_key: "regulatory", label: "Regulatory", employee_count: 1, work_item_count: 1, active_blocker_count: 0, canonical_basis: "Position.department" },
      ],
      missions: [
        {
          mission_key: "phase7e-coordination",
          objective_key: "phase7e_mission_coordination",
          root_work_item_id: CEO_WORK_ITEM,
          title: "Governed Mission coordination",
          state: "active",
          phase_key: "phase7e",
          participant_position_keys: ["ceo", "cto", "regulatory_lead"],
          work_item_ids: [CEO_WORK_ITEM, CTO_WORK_ITEM, REG_WORK_ITEM],
          blocker_count: 0,
          decision_count: 0,
          projection_only: true,
          canonical_basis: "OrganizationalWorkItem objective_key/parent topology",
        },
      ],
      employees,
      work_items: [
        workItem(CEO_WORK_ITEM, "Coordinate Phase 7E", "ceo", "Executive"),
        workItem(CTO_WORK_ITEM, "Review governed coordination boundary", "cto", "Technology"),
        workItem(REG_WORK_ITEM, "Validate governed coordination boundary", "regulatory_lead", "Regulatory"),
      ],
      conversations: [
        {
          conversation_id: "phase7e-coordination-conversation",
          participant_position_keys: ["cto", "regulatory_lead"],
          work_item_id: CTO_WORK_ITEM,
          status: "open",
          summary: "CTO and Regulatory Lead coordinated the Mission evidence boundary.",
          opened_activity_id: "activity-phase7e-open",
          latest_activity_id: "activity-phase7e-open",
          opened_at: "2026-09-07T19:20:00Z",
          lifecycle_at: "2026-09-07T19:20:00Z",
          authority_effect: "none",
          transcript_persisted: false,
          canonical_basis: "organization_activity_conversation_lifecycle_v1",
        },
      ],
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
    predictive: { enabled: false, canonical_projection: false, authoritative: false, status: "disabled", items: [] },
    environmental: { enabled: false, canonical_projection: false, authoritative: false, status: "disabled", items: [] },
    truth: {
      canonical_authority: "Canonical organization records",
      scene_authoritative: false,
      renderer_authoritative: false,
      prediction_authoritative: false,
      environmental_authoritative: false,
      scene_mutations_allowed: false,
    },
  };
}

async function installFixture(
  page: Page,
  writes: string[],
  missionCoverage = "workitem_objective_topology_projection",
  conversationCoverage = "organization_activity_conversation_lifecycle_v1",
) {
  await page.route("http://127.0.0.1:8000/**", async (route) => {
    const request = route.request();
    const pathname = new URL(request.url()).pathname;
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
    if (request.method() !== "GET") writes.push(`${request.method()} ${pathname}`);

    const json = (body: unknown) => route.fulfill({
      status: 200,
      headers,
      contentType: "application/json",
      body: JSON.stringify(body),
    });
    const unavailable = () => route.fulfill({
      status: 503,
      headers,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Phase 7E fixture source unavailable" }),
    });

    if (pathname === "/health") return json({ status: "ok", service: "fixture", environment: "test" });
    if (pathname === "/api/v1/organization/board-packet") return json({ generated_at: "2026-09-07T19:30:00Z", pending_decisions: [], open_risks: [], recent_packets: [] });
    if (pathname === "/api/v1/organization/human-action-requests") return json({ data: [] });
    if (pathname === "/api/v1/organization/blockers") return json({ data: [] });
    if (pathname === "/api/v1/organization/activities") return json({ data: [] });
    if (pathname.endsWith("/scene/austria/latest")) return json({ established: true, scene: scene(missionCoverage, conversationCoverage) });
    return unavailable();
  });
}

function artifactPath(filename: string) {
  const directory = path.join(process.cwd(), "phase7e-artifacts");
  mkdirSync(directory, { recursive: true });
  return path.join(directory, filename);
}

test("Phase 7E surfaces governed Mission coordination without promoting topology membership to active collaboration", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.emulateMedia({ colorScheme: "dark", reducedMotion: "no-preference" });
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await installFixture(page, writes);

  await page.goto("/cockpit/v2/organization");
  const stage = page.getByLabel("Living HQ visual stage");
  await expect(stage).toBeVisible();
  const signal = page.locator('[data-aios-v2-mission-collaboration="governed-coordination"][data-variant="spatial"]');
  await expect(signal).toBeVisible();
  await expect(signal).toHaveAttribute("data-coordination-count", "1");
  await expect(signal).toHaveAttribute("data-active-collaboration-claimed", "false");
  await expect(signal).toHaveAttribute("data-physical-presence-claimed", "false");
  await expect(signal.getByText(/CTO and Regulatory Lead coordinated the Mission evidence boundary/)).toBeVisible();
  await expect(signal.getByText(/Chief Technology Officer · Regulatory Lead/)).toBeVisible();
  await expect(signal.getByText(/Chief Executive Officer/)).toHaveCount(0);
  await expect(signal.getByText(/not live teamwork · not co-location/)).toBeVisible();

  await stage.getByRole("button", { name: /Chief Technology Officer/ }).click();
  const inspector = page.getByRole("complementary", { name: "Chief Technology Officer" });
  await expect(
    inspector.locator("section.aios-v2-inspector-missions > span", { hasText: "Governed Mission coordination" }),
  ).toBeVisible();
  await expect(inspector.getByText(/Exact coordination participants: Chief Technology Officer · Regulatory Lead/)).toBeVisible();
  await expect(inspector).toHaveAttribute("data-active-collaboration-claimed", "false");
  await expect(inspector).toHaveAttribute("data-presence-claimed", "false");

  await page.locator("main").screenshot({ path: artifactPath("phase7e-mission-collaboration-dark-1280.png") });

  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);
});

test("Phase 7E Structured reduced-motion view preserves governed coordination without the HQ renderer", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.emulateMedia({ colorScheme: "dark", reducedMotion: "reduce" });
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await installFixture(page, writes);

  await page.goto("/cockpit/v2/organization");
  await page.getByRole("radio", { name: "Structured", exact: true }).check();
  await expect(page.getByLabel("Living HQ visual stage")).toHaveCount(0);
  const signal = page.locator('[data-aios-v2-mission-collaboration="governed-coordination"][data-variant="structured"]');
  await expect(signal).toBeVisible();
  await expect(signal).toHaveAttribute("data-active-collaboration-claimed", "false");
  await expect(signal.getByText(/CTO and Regulatory Lead coordinated the Mission evidence boundary/)).toBeVisible();

  await page.locator("main").screenshot({ path: artifactPath("phase7e-mission-collaboration-reduced-structured-1280.png") });

  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);
});

test("Phase 7E fails closed when Mission coverage is unavailable", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await installFixture(page, writes, "unavailable");

  await page.goto("/cockpit/v2/organization");
  await expect(page.locator('[data-aios-v2-mission-collaboration="governed-coordination"]')).toHaveCount(0);
  const warning = page.locator('[data-mission-collaboration-coverage="unavailable"]').first();
  await expect(warning).toBeVisible();
  await expect(warning.getByText(/will not infer collaboration from roster membership, room placement or shared work topology/)).toBeVisible();

  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);
});
