import { expect, test, type Page } from "@playwright/test";

async function unavailableApi(page: Page) {
  const writes: string[] = [];
  await page.route("http://127.0.0.1:8000/**", async (route) => {
    if (!["GET", "OPTIONS"].includes(route.request().method())) writes.push(route.request().method());
    await route.fulfill({ status: 503, headers: {
      "access-control-allow-origin": route.request().headers().origin || "http://127.0.0.1:3000",
      "access-control-allow-credentials": "true",
      "access-control-allow-headers": "content-type,x-gmai-role,x-gmai-user",
      "access-control-allow-methods": "GET,OPTIONS",
    }, contentType: "application/json", body: '{"detail":"Unavailable test fixture"}' });
  });
  return writes;
}

test("Owner navigation stays usable without data; collapse preserves accessible names", async ({ page }, testInfo) => {
  const writes = await unavailableApi(page);
  await page.goto("/cockpit/v2");
  const owner = page.getByRole("navigation", { name: "Owner", exact: true });
  await expect(owner.getByRole("link", { name: "Home", exact: true })).toHaveAttribute("aria-current", "page");
  await expect(page.getByText("Backend status unavailable", { exact: true })).toBeVisible();
  await expect(page.getByText("Attention could not be fully assessed.", { exact: true })).toBeVisible();
  await expect(page.getByText(/canonical zero state/)).toHaveCount(0);
  await expect(owner.getByRole("link")).toHaveCount(7);
  await page.getByRole("button", { name: "Collapse navigation", exact: true }).click();
  await expect(owner.getByRole("link", { name: "Organization", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Expand navigation", exact: true }).click();
  await page.screenshot({ path: testInfo.outputPath("owner-shell-desktop.png"), fullPage: true });
  await page.getByRole("link", { name: "Skip to main content" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("main")).toBeFocused();
  expect(writes).toEqual([]);
});

test("command navigation filters, handles empty results, restores focus and follows keyboard selection", async ({ page }) => {
  const writes = await unavailableApi(page);
  await page.goto("/cockpit/v2");
  const trigger = page.getByRole("button", { name: /Navigate AIOS/ });
  await trigger.click();
  const dialog = page.getByRole("dialog", { name: "Navigate AIOS" });
  const search = dialog.getByRole("searchbox", { name: "Find a workspace" });
  await expect(search).toBeFocused();
  await search.fill("no-such-workspace");
  await expect(dialog.getByText(/No matching destinations/)).toBeVisible();
  await expect(dialog.getByRole("link")).toHaveCount(0);
  await page.keyboard.press("Escape");
  await expect(dialog).not.toBeVisible();
  await expect(trigger).toBeFocused();
  await page.keyboard.press("Control+k");
  await expect(search).toBeFocused();
  await search.fill("organization rooms");
  await page.keyboard.press("ArrowDown");
  await expect(dialog.getByRole("link", { name: /Organization Workspace.*Living HQ/ })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/cockpit\/v2\/organization$/);
  await expect(page.getByRole("navigation", { name: "Owner", exact: true }).getByRole("link", { name: "Organization", exact: true })).toHaveAttribute("aria-current", "page");
  expect(writes).toEqual([]);
});

for (const width of [390, 768]) {
  test(`mobile/tablet navigation keeps labels and focus inside its modal at ${width}px`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width, height: 844 });
    await page.emulateMedia({ reducedMotion: "reduce" });
    const writes = await unavailableApi(page);
    await page.goto("/cockpit/v2");
    const trigger = page.getByRole("button", { name: "Open navigation", exact: true });
    await trigger.click();
    const dialog = page.getByRole("dialog", { name: "Owner navigation" });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByText("Intelligence", { exact: true })).toBeVisible();
    await expect(dialog.getByRole("navigation").getByRole("link")).toHaveCount(7);
    for (let index = 0; index < 8; index++) {
      await page.keyboard.press("Tab");
      expect(await dialog.evaluate((element) => element.contains(document.activeElement))).toBe(true);
    }
    await page.screenshot({ path: testInfo.outputPath(`owner-navigation-${width}.png`) });
    await page.keyboard.press("Escape");
    await expect(trigger).toBeFocused();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await page.screenshot({ path: testInfo.outputPath(`owner-shell-${width}.png`), fullPage: true });
    await trigger.click();
    await dialog.getByRole("link", { name: "Organization", exact: true }).click();
    await expect(page).toHaveURL(/\/cockpit\/v2\/organization$/);
    await expect(page.getByRole("dialog")).not.toBeVisible();
    expect(writes).toEqual([]);
  });
}
