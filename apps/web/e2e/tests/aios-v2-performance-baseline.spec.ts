import { expect, test, type Browser, type Page } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import { performance as nodePerformance } from "node:perf_hooks";
import { resolve } from "node:path";

const ROOT_ID = "11111111-1111-4111-8111-111111111111";
const REPORT_PATH = resolve(process.cwd(), "performance-results/aios-v2-performance-baseline.json");

const scene = {
  contract_version: "living-organization-scene.v5",
  generated_at: "2026-09-07T10:15:00Z",
  scope: "q17_performance_fixture",
  root_work_item_id: ROOT_ID,
  objective_key: "q17_performance_fixture",
  truth: {
    scene_authoritative: false,
    renderer_authoritative: false,
    scene_mutations_allowed: false,
    canonical_authority: "Q17 frozen profiling fixture",
    prediction_authoritative: false,
    environmental_authoritative: false,
  },
  coverage: {
    departments: "covered",
    missions: "covered",
    conversations: "unavailable",
    handoffs: "unavailable",
    blockers: "covered",
    human_actions: "covered",
    risk_escalations: "unavailable",
    incidents: "unavailable",
    smart_objects: "unavailable",
    runtime_costs: "unavailable",
    presence: "not_asserted",
  },
  deterministic: {
    canonical_projection: true,
    authoritative: false,
    departments: [{
      department_key: "Global Mobility Operations",
      label: "Global Mobility Operations",
      employee_count: 1,
      work_item_count: 1,
      active_blocker_count: 0,
      canonical_basis: "Q17 fixture projection",
    }],
    missions: [{
      mission_key: `objective:${ROOT_ID}`,
      objective_key: "q17_performance_fixture",
      root_work_item_id: ROOT_ID,
      title: "Austria profiling fixture mission",
      state: "running",
      phase_key: "Q17",
      participant_position_keys: ["mobility_operations_lead"],
      work_item_ids: [ROOT_ID],
      blocker_count: 0,
      decision_count: 0,
      projection_only: true,
      canonical_basis: "Q17 fixture projection",
    }],
    employees: [{
      position_key: "mobility_operations_lead",
      title: "Mobility Operations Lead",
      department: "Global Mobility Operations",
      reports_to_position_key: "ceo",
      authority_level: "L2",
      organization_status: "active",
      work_item_id: ROOT_ID,
      work_status: "running",
      semantic_state: "working",
      presence_state: "not_asserted",
      state_reason: "Canonical work is active; physical presence is not asserted.",
    }],
    work_items: [{
      work_item_id: ROOT_ID,
      parent_work_item_id: null,
      title: "Austria profiling fixture mission",
      objective_key: "q17_performance_fixture",
      phase_key: "Q17",
      status: "running",
      priority: "normal",
      risk_level: "routine",
      assigned_position_key: "mobility_operations_lead",
      department: "Global Mobility Operations",
      authority_level: "L2",
      created_at: "2026-09-07T09:00:00Z",
      updated_at: "2026-09-07T10:15:00Z",
      due_at: null,
      completed_at: null,
      elapsed_seconds: 4500,
      overdue: false,
      specialist_evidence_valid: null,
      specialist_evidence_reason: null,
    }],
    conversations: [], handoffs: [], blockers: [], human_actions: [], risk_escalations: [], incidents: [], smart_objects: [], rooms: [], relationships: [], decisions: [],
  },
  predictive: { enabled: false, canonical_projection: false, authoritative: false, status: "disabled", items: [] },
  environmental: { enabled: false, canonical_projection: false, authoritative: false, status: "disabled", items: [] },
};

const activities = Array.from({ length: 12 }, (_, index) => ({
  id: `00000000-0000-4000-8000-${String(index + 1).padStart(12, "0")}`,
  activity_class: "work",
  activity_type: "work.updated",
  title: `Recorded work change ${index + 1}`,
  summary: "Frozen bounded Activity fixture for frontend profiling.",
  occurred_at: `2026-09-07T10:${String(index).padStart(2, "0")}:00Z`,
  actor_type: "system",
  actor_id: "q17-fixture",
  department: "Global Mobility Operations",
  position_key: "mobility_operations_lead",
  authority_level: "L2",
  work_item_id: ROOT_ID,
  source_object_type: "WorkItem",
  source_object_id: ROOT_ID,
  source_object_version: String(index + 1),
  correlation_key: null,
  causation_activity_id: null,
  supersedes_activity_id: null,
  created_at: `2026-09-07T10:${String(index).padStart(2, "0")}:00Z`,
}));

