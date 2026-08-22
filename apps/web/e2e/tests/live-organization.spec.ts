import { expect, test, type Page, type Route } from "@playwright/test";

const API_BASE = "http://127.0.0.1:8000";
const LATEST_PATH = "/api/v1/organization/transparency/live-organization/austria/latest";
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

test("shows loading then truthful empty persisted state", async ({ page }) => {
  const recorded = await installApi(page, {
    firstLatestDelayMs: 400,
    latest: () => ({ body: { established: false, snapshot: null } }),
  });

  await page.goto("/cockpit/live-organization");

  await expect(page.getByRole("status").first()).toHaveText("loading");
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

  await command.click();

  await expect(page.getByText("The Mobility Operations Lead synthesis was persisted and moved the cycle to human review.")).toBeVisible();
  await expect(page.getByText("Proceed to bounded human review; no external action is authorized.")).toBeVisible();
  await expect(command).toBeDisabled();
  await expect(page.getByText("Human review is required.")).toBeVisible();
  await expect(page.getByText("Not authorized", { exact: true })).toBeVisible();

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
  await expect(page.getByRole("status").first()).toHaveText("Needs attention");
});
