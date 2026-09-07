import { mkdirSync } from "node:fs";
import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

const CEO_WORK_ITEM = "55555555-5555-4555-8555-555555555550";
const CTO_WORK_ITEM = "55555555-5555-4555-8555-555555555551";

const employees = [
  {
    position_key: "ceo", title: "Chief Executive Officer", department: "Executive",
    reports_to_position_key: null, authority_level: "executive", organization_status: "active",
    work_item_id: CEO_WORK_ITEM, work_status: "running", semantic_state: "working",
    presence_state: "not_asserted", state_reason: "Phase 7F canonical accountable-position fixture",
  },
  {
    position_key: "cto", title: "Chief Technology Officer", department: "Technology",
    reports_to_position_key: "ceo", authority_level: "operational", organization_status: "active",
    work_item_id: CTO_WORK_ITEM, work_status: "running", semantic_state: "working",
    presence_state: "not_asserted", state_reason: "Phase 7F non-escalated roster fixture",
  },
];

function workItem(work_item_id: string, title: string, assigned_position_key: string, department: string) {
  return {
    work_item_id, parent_work_item_id: work_item_id === CEO_WORK_ITEM ? null : CEO_WORK_ITEM,
    title, objective_key: "phase7f_owner_board_attention", phase_key: "phase7f", status: "running",
    priority: "high", risk_level: "high", assigned_position_key, department,
    authority_level: assigned_position_key === "ceo" ? "executive" : "operational",
    created_at: "2026-09-07T20:30:00Z", updated_at: "2026-09-07T20:45:00Z",
    due_at: null, completed_at: null, elapsed_seconds: 900, overdue: false,
    specialist_evidence_valid: null, specialist_evidence_reason: null,
  };
}

