import { expect, test, type Page } from "@playwright/test";

async function installReadOnlyFixture(page: Page, writes: string[]) {
  await page.route("http://127.0.0.1:8000/**", async (route) => {
    const request = route.request();
    const origin = request.headers().origin || "http://127.0.0.1:3000";
    const headers = {
      "access-control-allow-origin": origin,
      "access-control-allow-credentials": "true",
      "access-control-allow-headers": "content-type,x-gmai-role,x-gmai-user",
      "access-control-allow-methods": "GET,OPTIONS",
    };

    if (request.method() === "OPTIONS") {
      await route.fulfill({ status: 204, headers, body: "" });
      return;
    }

    if (request.method() !== "GET") writes.push(`${request.method()} ${request.url()}`);

    if (new URL(request.url()).pathname === "/health") {
      await route.fulfill({
        status: 200,
        headers,
        contentType: "application/json",
        body: JSON.stringify({ status: "ok", service: "q19-fixture", environment: "test" }),
      });
      return;
    }

    await route.fulfill({
      status: 503,
      headers,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Q19 fixture intentionally leaves governed sources unavailable" }),
    });
  });
}

function expectTreeContains(snapshot: string, labels: readonly string[]) {
  for (const label of labels) expect(snapshot).toContain(label);
}

test("Q19 automated accessibility-tree smoke exposes Owner structure and structured Organization", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.emulateMedia({ colorScheme: "dark", reducedMotion: "reduce" });
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await installReadOnlyFixture(page, writes);

  await page.goto("/cockpit/v2");
  const main = page.locator("main");
  await expect(main).toBeVisible();

  const homeTree = await main.ariaSnapshot();
  expectTreeContains(homeTree, [
    "Know what needs you before you open the details.",
    "Authority & human review",
    "What is moving or blocked",
    "Living Organization",
    "Recent Activity",
  ]);

  const ownerNav = page.getByRole("navigation", { name: "Owner" });
  const navTree = await ownerNav.ariaSnapshot();
  expectTreeContains(navTree, ["Home", "Organization", "Missions", "Intelligence", "Evidence", "Decisions", "History"]);

  const command = page.getByRole("button", { name: "Search / Command", exact: true });
  await command.press("Enter");
  const palette = page.getByRole("dialog", { name: "Navigate AIOS" });
  await expect(palette).toBeVisible();
  const paletteTree = await palette.ariaSnapshot();
  expectTreeContains(paletteTree, ["Navigate AIOS", "Organization", "Missions", "Evidence", "Decisions", "History"]);
  await page.keyboard.press("Escape");

  await page.goto("/cockpit/v2/organization");
  await expect(page.getByRole("radio", { name: "Spatial" })).toBeVisible();
  const organizationTree = await page.locator("main").ariaSnapshot();
  expectTreeContains(organizationTree, [
    "Spatial",
    "Structured",
    "Living HQ visual stage",
    "Structured organization",
  ]);

  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);
});

test("Q19 touch-enabled mobile context executes Owner navigation and controls", async ({ browser }) => {
  test.setTimeout(45_000);
  const context = await browser.newContext({
    baseURL: "http://127.0.0.1:3000",
    viewport: { width: 390, height: 844 },
    hasTouch: true,
    isMobile: true,
    colorScheme: "light",
    reducedMotion: "reduce",
  });
  const page = await context.newPage();
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await installReadOnlyFixture(page, writes);

  try {
    await page.goto("/cockpit/v2");
    expect(await page.evaluate(() => navigator.maxTouchPoints)).toBeGreaterThan(0);

    const command = page.getByRole("button", { name: "Search / Command", exact: true });
    await expect(command).toBeVisible();
    await command.tap({ timeout: 5_000 });

    const palette = page.getByRole("dialog", { name: "Navigate AIOS" });
    await expect(palette).toBeVisible();
    const organizationLink = palette.getByRole("link", { name: /^Organization\b/ });
    await expect(organizationLink).toBeVisible();
    await organizationLink.tap({ timeout: 5_000 });
    await expect(page).toHaveURL(/\/cockpit\/v2\/organization$/);

    const structured = page.getByRole("radio", { name: "Structured" });
    const structuredLabel = structured.locator("xpath=ancestor::label[1]");
    await expect(structuredLabel).toBeVisible();
    await structuredLabel.tap({ timeout: 5_000 });
    await expect(structured).toBeChecked();
    await expect(page.getByRole("heading", { level: 2, name: "Structured organization" })).toBeVisible();

    const ownerNav = page.getByRole("navigation", { name: "Owner" });
    const missions = ownerNav.getByLabel("Missions", { exact: true });
    await missions.scrollIntoViewIfNeeded();
    await expect(missions).toBeVisible();
    await missions.tap({ timeout: 5_000 });
    await expect(page).toHaveURL(/\/cockpit\/v2\/missions$/);

    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth && document.body.scrollWidth <= window.innerWidth)).toBe(true);
    expect(writes).toEqual([]);
    expect(pageErrors).toEqual([]);
  } finally {
    await context.close();
  }
});
