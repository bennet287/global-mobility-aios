import { mkdirSync } from "node:fs";
import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

const CEO_WORK_ITEM = "33333333-3333-4333-8333-333333333333";
const CTO_WORK_ITEM = "33333333-3333-4333-8333-333333333331";

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
    state_reason: "Phase 7D canonical fixture state",
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
    state_reason: "Phase 7D canonical fixture state",
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
    parent_work_item_id: null,
    title,
    objective_key: "phase7d_governed_conversation",
    phase_key: "phase7d",
    status: "running",
    priority: "high",
    risk_level: "low",
    assigned_position_key,
    department,
    authority_level: assigned_position_key === "ceo" ? "executive" : "operational",
    created_at: "2026-09-07T18:00:00Z",
    updated_at: "2026-09-07T18:30:00Z",
    due_at: null,
    completed_at: null,
    elapsed_seconds: 1800,
    overdue: false,
    specialist_evidence_valid: null,
    specialist_evidence_reason: null,
  };
}

function scene(conversationCoverage = "organization_activity_conversation_lifecycle_v1") {
  return {
    contract_version: "living-organization-scene.v5",
    generated_at: "2026-09-07T18:30:00Z",
    scope: "phase7d_governed_conversation_browser_fixture",
    root_work_item_id: CEO_WORK_ITEM,
    objective_key: "phase7d_governed_conversation",
    coverage: {
      departments: "projected_from_canonical_positions_and_work",
      missions: "workitem_objective_topology_projection",
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
        {
          department_key: "executive",
          label: "Executive",
          employee_count: 1,
          work_item_count: 1,
          active_blocker_count: 0,
          canonical_basis: "Position.department",
        },
        {
          department_key: "technology",
          label: "Technology",
          employee_count: 1,
          work_item_count: 1,
          active_blocker_count: 0,
          canonical_basis: "Position.department",
        },
      ],
      missions: [
        {
          mission_key: "phase7d-conversation",
          objective_key: "phase7d_governed_conversation",
          root_work_item_id: CEO_WORK_ITEM,
          title: "Governed conversation visibility",
          state: "active",
          phase_key: "phase7d",
          participant_position_keys: ["ceo", "cto"],
          work_item_ids: [CEO_WORK_ITEM, CTO_WORK_ITEM],
          blocker_count: 0,
          decision_count: 0,
          projection_only: true,
          canonical_basis: "WorkItem.objective_key",
        },
      ],
      employees,
      work_items: [
        workItem(CEO_WORK_ITEM, "Coordinate Phase 7D", "ceo", "Executive"),
        workItem(CTO_WORK_ITEM, "Review governed conversation boundary", "cto", "Technology"),
      ],
      conversations: [
        {
          conversation_id: "phase7d-conversation-1",
          participant_position_keys: ["cto", "ceo"],
          work_item_id: CTO_WORK_ITEM,
          status: "open",
          summary: "CTO and CEO reviewed the governed conversation boundary.",
          opened_activity_id: "activity-conversation-open",
          latest_activity_id: "activity-conversation-open",
          opened_at: "2026-09-07T18:20:00Z",
          lifecycle_at: "2026-09-07T18:20:00Z",
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
    predictive: {
      enabled: false,
      canonical_projection: false,
      authoritative: false,
      status: "disabled",
      items: [],
    },
    environmental: {
      enabled: false,
      canonical_projection: false,
      authoritative: false,
      status: "disabled",
      items: [],
    },
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
      body: JSON.stringify({ detail: "Phase 7D fixture source unavailable" }),
    });

    if (pathname === "/health") return json({ status: "ok", service: "fixture", environment: "test" });
    if (pathname === "/api/v1/organization/board-packet") {
      return json({ generated_at: "2026-09-07T18:30:00Z", pending_decisions: [], open_risks: [], recent_packets: [] });
    }
    if (pathname === "/api/v1/organization/human-action-requests") return json({ data: [] });
    if (pathname === "/api/v1/organization/blockers") return json({ data: [] });
    if (pathname === "/api/v1/organization/activities") return json({ data: [] });
    if (pathname.endsWith("/scene/austria/latest")) {
      return json({ established: true, scene: scene(conversationCoverage) });
    }
    return unavailable();
  });
}

function artifactPath(filename: string) {
  const directory = path.join(process.cwd(), "phase7d-artifacts");
  mkdirSync(directory, { recursive: true });
  return path.join(directory, filename);
}

test("Phase 7D surfaces canonical conversation lifecycle without live-speech or transcript claims", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.emulateMedia({ colorScheme: "dark", reducedMotion: "no-preference" });
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await installFixture(page, writes);

  await page.goto("/cockpit/v2/organization");
  const stage = page.getByLabel("Living HQ visual stage");
  await expect(stage).toBeVisible();
  const signal = page.locator('[data-aios-v2-conversation="canonical-lifecycle"][data-variant="spatial"]');
  await expect(signal).toBeVisible();
  await expect(signal).toHaveAttribute("data-conversation-count", "1");
  await expect(signal).toHaveAttribute("data-live-speech-claimed", "false");
  await expect(signal).toHaveAttribute("data-transcript-claimed", "false");
  await expect(signal).toHaveAttribute("data-physical-presence-claimed", "false");
  await expect(signal.getByText(/CTO and CEO reviewed the governed conversation boundary/)).toBeVisible();
  await expect(signal.getByText(/transcript not persisted/)).toBeVisible();

  await stage.getByRole("button", { name: /Chief Technology Officer/ }).click();
  const inspector = page.getByRole("complementary", { name: "Chief Technology Officer" });
  await expect(inspector.getByText(/Governed conversations/)).toBeVisible();
  await expect(inspector.getByText(/Authority effect: none · transcript not persisted/)).toBeVisible();
  await expect(inspector).toHaveAttribute("data-live-speech-claimed", "false");
  await expect(inspector).toHaveAttribute("data-transcript-claimed", "false");

  await page.locator("main").screenshot({
    path: artifactPath("phase7d-governed-conversation-dark-1280.png"),
  });

  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);
});

test("Phase 7D Structured reduced-motion view preserves the same conversation truth without HQ renderer", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.emulateMedia({ colorScheme: "dark", reducedMotion: "reduce" });
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await installFixture(page, writes);

  await page.goto("/cockpit/v2/organization");
  await page.getByRole("radio", { name: "Structured", exact: true }).check();
  await expect(page.getByLabel("Living HQ visual stage")).toHaveCount(0);
  const structuredSignal = page.locator('[data-aios-v2-conversation="canonical-lifecycle"][data-variant="structured"]');
  await expect(structuredSignal).toBeVisible();
  await expect(structuredSignal).toHaveAttribute("data-live-speech-claimed", "false");
  await expect(structuredSignal.getByText(/CTO and CEO reviewed the governed conversation boundary/)).toBeVisible();

  await page.locator("main").screenshot({
    path: artifactPath("phase7d-governed-conversation-reduced-structured-1280.png"),
  });

  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);
});

test("Phase 7D fails closed when conversation coverage is unavailable", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await installFixture(page, writes, "unavailable");

  await page.goto("/cockpit/v2/organization");
  await expect(page.locator('[data-aios-v2-conversation="canonical-lifecycle"]')).toHaveCount(0);
  const warning = page.locator('[data-conversation-coverage="unavailable"]').first();
  await expect(warning).toBeVisible();
  await expect(warning.getByText(/will not infer dialogue/)).toBeVisible();

  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);
});
