import { expect, test, type Page, type Route } from "@playwright/test";

const API_BASE = "http://127.0.0.1:8000";
const LATEST_PATH = "/api/v1/organization/transparency/live-organization/austria/latest";
const SCENE_PATH = "/api/v1/organization/transparency/live-organization/scene/austria/latest";
const ROOT_ID = "11111111-1111-4111-8111-111111111111";
const OWNER_PATH = `/api/v1/organization/live-organization/austria/${ROOT_ID}/owner-synthesis`;

const CORS_HEADERS = {
  "access-control-allow-credentials": "true",
  "access-control-allow-headers": "content-type,x-gmai-role,x-gmai-user",
  "access-control-allow-methods": "GET,POST,OPTIONS",
  "access-control-allow-origin": "http://127.0.0.1:3000",
  "content-type": "application/json",
};

type JsonResult = {
  status?: number;
  body: unknown;
};

type RecordedRequest = {
  method: string;
  path: string;
  headers: Record<string, string>;
};

type ApiScenario = {
  latest: (call: number) => JsonResult;
  scene?: (call: number) => JsonResult;
  post?: (call: number) => JsonResult;
  firstLatestDelayMs?: number;
};

async function fulfillJson(route: Route, result: JsonResult) {
  await route.fulfill({
    status: result.status ?? 200,
    headers: CORS_HEADERS,
    body: JSON.stringify(result.body),
  });
}

async function installApi(page: Page, scenario: ApiScenario) {
  const recorded: RecordedRequest[] = [];
  let latestCalls = 0;
  let sceneCalls = 0;
  let postCalls = 0;

  await page.route(`${API_BASE}/**`, async (route) => {
    const request = route.request();
    const method = request.method();
    const url = new URL(request.url());

    if (method === "OPTIONS") {
      await route.fulfill({ status: 204, headers: CORS_HEADERS, body: "" });
      return;
    }

    recorded.push({ method, path: url.pathname, headers: request.headers() });

    if (method === "GET" && url.pathname === "/health") {
      await fulfillJson(route, { body: { status: "ok" } });
      return;
    }

    if (method === "GET" && url.pathname === LATEST_PATH) {
      if (latestCalls === 0 && scenario.firstLatestDelayMs) {
        await new Promise((resolve) => setTimeout(resolve, scenario.firstLatestDelayMs));
      }
      const result = scenario.latest(latestCalls);
      latestCalls += 1;
      await fulfillJson(route, result);
      return;
    }

    if (method === "GET" && url.pathname === SCENE_PATH) {
      const result = scenario.scene
        ? scenario.scene(sceneCalls)
        : { body: { established: false, scene: null } };
      sceneCalls += 1;
      await fulfillJson(route, result);
      return;
    }

    if (method === "POST" && url.pathname === OWNER_PATH && scenario.post) {
      const result = scenario.post(postCalls);
      postCalls += 1;
      await fulfillJson(route, result);
      return;
    }

    await fulfillJson(route, {
      status: 404,
      body: { detail: `Unexpected browser test request: ${method} ${url.pathname}` },
    });
  });

  return recorded;
}

function specialist(positionKey: string, index: number) {
  return {
    position_key: positionKey,
    work_item_id: `22222222-2222-4222-8222-22222222222${index}`,
    status: "completed",
    evidence_valid: true,
    evidence_reason: null,
    action_output_id: `output-${index}`,
    execution_attempt_id: `attempt-${index}`,
    agent_run_id: `run-${index}`,
    context_hash: `context-${index}`,
    runtime_binding_hash: `runtime-${index}`,
    latency_ms: 120 + index,
    retry_count: 0,
    confidence: 0.92,
    provider_model_authority: false,
    external_action_authorized: false,
    runtime_quality: {
      contract_version: "austria-live-provider-quality.v1",
      execution_mode: "live_provider",
      provider_outcome: "success",
      configured_provider: "gemini",
      configured_model: "gemini-3.7-flash",
      response_provider: "gemini",
      response_model: "gemini-3.7-flash",
      configured_runtime_matches_binding: true,
      provider_egress_occurred: true,
      fallback_to_template: false,
      prompt_tokens: 800 + index * 10,
      completion_tokens: 200 + index * 10,
      total_tokens: 1000 + index * 20,
      estimated_cost_usd: 0.002 + index * 0.0005,
      grounding_state: "fresh_retrieval",
      evidence_ref_count: 1,
      verified_rule_ref_count: 1,
      source_snapshot_ref_count: 1,
      fresh_retrieval_provenance_present: true,
      provider_model_authority: false,
      warnings: [],
    },
  };
}