async function installFixture(page: Page, writes: string[]) {
  await page.route("http://127.0.0.1:8000/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
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
    if (request.method() !== "GET") writes.push(`${request.method()} ${request.url()}`);
    const json = async (body: unknown) => route.fulfill({ status: 200, headers, contentType: "application/json", body: JSON.stringify(body) });
    if (path === "/health") return json({ status: "ok", service: "fixture", environment: "test" });
    if (path === "/api/v1/organization/board-packet") return json({ generated_at: "2026-09-07T10:15:00Z", pending_decisions: [], open_risks: [], recent_packets: [] });
    if (path === "/api/v1/organization/human-action-requests") return json({ data: [] });
    if (path === "/api/v1/organization/blockers") return json({ data: [] });
    if (path === "/api/v1/organization/activities") return json({ data: activities });
    if (path.endsWith("/scene/austria/latest")) return json({ established: true, scene });
    await route.fulfill({ status: 503, headers, contentType: "application/json", body: JSON.stringify({ detail: "Q17 fixture leaves unrelated governed sources unavailable" }) });
  });
}

async function cdpMetrics(page: Page) {
  const client = await page.context().newCDPSession(page);
  await client.send("Performance.enable");
  const response = await client.send("Performance.getMetrics") as { metrics: Array<{ name: string; value: number }> };
  const metrics = Object.fromEntries(response.metrics.map((entry) => [entry.name, entry.value]));
  await client.detach();
  return {
    jsHeapUsedBytes: metrics.JSHeapUsedSize ?? null,
    jsHeapTotalBytes: metrics.JSHeapTotalSize ?? null,
    nodes: metrics.Nodes ?? null,
    documents: metrics.Documents ?? null,
    layoutCount: metrics.LayoutCount ?? null,
    recalcStyleCount: metrics.RecalcStyleCount ?? null,
    taskDurationSeconds: metrics.TaskDuration ?? null,
  };
}

async function frameCadence(page: Page) {
  return page.evaluate(async () => {
    const intervals: number[] = [];
    let previous = performance.now();
    const finishAt = previous + 1000;
    await new Promise<void>((resolveFrame) => {
      const tick = (now: number) => {
        intervals.push(now - previous);
        previous = now;
        if (now >= finishAt) resolveFrame();
        else requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    });
    const sorted = [...intervals].sort((a, b) => a - b);
    const p95Index = Math.min(sorted.length - 1, Math.floor(sorted.length * 0.95));
    return {
      sampleCount: intervals.length,
      averageIntervalMs: intervals.reduce((sum, value) => sum + value, 0) / intervals.length,
      p95IntervalMs: sorted[p95Index] ?? 0,
      maxIntervalMs: Math.max(...intervals),
      intervalsOver34Ms: intervals.filter((value) => value > 34).length,
    };
  });
}

async function longTasks(page: Page) {
  return page.evaluate(async () => {
    const supported = PerformanceObserver.supportedEntryTypes.includes("longtask");
    if (!supported) return { supported: false, count: 0, totalDurationMs: 0, maxDurationMs: 0 };
    const durations: number[] = [];
    const observer = new PerformanceObserver((list) => durations.push(...list.getEntries().map((entry) => entry.duration)));
    observer.observe({ entryTypes: ["longtask"] });
    await new Promise((resolveWait) => setTimeout(resolveWait, 1000));
    observer.disconnect();
    return {
      supported: true,
      count: durations.length,
      totalDurationMs: durations.reduce((sum, value) => sum + value, 0),
      maxDurationMs: durations.length ? Math.max(...durations) : 0,
    };
  });
}

async function resourceSummary(page: Page) {
  return page.evaluate(() => {
    const resources = performance.getEntriesByType("resource") as PerformanceResourceTiming[];
    return {
      count: resources.length,
      transferBytes: resources.reduce((sum, entry) => sum + entry.transferSize, 0),
      decodedBodyBytes: resources.reduce((sum, entry) => sum + entry.decodedBodySize, 0),
      totalResourceDurationMs: resources.reduce((sum, entry) => sum + entry.duration, 0),
    };
  });
}

async function measureCpuThrottledProxy(browser: Browser) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: "dark", reducedMotion: "reduce" });
  const page = await context.newPage();
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await installFixture(page, writes);
  const client = await context.newCDPSession(page);
  await client.send("Emulation.setCPUThrottlingRate", { rate: 4 });

  const shellStart = nodePerformance.now();
  await page.goto("/cockpit/v2", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { level: 1, name: /Know what needs you/ })).toBeVisible();
  const shellReadyMs = nodePerformance.now() - shellStart;

  const sceneStart = nodePerformance.now();
  await page.goto("/cockpit/v2/organization", { waitUntil: "domcontentloaded" });
  await expect(page.getByLabel("Living HQ visual stage")).toBeVisible();
  const organizationStageReadyMs = nodePerformance.now() - sceneStart;

  const memory = await cdpMetrics(page);
  await client.send("Emulation.setCPUThrottlingRate", { rate: 1 });
  await client.detach();
  await context.close();
  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);
  return { proxy: "Chromium 4x CPU throttling + reduced motion", cpuThrottlingRate: 4, shellReadyMs, organizationStageReadyMs, memory };
}

