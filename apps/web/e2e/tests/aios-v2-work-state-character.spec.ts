import { mkdirSync } from "node:fs";
import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

const WORK_ITEM_ID = "22222222-2222-4222-8222-222222222222";

const employees = [
  {
    position_key: "ceo",
    title: "Chief Executive Officer",
    department: "Executive",
    semantic_state: "working",
    work_item_id: WORK_ITEM_ID,
  },
  {
    position_key: "cto",
    title: "Chief Technology Officer",
    department: "Technology",
    semantic_state: "blocked",
    work_item_id: WORK_ITEM_ID,
  },
  {
    position_key: "regulatory_lead",
    title: "Regulatory Lead",
    department: "Regulatory",
    semantic_state: "awaiting_owner",
    work_item_id: WORK_ITEM_ID,
  },
  {
    position_key: "operations_lead",
    title: "Operations Lead",
    department: "Operations",
    semantic_state: "queued",
    work_item_id: WORK_ITEM_ID,
  },
  {
    position_key: "operations_specialist",
    title: "Operations Specialist",
    department: "Operations",
    semantic_state: "completed",
    work_item_id: WORK_ITEM_ID,
  },
  {
    position_key: "observer",
    title: "Operations Observer",
    department: "Operations",
    semantic_state: "future_unmodeled_state",
    work_item_id: null,
  },
].map((employee) => ({
  reports_to_position_key: employee.position_key === "ceo" ? null : "ceo",
  authority_level: employee.position_key === "ceo" ? "executive" : "operational",
  organization_status: "active",
  work_status: employee.semantic_state,
  presence_state: "not_asserted",
  state_reason: `Phase 7B canonical ${employee.semantic_state} fixture state`,
  ...employee,
}));

