import { mkdirSync } from "node:fs";
import { expect, test, type Page, type Route } from "@playwright/test";

const API_BASE = "http://127.0.0.1:8000";
const ROOT_ID = "11111111-1111-4111-8111-111111111111";
const LATEST_PATH = "/api/v1/organization/transparency/live-organization/austria/latest";
const SCENE_PATH = "/api/v1/organization/transparency/live-organization/scene/austria/latest";
const REPLAY_PATH = "/api/v1/organization/transparency/live-organization/replay/austria/latest";
const MEMORY_PATH = "/api/v1/organization/transparency/live-organization/environmental-memory/austria/latest";

const CORS_HEADERS = {
  "access-control-allow-credentials": "true",
  "access-control-allow-headers": "content-type,x-gmai-role,x-gmai-user",
  "access-control-allow-methods": "GET,POST,OPTIONS",
  "access-control-allow-origin": "http://127.0.0.1:3000",
  "content-type": "application/json",
};

async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({ status, headers: CORS_HEADERS, body: JSON.stringify(body) });
}

function latestSnapshot() {
  return {
    established: true,
    snapshot: {
      generated_at: "2026-09-09T18:30:00Z",
      root_work_item_id: ROOT_ID,
      objective_key: "austria_rwr_shortage_occupation",
      owner_position_key: "ceo",
      root_status: "running",
      cycle_status: "specialists_active",
      owner_synthesis_state: "pending",
      ready_for_owner_synthesis: false,
      readiness_reasons: ["Specialist work is still active."],
      authority_level: "bounded",
      authority_posture: "human_review_gated",
      autonomy_profile_state: null,
      provider_model_authority: false,
      external_action_authorized: false,
      specialist_outputs: [],
      owner_synthesis: null,
      blockers: [],
      total_latency_ms: 0,
      max_latency_ms: 0,
      total_retry_count: 0,
      activity_count: 0,
      activities: [],
      domain_evidence_refs: [],
      verified_rule_refs: [],
      source_snapshot_refs: [],
    },
  };
}

function workItem(
  id: string,
  title: string,
  department: string,
  assignedPosition: string,
  status: string,
  parent: string | null = ROOT_ID,
) {
  return {
    work_item_id: id,
    parent_work_item_id: parent,
    title,
    objective_key: "austria_rwr_shortage_occupation",
    phase_key: null,
    status,
    priority: "high",
    risk_level: "medium",
    assigned_position_key: assignedPosition,
    department,
    authority_level: "bounded",
    created_at: "2026-09-09T16:00:00Z",
    updated_at: "2026-09-09T18:20:00Z",
    due_at: null,
    completed_at: status === "completed" ? "2026-09-09T18:00:00Z" : null,
    elapsed_seconds: 7200,
    overdue: false,
    specialist_evidence_valid: status === "completed" ? true : null,
    specialist_evidence_reason: null,
  };
}

function employee(
  positionKey: string,
  title: string,
  department: string,
  semanticState: string,
  workItemId: string | null,
) {
  return {
    position_key: positionKey,
    title,
    department,
    reports_to_position_key: positionKey === "ceo" ? null : "ceo",
    authority_level: positionKey === "ceo" ? "L4" : "L2",
    organization_status: "active",
    work_item_id: workItemId,
    work_status: semanticState === "completed" ? "completed" : "running",
    semantic_state: semanticState,
    presence_state: "not_asserted",
    state_reason: "Canonical semantic-state projection for visible-review proof.",
  };
}

