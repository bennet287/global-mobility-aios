import { mkdirSync } from "node:fs";
import { expect, test, type Page } from "@playwright/test";

const ARTIFACT_DIR = "mobility-overview-artifacts";

async function prepare(page: Page) {
  await page.route("http://127.0.0.1:8000/health", async (route) => {
    await route.fulfill({
      status: 200,
      headers: {
        "access-control-allow-origin": "http://127.0.0.1:3000",
        "content-type": "application/json",
      },
      body: JSON.stringify({ status: "ok", environment: "visible-review" }),
    });
  });
  await page.goto("/my-mobility", { waitUntil: "networkidle" });
  await expect(page.getByRole("heading", { name: /Know where your case stands/i })).toBeVisible();
  await expect(page.getByRole("link", { name: "Open My Case" })).toHaveAttribute("href", "/portal");

  const navigation = page.getByRole("navigation", { name: "My Mobility V2 navigation" });
  await expect(navigation.getByRole("link", { name: /Documents/i })).toHaveAttribute("href", "/portal/documents");
  await expect(navigation.getByRole("link", { name: /Timeline/i })).toHaveAttribute("href", "/portal/timeline");
  await expect(navigation.getByRole("link", { name: /Messages/i })).toHaveAttribute("href", "/portal/messages");
  await expect(navigation.locator('[aria-disabled="true"]')).toHaveCount(0);
  await expect(page.getByText(/Secure client-safe communication surface available/)).toBeVisible();
  await expect(page.getByText(/communication history stays explicitly unavailable/i)).toBeVisible();
}

test("Mobility Overview desktop visible-review proof", async ({ page }) => {
  mkdirSync(ARTIFACT_DIR, { recursive: true });
  await page.setViewportSize({ width: 1440, height: 1100 });
  await prepare(page);
  await page.screenshot({ path: `${ARTIFACT_DIR}/mobility-overview-desktop.png`, fullPage: true, animations: "disabled" });
});

test("Mobility Overview phone visible-review proof", async ({ page }) => {
  mkdirSync(ARTIFACT_DIR, { recursive: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await prepare(page);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(1);
  await page.screenshot({ path: `${ARTIFACT_DIR}/mobility-overview-phone.png`, fullPage: true, animations: "disabled" });
});