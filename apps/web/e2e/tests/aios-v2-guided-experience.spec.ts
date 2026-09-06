import { expect, test } from "@playwright/test";

for (const width of [1280, 390]) test(`Q9 guided experience stays explicit and responsive at ${width}px`, async ({ page }) => {
  await page.setViewportSize({ width, height: 844 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  const writes: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));

  await page.route("http://127.0.0.1:8000/**", async (route) => {
    const request = route.request();
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
    if (request.method() !== "GET") writes.push(request.method());
    if (new URL(request.url()).pathname === "/health") {
      await route.fulfill({ status: 200, headers, contentType: "application/json", body: JSON.stringify({ status: "ok", service: "fixture", environment: "test" }) });
      return;
    }
    await route.fulfill({ status: 503, headers, contentType: "application/json", body: JSON.stringify({ detail: "Fixture source intentionally unavailable" }) });
  });

  await page.goto("/cockpit/v2");
  const trigger = page.getByRole("button", { name: "Open guided experience" });
  await expect(trigger).toBeVisible();
  await trigger.click();

  const guide = page.getByRole("dialog", { name: "Guided experience" });
  await expect(guide).toBeVisible();
  await expect(guide.getByText("Step 1 of 7 · Home", { exact: true })).toBeVisible();
  await expect(guide.getByText("You are here", { exact: true }).first()).toBeVisible();

  await guide.getByRole("button", { name: /Missions/ }).click();
  await expect(guide.getByRole("heading", { name: "Missions", level: 3 })).toBeVisible();
  await expect(guide.getByText("Selection is inspection only.", { exact: false })).toBeVisible();
  await expect(guide.getByRole("link", { name: "Open Missions" })).toHaveAttribute("href", "/cockpit/v2/missions");

  await guide.getByRole("button", { name: /Evidence/ }).click();
  await expect(guide.getByText("Reference presence does not prove source content", { exact: false })).toBeVisible();

  await guide.getByRole("button", { name: /History/ }).click();
  await expect(guide.getByText("Historical reconstruction is not current state", { exact: false })).toBeVisible();
  await expect(guide.getByRole("button", { name: "Finish" })).toBeVisible();

  await page.keyboard.press("Control+K");
  await expect(page.getByRole("dialog", { name: "Navigate AIOS" })).not.toBeVisible();
  await page.keyboard.press("Escape");
  await expect(guide).not.toBeVisible();
  await expect(trigger).toBeFocused();

  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth && document.body.scrollWidth <= window.innerWidth)).toBe(true);
  expect(writes).toEqual([]);
  expect(pageErrors).toEqual([]);
});