function sceneLatest() {
  const operationsWork = "22222222-2222-4222-8222-222222222221";
  const regulatoryWork = "22222222-2222-4222-8222-222222222222";
  const technologyWork = "22222222-2222-4222-8222-222222222223";
  return {
    established: true,
    scene: {
      contract_version: "living-organization-scene.v5",
      generated_at: "2026-09-09T18:30:00Z",
      scope: "austria_mobility_latest_work_tree",
      root_work_item_id: ROOT_ID,
      objective_key: "austria_rwr_shortage_occupation",
      coverage: {
        departments: "established",
        missions: "established",
        conversations: "established",
        handoffs: "established",
        blockers: "established",
        human_actions: "established",
        risk_escalations: "established",
        incidents: "unavailable",
        smart_objects: "established",
        runtime_costs: "unavailable",
        presence: "not_asserted",
      },
      deterministic: {
        canonical_projection: true,
        authoritative: false,
        departments: [
          { department_key: "executive", label: "Executive Office", employee_count: 1, work_item_count: 1, active_blocker_count: 0, canonical_basis: "OrganizationPosition.department" },
          { department_key: "mobility_operations", label: "Mobility Operations", employee_count: 2, work_item_count: 1, active_blocker_count: 1, canonical_basis: "OrganizationPosition.department" },
          { department_key: "regulatory_intelligence", label: "Regulatory Intelligence", employee_count: 1, work_item_count: 1, active_blocker_count: 0, canonical_basis: "OrganizationPosition.department" },
          { department_key: "technology", label: "Technology Office", employee_count: 1, work_item_count: 1, active_blocker_count: 0, canonical_basis: "OrganizationPosition.department" },
        ],
        missions: [
          {
            mission_key: "austria-mobility-cycle",
            objective_key: "austria_rwr_shortage_occupation",
            root_work_item_id: ROOT_ID,
            title: "Austria mobility cycle",
            state: "running",
            phase_key: null,
            participant_position_keys: ["ceo", "mobility_operations_lead", "regulatory_intelligence_analyst", "cto"],
            work_item_ids: [ROOT_ID, operationsWork, regulatoryWork, technologyWork],
            blocker_count: 1,
            decision_count: 1,
            projection_only: true,
            canonical_basis: "OrganizationalWorkItem root tree",
          },
        ],
        employees: [
          employee("ceo", "Chief Executive Officer", "executive", "awaiting_owner", ROOT_ID),
          employee("mobility_operations_lead", "Mobility Operations Lead", "mobility_operations", "working", operationsWork),
          employee("pathway_operations_specialist", "Pathway Operations Specialist", "mobility_operations", "blocked", operationsWork),
          employee("regulatory_intelligence_analyst", "Regulatory Intelligence Analyst", "regulatory_intelligence", "queued", regulatoryWork),
          employee("cto", "Chief Technology Officer", "technology", "completed", technologyWork),
        ],
        work_items: [
          workItem(ROOT_ID, "Austria mobility executive cycle", "executive", "ceo", "running", null),
          workItem(operationsWork, "Coordinate mobility pathway evidence", "mobility_operations", "mobility_operations_lead", "running"),
          workItem(regulatoryWork, "Validate regulated pathway rules", "regulatory_intelligence", "regulatory_intelligence_analyst", "queued"),
          workItem(technologyWork, "Verify automation runtime envelope", "technology", "cto", "completed"),
        ],
        conversations: [],
        handoffs: [],
        blockers: [
          {
            blocker_id: "77777777-7777-4777-8777-777777777777",
            work_item_id: operationsWork,
            blocker_type: "evidence_lineage",
            title: "Employer evidence review required",
            description: "Professional evidence lineage is still under review.",
            severity: "high",
            status: "open",
            accountable_position_key: "mobility_operations_lead",
            decision_id: null,
            risk_escalation_id: null,
            requires_human_action: true,
            opened_at: "2026-09-09T17:00:00Z",
            due_at: null,
            open_elapsed_seconds: 5400,
            overdue: false,
          },
        ],
        decisions: [],
        human_actions: [],
        risk_escalations: [],
        incidents: [],
        smart_objects: [
          { object_key: "mission-map", object_type: "mission_map", label: "Mission Map", state: "active", metric_label: "missions", metric_value: 1, projection_only: true, canonical_basis: "Mission projection" },
          { object_key: "evidence-console", object_type: "evidence_console", label: "Evidence Console", state: "attention", metric_label: "open blockers", metric_value: 1, projection_only: true, canonical_basis: "Evidence projection" },
          { object_key: "board-desk", object_type: "board_desk", label: "Board Desk", state: "ready", metric_label: "decisions", metric_value: 0, projection_only: true, canonical_basis: "Board projection" },
          { object_key: "owner-inbox", object_type: "owner_inbox", label: "Owner Inbox", state: "attention", metric_label: "owner actions", metric_value: 1, projection_only: true, canonical_basis: "Owner projection" },
        ],
        rooms: [
          { room_key: "mission-room", room_type: "mission_room", label: "Mission Room", state: "active", metric_label: "active missions", metric_value: 1, projection_only: true, canonical_basis: "Mission room projection" },
          { room_key: "evidence-lab", room_type: "evidence_lab", label: "Evidence Lab", state: "attention", metric_label: "open evidence blockers", metric_value: 1, projection_only: true, canonical_basis: "Evidence room projection" },
          { room_key: "board-room", room_type: "board_room", label: "Board Room", state: "ready", metric_label: "board items", metric_value: 0, projection_only: true, canonical_basis: "Board room projection" },
        ],
        relationships: [],
      },
      predictive: { enabled: false, canonical_projection: false, authoritative: false, status: "reserved", items: [] },
      environmental: { enabled: false, canonical_projection: false, authoritative: false, status: "reserved", items: [] },
      truth: {
        canonical_authority: "backend_domain_records",
        scene_authoritative: false,
        renderer_authoritative: false,
        prediction_authoritative: false,
        environmental_authoritative: false,
        scene_mutations_allowed: false,
      },
    },
  };
}

