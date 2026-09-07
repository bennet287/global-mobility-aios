import { mkdirSync } from "node:fs";
import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

const CTO_WORK_ITEM = "33333333-3333-4333-8333-333333333331";
const REG_WORK_ITEM = "33333333-3333-4333-8333-333333333332";
const CEO_WORK_ITEM = "33333333-3333-4333-8333-333333333333";

const employees = [
  {
    position_key: "ceo",
    title: "Chief Executive Officer",
    department: "Executive",
    semantic_state: "working",
    work_item_id: CEO_WORK_ITEM,
  },
  {
    position_key: "cto",
    title: "Chief Technology Officer",
    department: "Technology",
    semantic_state: "blocked",
    work_item_id: CTO_WORK_ITEM,
  },
  {
    position_key: "regulatory_lead",
    title: "Regulatory Lead",
    department: "Regulatory",
    semantic_state: "blocked",
    work_item_id: REG_WORK_ITEM,
  },
].map((employee) => ({
  reports_to_position_key: employee.position_key === "ceo" ? null : "ceo",
  authority_level: employee.position_key === "ceo" ? "executive" : "operational",
  organization_status: "active",
  work_status: employee.semantic_state,
  presence_state: "not_asserted",
  state_reason: `Phase 7C canonical ${employee.semantic_state} fixture state`,
  ...employee,
}));

const blockers = [
  {
    blocker_id: "blocker-regulatory-api-evidence",
    work_item_id: CTO_WORK_ITEM,
    blocker_type: "dependency",
    title: "Regulatory API evidence missing",
    description: "A governed regulatory evidence response is required before the technical work can proceed.",
    severity: "high",
    status: "open",
    accountable_position_key: "cto",
    decision_id: null,
    risk_escalation_id: null,
    requires_human_action: true,
    opened_at: "2026-09-07T15:00:00Z",
    due_at: "2026-09-08T12:00:00Z",
    open_elapsed_seconds: 1800,
    overdue: false,
  },
  {
    blocker_id: "blocker-policy-source",
    work_item_id: REG_WORK_ITEM,
    blocker_type: "evidence",
    title: "Policy source requires review",
    description: "The canonical policy source requires professional review.",
    severity: "critical",
    status: "open",
    accountable_position_key: "regulatory_lead",
    decision_id: null,
    risk_escalation_id: "risk-phase7c-1",
    requires_human_action: true,
    opened_at: "2026-09-07T15:05:00Z",
    due_at: null,
    open_elapsed_seconds: 1500,
    overdue: false,
  },
  {
    blocker_id: "blocker-document-gap",
    work_item_id: REG_WORK_ITEM,
    blocker_type: "document",
    title: "Document gap remains open",
    description: "A required source document is not yet available.",
    severity: "medium",
    status: "open",
    accountable_position_key: "regulatory_lead",
    decision_id: null,
    risk_escalation_id: null,
    requires_human_action: false,
    opened_at: "2026-09-07T15:10:00Z",
    due_at: null,
    open_elapsed_seconds: 1200,
    overdue: false,
  },
];

function workItem(work_item_id: string, title: string, assigned_position_key: string, department: string) {
  return {
    work_item_id,
    parent_work_item_id: null,
    title,
    objective_key: "phase7c_blocker_detail",
    phase_key: "phase7c",
    status: assigned_position_key === "ceo" ? "running" : "blocked",
    priority: "high",
    risk_level: "medium",
    assigned_position_key,
    department,
    authority_level: assigned_position_key === "ceo" ? "executive" : "operational",
    created_at: "2026-09-07T14:00:00Z",
    updated_at: "2026-09-07T15:30:00Z",
    due_at: null,
    completed_at: null,
    elapsed_seconds: 5400,
    overdue: false,
    specialist_evidence_valid: null,
    specialist_evidence_reason: null,
  };
}

