import { mkdirSync } from "node:fs";
import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

const CEO_WORK_ITEM = "77777777-7777-4777-8777-777777777770";
const CTO_WORK_ITEM = "77777777-7777-4777-8777-777777777771";
const BLOCKER_ID = "77777777-7777-4777-8777-777777777780";
const DECISION_ID = "77777777-7777-4777-8777-777777777790";

function employee(
  position_key: string,
  title: string,
  department: string,
  work_item_id: string,
  work_status: string,
  semantic_state: string,
) {
  return {
    position_key,
    title,
    department,
    reports_to_position_key: position_key === "ceo" ? null : "ceo",
    authority_level: position_key === "ceo" ? "executive" : "operational",
    organization_status: "active",
    work_item_id,
    work_status,
    semantic_state,
    presence_state: "not_asserted",
    state_reason: "Phase 7G canonical transition fixture",
  };
}

function workItem(input: {
  work_item_id: string;
  title: string;
  assigned_position_key: string;
  department: string;
  status: string;
  completed_at: string | null;
}) {
  return {
    work_item_id: input.work_item_id,
    parent_work_item_id: input.work_item_id === CEO_WORK_ITEM ? null : CEO_WORK_ITEM,
    title: input.title,
    objective_key: "phase7g_completion_resolution",
    phase_key: "phase7g",
    status: input.status,
    priority: "high",
    risk_level: "normal",
    assigned_position_key: input.assigned_position_key,
    department: input.department,
    authority_level: input.assigned_position_key === "ceo" ? "executive" : "operational",
    created_at: "2026-09-07T20:00:00Z",
    updated_at: "2026-09-07T20:45:00Z",
    due_at: null,
    completed_at: input.completed_at,
    elapsed_seconds: input.completed_at ? 2700 : 3600,
    overdue: false,
    specialist_evidence_valid: false,
    specialist_evidence_reason: "Structural completion does not establish execution-evidence success.",
  };
}

