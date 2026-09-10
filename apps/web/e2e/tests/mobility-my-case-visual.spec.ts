import { mkdirSync } from "node:fs";
import { expect, test, type Page } from "@playwright/test";

const ARTIFACT_DIR = "mobility-my-case-artifacts";

async function prepareSecureEntry(page: Page) {
  await page.addInitScript(() => {
    sessionStorage.removeItem("gmai-client-portal-token");
    sessionStorage.removeItem("gmai-client-portal-device");
  });
  await page.goto("/portal", { waitUntil: "networkidle" });
  await expect(page.getByRole("heading", { name: /Your mobility case/i })).toBeVisible();
  await expect(page.getByLabel("Access token")).toBeVisible();
  await expect(page.getByRole("button", { name: "Open secure workspace" })).toBeDisabled();
  await expect(page.getByText("No password, public case search, or personal-data lookup is used.")).toBeVisible();
  await expect(page.getByText("Encrypted transport", { exact: true })).toBeVisible();
  await expect(page.getByText("Expiring access", { exact: true })).toBeVisible();
  await expect(page.getByText("Audited activity", { exact: true })).toBeVisible();
}

test("Mobility My Case secure entry desktop visible-review proof", async ({ page }) => {
  mkdirSync(ARTIFACT_DIR, { recursive: true });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await prepareSecureEntry(page);
  await page.screenshot({
    path: `${ARTIFACT_DIR}/mobility-my-case-desktop.png`,
    fullPage: true,
    animations: "disabled",
  });
});

test("Mobility My Case secure entry phone visible-review proof", async ({ page }) => {
  mkdirSync(ARTIFACT_DIR, { recursive: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await prepareSecureEntry(page);
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(1);
  await page.screenshot({
    path: `${ARTIFACT_DIR}/mobility-my-case-phone.png`,
    fullPage: true,
    animations: "disabled",
  });
});

test("Mobility My Case permits user zoom", async ({ page }) => {
  await prepareSecureEntry(page);
  const viewport = page.locator('meta[name="viewport"]');
  await expect(viewport).toHaveAttribute("content", /width=device-width/);
  await expect(viewport).not.toHaveAttribute("content", /user-scalable=no/i);
  await expect(viewport).not.toHaveAttribute("content", /maximum-scale=1/i);
});
