import { expect, test, type Page } from "@playwright/test";

const decisionPath = "/api/v1/organization/decisions/records";
const decision = { id: "review-1", title: "Review the bounded evidence pack", question: "Is this pack ready for professional review?", recommendation: "Return incomplete evidence for revision.", status: "pending_board", is_current: true, authority_level: "board", decision_owner_position: "owner", updated_at: "2026-09-01T10:00:00Z", source_version: "fixture-v1" };
type Fixture = { status?: number; body: unknown; delay?: number };
async function api(page: Page, resolve: (path: string, method: string, call: number, body: unknown) => Fixture) {
  const writes: { path: string; body: unknown }[] = [];
  const counts = new Map<string, number>();
  await page.route("http://127.0.0.1:8000/**", async (route) => {
    const request = route.request(); const path = new URL(request.url()).pathname; const method = request.method();
    const headers = { "access-control-allow-origin": request.headers().origin || "http://127.0.0.1:3016", "access-control-allow-credentials": "true", "access-control-allow-headers": "content-type,x-gmai-role,x-gmai-user", "access-control-allow-methods": "GET,POST,OPTIONS" };
    if (method === "OPTIONS") { await route.fulfill({ status: 204, headers, body: "" }); return; }
    const body = request.postDataJSON();
    if (method !== "GET") writes.push({ path, body });
    const key = `${method}:${path}`; const call = (counts.get(key) ?? 0) + 1; counts.set(key, call);
    const result = path === "/health" ? { body: { status: "ok" } } : resolve(path, method, call, body);
    if (result.delay) await new Promise((done) => setTimeout(done, result.delay));
    await route.fulfill({ status: result.status ?? 200, headers, contentType: "application/json", body: JSON.stringify(result.body) });
  });
  return writes;
}
const unavailable: Fixture = { status: 503, body: { detail: "Unavailable fixture source" } };
const recordPage = (data: unknown[]) => ({ data, total: data.length, page: 1, page_size: 25, total_pages: 1 });

test("all Owner workspaces recover their navigation when sources fail", async ({ page }) => {
  const errors: string[] = []; page.on("pageerror", (error) => errors.push(error.message));
  const writes = await api(page, () => unavailable);
  for (const route of ["", "/organization", "/missions", "/evidence", "/intelligence", "/decisions", "/history"]) {
    await page.goto(`/cockpit/v2${route}`);
    await expect(page.getByRole("main")).toBeVisible();
    await expect(page.getByRole("navigation", { name: "Owner", exact: true }).getByRole("link")).toHaveCount(7);
    await expect(page.getByRole("button", { name: "Help", exact: true })).toBeVisible();
  }
  expect(errors).toEqual([]); expect(writes).toEqual([]);
});

test("Evidence retains exact source lineage and labels partial data", async ({ page }, testInfo) => {
  const writes = await api(page, (path) => {
    if (path.endsWith("/verified-rules")) return { body: { verified_rules: [{ id: "rule-a", rule_key: "Test evidence requirement", statement: "Synthetic statement for UI verification only.", country: "AT", domain: "test", active: false, official_source_id: "source-a", source_snapshot_id: "snapshot-missing", retirement_reason: "Replaced in test fixture" }] } };
    if (path.endsWith("/official-sources")) return { body: { sources: [{ id: "source-a", name: "Fixture official source", url: "https://example.org/source-a", active: true, source_type: "government" }, { id: "source-b", name: "Unrelated source", url: "javascript:alert(1)", active: true }] } };
    return unavailable;
  });
  await page.goto("/cockpit/v2/evidence?rule=rule-a");
  await expect(page.getByRole("heading", { name: "Test evidence requirement" })).toBeVisible();
  await expect(page.getByText("Linked snapshot not in the returned snapshot set.")).toBeVisible();
  await expect(page.getByText(/Unavailable: Source snapshots/)).toBeVisible();
  await expect(page.getByRole("link", { name: /Fixture official source/ }).first()).toHaveAttribute("href", "https://example.org/source-a");
  await expect(page.locator('a[href^="javascript:"]')).toHaveCount(0);
  await page.getByLabel("Appearance", { exact: true }).selectOption("light");
  await expect(page.locator(".aios-v2-root")).toHaveAttribute("data-v2-theme", "light");
  await page.screenshot({ path: testInfo.outputPath("evidence-light.png"), fullPage: true });
  await page.getByRole("button", { name: /Navigate AIOS/ }).click();
  await page.getByRole("searchbox", { name: "Find a workspace" }).fill("Test evidence requirement");
  await expect(page.getByRole("dialog").getByRole("link", { name: /Test evidence requirement/ })).toHaveAttribute("href", "/cockpit/v2/evidence?rule=rule-a");
  expect(writes).toEqual([]);
});

for (const changed of [false, true]) test(`Board action requires review and reconciles current state (changed=${changed})`, async ({ page }) => {
  let recorded = false;
  const writes = await api(page, (path, method, call) => {
    if (path === decisionPath) return { body: recordPage([decision]) };
    if (path === `${decisionPath}/review-1`) return { body: { ...decision, status: recorded ? "returned" : "pending_board", is_current: !(changed && call > 1) } };
    if (path.endsWith("/references")) return { body: recordPage([]) };
    if (method === "POST") { recorded = true; return { body: { ...decision, status: "returned" } }; }
    return unavailable;
  });
  await page.goto("/cockpit/v2/decisions");
  await page.getByRole("button", { name: /Review the bounded evidence pack/ }).click();
  const submit = page.getByRole("button", { name: "Record: returned", exact: true });
  await expect(submit).toBeDisabled();
  await page.getByRole("textbox", { name: "Rationale" }).fill("Fixture evidence needs revision.");
  await expect(submit).toBeDisabled();
  expect(writes).toEqual([]);
  await page.getByRole("checkbox", { name: /I reviewed this decision/ }).check();
  await submit.click();
  if (changed) {
    await expect(page.getByRole("alert").filter({ hasText: "This decision changed" })).toBeVisible();
    await expect(submit).toBeDisabled(); expect(writes).toEqual([]);
  } else {
    await expect(page.getByText("Recorded status: returned.")).toBeVisible();
    expect(writes).toEqual([{ path: "/api/v1/organization/decisions/review-1/board-decision", body: { decision: "returned", reason: "Fixture evidence needs revision." } }]);
    await expect(submit).toHaveCount(0);
  }
});

test("guided highlights are opt-in, keyboard dismissible and do not write", async ({ page }) => {
  const writes = await api(page, () => unavailable);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/cockpit/v2");
  await expect(page.locator(".driver-popover")).toHaveCount(0);
  const help = page.getByRole("button", { name: "Help", exact: true });
  await help.click();
  await expect(page.getByRole("region", { name: "Workspace guide" })).toBeVisible();
  await page.getByRole("button", { name: "Start guided highlights" }).click();
  await expect(page.locator(".driver-popover")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.locator(".driver-popover")).toHaveCount(0);
  await expect(help).toBeFocused(); expect(writes).toEqual([]);
});

test("mobile appearance and evidence layout remain usable", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await api(page, () => unavailable);
  await page.goto("/cockpit/v2/evidence");
  await page.getByRole("button", { name: "Open navigation", exact: true }).click();
  await page.getByLabel("Mobile appearance").selectOption("light");
  await page.keyboard.press("Escape");
  await expect(page.locator(".aios-v2-root")).toHaveAttribute("data-v2-theme", "light");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath("evidence-mobile-light.png"), fullPage: true });
});