function scene(valid = true) {
  const completionAt = valid ? "2026-09-07T20:45:00Z" : null;
  return {
    contract_version: "living-organization-scene.v5",
    generated_at: "2026-09-07T21:00:00Z",
    scope: "phase7g_completion_resolution_browser_fixture",
    root_work_item_id: CEO_WORK_ITEM,
    objective_key: "phase7g_completion_resolution",
    coverage: {
      departments: "projected_from_canonical_positions_and_work",
      missions: "workitem_objective_topology_projection",
      conversations: "organization_activity_conversation_lifecycle_v1",
      handoffs: "unavailable",
      blockers: "organization_blocker_canonical_records",
      human_actions: "organization_human_action_request_open_records",
      risk_escalations: "risk_escalation_open_records",
      incidents: "unavailable",
      smart_objects: "unavailable",
      runtime_costs: "unavailable",
      presence: "not_asserted_m6",
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
          canonical_basis: "OrganizationPosition.department",
        },
        {
          department_key: "technology",
          label: "Technology",
          employee_count: 1,
          work_item_count: 1,
          active_blocker_count: 0,
          canonical_basis: "OrganizationPosition.department",
        },
      ],
      missions: [{
        mission_key: "phase7g-transition-mission",
        objective_key: "phase7g_completion_resolution",
        root_work_item_id: CEO_WORK_ITEM,
        title: "Canonical completion review",
        state: "active",
        phase_key: "phase7g",
        participant_position_keys: ["ceo", "cto"],
        work_item_ids: [CEO_WORK_ITEM, CTO_WORK_ITEM],
        blocker_count: 1,
        decision_count: 1,
        projection_only: true,
        canonical_basis: "OrganizationalWorkItem objective_key/parent topology",
      }],
      employees: [
        employee("ceo", "Chief Executive Officer", "Executive", CEO_WORK_ITEM, "running", "working"),
        employee("cto", "Chief Technology Officer", "Technology", CTO_WORK_ITEM, "completed", "completed"),
      ],
      work_items: [
        workItem({
          work_item_id: CEO_WORK_ITEM,
          title: "Review canonical transitions",
          assigned_position_key: "ceo",
          department: "Executive",
          status: "running",
          completed_at: null,
        }),
        workItem({
          work_item_id: CTO_WORK_ITEM,
          title: "Deliver governed technical package",
          assigned_position_key: "cto",
          department: "Technology",
          status: "completed",
          completed_at: completionAt,
        }),
      ],
      conversations: [],
      handoffs: [],
      blockers: [{
        blocker_id: BLOCKER_ID,
        work_item_id: CTO_WORK_ITEM,
        blocker_type: "dependency",
        title: "Evidence dependency",
        description: "Canonical dependency requiring governed resolution.",
        severity: "high",
        status: valid ? "resolved" : "mitigated",
        accountable_position_key: "cto",
        decision_id: null,
        risk_escalation_id: null,
        requires_human_action: false,
        opened_at: "2026-09-07T19:30:00Z",
        due_at: null,
        resolved_at: "2026-09-07T20:30:00Z",
        resolution_summary: "Required dependency evidence was supplied.",
        resolving_actor_type: "human",
        resolving_actor_id: "owner-1",
        waived_at: null,
        waived_by_human_id: null,
        waiver_reason: null,
        open_elapsed_seconds: 3600,
        overdue: false,
      }],
      decisions: [{
        decision_id: DECISION_ID,
        decision_key: "phase7g-governed-outcome",
        title: "Approve governed technical package",
        question: "Is the package accepted?",
        recommendation: "Accept after canonical review.",
        status: "approved",
        authority_level: "L4",
        decision_owner_position: "board",
        work_item_id: CTO_WORK_ITEM,
        evidence_items: [],
        record_fingerprint: "phase7g-decision-fingerprint",
        source_object_type: "organizational_work_item",
        source_object_id: CTO_WORK_ITEM,
        source_object_version: "1",
        supersedes_decision_id: null,
        superseded_by_decision_id: null,
        is_current: true,
        required_owner_action: false,
        decided_at: valid ? "2026-09-07T20:50:00Z" : null,
        created_at: "2026-09-07T20:10:00Z",
        superseded_by_created_at: null,
        superseded_in_projection_week: false,
      }],
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

async function installFixture(page: Page, writes: string[], valid = true) {
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
      return route.fulfill({ status: 204, headers, body: "" });
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
      body: JSON.stringify({ detail: "Phase 7G fixture source unavailable" }),
    });

    if (pathname === "/health") return json({ status: "ok", service: "fixture", environment: "test" });
    if (pathname === "/api/v1/organization/board-packet") {
      return json({ generated_at: "2026-09-07T21:00:00Z", pending_decisions: [], open_risks: [], recent_packets: [] });
    }
    if (pathname === "/api/v1/organization/human-action-requests") return json({ data: [] });
    if (pathname === "/api/v1/organization/blockers") return json({ data: [] });
    if (pathname === "/api/v1/organization/activities") return json({ data: [] });
    if (pathname.endsWith("/scene/austria/latest")) return json({ established: true, scene: scene(valid) });
    return unavailable();
  });
}

function artifactPath(filename: string) {
  const directory = path.join(process.cwd(), "phase7g-artifacts");
  mkdirSync(directory, { recursive: true });
  return path.join(directory, filename);
}

