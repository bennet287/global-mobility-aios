import { expect, test, type Page } from "@playwright/test";
import fixture from "../../scripts/fixtures/v2-missions.json";

type Response = { status?: number; body: unknown; wait?: Promise<void> };
async function install(page: Page, respond: (call: number) => Response) {
  const observed = { reads: 0, finished: [] as number[], writes: [] as string[] };
  await page.route("http://127.0.0.1:8000/**", async (route) => {
    const request = route.request(); const path = new URL(request.url()).pathname;
    const headers = { "access-control-allow-origin": request.headers().origin || "http://127.0.0.1:3000", "access-control-allow-credentials": "true", "access-control-allow-headers": "content-type,x-gmai-role,x-gmai-user", "access-control-allow-methods": "GET,OPTIONS" };
    if (request.method() === "OPTIONS") { await route.fulfill({ status: 204, headers, body: "" }); return; }
    if (request.method() !== "GET") observed.writes.push(request.method());
    const call = path.endsWith("/scene/austria/latest") ? ++observed.reads : 0;
    const response = call ? respond(call) : { body: { status: "ok" } };
    if (response.wait) await response.wait;
    await route.fulfill({ status: response.status ?? 200, headers, contentType: "application/json", body: JSON.stringify(response.body) });
    if (call) observed.finished.push(call);
  });
  return observed;
}

test("Mission navigation, selection, history and loaded-record search remain read-only", async ({ page }) => {
  const observed = await install(page, () => ({ body: fixture }));
  await page.goto("/cockpit/v2/missions");
  await expect(page.getByRole("navigation", { name: "Owner", exact: true }).getByRole("link", { name: "Missions", exact: true })).toHaveAttribute("aria-current", "page");
  await page.getByRole("region", { name: "Mission results" }).getByRole("button", { name: /Alpha evidence review/ }).click();
  await expect(page).toHaveURL(/mission=mission%3Aalpha/);
  await expect(page.getByRole("heading", { name: "Alpha evidence review", exact: true })).toBeVisible();
  await expect(page.getByText("Alpha missing snapshot", { exact: true })).toBeVisible();
  await expect(page.getByText("Beta work", { exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Close Alpha evidence review" }).click();
  await expect(page.getByRole("region", { name: "Mission results" }).getByRole("button", { name: /Alpha evidence review/ })).toBeFocused();
  await page.getByRole("button", { name: "Navigate AIOS", exact: true }).click();
  await page.getByRole("searchbox", { name: "Find a workspace" }).fill("Beta pathway review");
  await page.getByRole("dialog").getByRole("link", { name: /Beta pathway review/ }).click();
  await expect(page.getByRole("heading", { name: "Beta pathway review", exact: true })).toBeVisible();
  expect(observed.reads).toBe(1); expect(observed.writes).toEqual([]);
  await page.goBack();
  await expect(page.getByRole("heading", { name: "Beta pathway review", exact: true })).toHaveCount(0);
});

test("exact deep links and filters never substitute another Mission", async ({ page }) => {
  await install(page, () => ({ body: fixture }));
  await page.goto("/cockpit/v2/missions?mission=missing&q=Alpha");
  await expect(page.getByText("Selected Mission not returned", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Alpha evidence review", exact: true })).toHaveCount(0);
  await page.getByRole("searchbox", { name: "Search returned Missions" }).fill("does not exist");
  await expect(page.getByText("No Missions match these filters", { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("searchbox", { name: "Search returned Missions" })).toHaveValue("does not exist");
});

test("partial linked records keep the Mission and disclose missing detail", async ({ page }) => {
  const partial = structuredClone(fixture); partial.scene.deterministic.work_items = []; partial.scene.deterministic.employees = [];
  await install(page, () => ({ body: partial }));
  await page.goto("/cockpit/v2/missions?mission=mission%3Aalpha");
  await expect(page.getByText("Mission detail is incomplete", { exact: true })).toBeVisible();
  await expect(page.getByText(/Unavailable: linked work items, linked participants/)).toBeVisible();
  await expect(page.getByText("Alpha work", { exact: true })).toHaveCount(0);
});

test("failure retains labelled stale data; access denial clears it and search", async ({ page }) => {
  const observed = await install(page, (call) => call === 1 ? { body: fixture } : { status: call === 2 ? 503 : 403, body: { detail: "Test source failure" } });
  await page.goto("/cockpit/v2/missions?mission=mission%3Aalpha");
  await expect(page.getByRole("heading", { name: "Alpha evidence review", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Refresh Missions" }).click();
  await expect(page.getByText("Mission refresh failed", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Alpha evidence review", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await expect(page.getByText("Access to Mission records was denied.", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Alpha evidence review", exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Navigate AIOS", exact: true }).click();
  await page.getByRole("searchbox", { name: "Find a workspace" }).fill("Alpha evidence review");
  await expect(page.getByRole("dialog").getByRole("link")).toHaveCount(0);
  expect(observed.writes).toEqual([]);
});

test("an older refresh cannot overwrite a newer snapshot", async ({ page }) => {
  let release!: () => void; const delayed = new Promise<void>((resolve) => { release = resolve; });
  const newer = structuredClone(fixture); newer.scene.deterministic.missions[0].title = "Newer Alpha snapshot";
  const observed = await install(page, (call) => ({ body: call === 3 ? newer : fixture, wait: call === 2 ? delayed : undefined }));
  await page.goto("/cockpit/v2/missions?mission=mission%3Aalpha");
  await expect(page.getByRole("heading", { name: "Alpha evidence review", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Refresh Missions" }).click();
  await expect.poll(() => observed.reads).toBe(2);
  await page.getByRole("button", { name: "Refresh Missions" }).click();
  await expect(page.getByRole("heading", { name: "Newer Alpha snapshot", exact: true })).toBeVisible();
  release(); await expect.poll(() => observed.finished.includes(2)).toBe(true);
  await expect(page.getByRole("heading", { name: "Alpha evidence review", exact: true })).toHaveCount(0);
});

for (const established of [false, true]) test(`empty and unestablished states stay explicit (established=${established})`, async ({ page }) => {
  const empty = structuredClone(fixture); empty.scene.deterministic.missions = [];
  await install(page, () => ({ body: established ? empty : { established: false, scene: null } }));
  await page.goto("/cockpit/v2/missions");
  await expect(page.getByText(established ? "No Missions returned" : "Mission projection not established", { exact: true })).toBeVisible();
});

test("mobile reduced-motion Mission inspection uses Q4 primitives without overflow", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 390, height: 844 }); await page.emulateMedia({ reducedMotion: "reduce" });
  const errors: string[] = []; page.on("pageerror", (error) => errors.push(error.message));
  const observed = await install(page, () => ({ body: fixture }));
  await page.goto("/cockpit/v2/missions?mission=mission%3Aalpha");
  await expect(page.getByRole("heading", { name: "Alpha evidence review", exact: true })).toBeVisible();
  await page.getByText("Mission lineage and coverage", { exact: true }).focus(); await page.keyboard.press("Enter");
  await expect(page.getByText("Synthetic test work topology", { exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath("q5-mobile.png"), fullPage: true });
  expect(observed.writes).toEqual([]); expect(errors).toEqual([]);
});
