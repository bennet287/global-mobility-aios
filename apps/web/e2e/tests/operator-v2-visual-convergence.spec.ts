import { mkdirSync } from "node:fs";
import { expect, test } from "@playwright/test";

const ARTIFACT_DIR = "operator-v2-artifacts";
const workspaceLabels = ["Work", "Profiles", "Pathways", "Evidence", "Communication", "Tools"] as const;

async function assertOperatorSurface(page: import("@playwright/test").Page) {
  await expect(page.getByRole("heading", { level: 1, name: "Run mobility work from one governed command surface." })).toBeVisible();
  await expect(page.getByText("Evidence-aware.", { exact: false })).toBeVisible();
  await expect(page.getByText("Human-controlled.", { exact: false })).toBeVisible();

  const navigation = page.getByRole("navigation", { name: "Professional / Operator" });
  for (const label of workspaceLabels) {
    await expect(navigation.getByLabel(label, { exact: true })).toBeVisible();
  }

  await expect(page.getByRole("link", { name: "Open current Work Home" })).toHaveAttribute("href", "/");
  await expect(page.getByRole("link", { name: "Browse specialist tools" })).toHaveAttribute("href", "/operator/v2/tools");
  await expect(page.getByRole("heading", { level: 2, name: "The professional operating model" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 2, name: "Reach specialist workflows without exposing module topology." })).toBeVisible();
  await expect(page.getByText("This surface changes organization, hierarchy, and discovery only.", { exact: false })).toBeVisible();

  expect(await page.getByText("Available", { exact: true }).count()).toBe(6);
  for (const label of workspaceLabels) {
    await expect(page.getByRole("link", { name: `Open ${label}`, exact: true })).toBeVisible();
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth && document.body.scrollWidth <= window.innerWidth)).toBe(true);
}

test("Operator V2 desktop visual convergence proof", async ({ page }) => {
  mkdirSync(ARTIFACT_DIR, { recursive: true });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/operator/v2", { waitUntil: "networkidle" });
  await assertOperatorSurface(page);
  await page.screenshot({
    path: `${ARTIFACT_DIR}/operator-v2-desktop.png`,
    fullPage: true,
    animations: "disabled",
  });
});

test("Operator V2 phone visual convergence proof", async ({ page }) => {
  mkdirSync(ARTIFACT_DIR, { recursive: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/operator/v2", { waitUntil: "networkidle" });
  await assertOperatorSurface(page);
  await page.screenshot({
    path: `${ARTIFACT_DIR}/operator-v2-phone.png`,
    fullPage: true,
    animations: "disabled",
  });
});

test("Operator V2 remains presentation-only and keyboard-operable", async ({ page }) => {
  const writes: string[] = [];
  page.on("request", (request) => {
    if (!["GET", "HEAD", "OPTIONS"].includes(request.method())) writes.push(`${request.method()} ${request.url()}`);
  });

  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto("/operator/v2");

  const primaryAction = page.getByRole("link", { name: "Open current Work Home" });
  await primaryAction.focus();
  expect(await primaryAction.evaluate((element) => getComputedStyle(element).outlineStyle)).not.toBe("none");
  expect(writes).toEqual([]);
});