function readySnapshot() {
  return {
    generated_at: "2026-08-22T20:00:00Z",
    root_work_item_id: ROOT_ID,
    objective_key: "austria_rwr_shortage_occupation",
    owner_position_key: "mobility_operations_lead",
    root_status: "running",
    cycle_status: "specialists_complete",
    owner_synthesis_state: "pending",
    ready_for_owner_synthesis: true,
    readiness_reasons: [],
    authority_level: "bounded",
    authority_posture: "human_review_gated",
    autonomy_profile_state: null,
    provider_model_authority: false,
    external_action_authorized: false,
    specialist_outputs: [
      specialist("pathway_operations_specialist", 1),
      specialist("regulatory_intelligence_analyst", 2),
    ],
    owner_synthesis: null,
    blockers: [],
    total_latency_ms: 243,
    max_latency_ms: 122,
    total_retry_count: 0,
    activity_count: 0,
    activities: [],
    domain_evidence_refs: [],
    verified_rule_refs: [],
  };
}


function livingScene() {
  return {
    established: true,
    scene: {
      contract_version: "living-organization-scene.v1",
      generated_at: "2026-09-02T01:30:00Z",
      scope: "austria_mobility",
      root_work_item_id: ROOT_ID,
      objective_key: "austria_rwr_shortage_occupation",
      coverage: {
        departments: "projected_from_canonical_positions_and_work",
        missions: "workitem_objective_topology_projection",
        conversations: "not_connected_m3",
        incidents: "not_connected_m3",
        smart_objects: "derived_read_only_scene_metrics",
        presence: "not_asserted_m3",
      },
      deterministic: {
        departments: [
          {
            department_key: "Global Mobility Operations",
            label: "Global Mobility Operations",
            employee_count: 3,
            work_item_count: 3,
            active_blocker_count: 0,
            canonical_basis: "OrganizationPosition.department + OrganizationalWorkItem.department",
          },
        ],
        missions: [
          {
            mission_key: `objective:${ROOT_ID}`,
            objective_key: "austria_rwr_shortage_occupation",
            root_work_item_id: ROOT_ID,
            title: "Austria mobility objective",
            state: "ready_for_owner_synthesis",
            phase_key: "J.1",
            participant_position_keys: [
              "mobility_operations_lead",
              "pathway_operations_specialist",
              "regulatory_intelligence_analyst",
            ],
            work_item_ids: [
              ROOT_ID,
              "22222222-2222-4222-8222-222222222221",
              "22222222-2222-4222-8222-222222222222",
            ],
            blocker_count: 0,
            decision_count: 0,
            projection_only: true,
            canonical_basis: "OrganizationalWorkItem objective_key/parent topology",
          },
        ],
        canonical_projection: true,
        authoritative: false,
        employees: [
          {
            position_key: "mobility_operations_lead",
            title: "Mobility Operations Lead",
            department: "Global Mobility Operations",
            reports_to_position_key: "ceo",
            authority_level: "L2",
            organization_status: "active",
            work_item_id: ROOT_ID,
            work_status: "running",
            semantic_state: "awaiting_owner",
            presence_state: "not_asserted",
            state_reason: "Canonical specialist readiness requires the bounded owner step.",
          },
          {
            position_key: "pathway_operations_specialist",
            title: "Pathway Operations Specialist",
            department: "Global Mobility Operations",
            reports_to_position_key: "mobility_operations_lead",
            authority_level: "L1",
            organization_status: "active",
            work_item_id: "22222222-2222-4222-8222-222222222221",
            work_status: "completed",
            semantic_state: "completed",
            presence_state: "not_asserted",
            state_reason: "The canonical WorkItem is completed.",
          },
          {
            position_key: "regulatory_intelligence_analyst",
            title: "Regulatory Intelligence Analyst",
            department: "Global Mobility Operations",
            reports_to_position_key: "mobility_operations_lead",
            authority_level: "L1",
            organization_status: "active",
            work_item_id: "22222222-2222-4222-8222-222222222222",
            work_status: "completed",
            semantic_state: "completed",
            presence_state: "not_asserted",
            state_reason: "The canonical WorkItem is completed.",
          },
        ],
        work_items: [
          {
            work_item_id: ROOT_ID,
            parent_work_item_id: null,
            title: "Austria mobility objective",
            objective_key: "austria_rwr_shortage_occupation",
            phase_key: "J.1",
            status: "running",
            priority: "normal",
            risk_level: "routine",
            assigned_position_key: "mobility_operations_lead",
            department: "Global Mobility Operations",
            authority_level: "L2",
          },
          {
            work_item_id: "22222222-2222-4222-8222-222222222221",
            parent_work_item_id: ROOT_ID,
            title: "Pathway analysis",
            objective_key: "austria_rwr_shortage_occupation",
            phase_key: "J.1.pathway",
            status: "completed",
            priority: "normal",
            risk_level: "routine",
            assigned_position_key: "pathway_operations_specialist",
            department: "Global Mobility Operations",
            authority_level: "L1",
          },
          {
            work_item_id: "22222222-2222-4222-8222-222222222222",
            parent_work_item_id: ROOT_ID,
            title: "Regulatory analysis",
            objective_key: "austria_rwr_shortage_occupation",
            phase_key: "J.1.regulatory",
            status: "completed",
            priority: "normal",
            risk_level: "routine",
            assigned_position_key: "regulatory_intelligence_analyst",
            department: "Global Mobility Operations",
            authority_level: "L1",
          },
        ],
        conversations: [],
        blockers: [],
        decisions: [],
        incidents: [],
        smart_objects: [
          {
            object_key: `mission-board:${ROOT_ID}`,
            object_type: "mission_board",
            label: "Mission Board",
            state: "ready_for_owner_synthesis",
            metric_label: "WorkItems",
            metric_value: 3,
            projection_only: true,
            canonical_basis: "OrganizationalWorkItem objective topology",
          },
          {
            object_key: `evidence-console:${ROOT_ID}`,
            object_type: "evidence_console",
            label: "Evidence Console",
            state: "empty",
            metric_label: "Evidence + VerifiedRules",
            metric_value: 0,
            projection_only: true,
            canonical_basis: "Persisted context Evidence and VerifiedRule references",
          },
          {
            object_key: `board-beacon:${ROOT_ID}`,
            object_type: "board_beacon",
            label: "Board Attention",
            state: "quiet",
            metric_label: "Board decisions",
            metric_value: 0,
            projection_only: true,
            canonical_basis: "Current ExecutiveDecision records linked to scene WorkItems",
          },
        ],
        rooms: [
          {
            room_key: `mission:${ROOT_ID}`,
            room_type: "mission_room",
            label: "austria_rwr_shortage_occupation",
            state: "ready_for_owner_synthesis",
            metric_label: "WorkItems",
            metric_value: 3,
            projection_only: true,
            canonical_basis: "OrganizationalWorkItem objective topology",
          },
          {
            room_key: `evidence:${ROOT_ID}`,
            room_type: "evidence_lab",
            label: "Evidence Lab",
            state: "empty",
            metric_label: "Evidence + VerifiedRules",
            metric_value: 0,
            projection_only: true,
            canonical_basis: "Persisted context Evidence and VerifiedRule references",
          },
          {
            room_key: `board:${ROOT_ID}`,
            room_type: "board_room",
            label: "Board Room",
            state: "quiet",
            metric_label: "Decisions requiring Board attention",
            metric_value: 0,
            projection_only: true,
            canonical_basis: "ExecutiveDecision records linked to scene WorkItems",
          },
        ],
        relationships: [
          {
            relationship_key: "assignment-owner",
            relationship_type: "assigned_to",
            source_type: "employee",
            source_id: "mobility_operations_lead",
            target_type: "work_item",
            target_id: ROOT_ID,
            canonical_basis: "OrganizationalWorkItem.assigned_position_key",
          },
        ],
      },
      predictive: {
        enabled: false,
        canonical_projection: false,
        authoritative: false,
        status: "reserved_for_m9_phantom_futures",
        items: [],
      },
      environmental: {
        enabled: false,
        canonical_projection: false,
        authoritative: false,
        status: "reserved_for_m9_environmental_memory",
        items: [],
      },
      truth: {
        canonical_authority: "AIOS canonical records and accepted projections",
        scene_authoritative: false,
        renderer_authoritative: false,
        prediction_authoritative: false,
        environmental_authoritative: false,
        scene_mutations_allowed: false,
      },
    },
  };
}