function scene() {
  const departments = [
    ["executive", "Executive"],
    ["technology", "Technology"],
    ["regulatory", "Regulatory"],
    ["operations", "Operations"],
  ].map(([department_key, label]) => ({
    department_key,
    label,
    employee_count: employees.filter((employee) => employee.department === label).length,
    work_item_count: 1,
    active_blocker_count: label === "Technology" ? 1 : 0,
    canonical_basis: "Position.department",
  }));

  return {
    contract_version: "living-organization-scene.v5",
    generated_at: "2026-09-07T14:00:00Z",
    scope: "phase7b_work_state_browser_fixture",
    root_work_item_id: WORK_ITEM_ID,
    objective_key: "phase7b_work_state",
    coverage: {
      departments: "projected_from_canonical_positions_and_work",
      missions: "workitem_objective_topology_projection",
      conversations: "unavailable",
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
      departments,
      missions: [
        {
          mission_key: "phase7b-work-state",
          objective_key: "phase7b_work_state",
          root_work_item_id: WORK_ITEM_ID,
          title: "Canonical employee work-state visibility",
          state: "active",
          phase_key: "phase7b",
          participant_position_keys: employees.map((employee) => employee.position_key),
          work_item_ids: [WORK_ITEM_ID],
          blocker_count: 1,
          decision_count: 0,
          projection_only: true,
          canonical_basis: "WorkItem.objective_key",
        },
      ],
      employees,
      work_items: [
        {
          work_item_id: WORK_ITEM_ID,
          parent_work_item_id: null,
          title: "Canonical employee work-state visibility",
          objective_key: "phase7b_work_state",
          phase_key: "phase7b",
          status: "running",
          priority: "high",
          risk_level: "medium",
          assigned_position_key: "cto",
          department: "Technology",
          authority_level: "executive",
          created_at: "2026-09-07T13:30:00Z",
          updated_at: "2026-09-07T14:00:00Z",
          due_at: null,
          completed_at: null,
          elapsed_seconds: 1800,
          overdue: false,
          specialist_evidence_valid: null,
          specialist_evidence_reason: null,
        },
      ],
      conversations: [],
      handoffs: [],
      blockers: [
        {
          blocker_id: "blocker-phase7b",
          work_item_id: WORK_ITEM_ID,
          blocker_type: "dependency",
          title: "Fixture blocker intentionally not rendered by Phase 7B",
          description: "Reserved for Phase 7C blocker-object semantics",
          severity: "high",
          status: "open",
          accountable_position_key: "cto",
          decision_id: null,
          risk_escalation_id: null,
          requires_human_action: false,
          opened_at: "2026-09-07T13:50:00Z",
          due_at: null,
          open_elapsed_seconds: 600,
          overdue: false,
        },
      ],
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

async function installFixture(page: Page, writes: string[]) {
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

    const json = (body: unknown) =>
      route.fulfill({
        status: 200,
        headers,
        contentType: "application/json",
        body: JSON.stringify(body),
      });
    const unavailable = () =>
      route.fulfill({
        status: 503,
        headers,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Phase 7B fixture source unavailable" }),
      });

    if (pathname === "/health") return json({ status: "ok", service: "fixture", environment: "test" });
    if (pathname === "/api/v1/organization/board-packet") {
      return json({ generated_at: "2026-09-07T14:00:00Z", pending_decisions: [], open_risks: [], recent_packets: [] });
    }
    if (pathname === "/api/v1/organization/human-action-requests") return json({ data: [] });
    if (pathname === "/api/v1/organization/blockers") return json({ data: [] });
    if (pathname === "/api/v1/organization/activities") return json({ data: [] });
    if (pathname.endsWith("/scene/austria/latest")) return json({ established: true, scene: scene() });
    return unavailable();
  });
}

function artifactPath(filename: string) {
  const directory = path.join(process.cwd(), "phase7b-artifacts");
  mkdirSync(directory, { recursive: true });
  return path.join(directory, filename);
}

const stateCases = [
  ["working", "WORK"],
  ["blocked", "BLOCKED"],
  ["awaiting_owner", "OWNER"],
  ["queued", "QUEUED"],
  ["completed", "DONE"],
] as const;

test("Phase 7B renders canonical employee work states while semantic motion supersedes ambience", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 960 });
  await page.emulateMedia({ colorScheme: "dark", reducedMotion: "no-preference" });
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await installFixture(page, writes);

  await page.goto("/cockpit/v2/organization");
  const stage = page.getByLabel("Living HQ visual stage");
  await expect(stage).toBeVisible();

  for (const [kind, badge] of stateCases) {
    const state = stage.locator(`[data-aios-v2-work-state="canonical"][data-work-state-kind="${kind}"]`);
    await expect(state).toHaveCount(1);
    await expect(state.getByText(badge, { exact: true })).toBeVisible();
    await expect(state).toHaveAttribute("data-canonical-state-source", "LivingSceneEmployee.semantic_state");
    await expect(state).toHaveAttribute("data-presentation-only", "true");
    await expect(state).toHaveAttribute("data-canonical-state-writable", "false");
    await expect(state).toHaveAttribute("data-physical-presence-claimed", "false");
    await expect(state).toHaveAttribute("data-physical-location-claimed", "false");
    await expect(state).toHaveAttribute("data-physical-travel-claimed", "false");
    await expect(state).toHaveAttribute("data-locomotion-allowed", "false");
    await expect(state).toHaveAttribute("data-blocker-details-claimed", "false");
    await expect(state).toHaveAttribute("data-blocker-resolution-claimed", "false");
    await expect(state).toHaveAttribute("data-completion-event-claimed", "false");
    await expect(state.locator('[data-ambient-renderer="true"]')).toHaveCount(0);
  }

  const workingAnimation = await stage
    .locator('[data-work-state-kind="working"]')
    .locator("span")
    .first()
    .evaluate((element) => getComputedStyle(element).animationName);
  expect(workingAnimation).not.toBe("none");

  const observerButton = stage.getByRole("button", { name: /^Operations Observer · Operations/ });
  await expect(observerButton).toBeVisible();
  await expect(observerButton.locator('[data-aios-v2-work-state="canonical"]')).toHaveCount(0);
  await expect(observerButton.locator('[data-ambient-renderer="true"]')).toHaveCount(1);

  await page.screenshot({
    path: artifactPath("phase7b-work-states-dark-1280.png"),
    fullPage: true,
  });
  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);
});

test("Phase 7B reduced motion is static and Structured Organization preserves canonical state text", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 960 });
  await page.emulateMedia({ colorScheme: "dark", reducedMotion: "reduce" });
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await installFixture(page, writes);

  await page.goto("/cockpit/v2/organization");
  const spatialWorking = page.locator('[data-aios-v2-work-state="canonical"][data-work-state-kind="working"]');
  await expect(spatialWorking).toHaveAttribute("data-semantic-animation-active", "false");
  const animationNames = await spatialWorking.locator("span").evaluateAll((elements) =>
    elements.map((element) => getComputedStyle(element).animationName),
  );
  expect(animationNames.every((name) => name === "none")).toBe(true);

  await page.getByRole("radio", { name: "Structured", exact: true }).check();
  await expect(page.getByLabel("Living HQ visual stage")).toHaveCount(0);
  const structured = page.locator('[data-v2-organization-representation="structured"]');
  for (const label of [
    "Working · canonical employee state",
    "Blocked · canonical employee state",
    "Awaiting Owner · canonical employee state",
    "Queued · canonical employee state",
    "Completed state · canonical employee state",
  ]) {
    await expect(structured.getByText(new RegExp(label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")))).toBeVisible();
  }
  await expect(structured.getByText(/Canonical state · future_unmodeled_state/)).toBeVisible();
  await expect(structured.getByText(/canonical employee state does not establish physical activity or room presence/i)).toBeVisible();

  await page.screenshot({
    path: artifactPath("phase7b-work-states-reduced-structured-1280.png"),
    fullPage: true,
  });
  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);
});
