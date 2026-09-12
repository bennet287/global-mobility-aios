import { mkdirSync } from "node:fs";
import { expect, test, type Page, type Route } from "@playwright/test";

const API_BASE = "http://127.0.0.1:8000";
const ROOT_ID = "11111111-1111-4111-8111-111111111111";
const WORK_ID = "22222222-2222-4222-8222-222222222222";
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
      generated_at: "2026-09-11T04:50:00Z",
      root_work_item_id: ROOT_ID,
      objective_key: "owner_live_hq_proof",
      owner_position_key: "ceo",
      root_status: "running",
      cycle_status: "specialists_active",
      owner_synthesis_state: "pending",
      ready_for_owner_synthesis: false,
      readiness_reasons: ["Canonical specialist work remains active."],
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

function sceneLatest(state: "working" | "blocked") {
  const blocked = state === "blocked";
  return {
    established: true,
    scene: {
      contract_version: "living-organization-scene.v5",
      generated_at: blocked ? "2026-09-11T04:50:10Z" : "2026-09-11T04:50:00Z",
      scope: "owner_live_hq_proof",
      root_work_item_id: ROOT_ID,
      objective_key: "owner_live_hq_proof",
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
          { department_key: "mobility_operations", label: "Mobility Operations", employee_count: 1, work_item_count: 1, active_blocker_count: blocked ? 1 : 0, canonical_basis: "OrganizationPosition.department" },
        ],
        missions: [{
          mission_key: "owner-proof-mission",
          objective_key: "owner_live_hq_proof",
          root_work_item_id: ROOT_ID,
          title: "Owner Living HQ proof mission",
          state: "running",
          phase_key: null,
          participant_position_keys: ["ceo", "mobility_operations_lead"],
          work_item_ids: [ROOT_ID, WORK_ID],
          blocker_count: blocked ? 1 : 0,
          decision_count: 0,
          projection_only: true,
          canonical_basis: "OrganizationalWorkItem root tree",
        }],
        employees: [
          {
            position_key: "ceo",
            title: "Chief Executive Officer",
            department: "executive",
            reports_to_position_key: null,
            authority_level: "L4",
            organization_status: "active",
            work_item_id: ROOT_ID,
            work_status: "running",
            semantic_state: "awaiting_owner",
            presence_state: "not_asserted",
            state_reason: "Owner proof canonical projection.",
          },
          {
            position_key: "mobility_operations_lead",
            title: "Mobility Operations Lead",
            department: "mobility_operations",
            reports_to_position_key: "ceo",
            authority_level: "L2",
            organization_status: "active",
            work_item_id: WORK_ID,
            work_status: blocked ? "blocked" : "running",
            semantic_state: state,
            presence_state: "not_asserted",
            state_reason: blocked ? "Canonical blocker now governs this WorkItem." : "Canonical WorkItem is executing.",
          },
        ],
        work_items: [
          {
            work_item_id: ROOT_ID,
            parent_work_item_id: null,
            title: "Owner proof root",
            objective_key: "owner_live_hq_proof",
            phase_key: null,
            status: "running",
            priority: "high",
            risk_level: "medium",
            assigned_position_key: "ceo",
            department: "executive",
            authority_level: "bounded",
            created_at: "2026-09-11T04:40:00Z",
            updated_at: "2026-09-11T04:50:00Z",
            due_at: null,
            completed_at: null,
            elapsed_seconds: 600,
            overdue: false,
            specialist_evidence_valid: null,
            specialist_evidence_reason: null,
          },
          {
            work_item_id: WORK_ID,
            parent_work_item_id: ROOT_ID,
            title: "Validate live visual state binding",
            objective_key: "owner_live_hq_proof",
            phase_key: null,
            status: blocked ? "blocked" : "running",
            priority: "high",
            risk_level: "medium",
            assigned_position_key: "mobility_operations_lead",
            department: "mobility_operations",
            authority_level: "bounded",
            created_at: "2026-09-11T04:40:00Z",
            updated_at: blocked ? "2026-09-11T04:50:10Z" : "2026-09-11T04:50:00Z",
            due_at: null,
            completed_at: null,
            elapsed_seconds: 600,
            overdue: false,
            specialist_evidence_valid: null,
            specialist_evidence_reason: null,
          },
        ],
        conversations: [],
        handoffs: [],
        blockers: blocked ? [{
          blocker_id: "77777777-7777-4777-8777-777777777777",
          work_item_id: WORK_ID,
          blocker_type: "evidence_lineage",
          title: "Canonical proof blocker",
          description: "Used only to prove a real scene-state transition.",
          severity: "high",
          status: "open",
          accountable_position_key: "mobility_operations_lead",
          decision_id: null,
          risk_escalation_id: null,
          requires_human_action: false,
          opened_at: "2026-09-11T04:50:10Z",
          due_at: null,
          open_elapsed_seconds: 0,
          overdue: false,
        }] : [],
        decisions: [],
        human_actions: [],
        risk_escalations: [],
        incidents: [],
        smart_objects: [
          { object_key: "mission-map", object_type: "mission_map", label: "Mission Map", state: "active", metric_label: "missions", metric_value: 1, projection_only: true, canonical_basis: "Mission projection" },
          { object_key: "evidence-console", object_type: "evidence_console", label: "Evidence Console", state: blocked ? "attention" : "ready", metric_label: "open blockers", metric_value: blocked ? 1 : 0, projection_only: true, canonical_basis: "Evidence projection" },
        ],
        rooms: [
          { room_key: "mission-room", room_type: "mission_room", label: "Mission Room", state: "active", metric_label: "active missions", metric_value: 1, projection_only: true, canonical_basis: "Mission projection" },
          { room_key: "evidence-lab", room_type: "evidence_lab", label: "Evidence Lab", state: blocked ? "attention" : "ready", metric_label: "open blockers", metric_value: blocked ? 1 : 0, projection_only: true, canonical_basis: "Evidence projection" },
          { room_key: "board-room", room_type: "board_room", label: "Board Room", state: "ready", metric_label: "board items", metric_value: 0, projection_only: true, canonical_basis: "Board projection" },
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

async function installApi(page: Page, currentState: () => "working" | "blocked") {
  await page.route(`${API_BASE}/**`, async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (request.method() === "OPTIONS") return route.fulfill({ status: 204, headers: CORS_HEADERS, body: "" });
    if (request.method() === "GET" && url.pathname === "/health") return fulfillJson(route, { status: "ok" });
    if (request.method() === "GET" && url.pathname === LATEST_PATH) return fulfillJson(route, latestSnapshot());
    if (request.method() === "GET" && url.pathname === SCENE_PATH) return fulfillJson(route, sceneLatest(currentState()));
    if (request.method() === "GET" && url.pathname === REPLAY_PATH) return fulfillJson(route, { established: false, replay: null });
    if (request.method() === "GET" && url.pathname === MEMORY_PATH) return fulfillJson(route, { established: false, memory: null });
    return fulfillJson(route, { detail: `Unexpected request: ${request.method()} ${url.pathname}` }, 404);
  });
}

test.beforeAll(() => mkdirSync("living-hq-artifacts", { recursive: true }));

test("13G.1H proves canonical working to blocked transition without page reload", async ({ page }) => {
  let state: "working" | "blocked" = "working";
  await installApi(page, () => state);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/cockpit/live-organization");

  const employee = page.locator('[data-position-key="mobility_operations_lead"]');
  const workforce = page.locator(".living-hq-workforce");
  const architecture = page.locator(".living-hq-architecture");

  await expect(employee).toHaveAttribute("data-live-semantic-state", "working");
  await expect(employee).toHaveAttribute("data-character-state", "focused_work");
  await expect(workforce).toHaveAttribute("data-presentation-only", "true");
  await expect(workforce).toHaveAttribute("data-presence-claimed", "false");
  await expect(workforce).toHaveAttribute("data-locomotion-allowed", "false");
  await expect(architecture).toHaveAttribute("data-authority", "none");
  await expect(page.getByText("Selection changes view focus only; it cannot mutate AIOS.")).toBeVisible();

  await page.screenshot({ path: "living-hq-artifacts/living-hq-owner-proof-working.png", fullPage: true });

  state = "blocked";
  await expect(employee).toHaveAttribute("data-live-semantic-state", "blocked", { timeout: 8000 });
  await expect(employee).toHaveAttribute("data-character-state", "blocked_wait");
  await expect(page.locator('.living-hq-event-reactions[data-blocker-count="1"]')).toBeVisible();
  await expect(page.locator('.living-hq-workforce-neighborhood[data-zone-blocked="1"]')).toBeVisible();

  await page.screenshot({ path: "living-hq-artifacts/living-hq-owner-proof-blocked.png", fullPage: true });
});

test("13G.1H phone proof keeps the live HQ truth contract intact", async ({ page }) => {
  let state: "working" | "blocked" = "blocked";
  await installApi(page, () => state);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/cockpit/live-organization");

  await expect(page.locator('.living-hq-room-axis[data-office-world="continuous"]')).toBeVisible();
  await expect(page.locator('.living-hq-workforce[data-live-binding="canonical-render-model"]')).toBeVisible();
  await expect(page.locator('.living-hq-event-reactions[data-reaction-source="canonical-only"]')).toBeVisible();
  await expect(page.locator('[data-position-key="mobility_operations_lead"]')).toHaveAttribute("data-live-semantic-state", "blocked");

  state = "working";
  await expect(page.locator('[data-position-key="mobility_operations_lead"]')).toHaveAttribute("data-live-semantic-state", "working", { timeout: 8000 });
  await expect(page.locator("body")).not.toHaveCSS("overflow-x", "scroll");
  await page.screenshot({ path: "living-hq-artifacts/living-hq-owner-proof-phone.png", fullPage: true });
});