function scene(blockerCoverage = "organization_blocker_canonical_records") {
  const departments = [
    ["executive", "Executive", 1, 0],
    ["technology", "Technology", 1, 1],
    ["regulatory", "Regulatory", 1, 2],
  ].map(([department_key, label, employee_count, active_blocker_count]) => ({
    department_key,
    label,
    employee_count,
    work_item_count: 1,
    active_blocker_count,
    canonical_basis: "Position.department",
  }));

  return {
    contract_version: "living-organization-scene.v5",
    generated_at: "2026-09-07T15:30:00Z",
    scope: "phase7c_blocker_detail_browser_fixture",
    root_work_item_id: CEO_WORK_ITEM,
    objective_key: "phase7c_blocker_detail",
    coverage: {
      departments: "projected_from_canonical_positions_and_work",
      missions: "workitem_objective_topology_projection",
      conversations: "organization_activity_conversation_lifecycle_v1",
      handoffs: "unavailable",
      blockers: blockerCoverage,
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
          mission_key: "phase7c-blocker-detail",
          objective_key: "phase7c_blocker_detail",
          root_work_item_id: CEO_WORK_ITEM,
          title: "Canonical blocker visibility",
          state: "active",
          phase_key: "phase7c",
          participant_position_keys: employees.map((employee) => employee.position_key),
          work_item_ids: [CEO_WORK_ITEM, CTO_WORK_ITEM, REG_WORK_ITEM],
          blocker_count: blockers.length,
          decision_count: 0,
          projection_only: true,
          canonical_basis: "WorkItem.objective_key",
        },
      ],
      employees,
      work_items: [
        workItem(CEO_WORK_ITEM, "Coordinate blocker integration", "ceo", "Executive"),
        workItem(CTO_WORK_ITEM, "Resolve regulatory API evidence", "cto", "Technology"),
        workItem(REG_WORK_ITEM, "Review regulatory source set", "regulatory_lead", "Regulatory"),
      ],
      conversations: [],
      handoffs: [],
      blockers,
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
  blockerCoverage = "organization_blocker_canonical_records",
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
        body: JSON.stringify({ detail: "Phase 7C fixture source unavailable" }),
      });

    if (pathname === "/health") return json({ status: "ok", service: "fixture", environment: "test" });
    if (pathname === "/api/v1/organization/board-packet") {
      return json({ generated_at: "2026-09-07T15:30:00Z", pending_decisions: [], open_risks: [], recent_packets: [] });
    }
    if (pathname === "/api/v1/organization/human-action-requests") return json({ data: [] });
    if (pathname === "/api/v1/organization/blockers") return json({ data: [] });
    if (pathname === "/api/v1/organization/activities") return json({ data: [] });
    if (pathname.endsWith("/scene/austria/latest")) {
      return json({ established: true, scene: scene(blockerCoverage) });
    }
    return unavailable();
  });
}

function artifactPath(filename: string) {
  const directory = path.join(process.cwd(), "phase7c-artifacts");
  mkdirSync(directory, { recursive: true });
  return path.join(directory, filename);
}

test("Phase 7C binds exact canonical blocker detail to blocked HQ characters without a second animation system", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 960 });
  await page.emulateMedia({ colorScheme: "dark", reducedMotion: "no-preference" });
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await installFixture(page, writes);

  await page.goto("/cockpit/v2/organization");
  const stage = page.getByLabel("Living HQ visual stage");
  await expect(stage).toBeVisible();

  const cto = stage.getByRole("button", { name: /Chief Technology Officer · Technology · Blocked · HIGH blocker/ });
  await expect(cto).toBeVisible();
  const ctoBlocker = cto.locator('[data-aios-v2-blocker="canonical"]');
  await expect(ctoBlocker).toHaveAttribute("data-blocker-count", "1");
  await expect(ctoBlocker).toHaveAttribute("data-single-blocker-id", "blocker-regulatory-api-evidence");
  await expect(ctoBlocker).toHaveAttribute("data-blocker-resolution-claimed", "false");
  await expect(ctoBlocker).toHaveAttribute("data-causal-block-claimed", "false");
  await expect(ctoBlocker.getByText("HIGH", { exact: true })).toBeVisible();

  const regulatory = stage.getByRole("button", { name: /Regulatory Lead · Regulatory · Blocked · 2 blockers/ });
  const regulatoryBlocker = regulatory.locator('[data-aios-v2-blocker="canonical"]');
  await expect(regulatoryBlocker).toHaveAttribute("data-blocker-count", "2");
  await expect(regulatoryBlocker).toHaveAttribute("data-single-blocker-id", "");
  await expect(regulatoryBlocker.getByText("2 BLOCKERS", { exact: true })).toBeVisible();
  await expect(regulatoryBlocker.getByText("CRITICAL", { exact: true })).toHaveCount(0);
  await expect(regulatoryBlocker.getByText("MEDIUM", { exact: true })).toHaveCount(0);

  const ceo = stage.getByRole("button", { name: /Chief Executive Officer · Executive · Working/ });
  await expect(ceo.locator('[data-aios-v2-blocker="canonical"]')).toHaveCount(0);

  await cto.click();
  const inspector = page.getByRole("complementary", { name: "Chief Technology Officer" });
  await expect(inspector).toBeVisible();
  await expect(inspector).toHaveAttribute("data-blocker-details-claimed", "true");
  await expect(inspector).toHaveAttribute("data-blocker-resolution-claimed", "false");
  await expect(inspector.getByText("Regulatory API evidence missing", { exact: true })).toBeVisible();
  await expect(inspector.getByText(/high · dependency · open/i)).toBeVisible();
  await expect(inspector.getByText(/governed regulatory evidence response/i)).toBeVisible();
  await expect(inspector.getByText(/Relationship: Accountable position/i)).toBeVisible();
  await expect(inspector.getByText(/Human action: required/i)).toBeVisible();

  const reviewSurface = page.locator("main");
  await expect(reviewSurface).toBeVisible();
  await reviewSurface.screenshot({
    path: artifactPath("phase7c-blocker-detail-dark-1280.png"),
  });
  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);
});