function completedSnapshot() {
  return {
    ...readySnapshot(),
    generated_at: "2026-08-22T20:01:00Z",
    root_status: "completed",
    cycle_status: "human_review_required",
    owner_synthesis_state: "human_review_required",
    owner_synthesis: {
      action_output_id: "owner-output-1",
      activity_id: "owner-activity-1",
      disposition: "human_review_required",
      recommendation: "Proceed to bounded human review; no external action is authorized.",
      confidence: 0.91,
      total_latency_ms: 243,
      max_latency_ms: 122,
      total_retry_count: 0,
      external_action_authorized: false,
      human_review_required: true,
      completed_at: "2026-08-22T20:01:00Z",
    },
    activity_count: 1,
    activities: [
      {
        activity_id: "owner-activity-1",
        role: "owner",
        physical_activity_class: "material",
        constitutional_activity_class: "material",
        board_inspectable: true,
        activity_type: "owner_synthesis",
        title: "Austria owner synthesis",
        summary: "Bounded owner synthesis persisted for human review.",
        actor_type: "organization_position",
        actor_id: "mobility_operations_lead",
        department: "mobility_operations",
        position_key: "mobility_operations_lead",
        authority_level: "bounded",
        source_object_type: "work_item",
        source_object_id: ROOT_ID,
        source_object_version: null,
        work_item_id: ROOT_ID,
        trace_id: null,
        causation_activity_id: null,
        occurred_at: "2026-08-22T20:01:00Z",
      },
    ],
  };
}