function scene(
  humanActionCoverage = "organization_human_action_request_open_records",
  riskEscalationCoverage = "risk_escalation_open_records",
) {
  return {
    contract_version: "living-organization-scene.v5",
    generated_at: "2026-09-07T20:45:00Z",
    scope: "phase7f_owner_board_attention_browser_fixture",
    root_work_item_id: CEO_WORK_ITEM,
    objective_key: "phase7f_owner_board_attention",
    coverage: {
      departments: "projected_from_canonical_positions_and_work",
      missions: "workitem_objective_topology_projection",
      conversations: "organization_activity_conversation_lifecycle_v1",
      handoffs: "unavailable",
      blockers: "organization_blocker_canonical_records",
      human_actions: humanActionCoverage,
      risk_escalations: riskEscalationCoverage,
      incidents: "unavailable", smart_objects: "unavailable", runtime_costs: "unavailable",
      presence: "not_asserted_m6",
    },
    deterministic: {
      canonical_projection: true,
      authoritative: false,
      departments: [
        { department_key: "executive", label: "Executive", employee_count: 1, work_item_count: 1, active_blocker_count: 0, canonical_basis: "Position.department" },
        { department_key: "technology", label: "Technology", employee_count: 1, work_item_count: 1, active_blocker_count: 0, canonical_basis: "Position.department" },
      ],
      missions: [{
        mission_key: "phase7f-attention", objective_key: "phase7f_owner_board_attention",
        root_work_item_id: CEO_WORK_ITEM, title: "Governed escalation review", state: "active",
        phase_key: "phase7f", participant_position_keys: ["ceo", "cto"],
        work_item_ids: [CEO_WORK_ITEM, CTO_WORK_ITEM], blocker_count: 0, decision_count: 1,
        projection_only: true, canonical_basis: "OrganizationalWorkItem objective_key/parent topology",
      }],
      employees,
      work_items: [
        workItem(CEO_WORK_ITEM, "Review Owner and Board attention", "ceo", "Executive"),
        workItem(CTO_WORK_ITEM, "Prepare governed evidence", "cto", "Technology"),
      ],
      conversations: [], handoffs: [], blockers: [],
      decisions: [{
        decision_id: "55555555-5555-4555-8555-555555555560",
        decision_key: "phase7f-board-decision", title: "Board review of governed route",
        question: "Should the governed route proceed?", recommendation: "Review canonical evidence before deciding.",
        status: "pending_board", authority_level: "board", decision_owner_position: "board",
        work_item_id: CEO_WORK_ITEM, evidence_items: [], record_fingerprint: "phase7f-decision-fingerprint",
        source_object_type: "OrganizationalWorkItem", source_object_id: CEO_WORK_ITEM, source_object_version: "1",
        supersedes_decision_id: null, superseded_by_decision_id: null, is_current: true,
        required_owner_action: true, decided_at: null, created_at: "2026-09-07T20:35:00Z",
        superseded_by_created_at: null, superseded_in_projection_week: false,
      }],
      human_actions: [{
        request_id: "55555555-5555-4555-8555-555555555570", request_type: "review",
        title: "Owner evidence review required", instructions: "Review the canonical escalation evidence bundle.",
        status: "required", priority: "high", required_role: "owner", assigned_human_id: null,
        authority_level: "owner", work_item_id: CEO_WORK_ITEM,
        decision_id: "55555555-5555-4555-8555-555555555560", blocker_id: null,
        requested_at: "2026-09-07T20:37:00Z", due_at: null,
        canonical_basis: "OrganizationHumanActionRequest canonical record",
      }],
      risk_escalations: [
        {
          risk_id: "55555555-5555-4555-8555-555555555580", risk_key: "phase7f-explicit-board",
          category: "governance", severity: "high", title: "Explicit Board attention route",
          description: "Canonical risk explicitly requires Board attention.", status: "open",
          accountable_position_key: "ceo", escalated_to_position_key: "board", work_item_id: CEO_WORK_ITEM,
          requires_board_attention: true, is_emergency: false, evidence_items: [],
          created_at: "2026-09-07T20:39:00Z",
          canonical_basis: "RiskEscalation canonical record linked to scene WorkItem",
        },
        {
          risk_id: "55555555-5555-4555-8555-555555555581", risk_key: "phase7f-critical-not-board",
          category: "delivery", severity: "critical", title: "Critical risk without Board-attention flag",
          description: "Severity is critical, but canonical Board attention is false.", status: "open",
          accountable_position_key: "cto", escalated_to_position_key: "ceo", work_item_id: CTO_WORK_ITEM,
          requires_board_attention: false, is_emergency: false, evidence_items: [],
          created_at: "2026-09-07T20:40:00Z",
          canonical_basis: "RiskEscalation canonical record linked to scene WorkItem",
        },
      ],
      incidents: [], smart_objects: [], rooms: [], relationships: [],
    },
    predictive: { enabled: false, canonical_projection: false, authoritative: false, status: "disabled", items: [] },
    environmental: { enabled: false, canonical_projection: false, authoritative: false, status: "disabled", items: [] },
    truth: {
      canonical_authority: "Canonical organization records", scene_authoritative: false,
      renderer_authoritative: false, prediction_authoritative: false,
      environmental_authoritative: false, scene_mutations_allowed: false,
    },
  };
}

async function installFixture(
  page: Page,
  writes: string[],
  humanActionCoverage = "organization_human_action_request_open_records",
  riskEscalationCoverage = "risk_escalation_open_records",
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
    if (request.method() === "OPTIONS") return route.fulfill({ status: 204, headers, body: "" });
    if (request.method() !== "GET") writes.push(`${request.method()} ${pathname}`);
    const json = (body: unknown) => route.fulfill({ status: 200, headers, contentType: "application/json", body: JSON.stringify(body) });
    const unavailable = () => route.fulfill({ status: 503, headers, contentType: "application/json", body: JSON.stringify({ detail: "Phase 7F fixture source unavailable" }) });
    if (pathname === "/health") return json({ status: "ok", service: "fixture", environment: "test" });
    if (pathname === "/api/v1/organization/board-packet") return json({ generated_at: "2026-09-07T20:45:00Z", pending_decisions: [], open_risks: [], recent_packets: [] });
    if (pathname === "/api/v1/organization/human-action-requests") return json({ data: [] });
    if (pathname === "/api/v1/organization/blockers") return json({ data: [] });
    if (pathname === "/api/v1/organization/activities") return json({ data: [] });
    if (pathname.endsWith("/scene/austria/latest")) return json({ established: true, scene: scene(humanActionCoverage, riskEscalationCoverage) });
    return unavailable();
  });
}