function expectFiniteRecord(record: Record<string, number | null>) {
  for (const value of Object.values(record)) {
    if (value !== null) expect(Number.isFinite(value)).toBe(true);
  }
}

test("Q17 records a deterministic V2 performance profile without invented budgets", async ({ page, browser }, testInfo) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.emulateMedia({ colorScheme: "dark", reducedMotion: "no-preference" });
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await installFixture(page, writes);

  const homeStart = nodePerformance.now();
  await page.goto("/cockpit/v2", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { level: 1, name: /Know what needs you/ })).toBeVisible();
  const homeReadyMs = nodePerformance.now() - homeStart;

  const commandStart = nodePerformance.now();
  await page.getByRole("button", { name: "Search / Command", exact: true }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  const commandOpenMs = nodePerformance.now() - commandStart;
  await page.keyboard.press("Escape");

  const routeStart = nodePerformance.now();
  await page.getByRole("link", { name: "Organization", exact: true }).click();
  await expect(page.getByLabel("Living HQ visual stage")).toBeVisible();
  const homeToOrganizationMs = nodePerformance.now() - routeStart;

  const directSceneStart = nodePerformance.now();
  await page.goto("/cockpit/v2/organization", { waitUntil: "domcontentloaded" });
  await expect(page.getByLabel("Living HQ visual stage")).toBeVisible();
  const organizationStageReadyMs = nodePerformance.now() - directSceneStart;

  const memory = await cdpMetrics(page);
  const frames = await frameCadence(page);
  const jank = await longTasks(page);
  const resources = await resourceSummary(page);
  const lowPowerProxy = await measureCpuThrottledProxy(browser);

  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);
  expect(frames.sampleCount).toBeGreaterThan(0);
  for (const value of [homeReadyMs, commandOpenMs, homeToOrganizationMs, organizationStageReadyMs, frames.averageIntervalMs, frames.p95IntervalMs, frames.maxIntervalMs, resources.count, resources.transferBytes, resources.decodedBodyBytes]) {
    expect(Number.isFinite(value)).toBe(true);
  }
  expectFiniteRecord(memory);
  expectFiniteRecord(lowPowerProxy.memory);

  const report = {
    contractVersion: "aios-v2-performance-baseline.v1",
    generatedAt: new Date().toISOString(),
    environment: {
      runner: "Playwright Chromium production build",
      viewport: "1280x900",
      fixture: "frozen governed read-only Q17 fixture",
      hardBudgetsEnforced: false,
      note: "Measurements are evidence for later budget setting; CI does not treat runner-specific milliseconds as product truth.",
    },
    shell: { homeReadyMs, commandOpenMs },
    routeTransitions: { homeToOrganizationMs },
    organizationStage: { directReadyMs: organizationStageReadyMs, renderer: "current DOM/CSS Living HQ stage; not a WebGL/GPU memory claim" },
    browserRuntime: { frames, longTasks: jank, memory, resources },
    lowPowerProxy,
  };

  await mkdir(resolve(process.cwd(), "performance-results"), { recursive: true });
  const json = JSON.stringify(report, null, 2) + "\n";
  await writeFile(REPORT_PATH, json, "utf8");
  await testInfo.attach("q17-performance-profile", { body: Buffer.from(json), contentType: "application/json" });
});
