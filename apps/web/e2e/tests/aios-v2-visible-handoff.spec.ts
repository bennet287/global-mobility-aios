import { mkdirSync } from "node:fs";
import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

const HANDOFF_ACTIVITY_ID = "act-phase7a-browser-handoff";
const HANDOFF_COVERAGE = "organization_work_assigned_activity_v1";
const WORK_ITEM_ID = "11111111-1111-4111-8111-111111111111";

function sceneFor(coverage = HANDOFF_COVERAGE) {
  return {
    contract_version: "living-organization-scene.v5",
    generated_at: "2026-09-07T12:40:00Z",
    scope: "phase7a_visible_handoff_browser_fixture",
    root_work_item_id: WORK_ITEM_ID,
    objective_key: "phase7a_visible_handoff",
    coverage: {
      departments: "projected_from_canonical_positions_and_work",
      missions: "workitem_objective_topology_projection",
      conversations: "unavailable",
      handoffs: coverage,
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
          work_item_count: 0,
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
          mission_key: "phase7a-visible-handoff",
          objective_key: "phase7a_visible_handoff",
          root_work_item_id: WORK_ITEM_ID,
          title: "Canonical handoff visibility",
          state: "active",
          phase_key: "phase7a",
          participant_position_keys: ["ceo", "cto"],
          work_item_ids: [WORK_ITEM_ID],
          blocker_count: 0,
          decision_count: 0,
          projection_only: true,
          canonical_basis: "WorkItem.objective_key",
        },
      ],
      employees: [
        {
          position_key: "ceo",
          title: "Chief Executive Officer",
          department: "Executive",
          reports_to_position_key: null,
          authority_level: "executive",
          organization_status: "active",
          work_item_id: null,
          work_status: null,
          semantic_state: "working",
          presence_state: "not_asserted",
          state_reason: "Browser fixture canonical roster",
        },
        {
          position_key: "cto",
          title: "Chief Technology Officer",
          department: "Technology",
          reports_to_position_key: "ceo",
          authority_level: "executive",
          organization_status: "active",
          work_item_id: WORK_ITEM_ID,
          work_status: "assigned",
          semantic_state: "working",
          presence_state: "not_asserted",
          state_reason: "Browser fixture canonical roster",
        },
      ],
      work_items: [
        {
          work_item_id: WORK_ITEM_ID,
          parent_work_item_id: null,
          title: "Canonical handoff visibility",
          objective_key: "phase7a_visible_handoff",
          phase_key: "phase7a",
          status: "assigned",
          priority: "high",
          risk_level: "low",
          assigned_position_key: "cto",
          department: "Technology",
          authority_level: "executive",
          created_at: "2026-09-07T12:30:00Z",
          updated_at: "2026-09-07T12:40:00Z",
          due_at: null,
          completed_at: null,
          elapsed_seconds: 600,
          overdue: false,
          specialist_evidence_valid: null,
          specialist_evidence_reason: null,
        },
      ],
      conversations: [],
      handoffs: [
        {
          activity_id: HANDOFF_ACTIVITY_ID,
          work_item_id: WORK_ITEM_ID,
          previous_position_key: "ceo",
          assigned_position_key: "cto",
          status: "assigned",
          occurred_at: "2026-09-07T12:40:00Z",
          causation_activity_id: "act-phase7a-browser-cause",
          canonical_basis: `OrganizationActivity:${HANDOFF_ACTIVITY_ID}`,
        },
      ],
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

async function installFixture(page: Page, writes: string[], coverage = HANDOFF_COVERAGE) {
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
        body: JSON.stringify({ detail: "Phase 7A fixture source unavailable" }),
      });

    if (pathname === "/health") return json({ status: "ok", service: "fixture", environment: "test" });
    if (pathname === "/api/v1/organization/board-packet") {
      return json({ generated_at: "2026-09-07T12:40:00Z", pending_decisions: [], open_risks: [], recent_packets: [] });
    }
    if (pathname === "/api/v1/organization/human-action-requests") return json({ data: [] });
    if (pathname === "/api/v1/organization/blockers") return json({ data: [] });
    if (pathname === "/api/v1/organization/activities") return json({ data: [] });
    if (pathname.endsWith("/scene/austria/latest")) {
      return json({ established: true, scene: sceneFor(coverage) });
    }
    return unavailable();
  });
}