async function installApi(page: Page) {
  await page.route(`${API_BASE}/**`, async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (request.method() === "OPTIONS") {
      await route.fulfill({ status: 204, headers: CORS_HEADERS, body: "" });
      return;
    }
    if (request.method() === "GET" && url.pathname === "/health") return fulfillJson(route, { status: "ok" });
    if (request.method() === "GET" && url.pathname === LATEST_PATH) return fulfillJson(route, latestSnapshot());
    if (request.method() === "GET" && url.pathname === SCENE_PATH) return fulfillJson(route, sceneLatest());
    if (request.method() === "GET" && url.pathname === REPLAY_PATH) return fulfillJson(route, { established: false, replay: null });
    if (request.method() === "GET" && url.pathname === MEMORY_PATH) return fulfillJson(route, { established: false, memory: null });
    return fulfillJson(route, { detail: `Unexpected visible-review request: ${request.method()} ${url.pathname}` }, 404);
  });
}

async function assertFlagship(page: Page) {
  const scene = page.locator(".living-scene-shell");
  const stage = page.locator(".living-webgpu-stage");
  const architecture = page.locator(".living-hq-architecture");
  const roster = page.locator(".living-hq-department-deck");

  await expect(scene.getByRole("heading", { name: "Living Organization Scene" })).toBeVisible();
  await expect(stage).toBeVisible();
  await expect(architecture.getByRole("heading", { name: "Executive HQ chambers" })).toBeVisible();
  await expect(architecture.locator(".living-hq-room")).toHaveCount(3);
  await expect(architecture.locator(".living-hq-smart-object-list article")).toHaveCount(4);
  await expect(roster.getByRole("heading", { name: "Department character deck" })).toBeVisible();
  await expect(roster.locator(".living-hq-department-pod")).toHaveCount(4);
  await expect(roster.locator(".living-hq-character")).toHaveCount(5);
  await expect(roster).toHaveAttribute("data-presentation-only", "true");
  await expect(roster).toHaveAttribute("data-presence-claimed", "false");
  await expect(roster).toHaveAttribute("data-locomotion-allowed", "false");
  await expect(architecture).toHaveAttribute("data-presentation-only", "true");
  await expect(architecture).toHaveAttribute("data-authority", "none");
}

test.beforeAll(() => mkdirSync("living-hq-artifacts", { recursive: true }));

test("Living HQ flagship desktop visible review", async ({ page }) => {
  await installApi(page);
  await page.setViewportSize({ width: 1440, height: 1100 });
  await page.goto("/cockpit/live-organization");
  await assertFlagship(page);
  await page.screenshot({ path: "living-hq-artifacts/living-hq-desktop.png", fullPage: true });
});

test("Living HQ flagship phone visible review", async ({ page }) => {
  await installApi(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/cockpit/live-organization");
  await assertFlagship(page);
  await expect(page.locator("body")).not.toHaveCSS("overflow-x", "scroll");
  await page.screenshot({ path: "living-hq-artifacts/living-hq-phone.png", fullPage: true });
});