test("Phase 7G Spatial view exposes exact completion and resolution evidence without physical inference", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.emulateMedia({ colorScheme: "dark", reducedMotion: "no-preference" });
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await installFixture(page, writes, true);
  await page.goto("/cockpit/v2/organization");

  const signal = page.locator('[data-aios-v2-completion-resolution="canonical-evidence"][data-variant="spatial"]');
  await expect(signal).toBeVisible();
  await expect(signal).toHaveAttribute("data-completion-inferred-from-animation", "false");
  await expect(signal).toHaveAttribute("data-physical-celebration-claimed", "false");
  await expect(signal).toHaveAttribute("data-physical-presence-claimed", "false");
  await expect(signal).toHaveAttribute("data-locomotion-claimed", "false");
  await expect(signal.getByText(/3 canonical transitions/)).toBeVisible();
  await expect(signal.getByText(/Deliver governed technical package/)).toBeVisible();
  await expect(signal.getByText(/Evidence dependency/)).toBeVisible();
  await expect(signal.getByText(/Approve governed technical package/)).toBeVisible();

  const stage = page.getByLabel("Living HQ visual stage");
  await stage.getByRole("button", { name: /Chief Technology Officer/ }).click();
  const inspector = page.getByRole("complementary", { name: "Chief Technology Officer" });
  await expect(inspector).toHaveAttribute("data-explicit-completion-resolution-claimed", "canonical-records-only");
  await expect(inspector).toHaveAttribute("data-completion-inferred-from-animation", "false");
  const transitionSection = inspector.getByRole("region", { name: "Canonical completion and resolution evidence" });
  await expect(transitionSection.locator('[data-transition-kind="work_completed"]')).toHaveCount(1);
  await expect(transitionSection.locator('[data-transition-kind="blocker_resolved"]')).toHaveCount(1);
  await expect(transitionSection.locator('[data-transition-kind="decision_outcome"]')).toHaveCount(1);
  await expect(transitionSection.getByText(/Required dependency evidence was supplied/)).toBeVisible();
  await expect(transitionSection.getByText(/Resolver: human:owner-1/)).toBeVisible();

  await page.getByRole("button", { name: /Canonical completion review/ }).click();
  const missionRoom = page.getByRole("region", { name: /Canonical completion review/ });
  await expect(missionRoom.locator('[data-canonical-completion-resolution="true"]')).toBeVisible();
  await expect(missionRoom.locator('[data-mission-completion-resolution-count="3"]')).toBeVisible();

  await page.locator("main").screenshot({
    path: artifactPath("phase7g-completion-resolution-dark-1280.png"),
    fullPage: true,
  });
  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);
});

test("Phase 7G Structured reduced-motion view preserves the same canonical transition semantics without HQ", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.emulateMedia({ colorScheme: "dark", reducedMotion: "reduce" });
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await installFixture(page, writes, true);
  await page.goto("/cockpit/v2/organization");
  await page.getByRole("radio", { name: "Structured", exact: true }).check();

  await expect(page.getByLabel("Living HQ visual stage")).toHaveCount(0);
  const signal = page.locator('[data-aios-v2-completion-resolution="canonical-evidence"][data-variant="structured"]');
  await expect(signal).toBeVisible();
  await expect(signal.getByText(/3 canonical transitions/)).toBeVisible();
  await expect(signal).toHaveAttribute("data-completion-inferred-from-animation", "false");
  await expect(signal).toHaveAttribute("data-physical-celebration-claimed", "false");
  await expect(signal.getByText(/no completion inferred from animation or elapsed time/)).toBeVisible();

  await page.locator("main").screenshot({
    path: artifactPath("phase7g-completion-resolution-reduced-structured-1280.png"),
    fullPage: true,
  });
  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);
});

test("Phase 7G fails closed when status exists without the complete canonical transition evidence", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await installFixture(page, writes, false);
  await page.goto("/cockpit/v2/organization");

  await expect(page.locator('[data-aios-v2-completion-resolution="canonical-evidence"][data-variant="spatial"]')).toHaveCount(0);
  await page.getByRole("button", { name: /Canonical completion review/ }).click();
  const missionRoom = page.getByRole("region", { name: /Canonical completion review/ });
  await expect(missionRoom.locator('[data-mission-completion-resolution-count="0"]')).toBeVisible();
  await expect(missionRoom.getByText(/No explicit canonical completion or resolution transition is linked to this Mission/)).toBeVisible();
  await expect(missionRoom.locator('[data-transition-kind="work_completed"]')).toHaveCount(0);
  await expect(missionRoom.locator('[data-transition-kind="blocker_resolved"]')).toHaveCount(0);
  await expect(missionRoom.locator('[data-transition-kind="decision_outcome"]')).toHaveCount(0);
  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);
});