test("Phase 7C reduced-motion Structured view preserves blocker detail without the HQ renderer", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 960 });
  await page.emulateMedia({ colorScheme: "dark", reducedMotion: "reduce" });
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await installFixture(page, writes);

  await page.goto("/cockpit/v2/organization");
  const spatialBlocked = page.locator('[data-aios-v2-work-state="canonical"][data-work-state-kind="blocked"]');
  await expect(spatialBlocked.first()).toHaveAttribute("data-semantic-animation-active", "false");

  await page.getByRole("radio", { name: "Structured", exact: true }).check();
  await expect(page.getByLabel("Living HQ visual stage")).toHaveCount(0);
  const structured = page.locator('[data-v2-organization-representation="structured"][data-view-placement="primary"]');
  await structured.getByRole("button", { name: /Chief Technology Officer/ }).click();

  const inspector = page.getByRole("complementary", { name: "Chief Technology Officer" });
  await expect(inspector.getByText("Regulatory API evidence missing", { exact: true })).toBeVisible();
  const presentationTruth = inspector.locator("summary").filter({ hasText: "Presentation truth" });
  await expect(presentationTruth).toBeVisible();
  await presentationTruth.click();
  await expect(inspector.getByText(/Blocker resolution claimed: no/i)).toBeVisible();

  const reviewSurface = page.locator("main");
  await expect(reviewSurface).toBeVisible();
  await reviewSurface.screenshot({
    path: artifactPath("phase7c-blocker-detail-reduced-structured-1280.png"),
  });
  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);
});

test("Phase 7C fails closed when canonical blocker coverage is unavailable", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.emulateMedia({ colorScheme: "dark", reducedMotion: "reduce" });
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await installFixture(page, writes, "unavailable");

  await page.goto("/cockpit/v2/organization");
  const stage = page.getByLabel("Living HQ visual stage");
  await expect(stage.locator('[data-aios-v2-blocker="canonical"]')).toHaveCount(0);

  const cto = stage.getByRole("button", { name: /Chief Technology Officer · Technology · Blocked/ });
  await cto.click();
  const inspector = page.getByRole("complementary", { name: "Chief Technology Officer" });
  await expect(inspector.getByText("Blocker details unavailable.", { exact: true })).toBeVisible();
  const blockerWarning = inspector.locator('[data-blocker-coverage="unavailable"]');
  await expect(blockerWarning.getByText(/Coverage: unavailable/)).toBeVisible();
  await expect(inspector.getByText("Regulatory API evidence missing", { exact: true })).toHaveCount(0);

  await page.getByRole("button", { name: /Canonical blocker visibility/ }).click();
  const missionRoom = page.getByLabel("Canonical links");
  await expect(missionRoom.getByText(/Blocker coverage unavailable · unavailable/)).toBeVisible();
  await expect(missionRoom.getByText(/No linked blockers/)).toHaveCount(0);

  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);
});