function blockedSnapshot() {
  return {
    ...readySnapshot(),
    cycle_status: "blocked",
    ready_for_owner_synthesis: false,
    readiness_reasons: ["Regulated evidence lineage is incomplete."],
    blockers: [
      {
        blocker_id: "blocker-1",
        work_item_id: ROOT_ID,
        blocker_type: "evidence_lineage",
        severity: "high",
        status: "open",
        title: "Professional evidence review required",
        description: "Regulated evidence lineage has not yet been professionally reviewed.",
        accountable_position_key: "mobility_operations_lead",
        requires_human_action: true,
        created_at: "2026-08-22T20:00:00Z",
      },
    ],
  };
}

function expectHeaderAuth(request: RecordedRequest | undefined) {
  expect(request, "expected browser API request").toBeTruthy();
  expect(request?.headers["x-gmai-role"]).toBe("admin");
  expect(request?.headers["x-gmai-user"]).toBe("frontend-operator");
  expect(request?.headers["content-type"]).toBe("application/json");
}


test("renders M.3 canonical scene planes without inventing presence or authority", async ({ page }) => {
  const recorded = await installApi(page, {
    latest: () => ({ body: { established: true, snapshot: readySnapshot() } }),
    scene: () => ({ body: livingScene() }),
  });

  await page.goto("/cockpit/live-organization");

  const sceneSurface = page.locator(".living-scene-shell");
  await expect(sceneSurface.getByRole("heading", { name: "Living Organization Scene" })).toBeVisible();
  await expect(sceneSurface.getByText("M.3 · Canonical scene foundation")).toBeVisible();
  await expect(sceneSurface.getByText("Mission Room", { exact: true })).toBeVisible();
  await expect(sceneSurface.getByText("Evidence Lab", { exact: true }).first()).toBeVisible();
  await expect(sceneSurface.getByText("Board Room", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("Not Asserted", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("Reserved for M.9 · disabled", { exact: true })).toHaveCount(2);
  await expect(page.getByText("three-webgpu", { exact: true })).toBeVisible();
  const smartObjects = sceneSurface.locator('.living-scene-smart-strip[aria-label="Living Organization Smart Objects"]');
  await expect(smartObjects.locator("article").filter({ hasText: "Mission Board" })).toBeVisible();
  await expect(smartObjects.locator("article").filter({ hasText: "Evidence Console" })).toBeVisible();
  await expect(smartObjects.locator("article").filter({ hasText: "Board Attention" })).toBeVisible();
  await expect(page.getByText("Not Connected M3", { exact: true })).toHaveCount(2);
  await expect(page.getByText("Disabled", { exact: true })).toBeVisible();

  expect(recorded.some((item) => item.method === "GET" && item.path === SCENE_PATH)).toBe(true);
  expect(recorded.some((item) => item.method === "POST")).toBe(false);
});

test("shows loading then truthful empty persisted state", async ({ page }) => {
  const recorded = await installApi(page, {
    firstLatestDelayMs: 400,
    latest: () => ({ body: { established: false, snapshot: null } }),
  });

  await page.goto("/cockpit/live-organization");

  await expect(page.getByRole("status").first()).toHaveText("CONNECTING");
  await expect(page.getByRole("heading", { name: "Austria live cycle not yet established" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "No Austria cycle exists yet" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Record bounded owner synthesis" })).toBeDisabled();
  await expect(page.getByText("No persisted J/K/L Austria objective is available.", { exact: false })).toBeVisible();

  expectHeaderAuth(recorded.find((item) => item.method === "GET" && item.path === LATEST_PATH));
});

test("executes the bounded owner command and reloads persisted completion", async ({ page }) => {
  let completed = false;
  const recorded = await installApi(page, {
    latest: () => ({ body: { established: true, snapshot: completed ? completedSnapshot() : readySnapshot() } }),
    post: () => {
      completed = true;
      return {
        body: {
          root_work_item_id: ROOT_ID,
          action_output_id: "owner-output-1",
          activity_id: "owner-activity-1",
          disposition: "human_review_required",
          replayed: false,
        },
      };
    },
  });

  await page.goto("/cockpit/live-organization");

  const command = page.getByRole("button", { name: "Record bounded owner synthesis" });
  await expect(command).toBeEnabled();
  await expect(page.getByText("Owner synthesis is ready for a Board-authorized command.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Persisted specialist runtime signals" })).toBeVisible();
  await expect(page.getByText("gemini · gemini-3.7-flash").first()).toBeVisible();

  await command.click();

  await expect(page.getByText("The Mobility Operations Lead synthesis was persisted and moved the cycle to human review.")).toBeVisible();
  await expect(page.getByText("Proceed to bounded human review; no external action is authorized.")).toBeVisible();
  await expect(command).toBeDisabled();
  await expect(page.getByText("Human review is required.")).toBeVisible();
  await expect(page.getByText("Not authorized", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Persisted organizational activity" })).toBeVisible();
  await expect(page.getByText("Austria owner synthesis", { exact: true })).toBeVisible();
  await expect(page.getByText("No persisted causation link", { exact: false })).toBeVisible();

  const latestRequest = recorded.find((item) => item.method === "GET" && item.path === LATEST_PATH);
  const postRequest = recorded.find((item) => item.method === "POST" && item.path === OWNER_PATH);
  expectHeaderAuth(latestRequest);
  expectHeaderAuth(postRequest);
});

test("renders blocked readiness without allowing owner synthesis", async ({ page }) => {
  const recorded = await installApi(page, {
    latest: () => ({ body: { established: true, snapshot: blockedSnapshot() } }),
  });

  await page.goto("/cockpit/live-organization");

  await expect(page.getByRole("button", { name: "Record bounded owner synthesis" })).toBeDisabled();
  await expect(page.getByText("The backend readiness gate has not authorized owner synthesis.")).toBeVisible();
  await expect(page.getByText("Regulated evidence lineage is incomplete.")).toBeVisible();
  await expect(page.getByText("Professional evidence review required")).toBeVisible();
  await expect(page.getByText("human action required", { exact: false })).toBeVisible();
  expect(recorded.some((item) => item.method === "POST")).toBe(false);
});

test("surfaces exact replay without implying duplicate evidence", async ({ page }) => {
  let replayed = false;
  const recorded = await installApi(page, {
    latest: () => ({ body: { established: true, snapshot: replayed ? completedSnapshot() : readySnapshot() } }),
    post: () => {
      replayed = true;
      return {
        body: {
          root_work_item_id: ROOT_ID,
          action_output_id: "owner-output-1",
          activity_id: "owner-activity-1",
          disposition: "human_review_required",
          replayed: true,
        },
      };
    },
  });

  await page.goto("/cockpit/live-organization");
  await page.getByRole("button", { name: "Record bounded owner synthesis" }).click();

  await expect(page.getByText("The existing bounded owner synthesis was replayed without creating duplicate evidence.")).toBeVisible();
  const postRequest = recorded.find((item) => item.method === "POST" && item.path === OWNER_PATH);
  expectHeaderAuth(postRequest);
});

test("shows backend projection failure as a visible partial state", async ({ page }) => {
  await installApi(page, {
    latest: () => ({
      status: 503,
      body: { detail: "Transparency projection unavailable" },
    }),
  });

  await page.goto("/cockpit/live-organization");

  await expect(page.getByText("Live organization data unavailable.")).toBeVisible();
  await expect(page.getByText("Transparency projection unavailable")).toBeVisible();
  await expect(page.getByRole("status").first()).toHaveText("PARTIAL");
});


test("M.4.0 mounts the optional spatial renderer while Structured remains available", async ({ page }) => {
  await installApi(page, {
    latest: () => ({ body: { established: true, snapshot: readySnapshot() } }),
    scene: () => ({ body: livingScene() }),
  });

  await page.goto("/cockpit/live-organization");

  const stage = page.locator(".living-webgpu-stage");
  await expect(stage).toBeVisible();
  await expect(stage).toHaveAttribute("data-scene-authoritative", "false");
  await expect(stage).toHaveAttribute("data-renderer-phase", "ready", { timeout: 15_000 });
  await expect(stage).toHaveAttribute("data-renderer-backend", /^(webgpu|webgl2)$/);

  const canvas = page.getByTestId("living-webgpu-canvas");
  await expect(canvas).toBeVisible();
  await expect(canvas).toHaveAttribute("data-scene-authoritative", "false");
  await expect(canvas).toHaveAttribute("data-renderer-authority", "none");
  await expect(canvas).toHaveAttribute("data-renderer-active-mounts", "1");
  await expect(page.getByText("STRUCTURED · permanent product surface", { exact: true })).toBeVisible();
  await expect(page.getByText("Canonical scene reference", { exact: true })).toBeVisible();

  const box = await canvas.boundingBox();
  expect(box).toBeTruthy();
  if (!box) return;
  await canvas.click({ position: { x: box.width / 2, y: box.height / 2 } });
  await expect(page.locator(".living-webgpu-overlay strong")).not.toHaveText("No spatial selection");
  await expect(page.locator('.living-webgpu-overlay [data-selection-authority="none"]'))
    .toContainText("Selection changes view focus only; it cannot mutate AIOS.");
});

test("M.4.0 refresh updates projection resources without remounting the GPU renderer", async ({ page }) => {
  const recorded = await installApi(page, {
    latest: () => ({ body: { established: true, snapshot: readySnapshot() } }),
    scene: () => ({ body: livingScene() }),
  });

  await page.goto("/cockpit/live-organization");

  const stage = page.locator(".living-webgpu-stage");
  const canvas = page.getByTestId("living-webgpu-canvas");
  await expect(stage).toHaveAttribute("data-renderer-phase", "ready", { timeout: 15_000 });
  await expect(canvas).toHaveAttribute("data-renderer-active-mounts", "1");

  const initialMountGeneration = Number(await canvas.getAttribute("data-renderer-mount-generation"));
  const initialModelRevision = Number(await canvas.getAttribute("data-renderer-model-revision"));
  const initialResourceCount = Number(await canvas.getAttribute("data-renderer-projection-resources"));
  expect(initialMountGeneration).toBeGreaterThanOrEqual(1);
  expect(initialModelRevision).toBeGreaterThanOrEqual(1);
  expect(initialResourceCount).toBeGreaterThan(0);

  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await expect.poll(
    () => recorded.filter((item) => item.method === "GET" && item.path === SCENE_PATH).length,
  ).toBeGreaterThanOrEqual(2);

  await expect(stage).toHaveAttribute("data-renderer-phase", "ready", { timeout: 15_000 });
  await expect(canvas).toHaveAttribute("data-renderer-active-mounts", "1");
  await expect(canvas).toHaveAttribute("data-renderer-mount-generation", String(initialMountGeneration));
  await expect.poll(async () => Number(await canvas.getAttribute("data-renderer-model-revision")))
    .toBeGreaterThan(initialModelRevision);
  await expect(canvas).toHaveAttribute("data-renderer-projection-resources", String(initialResourceCount));

  const box = await canvas.boundingBox();
  expect(box).toBeTruthy();
  if (!box) return;
  await canvas.click({ position: { x: box.width / 2, y: box.height / 2 } });
  await expect(page.locator(".living-webgpu-overlay strong")).not.toHaveText("No spatial selection");
});

test("M.4.0 keeps Structured usable with WebGPU disabled and reports actual WebGL2 backend", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "gpu", {
      configurable: true,
      value: undefined,
    });
  });
  await installApi(page, {
    latest: () => ({ body: { established: true, snapshot: readySnapshot() } }),
    scene: () => ({ body: livingScene() }),
  });

  await page.goto("/cockpit/live-organization");

  await expect.poll(async () => page.evaluate(() => typeof (navigator as Navigator & { gpu?: unknown }).gpu))
    .toBe("undefined");
  const stage = page.locator(".living-webgpu-stage");
  await expect(stage).toHaveAttribute("data-renderer-phase", "ready", { timeout: 15_000 });
  await expect(stage).toHaveAttribute("data-renderer-backend", "webgl2");
  await expect(page.getByText("STRUCTURED · permanent product surface", { exact: true })).toBeVisible();
  await expect(page.getByText("Canonical scene reference", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Record bounded owner synthesis" })).toBeEnabled();
});