function artifactPath(filename: string) {
  const directory = path.join(process.cwd(), "phase7f-artifacts");
  mkdirSync(directory, { recursive: true });
  return path.join(directory, filename);
}

test("Phase 7F renders exact Owner and Board attention without severity, meeting or presence inference", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.emulateMedia({ colorScheme: "dark", reducedMotion: "no-preference" });
  const writes: string[] = []; const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await installFixture(page, writes);
  await page.goto("/cockpit/v2/organization");

  const signal = page.locator('[data-aios-v2-owner-board-escalation="canonical-attention"][data-variant="spatial"]');
  await expect(signal).toBeVisible();
  await expect(signal).toHaveAttribute("data-board-attention-count", "3");
  await expect(signal).toHaveAttribute("data-board-meeting-claimed", "false");
  await expect(signal).toHaveAttribute("data-approval-claimed", "false");
  await expect(signal).toHaveAttribute("data-physical-presence-claimed", "false");
  await expect(signal.getByText(/Owner evidence review required/)).toBeVisible();
  await expect(signal.getByText(/Explicit Board attention route/)).toBeVisible();
  await expect(signal.getByText(/Critical risk without Board-attention flag/)).toBeVisible();
  await expect(signal.getByText(/3 canonical attention items/)).toBeVisible();

  const stage = page.getByLabel("Living HQ visual stage");
  await stage.getByRole("button", { name: /Chief Executive Officer/ }).click();
  const inspector = page.getByRole("complementary", { name: "Chief Executive Officer" });
  const riskSection = inspector.getByRole("region", { name: "Canonical risk escalation routes" });
  await expect(riskSection.getByText(/Explicit Board attention route/)).toBeVisible();
  await expect(riskSection.getByText(/Critical risk without Board-attention flag/)).toBeVisible();
  await expect(riskSection.getByText(/Board attention explicitly required/)).toBeVisible();
  await expect(inspector).toHaveAttribute("data-board-meeting-claimed", "false");
  await expect(inspector).toHaveAttribute("data-presence-claimed", "false");

  await page.locator("main").screenshot({ path: artifactPath("phase7f-owner-board-escalation-dark-1280.png") });
  expect(writes).toEqual([]); expect(pageErrors).toEqual([]);
});

test("Phase 7F Structured reduced-motion view preserves canonical attention without HQ", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.emulateMedia({ colorScheme: "dark", reducedMotion: "reduce" });
  const writes: string[] = []; const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await installFixture(page, writes);
  await page.goto("/cockpit/v2/organization");
  await page.getByRole("radio", { name: "Structured", exact: true }).check();
  await expect(page.getByLabel("Living HQ visual stage")).toHaveCount(0);
  const signal = page.locator('[data-aios-v2-owner-board-escalation="canonical-attention"][data-variant="structured"]');
  await expect(signal).toHaveAttribute("data-board-attention-count", "3");
  await expect(signal).toHaveAttribute("data-board-meeting-claimed", "false");
  await expect(signal.getByText(/no Board meeting · no approval inferred · no physical presence or room attendance/)).toBeVisible();
  await page.locator("main").screenshot({ path: artifactPath("phase7f-owner-board-escalation-reduced-structured-1280.png") });
  expect(writes).toEqual([]); expect(pageErrors).toEqual([]);
});

test("Phase 7F preserves available decision attention but marks aggregate unavailable when governed coverage is incomplete", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  const writes: string[] = []; const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await installFixture(page, writes, "unavailable", "unavailable");
  await page.goto("/cockpit/v2/organization");

  const signal = page.locator('[data-aios-v2-owner-board-escalation="canonical-attention"][data-variant="spatial"]');
  await expect(signal).toBeVisible();
  await expect(signal).toHaveAttribute("data-board-attention-count", "unavailable");
  await expect(signal.getByText(/Board review of governed route/)).toBeVisible();
  await expect(signal.getByText(/partial coverage/)).toBeVisible();
  await expect(signal.getByText(/will not infer a required human role/)).toBeVisible();
  await expect(signal.getByText(/will not infer Board attention from severity or room placement/)).toBeVisible();
  await expect(page.locator('[data-board-attention-count="0"]')).toHaveCount(0);
  expect(writes).toEqual([]); expect(pageErrors).toEqual([]);
});
