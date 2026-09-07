import { expect, test } from "@playwright/test";

async function installReadOnlyFixture(page: import("@playwright/test").Page, writes: string[]) {
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
        body: JSON.stringify({ status: "ok", service: "fixture", environment: "test" }),
      });
      return;
    }

    await route.fulfill({
      status: 503,
      headers,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Q12 fixture intentionally leaves governed sources unavailable" }),
    });
  });
}

for (const width of [1280, 390]) {
  test(`Q12 semantics and keyboard focus remain operable at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await page.emulateMedia({ colorScheme: "dark", reducedMotion: "reduce" });
    const writes: string[] = [];
    const pageErrors: string[] = [];
    page.on("pageerror", (error) => pageErrors.push(error.message));
    await installReadOnlyFixture(page, writes);

    await page.goto("/cockpit/v2");

    expect(await page.locator("main").count()).toBe(1);
    await expect(page.getByRole("heading", { level: 1, name: "Know what needs you before you open the details." })).toBeVisible();
    for (const heading of ["Authority & human review", "What is moving or blocked", "Living Organization", "Recent Activity"]) {
      await expect(page.getByRole("heading", { level: 2, name: heading })).toBeVisible();
    }

    const ownerNav = page.getByRole("navigation", { name: "Owner" });
    const home = ownerNav.getByLabel("Home", { exact: true });
    await expect(home).toHaveAttribute("aria-current", "page");
    await home.focus();
    expect(await home.evaluate((element) => getComputedStyle(element).outlineStyle)).not.toBe("none");

    const command = page.getByRole("button", { name: "Search / Command", exact: true });
    await expect(command).toContainText("Search / Command");
    await command.focus();
    expect(await command.evaluate((element) => getComputedStyle(element).outlineStyle)).not.toBe("none");
    await command.press("Enter");

    const palette = page.getByRole("dialog", { name: "Navigate AIOS" });
    await expect(palette).toBeVisible();
    const results = palette.getByRole("navigation", { name: "Navigation results" });
    await expect(results).toBeVisible();
    expect(await palette.getByRole("listbox").count()).toBe(0);
    expect(await palette.getByRole("option").count()).toBe(0);
    expect(await results.getByRole("link").count()).toBeGreaterThan(0);

    await page.keyboard.press("Escape");
    await expect(palette).toBeHidden();
    await expect(command).toBeFocused();

    const guide = page.getByRole("button", { name: "Open guided experience" });
    await guide.click();
    const guideDialog = page.getByRole("dialog", { name: "Guided experience" });
    await expect(guideDialog).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(guideDialog).toBeHidden();
    await expect(guide).toBeFocused();

    await expect(page.getByLabel("AIOS V2 theme")).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth && document.body.scrollWidth <= window.innerWidth)).toBe(true);
    expect(writes).toEqual([]);
    expect(pageErrors).toEqual([]);
  });
}