function artifactPath(filename: string) {
  const directory = path.join(process.cwd(), "phase7a-artifacts");
  mkdirSync(directory, { recursive: true });
  return path.join(directory, filename);
}

test("Phase 7A renders the real covered canonical handoff in Living HQ with one finite semantic sequence", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 960 });
  await page.emulateMedia({ colorScheme: "dark", reducedMotion: "no-preference" });
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await installFixture(page, writes);

  await page.goto("/cockpit/v2/organization");
  const stage = page.getByLabel("Living HQ visual stage");
  const signal = stage.getByLabel(
    "Recorded canonical handoff from Chief Executive Officer to Chief Technology Officer",
  );
  await expect(signal).toBeVisible();
  await expect(signal).toHaveAttribute("data-handoff-coverage", HANDOFF_COVERAGE);
  await expect(signal).toHaveAttribute("data-handoff-activity-id", HANDOFF_ACTIVITY_ID);
  await expect(signal).toHaveAttribute("data-semantic-animation-supported", "true");
  await expect(signal).toHaveAttribute("data-visualization-mode", "bounded-transfer-sequence");
  await expect(signal.getByText("assigned", { exact: true })).toBeVisible();
  await expect(signal.getByText(`Activity · ${HANDOFF_ACTIVITY_ID}`, { exact: true })).toBeVisible();
  await expect(signal.getByText("2026-09-07 12:40:00 UTC", { exact: true })).toBeVisible();
  await expect(signal.getByText(/no physical travel, presence, conversation, completion or canonical mutation/i)).toBeVisible();

  const workObject = signal.locator('[data-handoff-role="work-object"]');
  const animation = await workObject.evaluate((element) => {
    const style = getComputedStyle(element);
    return {
      name: style.animationName,
      iterationCount: style.animationIterationCount,
      duration: style.animationDuration,
    };
  });
  expect(animation.name).not.toBe("none");
  expect(animation.iterationCount).toBe("1");
  expect(animation.duration).toBe("1.28s");

  await page.waitForTimeout(1450);
  await page.screenshot({
    path: artifactPath("phase7a-visible-handoff-dark-1280.png"),
    fullPage: true,
  });
  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);
});

test("Phase 7A Structured representation keeps the same canonical relation without travel animation", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 960 });
  await page.emulateMedia({ colorScheme: "dark", reducedMotion: "reduce" });
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await installFixture(page, writes);

  await page.goto("/cockpit/v2/organization");
  await page.getByRole("radio", { name: "Structured", exact: true }).check();
  const structured = page.locator('[data-v2-organization-representation="structured"]');
  const signal = structured.getByLabel(
    "Recorded canonical handoff from Chief Executive Officer to Chief Technology Officer",
  );
  await expect(signal).toBeVisible();
  await expect(signal).toHaveAttribute("data-handoff-activity-id", HANDOFF_ACTIVITY_ID);
  await expect(signal).toHaveAttribute("data-visualization-mode", "static-relation");
  await expect(signal.getByText(`Work item ${WORK_ITEM_ID}`, { exact: true })).toBeVisible();
  await expect(signal.getByText("Chief Executive Officer", { exact: true })).toBeVisible();
  await expect(signal.getByText("Chief Technology Officer", { exact: true })).toBeVisible();

  const workObject = signal.locator('[data-handoff-role="work-object"]');
  const animationName = await workObject.evaluate((element) => getComputedStyle(element).animationName);
  expect(animationName).toBe("none");
  await page.screenshot({
    path: artifactPath("phase7a-visible-handoff-reduced-structured-1280.png"),
    fullPage: true,
  });
  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);
});

test("Phase 7A fails closed when handoff coverage is unavailable", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  const writes: string[] = [];
  await installFixture(page, writes, "unavailable");
  await page.goto("/cockpit/v2/organization");

  await expect(page.locator('[data-aios-v2-handoff-signal="spatial"]')).toHaveCount(0);
  await expect(page.locator('[data-aios-v2-handoff-signal="structured"]')).toHaveCount(0);
  expect(writes).toEqual([]);
});
